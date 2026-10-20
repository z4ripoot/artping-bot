import configparser
from pathlib import Path

# src/fjormcord/bot/artping/config.py -> repository root, where config.ini lives
PROJECT_ROOT = Path(__file__).resolve().parents[4]

_config = None


def read_config():
    global _config
    if _config is None:
        _config = configparser.ConfigParser()
        _config.read(PROJECT_ROOT / 'config.ini')
    return _config


def resolve_path(path):
    # Relative paths in config.ini are relative to the project root, not the working directory
    return PROJECT_ROOT / path
