import sqlite3

from config import art_ping_config

CONFIG = art_ping_config.readConfig()

def getIds(data):
    result = []
    for row in data:
        result.append(row[0])
    return result

def getDatabaseConnection():
    return sqlite3.connect(CONFIG.get('database', 'path'))