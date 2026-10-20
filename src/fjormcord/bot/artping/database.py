import sqlite3

from fjormcord.bot.artping import config

_connection = None


def get_ids(data):
    result = []
    for row in data:
        result.append(row[0])
    return result


def get_database_connection():
    if _connection is None:
        path = config.read_config().get('database', 'path')
        set_database_connection(sqlite3.connect(config.resolve_path(path)))
    return _connection


def set_database_connection(connection):
    global _connection
    _connection = connection
