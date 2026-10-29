import configparser
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path

# src/fjormcord/bot/artping/config.py -> repository root, where config.ini lives
PROJECT_ROOT = Path(__file__).resolve().parents[4]

# The only file read; not committed, as it holds the token. config.example.ini, which is committed, shows what it holds
CONFIG_FILE = PROJECT_ROOT / "config.ini"
EXAMPLE_CONFIG_FILE = PROJECT_ROOT / "config.example.ini"

# Discord allows at most 25 options per slash command, and shows at most 25 autocomplete choices
MAX_SLASH_OPTIONS = 25
MAX_AUTOCOMPLETE_CHOICES = 25


@dataclass(frozen=True)
class Settings:
    # Empty when no token is configured
    discord_token: str
    # None syncs the slash commands globally instead of to one server
    guild_id: int | None
    database_path: Path
    # Seconds a user has to wait after a command before using another one, except admins; 0 means no cooldown
    cooldown_seconds: float
    # How many names an autocomplete offers at most, between 1 and MAX_AUTOCOMPLETE_CHOICES
    autocomplete_max_choices: int
    # None disables the Coliseum reminders
    coliseum_channel_id: int | None
    # None disables the hourly Voting Gauntlet scores
    voting_gauntlet_channel_id: int | None
    # How many characters the /artping command takes, between 1 and MAX_SLASH_OPTIONS
    art_ping_slash_max_characters: int
    # Votes a non-admin's addcharacter vote needs before the character is added; below 2 there are no votes
    character_votes_needed: int
    # The Vote button's emoji, and the reaction that counted as a vote before the button, for converting those votes;
    # str() of a Discord emoji: the Unicode character or <:name:id>
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
    if not config.read(path, encoding="utf-8-sig"):
        raise FileNotFoundError(f"{path} not found. Copy config.example.ini to config.ini and fill in your bot's token")

    guild_id = config.get("discord", "guild_id")
    channel_id = config.get("tasks", "coliseum_notification_channel_id")
    voting_gauntlet_channel_id = config.get("tasks", "voting_gauntlet_channel_id")
    return Settings(
        discord_token=config.get("discord", "token"),
        guild_id=int(guild_id) if guild_id else None,
        # Relative paths are relative to the directory of the config file, not the working directory
        database_path=path.parent / config.get("database", "path"),
        cooldown_seconds=config.getfloat("commands", "cooldown_seconds"),
        autocomplete_max_choices=_get_between(config, "commands", "autocomplete_max_choices", MAX_AUTOCOMPLETE_CHOICES),
        coliseum_channel_id=int(channel_id) if channel_id else None,
        voting_gauntlet_channel_id=int(voting_gauntlet_channel_id) if voting_gauntlet_channel_id else None,
        art_ping_slash_max_characters=_get_between(config, "art_ping", "slash_max_characters", MAX_SLASH_OPTIONS),
        character_votes_needed=config.getint("character_vote", "votes_needed"),
        character_vote_emoji=config.get("character_vote", "emoji"),
        emoji=dict(config["emoji"]),
    )


def _get_between(config: configparser.ConfigParser, section: str, key: str, maximum: int) -> int:
    value = config.getint(section, key)
    if not 1 <= value <= maximum:
        raise ValueError(f"{section}.{key} must be between 1 and {maximum}")
    return value
