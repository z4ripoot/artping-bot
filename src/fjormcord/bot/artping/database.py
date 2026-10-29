import logging
import sqlite3
from collections.abc import Callable, Sequence
from pathlib import Path
from typing import Any, TypeVar

from fjormcord.bot.artping import config
from fjormcord.bot.artping.util.name_util import normalize_name

Model = TypeVar("Model")

# Numbered scripts (001_initial_schema.sql, ...); a database's user_version is the number of the last one applied to it
MIGRATIONS_PATH = config.PROJECT_ROOT / "db" / "migrations"

_connection: sqlite3.Connection | None = None


def get_database_connection() -> sqlite3.Connection:
    if _connection is None:
        set_database_connection(connect(config.read_settings().database_path))
    return _connection


def execute(sql: str, parameters: Sequence = ()):
    # A single write, committed on its own
    with get_database_connection() as conn:
        conn.execute(sql, parameters)


def exists(sql: str, parameters: Sequence = ()) -> bool:
    # Whether the query finds a row
    return get_database_connection().execute(sql, parameters).fetchone() is not None


def fetch_one(model: Callable[..., Model], sql: str, parameters: Sequence = ()) -> Model | None:
    # The row found as a model, its columns aliased to the model's fields; None when there is none
    row = get_database_connection().execute(sql, parameters).fetchone()
    return model(**row) if row else None


def fetch_all(model: Callable[..., Model], sql: str, parameters: Sequence = ()) -> list[Model]:
    # Every row found as a model, its columns aliased to the model's fields
    return [model(**row) for row in get_database_connection().execute(sql, parameters)]


def fetch_column(sql: str, parameters: Sequence = ()) -> list[Any]:
    # The values of a query that selects one column
    return [value for (value,) in get_database_connection().execute(sql, parameters)]


def fetch_value(sql: str, parameters: Sequence = ()) -> Any:
    # The first column of the first row found; None when there is none
    row = get_database_connection().execute(sql, parameters).fetchone()
    return row[0] if row else None


def fetch_names(names_sql: str, prefix: str = "", limit: int = -1, parameters: Sequence = ()) -> list[str]:
    # The names selected by names_sql, a query of one column with parameters, that start with prefix, ignoring case,
    # in alphabetical order; a limit of -1 means no limit
    sql = f"""
        SELECT N.NAME
        FROM ({names_sql}) N
        WHERE SUBSTR(N.NAME, 1, LENGTH(?)) = ? COLLATE NOCASE
        ORDER BY N.NAME COLLATE NOCASE
        LIMIT ?
        """

    return fetch_column(sql, (*parameters, prefix, prefix, limit))


def connect(path: str | Path) -> sqlite3.Connection:
    connection = sqlite3.connect(path)
    # Lets migrations normalize names the same way the commands do
    connection.create_function("NORMALIZE_NAME", 1, normalize_name, deterministic=True)
    # Runs before foreign keys are enabled: rebuilding a table would otherwise cascade-delete the rows referencing it
    migrate(connection)
    return connection


def migrate(connection: sqlite3.Connection):
    # A new database and one created before versioning are both at 0; 001 only creates tables that don't exist yet
    version = connection.execute("PRAGMA user_version").fetchone()[0]
    migrations = {int(path.name.split("_")[0]): path for path in MIGRATIONS_PATH.glob("*.sql")}

    # E.g. a development database that ran migrations which were later merged into fewer: it would skip new ones
    if version > max(migrations):
        raise sqlite3.DatabaseError(
            f"The database is at version {version}, but the latest migration is {max(migrations)}. "
            "Delete a development database to recreate it"
        )

    for number, path in sorted(migrations.items()):
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


def set_database_connection(connection: sqlite3.Connection):
    global _connection
    connection.row_factory = sqlite3.Row
    # SQLite only enforces foreign keys (and their ON DELETE CASCADE) when enabled per connection
    connection.execute("PRAGMA foreign_keys = ON")
    _connection = connection
