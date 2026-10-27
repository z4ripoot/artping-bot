import configparser
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path

# src/fjormcord/bot/artping/config.py -> repository root, where config.ini lives
PROJECT_ROOT = Path(__file__).resolve().parents[4]

# The only file read; not committed, as it holds the token. config.example.ini, which is committed, shows what it holds
CONFIG_FILE = PROJECT_ROOT / 'config.ini'
EXAMPLE_CONFIG_FILE = PROJECT_ROOT / 'config.example.ini'

# Discord allows at most 25 options per slash command
MAX_SLASH_OPTIONS = 25


@dataclass(frozen=True)
class Settings:
    # Empty when no token is configured
    discord_token: str
    # None syncs the slash commands globally instead of to one server
    guild_id: int | None
    database_path: Path
    # Seconds a user has to wait after a command before using another one, except admins; 0 means no cooldown
    cooldown_seconds: float
    # None disables the Coliseum reminders
    coliseum_channel_id: int | None
    # How many characters the /artping command takes, between 1 and MAX_SLASH_OPTIONS
    art_ping_slash_max_characters: int
    # Reactions a non-admin's ~addcharacter vote needs before the character is added; below 2 there are no votes
    character_votes_needed: int
    # The emoji that counts as a vote, as str() of a Discord emoji: the Unicode character or <:name:id>
    character_vote_emoji: str
    # Name -> custom emoji, e.g. 'lorenz_smile' -> '<:LorenzSmile:...>'
    emoji: Mapping[str, str]


_settings = None


def read_settings() -> Settings:
    global _settings
    if _settings is None:
        _settings = load_settings(CONFIG_FILE)
    return _settings


def load_settings(path: Path) -> Settings:
    # There are no defaults: the file holds every setting, and a missing one stops the bot at startup
    config = configparser.ConfigParser()
    # utf-8-sig also reads a file saved with a byte order mark, as Notepad may do
    if not config.read(path, encoding='utf-8-sig'):
        raise FileNotFoundError(f"{path} not found. Copy config.example.ini to config.ini and fill in your bot's token")

    guild_id = config.get('discord', 'guild_id')
    channel_id = config.get('tasks', 'coliseum_notification_channel_id')
    slash_max_characters = config.getint('art_ping', 'slash_max_characters')
    if not 1 <= slash_max_characters <= MAX_SLASH_OPTIONS:
        raise ValueError(f"art_ping.slash_max_characters must be between 1 and {MAX_SLASH_OPTIONS}")
    return Settings(
        discord_token=config.get('discord', 'token'),
        guild_id=int(guild_id) if guild_id else None,
        # Relative paths are relative to the directory of the config file, not the working directory
        database_path=path.parent / config.get('database', 'path'),
        cooldown_seconds=config.getfloat('commands', 'cooldown_seconds'),
        coliseum_channel_id=int(channel_id) if channel_id else None,
        art_ping_slash_max_characters=slash_max_characters,
        character_votes_needed=config.getint('character_vote', 'votes_needed'),
        character_vote_emoji=config.get('character_vote', 'emoji'),
        emoji=dict(config['emoji']),
    )
