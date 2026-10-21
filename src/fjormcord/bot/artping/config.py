import configparser
from pathlib import Path

# src/fjormcord/bot/artping/config.py -> repository root, where config.ini lives
PROJECT_ROOT = Path(__file__).resolve().parents[4]

# The committed example holds the defaults; config.ini (not committed) overrides them and holds the token
CONFIG_FILES = ('config.example.ini', 'config.ini')

_config = None


def read_config():
    global _config
    if _config is None:
        _config = load_config(PROJECT_ROOT)
    return _config


def load_config(directory):
    config = configparser.ConfigParser()
    # Later files override earlier ones; missing files are skipped
    config.read([Path(directory) / name for name in CONFIG_FILES])
    return config


def resolve_path(path):
    # Relative paths in config.ini are relative to the project root, not the working directory
    return PROJECT_ROOT / path
