from dataclasses import dataclass
from typing import Awaitable, Callable

import discord

from fjormcord.bot.artping import config
from fjormcord.bot.artping.service.alias_service import add_alias, remove_alias, set_primary_name
from fjormcord.bot.artping.service.art_ping_service import do_art_ping, add_ping, remove_ping, check_ping
from fjormcord.bot.artping.service.character_service import add_character, remove_character, check_character
from fjormcord.bot.artping.service.currency_service import add_currency, remove_currency, set_currency, \
    clear_currency, check_wallet, get_scoreboard
from fjormcord.bot.artping.util.message_util import MULTI_WORD_HINT
from fjormcord.bot.artping.util.user_util import is_administrator

COMMAND_PREFIX = "~"

SECTION_ART_PING = ""
SECTION_CURRENCY = "Gacha Currency Commands:"
SECTION_ADMIN = "Admin Commands:"

# Called as handler(client, message); returns the reply, either directly or as a coroutine
Handler = Callable[[discord.Client, discord.Message], str | Awaitable[str]]


@dataclass(frozen=True)
class Command:
    name: str
    handler: Handler
    description: str
    # The arguments, in order, e.g. ("currency name", "amount")
    usage: tuple[str, ...] = ()
    section: str = SECTION_ART_PING
    admin_only: bool = False
    # Seconds a user has to wait before using the command again, except admins; 0 means no cooldown
    cooldown_seconds: float = 0


def format_usage(command):
    # ~setcurrency (currency name) (amount)
    return " ".join([command.name] + [f"({argument})" for argument in command.usage])


def show_help(client: discord.Client, message: discord.Message) -> str:
    show_admin = is_administrator(message.author)
    out = 'Commands (content in brackets is what to add when using command):\n'
    out += f'{MULTI_WORD_HINT}\n'

    current_section = SECTION_ART_PING
    for command in COMMANDS:
        if command.admin_only and not show_admin:
            continue

        section = SECTION_ADMIN if command.admin_only else command.section
        if section != current_section:
            out += f'\n{section}\n'
            current_section = section

        out += f'{format_usage(command)}: {command.description}\n'

    return out


# TODO: consider migrating to discord.ext.commands (Bot + Cogs). It would give quoted multi-word arguments,
#  typed argument conversion, permission check decorators and a path to slash commands, but changes how
#  missing/invalid arguments, permission denials, unknown commands and ~help are answered.
# Commands are listed in ~help order; keep each section together and admin-only commands last.
COMMANDS = [
    Command("~artping", do_art_ping, "Ping users for art of this character", usage=("character name",),
            cooldown_seconds=config.read_settings().art_ping_cooldown_seconds),
    Command("~addping", add_ping, "Call to add yourself to the ping list when this character is pinged",
            usage=("character name",)),
    Command("~removeping", remove_ping, "Remove yourself from the ping list of this character",
            usage=("character name",)),
    Command("~checkping", check_ping, "See which characters you are being pinged for"),
    Command("~addcharacter", add_character,
            "Add a character that users can be pinged for; for non-admins this starts a vote, and everyone who "
            "votes is subscribed once it passes", usage=("character name",)),
    Command("~checkcharacter", check_character, "See which users are pinged for this character",
            usage=("character name",)),
    Command("~help", show_help, "Shows this overview of all the available commands"),

    Command("~setcurrency", set_currency, "Set the number of orbs, primos or any other currency that you have",
            usage=("currency name", "amount"), section=SECTION_CURRENCY),
    Command("~clearcurrency", clear_currency, "Clears the number you have saved for that particular currency",
            usage=("currency name",), section=SECTION_CURRENCY),
    Command("~checkwallet", check_wallet, "Shows a list of all currencies you have and their count",
            section=SECTION_CURRENCY),
    Command("~scoreboard", get_scoreboard, "Shows a leaderboard of the specified currency, 10 users per page",
            usage=("currency name", "optional page number"), section=SECTION_CURRENCY),

    Command("~removecharacter", remove_character, "Remove a character and unsubscribe all its users",
            usage=("character name",), admin_only=True),
    Command("~addalias", add_alias, "Add an alias to a character", usage=("character name", "alias"),
            admin_only=True),
    Command("~removealias", remove_alias, "Remove an alias from a character", usage=("character name", "alias"),
            admin_only=True),
    Command("~setprimaryname", set_primary_name, "Make an alias the character's name; the old name becomes an alias",
            usage=("alias",), admin_only=True),
    Command("~addcurrency", add_currency, "Add a currency that users can track", usage=("currency name",),
            admin_only=True),
    Command("~removecurrency", remove_currency, "Remove a currency and clear it from all wallets",
            usage=("currency name",), admin_only=True),
]

COMMANDS_BY_NAME = {command.name: command for command in COMMANDS}
