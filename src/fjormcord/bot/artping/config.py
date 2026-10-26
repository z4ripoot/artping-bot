import configparser
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path

# src/fjormcord/bot/artping/config.py -> repository root, where config.ini lives
PROJECT_ROOT = Path(__file__).resolve().parents[4]

# The committed example holds the defaults; config.ini (not committed) overrides them and holds the token
CONFIG_FILES = ('config.example.ini', 'config.ini')

# Discord allows at most 25 options per slash command
MAX_SLASH_OPTIONS = 25


@dataclass(frozen=True)
class Settings:
    # Empty when no token is configured
    discord_token: str
    # None syncs the slash commands globally instead of to one server
    guild_id: int | None
    database_path: Path
    art_ping_cooldown_seconds: float
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
        _settings = load_settings(PROJECT_ROOT)
    return _settings


def load_settings(directory: Path) -> Settings:
    # Every setting has a default in config.example.ini, so a missing one stops the bot at startup
    config = configparser.ConfigParser()
    # Later files override earlier ones; missing files are skipped
    # utf-8-sig also reads a file saved with a byte order mark, as Notepad may do
    config.read([directory / name for name in CONFIG_FILES], encoding='utf-8-sig')

    guild_id = config.get('discord', 'guild_id')
    channel_id = config.get('tasks', 'coliseum_notification_channel_id')
    slash_max_characters = config.getint('art_ping', 'slash_max_characters')
    if not 1 <= slash_max_characters <= MAX_SLASH_OPTIONS:
        raise ValueError(f"art_ping.slash_max_characters must be between 1 and {MAX_SLASH_OPTIONS}")
    return Settings(
        discord_token=config.get('discord', 'token'),
        guild_id=int(guild_id) if guild_id else None,
        # Relative paths are relative to the directory of the config files, not the working directory
        database_path=directory / config.get('database', 'path'),
        art_ping_cooldown_seconds=config.getfloat('art_ping', 'cooldown_seconds'),
        coliseum_channel_id=int(channel_id) if channel_id else None,
        art_ping_slash_max_characters=slash_max_characters,
        character_votes_needed=config.getint('character_vote', 'votes_needed'),
        character_vote_emoji=config.get('character_vote', 'emoji'),
        emoji=dict(config['emoji']),
    )
