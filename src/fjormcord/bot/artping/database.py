import logging
import sqlite3

from fjormcord.bot.artping import config
from fjormcord.bot.artping.util.name_util import normalize_name

# Numbered scripts (001_initial_schema.sql, ...); a database's user_version is the number of the last one applied to it
MIGRATIONS_PATH = config.PROJECT_ROOT / 'db' / 'migrations'

_connection = None


def get_database_connection():
    if _connection is None:
        set_database_connection(connect(config.read_settings().database_path))
    return _connection


def connect(path):
    connection = sqlite3.connect(path)
    # Lets migrations normalize names the same way the commands do
    connection.create_function("NORMALIZE_NAME", 1, normalize_name, deterministic=True)
    # Runs before foreign keys are enabled: rebuilding a table would otherwise cascade-delete the rows referencing it
    migrate(connection)
    return connection


def migrate(connection):
    # A new database and one created before versioning are both at 0; 001 only creates tables that don't exist yet
    version = connection.execute("PRAGMA user_version").fetchone()[0]

    for path in sorted(MIGRATIONS_PATH.glob('*.sql')):
        number = int(path.name.split('_')[0])
        if number <= version:
            continue

        logging.info("Applying database migration %s", path.name)
        try:
            # Each migration and its version bump are applied together or not at all
            connection.executescript(f"BEGIN;\n{path.read_text(encoding='utf-8')}\nPRAGMA user_version = {number};")
            violations = connection.execute("PRAGMA foreign_key_check").fetchall()
            if violations:
                raise sqlite3.IntegrityError(f"Migration {path.name} leaves broken foreign keys: {violations}")
            connection.commit()
        except Exception:
            logging.exception("Database migration %s failed and was rolled back", path.name)
            connection.rollback()
            raise


def set_database_connection(connection):
    global _connection
    connection.row_factory = sqlite3.Row
    # SQLite only enforces foreign keys (and their ON DELETE CASCADE) when enabled per connection
    connection.execute("PRAGMA foreign_keys = ON")
    _connection = connection
