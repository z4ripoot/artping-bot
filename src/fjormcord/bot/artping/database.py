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


def migrate(connection: sqlite3.Connection):
    version = connection.execute("PRAGMA user_version").fetchone()[0]
    migrations = {int(path.name.split("_")[0]): path for path in MIGRATIONS_PATH.glob("*.sql")}

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
            connection.executescript(f"BEGIN;\n{path.read_text(encoding='utf-8')}\nPRAGMA user_version = {number};")
            violations = connection.execute("PRAGMA foreign_key_check").fetchall()
            if violations:
                raise sqlite3.IntegrityError(f"Migration {path.name} leaves broken foreign keys: {violations}")
            connection.commit()
        except Exception:
            logging.exception("Database migration %s failed and was rolled back", path.name)
            connection.rollback()
            raise


def connect(path: str | Path) -> sqlite3.Connection:
    connection = sqlite3.connect(path)
    connection.create_function("NORMALIZE_NAME", 1, normalize_name, deterministic=True)
    migrate(connection)
    return connection


def set_database_connection(connection: sqlite3.Connection):
    global _connection
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    _connection = connection


def get_database_connection() -> sqlite3.Connection:
    if _connection is None:
        set_database_connection(connect(config.read_settings().database_path))
    return _connection


def execute(sql: str, parameters: Sequence = ()):
    with get_database_connection() as conn:
        conn.execute(sql, parameters)


def _fetch_one(sql: str, parameters: Sequence) -> Any:
    return get_database_connection().execute(sql, parameters).fetchone()


def exists(sql: str, parameters: Sequence = ()) -> bool:
    return _fetch_one(sql, parameters) is not None


def fetch_one(model: Callable[..., Model], sql: str, parameters: Sequence = ()) -> Model | None:
    row = _fetch_one(sql, parameters)
    return model(**row) if row else None


def fetch_all(model: Callable[..., Model], sql: str, parameters: Sequence = ()) -> list[Model]:
    return [model(**row) for row in get_database_connection().execute(sql, parameters)]


def fetch_column(sql: str, parameters: Sequence = ()) -> list[Any]:
    return [value for (value,) in get_database_connection().execute(sql, parameters)]


def fetch_value(sql: str, parameters: Sequence = ()) -> Any:
    row = _fetch_one(sql, parameters)
    return row[0] if row else None


def fetch_names(names_sql: str, prefix: str = "", limit: int = -1, parameters: Sequence = ()) -> list[str]:
    sql = f"""
        SELECT N.NAME
        FROM ({names_sql}) N
        WHERE SUBSTR(N.NAME, 1, LENGTH(?)) = ? COLLATE NOCASE
        ORDER BY N.NAME COLLATE NOCASE
        LIMIT ?
        """

    return fetch_column(sql, (*parameters, prefix, prefix, limit))
