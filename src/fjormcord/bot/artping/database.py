import sqlite3

from fjormcord.bot.artping import config

_connection = None


def get_database_connection():
    if _connection is None:
        path = config.read_config().get('database', 'path')
        set_database_connection(sqlite3.connect(config.resolve_path(path)))
    return _connection


def set_database_connection(connection):
    global _connection
    connection.row_factory = sqlite3.Row
    # SQLite only enforces foreign keys (and their ON DELETE CASCADE) when enabled per connection
    connection.execute("PRAGMA foreign_keys = ON")
    _connection = connection
