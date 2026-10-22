import logging
import math
from time import monotonic

import discord

from fjormcord.bot.artping.repository import art_ping_repository, character_repository
from fjormcord.bot.artping.service.character_service import require_character
from fjormcord.bot.artping.util.message_util import CommandError, MissingArgument, get_entries, get_single_name
from fjormcord.bot.artping.util.user_util import is_administrator

# A character can't be pinged again within this many seconds, except by admins
ART_PING_COOLDOWN_SECONDS = 1

# Character ID -> monotonic() time of its last ping; kept in memory, so it resets when the bot restarts
_last_pinged = {}


def _cooldown_remaining(character_id, now):
    # Seconds until the character can be pinged again; zero or less when it can be pinged now
    return ART_PING_COOLDOWN_SECONDS - (now - _last_pinged.get(character_id, -math.inf))


def do_art_ping(client: discord.Client, message: discord.Message):
    entries = get_entries(message.content)

    if not entries:
        raise MissingArgument("character name")

    character_rows = character_repository.get_character_rows(entries)
    found_names = {row['NAME'].lower() for row in character_rows}
    missing_characters = [entry for entry in entries if entry.lower() not in found_names]

    lines = []
    if missing_characters:
        lines.append(f"No character entry for {', '.join(missing_characters)}")

    now = monotonic()
    if not is_administrator(message.author):
        remaining = {row['CHARACTER_ID']: _cooldown_remaining(row['CHARACTER_ID'], now) for row in character_rows}
        cooling_down = [row for row in character_rows if remaining[row['CHARACTER_ID']] > 0]
        if cooling_down:
            names = ", ".join(row['NAME'] for row in cooling_down)
            seconds = math.ceil(max(remaining[row['CHARACTER_ID']] for row in cooling_down))
            lines.append(f"{names} was pinged recently. Try again in {seconds} second{'' if seconds == 1 else 's'}")
            character_rows = [row for row in character_rows if remaining[row['CHARACTER_ID']] <= 0]

    if not character_rows:
        raise CommandError("\n".join(lines))

    character_names = ", ".join(row['NAME'] for row in character_rows)
    user_ids = art_ping_repository.get_art_ping_users([row['CHARACTER_ID'] for row in character_rows])
    for row in character_rows:
        _last_pinged[row['CHARACTER_ID']] = now

    if user_ids:
        lines.append(f"{character_names}: " + " ".join(f"<@{user_id}>" for user_id in user_ids))
    else:
        lines.append(f"Nobody is subscribed to {character_names}")

    logging.info("Pinged %s users for %s", len(user_ids), character_names)
    return "\n".join(lines)


def add_ping(client: discord.Client, message: discord.Message):
    character = require_character(get_single_name(message.content, "character name"))
    user_id = str(message.author.id)

    if art_ping_repository.get_art_ping_row(character['CHARACTER_ID'], user_id):
        raise CommandError(f"Ping for {character['NAME']} already exists")

    art_ping_repository.add_ping(character['CHARACTER_ID'], user_id)

    out = f"Ping for {character['NAME']} has been added"
    logging.info(out)
    return out


def remove_ping(client: discord.Client, message: discord.Message):
    character = require_character(get_single_name(message.content, "character name"))
    user_id = str(message.author.id)

    if not art_ping_repository.get_art_ping_row(character['CHARACTER_ID'], user_id):
        raise CommandError(f"Ping for {character['NAME']} doesn't exist")

    art_ping_repository.remove_ping(character['CHARACTER_ID'], user_id)

    out = f"Ping for {character['NAME']} has been removed"
    logging.info(out)
    return out


def check_ping(client: discord.Client, message: discord.Message):
    pings = art_ping_repository.get_pings_from_user(str(message.author.id))

    if not pings:
        return "You are not subscribed to any characters"

    return ", ".join(pings)
