import logging
import sqlite3
from collections.abc import Callable
from typing import TypeVar

from fjormcord.bot.artping import config
from fjormcord.bot.artping.util.name_util import normalize_name

Model = TypeVar("Model")

# Numbered scripts (001_initial_schema.sql, ...); a database's user_version is the number of the last one applied to it
MIGRATIONS_PATH = config.PROJECT_ROOT / 'db' / 'migrations'

_connection = None


def get_database_connection():
    if _connection is None:
        set_database_connection(connect(config.read_settings().database_path))
    return _connection


def execute(sql, parameters=()):
    # A single write, committed on its own
    with get_database_connection() as conn:
        conn.execute(sql, parameters)


def exists(sql, parameters=()) -> bool:
    # Whether the query finds a row
    return get_database_connection().execute(sql, parameters).fetchone() is not None


def fetch_one(model: Callable[..., Model], sql, parameters=()) -> Model | None:
    # The row found as a model, its columns aliased to the model's fields; None when there is none
    row = get_database_connection().execute(sql, parameters).fetchone()
    return model(**row) if row else None


def fetch_all(model: Callable[..., Model], sql, parameters=()) -> list[Model]:
    # Every row found as a model, its columns aliased to the model's fields
    return [model(**row) for row in get_database_connection().execute(sql, parameters)]


def fetch_column(sql, parameters=()) -> list:
    # The values of a query that selects one column
    return [value for (value,) in get_database_connection().execute(sql, parameters)]


def fetch_value(sql, parameters=()):
    # The first column of the first row found; None when there is none
    row = get_database_connection().execute(sql, parameters).fetchone()
    return row[0] if row else None


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
