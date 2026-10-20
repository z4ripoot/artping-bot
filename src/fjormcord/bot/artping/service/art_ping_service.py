import logging

import discord

from fjormcord.bot.artping.repository import art_ping_repository
from fjormcord.bot.artping.repository.art_ping_repository import get_art_ping_users, get_art_ping_row, get_pings_from_user
from fjormcord.bot.artping.repository.character_repository import get_character_rows, get_character_name, get_character_row, \
    get_missing_character_rows
from fjormcord.bot.artping.util.message_util import get_entries, get_first


async def do_art_ping(client: discord.Client, message: discord.Message):
    entries = get_entries(message.content)

    if not entries:
        out = "Character is missing. Please add the character to your ping"
        logging.warning(out)
        return out

    missing_characters = await get_missing_characters(message, entries)
    characters = list(filter(lambda character: character not in missing_characters, entries))

    logging.info("Pinging characters %s", characters)

    if not characters:
        out = "Character is missing. Please add the character to your ping"
        logging.warning(out)
        return out

    character_rows = get_character_rows(characters)
    user_rows = get_art_ping_users([row['CHARACTER_ID'] for row in character_rows])

    out = ", ".join(row['NAME'] for row in character_rows)
    out += ": "

    users = []
    for row in user_rows:
        users.append(f"<@{row}>")

    out += " ".join(users)

    logging.info("Pinged %s users for %s", len(users), characters)
    return out


def add_ping(client: discord.Client, message: discord.Message):
    entries = get_entries(message.content)

    if not entries:
        out = "Character is missing. Please add the character to be pinged for"
        logging.warning(out)
        return out
    elif len(entries) > 1:
        out = "More than one character detected. Please add the characters separately"
        logging.warning(out)
        return out

    entry = get_first(message.content)

    if not get_character_name(entry):
        out = f"Character {entry} doesn't exist"
        logging.warning(out)
        return out

    user_id = str(message.author.id)
    character = get_character_row(entry)
    character_id = character['CHARACTER_ID']
    character_name = character['NAME']

    if get_art_ping_row(character_id, user_id):
        out = f"Ping for {character_name} already exists"
        logging.info(out)
        return out

    logging.info("Adding ping for %s", character_name)
    is_added = art_ping_repository.add_ping(character_id, user_id)

    if is_added:
        out = f"A ping for {character_name} has been added"
        logging.info(out)
        return out
    else:
        out = f"Failed to add ping for {entry}"
        logging.warning(out)
        return out


def remove_ping(client: discord.Client, message: discord.Message):
    entries = get_entries(message.content)

    if not entries:
        return "Character is missing. Please add the character you would like to remove"
    elif len(entries) > 1:
        return "More than one character detected. Please remove the characters separately"

    entry = get_first(message.content)

    if not get_character_name(entry):
        out = f"Character {entry} doesn't exist"
        logging.warning(out)
        return out

    user_id = str(message.author.id)
    character = get_character_row(entry)
    character_id = character['CHARACTER_ID']
    character_name = character['NAME']

    if not get_art_ping_row(character_id, user_id):
        out = f"Ping for {character_name} doesn't exist"
        logging.warning(out)
        return out

    logging.info("Removing ping for %s", character_name)
    is_removed = art_ping_repository.remove_ping(character_id, user_id)

    if is_removed:
        out = f"Ping for {character_name} has been removed"
        logging.info(out)
        return out
    else:
        out = f"Failed to remove ping for {character_name}"
        logging.warning(out)
        return out


async def check_ping(client: discord.Client, message: discord.Message):
    user_id = str(message.author.id)

    logging.info(f"Getting pings for user {user_id}")

    pings = get_pings_from_user(user_id)

    logging.info(f"Got pings for user {user_id}")

    return ", ".join(pings)


async def get_missing_characters(message: discord.Message, characters):
    logging.info("Checking for missing characters")

    missing_characters = []
    missing_character_rows = get_missing_character_rows(characters)

    if missing_character_rows:
        logging.info("Missing characters found")

        for row in missing_character_rows:
            missing_characters.append(row['NAME'])
        await message.channel.send(f"No character entry for {', '.join(missing_characters)}")

    return missing_characters
