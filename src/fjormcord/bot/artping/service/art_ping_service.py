import logging

import discord

from fjormcord.bot.artping.repository import art_ping_repository
from fjormcord.bot.artping.repository.art_ping_repository import get_art_ping_users, get_art_ping_row, get_pings_from_user
from fjormcord.bot.artping.repository.character_repository import get_character_rows, get_character_row
from fjormcord.bot.artping.util.message_util import MULTI_WORD_HINT, get_entries


def do_art_ping(client: discord.Client, message: discord.Message):
    entries = get_entries(message.content)

    if not entries:
        out = "Character is missing. Please add the character to your ping"
        logging.warning(out)
        return out

    character_rows = get_character_rows(entries)
    found_names = {row['NAME'].lower() for row in character_rows}
    missing_characters = [entry for entry in entries if entry.lower() not in found_names]

    lines = []
    if missing_characters:
        lines.append(f"No character entry for {', '.join(missing_characters)}")

    if not character_rows:
        out = "\n".join(lines)
        logging.warning(out)
        return out

    character_names = ", ".join(row['NAME'] for row in character_rows)
    user_ids = get_art_ping_users([row['CHARACTER_ID'] for row in character_rows])

    if user_ids:
        lines.append(f"{character_names}: " + " ".join(f"<@{user_id}>" for user_id in user_ids))
    else:
        lines.append(f"Nobody is subscribed to {character_names}")

    logging.info("Pinged %s users for %s", len(user_ids), character_names)
    return "\n".join(lines)


def add_ping(client: discord.Client, message: discord.Message):
    entries = get_entries(message.content)

    if not entries:
        out = "Character is missing. Please add the character to be pinged for"
        logging.warning(out)
        return out
    elif len(entries) > 1:
        out = f"More than one character detected. Please add the characters separately. {MULTI_WORD_HINT}"
        logging.warning(out)
        return out

    entry = entries[0]
    character = get_character_row(entry)

    if character is None:
        out = f"Character {entry} doesn't exist"
        logging.warning(out)
        return out

    user_id = str(message.author.id)
    character_name = character['NAME']

    if get_art_ping_row(character['CHARACTER_ID'], user_id):
        out = f"Ping for {character_name} already exists"
        logging.info(out)
        return out

    art_ping_repository.add_ping(character['CHARACTER_ID'], user_id)

    out = f"A ping for {character_name} has been added"
    logging.info(out)
    return out


def remove_ping(client: discord.Client, message: discord.Message):
    entries = get_entries(message.content)

    if not entries:
        return "Character is missing. Please add the character you would like to remove"
    elif len(entries) > 1:
        return f"More than one character detected. Please remove the characters separately. {MULTI_WORD_HINT}"

    entry = entries[0]
    character = get_character_row(entry)

    if character is None:
        out = f"Character {entry} doesn't exist"
        logging.warning(out)
        return out

    user_id = str(message.author.id)
    character_name = character['NAME']

    if not get_art_ping_row(character['CHARACTER_ID'], user_id):
        out = f"Ping for {character_name} doesn't exist"
        logging.warning(out)
        return out

    art_ping_repository.remove_ping(character['CHARACTER_ID'], user_id)

    out = f"Ping for {character_name} has been removed"
    logging.info(out)
    return out


def check_ping(client: discord.Client, message: discord.Message):
    pings = get_pings_from_user(str(message.author.id))

    if not pings:
        return "You are not subscribed to any characters"

    return ", ".join(pings)
