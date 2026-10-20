import sqlite3

from fjormcord.bot.artping import config

CONFIG = config.read_config()


def get_ids(data):
    result = []
    for row in data:
        result.append(row[0])
    return result


def get_database_connection():
    return sqlite3.connect(config.resolve_path(CONFIG.get('database', 'path')))
