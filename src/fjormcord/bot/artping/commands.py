from dataclasses import dataclass
from typing import Callable

import discord

from fjormcord.bot.artping.service.alias_service import add_alias, remove_alias
from fjormcord.bot.artping.service.art_ping_service import do_art_ping, add_ping, remove_ping, check_ping
from fjormcord.bot.artping.service.character_service import add_character, remove_character, check_character
from fjormcord.bot.artping.service.currency_service import add_currency, remove_currency, set_currency, clear_currency, \
    check_wallet, get_scoreboard

COMMAND_PREFIX = "~"

MESSAGE_DENIED = "You do not have the permissions for this command"

SECTION_ART_PING = ""
SECTION_CURRENCY = "Gacha Currency Commands:"
SECTION_ADMIN = "Admin Commands:"


@dataclass(frozen=True)
class Command:
    name: str
    # Called as handler(client, message); returns the reply, either directly or as a coroutine
    handler: Callable
    description: str
    usage: str = ""
    section: str = SECTION_ART_PING
    admin_only: bool = False


def is_administrator(author):
    # Users in DMs have no guild permissions
    permissions = getattr(author, 'guild_permissions', None)
    return permissions is not None and permissions.administrator


def show_help(client: discord.Client, message: discord.Message):
    show_admin = is_administrator(message.author)
    out = 'Commands (content in brackets is what to add when using command):\n'

    current_section = SECTION_ART_PING
    for command in COMMANDS:
        if command.admin_only and not show_admin:
            continue

        section = SECTION_ADMIN if command.admin_only else command.section
        if section != current_section:
            out += f'\n{section}\n'
            current_section = section

        usage = f' ({command.usage})' if command.usage else ''
        out += f'{command.name}{usage}: {command.description}\n'

    return out


# TODO: consider migrating to discord.ext.commands (Bot + Cogs). It would give quoted multi-word arguments,
#  typed argument conversion, permission check decorators and a path to slash commands, but changes how
#  missing/invalid arguments, permission denials, unknown commands and ~help are answered.
# Commands are listed in ~help order; keep each section together and admin-only commands last.
COMMANDS = [
    Command("~artping", do_art_ping, "Ping users for art of this character", "character name"),
    Command("~addping", add_ping, "Call to add yourself to the ping list when this character is pinged",
            "character name"),
    Command("~removeping", remove_ping, "Remove yourself from the ping list of this character", "character name"),
    Command("~checkping", check_ping, "See which characters you are being pinged for"),
    Command("~checkcharacter", check_character, "See which users are pinged for this character", "character name"),
    Command("~help", show_help, "Shows this overview of all the available commands"),

    Command("~setcurrency", set_currency,
            "Set the number of orbs, primos or any other currency that you have", "currency name) (amount",
            SECTION_CURRENCY),
    Command("~clearcurrency", clear_currency, "Clears the number you have saved for that particular currency",
            "currency name", SECTION_CURRENCY),
    Command("~checkwallet", check_wallet, "Shows a list of all currencies you have and their count",
            section=SECTION_CURRENCY),
    Command("~scoreboard", get_scoreboard, "Shows a leaderboard of the specified currency", "currency name",
            SECTION_CURRENCY),

    Command("~addcharacter", add_character, "Add a character that users can be pinged for", "character name",
            admin_only=True),
    Command("~removecharacter", remove_character, "Remove a character and unsubscribe all its users",
            "character name", admin_only=True),
    Command("~addalias", add_alias, "Add an alias to a character", "character name) (alias", admin_only=True),
    Command("~removealias", remove_alias, "Remove an alias from a character", "character name) (alias",
            admin_only=True),
    Command("~addcurrency", add_currency, "Add a currency that users can track", "currency name", admin_only=True),
    Command("~removecurrency", remove_currency, "Remove a currency and clear it from all wallets", "currency name",
            admin_only=True),
]

COMMANDS_BY_NAME = {command.name: command for command in COMMANDS}
