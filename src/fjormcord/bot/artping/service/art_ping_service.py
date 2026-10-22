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


def _find_characters(names):
    # Returns the rows of the characters that exist, and the names that matched none
    character_rows = character_repository.get_character_rows(names)
    found_names = {row['NAME'].lower() for row in character_rows}
    return character_rows, [name for name in names if name.lower() not in found_names]


def _hold_back_cooling_down(character_rows, now):
    # Returns the rows that can be pinged now, and a notice about the others (None when there are none)
    remaining = {row['CHARACTER_ID']: _cooldown_remaining(row['CHARACTER_ID'], now) for row in character_rows}
    cooling_down = [row for row in character_rows if remaining[row['CHARACTER_ID']] > 0]
    if not cooling_down:
        return character_rows, None

    names = ", ".join(row['NAME'] for row in cooling_down)
    seconds = math.ceil(max(remaining[row['CHARACTER_ID']] for row in cooling_down))
    notice = f"{names} was pinged recently. Try again in {seconds} second{'' if seconds == 1 else 's'}"
    return [row for row in character_rows if remaining[row['CHARACTER_ID']] <= 0], notice


def _ping(character_rows, now):
    # Mentions everyone subscribed to these characters, and starts their cooldown
    character_names = ", ".join(row['NAME'] for row in character_rows)
    user_ids = art_ping_repository.get_art_ping_users([row['CHARACTER_ID'] for row in character_rows])
    for row in character_rows:
        _last_pinged[row['CHARACTER_ID']] = now

    logging.info("Pinged %s users for %s", len(user_ids), character_names)
    if not user_ids:
        return f"Nobody is subscribed to {character_names}"
    return f"{character_names}: " + " ".join(f"<@{user_id}>" for user_id in user_ids)


def do_art_ping(client: discord.Client, message: discord.Message) -> str:
    entries = get_entries(message.content)

    if not entries:
        raise MissingArgument("character name")

    # Unknown and cooling-down characters are reported in the same reply as the ping for the rest
    lines = []

    character_rows, missing_names = _find_characters(entries)
    if missing_names:
        lines.append(f"No character entry for {', '.join(missing_names)}")

    now = monotonic()
    if not is_administrator(message.author):
        character_rows, cooldown_notice = _hold_back_cooling_down(character_rows, now)
        if cooldown_notice:
            lines.append(cooldown_notice)

    if not character_rows:
        raise CommandError("\n".join(lines))

    lines.append(_ping(character_rows, now))
    return "\n".join(lines)


def add_ping(client: discord.Client, message: discord.Message) -> str:
    character = require_character(get_single_name(message.content, "character name"))
    user_id = str(message.author.id)

    if art_ping_repository.get_art_ping_row(character['CHARACTER_ID'], user_id):
        raise CommandError(f"Ping for {character['NAME']} already exists")

    art_ping_repository.add_ping(character['CHARACTER_ID'], user_id)

    out = f"Ping for {character['NAME']} has been added"
    logging.info(out)
    return out


def remove_ping(client: discord.Client, message: discord.Message) -> str:
    character = require_character(get_single_name(message.content, "character name"))
    user_id = str(message.author.id)

    if not art_ping_repository.get_art_ping_row(character['CHARACTER_ID'], user_id):
        raise CommandError(f"Ping for {character['NAME']} doesn't exist")

    art_ping_repository.remove_ping(character['CHARACTER_ID'], user_id)

    out = f"Ping for {character['NAME']} has been removed"
    logging.info(out)
    return out


def check_ping(client: discord.Client, message: discord.Message) -> str:
    pings = art_ping_repository.get_pings_from_user(str(message.author.id))

    if not pings:
        return "You are not subscribed to any characters"

    return ", ".join(pings)
