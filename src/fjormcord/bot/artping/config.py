import configparser

_config = None


def read_config():
    global _config
    if _config is None:
        _config = configparser.ConfigParser()
        _config.read('config.ini')
    return _config
