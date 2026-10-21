import sqlite3
from pathlib import Path

from fjormcord.bot.artping import config

SCHEMA_PATH = config.PROJECT_ROOT / 'db' / 'schema.sql'

_connection = None


def get_database_connection():
    if _connection is None:
        path = config.read_config().get('database', 'path')
        set_database_connection(connect(config.resolve_path(path)))
    return _connection


def connect(path):
    # A database that doesn't exist yet is created with the schema, so a fresh checkout needs no manual setup
    is_new = not Path(path).exists()
    connection = sqlite3.connect(path)
    if is_new:
        connection.executescript(SCHEMA_PATH.read_text())
    return connection


def set_database_connection(connection):
    global _connection
    connection.row_factory = sqlite3.Row
    # SQLite only enforces foreign keys (and their ON DELETE CASCADE) when enabled per connection
    connection.execute("PRAGMA foreign_keys = ON")
    _connection = connection
