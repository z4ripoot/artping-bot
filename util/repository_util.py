import configparser
import sqlite3

config = configparser.ConfigParser()
config.read('config.ini')

def getIds(data):
    result = []
    for row in data:
        result.append(row[0])
    return result

def getDatabaseConnection():
    return sqlite3.connect(config.get('database', 'path'))