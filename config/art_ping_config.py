import configparser

def readConfig():
    config = configparser.ConfigParser()
    config.read('config.ini')
    return config