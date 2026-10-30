from collections.abc import Awaitable, Callable, Iterable
from dataclasses import dataclass

import discord

from fjormcord.bot.artping.legacy.handler.alias_handlers import add_alias, remove_alias, set_primary_name
from fjormcord.bot.artping.legacy.handler.art_ping_handlers import add_ping, check_ping, do_art_ping, remove_ping
from fjormcord.bot.artping.legacy.handler.character_handlers import add_character, check_character, remove_character
from fjormcord.bot.artping.legacy.handler.currency_handlers import (
    add_currency,
    check_wallet,
    clear_currency,
    get_scoreboard,
    remove_currency,
    set_currency,
)
from fjormcord.bot.artping.legacy.handler.resource_handlers import list_resources, remove_resource, set_resource
from fjormcord.bot.artping.legacy.handler.voting_gauntlet_handlers import send_voting_gauntlet
from fjormcord.bot.artping.legacy.handler.weekly_reminder_handlers import get_closing_times, send_reminders
from fjormcord.bot.artping.model.layout import Layout
from fjormcord.bot.artping.util.message_util import MULTI_WORD_HINT
from fjormcord.bot.artping.util.user_util import is_administrator

COMMAND_PREFIX = "~"

SECTION_ART_PING = "Art Ping Commands"
SECTION_CURRENCY = "Gacha Currency Commands"
SECTION_REMINDER = "Reminder Commands"
SECTION_ADMIN = "Admin Commands"

# Called as handler(client, message); returns the reply, either directly or as a coroutine
Handler = Callable[[discord.Client, discord.Message], str | Layout | Awaitable[str | Layout]]


@dataclass(frozen=True)
class Command:
    name: str
    handler: Handler
    description: str
    # The arguments, in order, e.g. ("currency name", "amount")
    usage: tuple[str, ...] = ()
    section: str = SECTION_ART_PING
    admin_only: bool = False


def format_usage(command: Command) -> str:
    # ~setcurrency (currency name) (amount)
    return " ".join([command.name] + [f"({argument})" for argument in command.usage])


def help_layout(tips: list[str], entries: Iterable[tuple[str, str, str]]) -> Layout:
    # The title with the tips, then one part per section, in the order the entries name them, each command's usage in
    # bold over its description. entries are (section, usage, description); ~help and /help both lay out this way
    sections: dict[str, list[str]] = {}
    for section, usage, description in entries:
        sections.setdefault(section, []).append(f"**{usage}**\n{description}")

    parts = ["\n".join([f"### {section}", *lines]) for section, lines in sections.items()]
    return Layout(("\n".join(["## Commands", *tips]), *parts))


def show_help(client: discord.Client, message: discord.Message) -> Layout:
    # Generated from COMMANDS, which keeps each section together; the admin section is only shown to admins
    show_admin = is_administrator(message.author)
    tips = [
        "Content in brackets is what to add when using a command",
        MULTI_WORD_HINT,
        "All commands are also available as slash commands, type /",
    ]
    entries = [
        (SECTION_ADMIN if command.admin_only else command.section, format_usage(command), command.description)
        for command in COMMANDS
        if show_admin or not command.admin_only
    ]
    return help_layout(tips, entries)


# The ~ commands; slash commands are in fjormcord.bot.artping.slash
# (docs/superpowers/specs/2026-10-26-slash-commands-design.md)
# Commands are listed in ~help order; keep each section together and admin-only commands last.
COMMANDS = [
    Command("~artping", do_art_ping, "Ping users for art of this character", usage=("character name",)),
    Command(
        "~addping",
        add_ping,
        "Call to add yourself to the ping list when this character is pinged",
        usage=("character name",),
    ),
    Command(
        "~removeping", remove_ping, "Remove yourself from the ping list of this character", usage=("character name",)
    ),
    Command("~checkping", check_ping, "See which characters you are being pinged for"),
    Command(
        "~addcharacter",
        add_character,
        "Add a character that users can be pinged for; for non-admins this starts a vote, and everyone who "
        "votes is subscribed once it passes",
        usage=("character name",),
    ),
    Command(
        "~checkcharacter", check_character, "See which users are pinged for this character", usage=("character name",)
    ),
    Command("~resources", list_resources, "See which resources there are; ~(resource name) posts one"),
    Command("~help", show_help, "Shows this overview of all the available commands"),
    Command(
        "~setcurrency",
        set_currency,
        "Set the number of orbs, primos or any other currency that you have",
        usage=("currency name", "amount"),
        section=SECTION_CURRENCY,
    ),
    Command(
        "~clearcurrency",
        clear_currency,
        "Clears the number you have saved for that particular currency",
        usage=("currency name",),
        section=SECTION_CURRENCY,
    ),
    Command(
        "~checkwallet",
        check_wallet,
        "Shows a list of all currencies you have and their count",
        section=SECTION_CURRENCY,
    ),
    Command(
        "~scoreboard",
        get_scoreboard,
        "Shows a leaderboard of the specified currency, 10 users per page",
        usage=("currency name", "optional page number"),
        section=SECTION_CURRENCY,
    ),
    Command(
        "~closingtimes",
        get_closing_times,
        "See when Coliseum/Aether Raids and Divine Games close next",
        section=SECTION_REMINDER,
    ),
    Command(
        "~removecharacter",
        remove_character,
        "Remove a character and unsubscribe all its users",
        usage=("character name",),
        admin_only=True,
    ),
    Command("~addalias", add_alias, "Add an alias to a character", usage=("character name", "alias"), admin_only=True),
    Command(
        "~removealias",
        remove_alias,
        "Remove an alias from a character",
        usage=("character name", "alias"),
        admin_only=True,
    ),
    Command(
        "~setprimaryname",
        set_primary_name,
        "Make an alias the character's name; the old name becomes an alias",
        usage=("alias",),
        admin_only=True,
    ),
    Command(
        "~setresource",
        set_resource,
        "Save the text of a Discord message, or a website link, for everyone to post with ~(resource name)",
        usage=("resource name", "link"),
        admin_only=True,
    ),
    Command("~removeresource", remove_resource, "Remove a resource", usage=("resource name",), admin_only=True),
    Command(
        "~addcurrency", add_currency, "Add a currency that users can track", usage=("currency name",), admin_only=True
    ),
    Command(
        "~removecurrency",
        remove_currency,
        "Remove a currency and clear it from all wallets",
        usage=("currency name",),
        admin_only=True,
    ),
    Command(
        "~sendreminders",
        send_reminders,
        "Debug: send the weekly reminders to their channels now, whatever the day",
        admin_only=True,
    ),
    Command(
        "~sendvotinggauntlet",
        send_voting_gauntlet,
        "Debug: post the Voting Gauntlet scores now, as the hourly task does; only while a round runs",
        admin_only=True,
    ),
]

COMMANDS_BY_NAME = {command.name: command for command in COMMANDS}
