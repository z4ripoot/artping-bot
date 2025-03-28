import sqlite3

from config import art_ping_config

CONFIG = art_ping_config.read_config()


def get_ids(data):
    result = []
    for row in data:
        result.append(row[0])
    return result


def get_database_connection():
    return sqlite3.connect(CONFIG.get('database', 'path'))
