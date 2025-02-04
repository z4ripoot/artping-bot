import configparser
import sqlite3

CONFIG = configparser.ConfigParser()
CONFIG.read('config.ini')

def getIds(data):
    result = []
    for row in data:
        result.append(row[0])
    return result

def getDatabaseConnection():
    return sqlite3.connect(CONFIG.get('database', 'path'))