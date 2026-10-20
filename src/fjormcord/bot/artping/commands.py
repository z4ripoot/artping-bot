from dataclasses import dataclass
from typing import Callable

import discord

from fjormcord.bot.artping.service.alias_service import add_alias, remove_alias
from fjormcord.bot.artping.service.art_ping_service import do_art_ping, add_ping, remove_ping, check_ping
from fjormcord.bot.artping.service.character_service import add_character_ping, remove_character, check_character
from fjormcord.bot.artping.service.currency_service import add_currency, remove_currency, set_currency, clear_currency, \
    check_wallet, get_scoreboard

COMMAND_PREFIX = "~"

MESSAGE_DENIED = "You do not have the permissions for this command"


@dataclass(frozen=True)
class Command:
    name: str
    # Called as handler(client, message); returns the reply, either directly or as a coroutine
    handler: Callable
    admin_only: bool = False


def is_administrator(author):
    return author.guild_permissions.administrator


def show_help(client: discord.Client, message: discord.Message):
    return 'Commands (content in brackets is what to add when using command):\n' \
        + '~artping (character name): Ping users for art of this character \n' \
        + '~addping (character name): Call to add yourself to the ping list when this character is pinged \n' \
        + '~removeping (character name): Remove yourself from the ping list of this character \n' \
        + '~checkping: See which characters you are being pinged for \n' \
        + '~checkcharacter (character name): See which users are pinged for this character \n' \
        + '\n' \
        + 'Gacha Currency Commands:\n' \
        + '~setcurrency (currency name) (amount): Set the number of orbs, primos or any other currency that you have\n' \
        + '~clearcurrency (currency name): Clears the number you have saved for that particular currency\n' \
        + '~checkwallet: Shows a list of all currencies you have and their count\n' \
        + '~scoreboard (currency name): Shows a leaderboard of the specified currency\n'


# TODO: consider migrating to discord.ext.commands (Bot + Cogs). It would give quoted multi-word arguments,
#  typed argument conversion, permission check decorators and a path to slash commands, but changes how
#  missing/invalid arguments, permission denials, unknown commands and ~help are answered.
COMMANDS = [
    Command("~artping", do_art_ping),
    Command("~addping", add_ping),
    Command("~removeping", remove_ping),
    Command("~checkping", check_ping),
    Command("~checkcharacter", check_character),
    Command("~help", show_help),

    Command("~setcurrency", set_currency),
    Command("~clearcurrency", clear_currency),
    Command("~checkwallet", check_wallet),
    Command("~scoreboard", get_scoreboard),

    Command("~addcharacter", add_character_ping, admin_only=True),
    Command("~removecharacter", remove_character, admin_only=True),
    Command("~addalias", add_alias, admin_only=True),
    Command("~removealias", remove_alias, admin_only=True),
    Command("~addcurrency", add_currency, admin_only=True),
    Command("~removecurrency", remove_currency, admin_only=True),
]

COMMANDS_BY_NAME = {command.name: command for command in COMMANDS}
