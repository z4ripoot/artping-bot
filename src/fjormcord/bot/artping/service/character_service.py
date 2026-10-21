import logging

import discord

from fjormcord.bot.artping.repository import character_repository
from fjormcord.bot.artping.repository.art_ping_repository import get_art_ping_users
from fjormcord.bot.artping.repository.character_repository import get_character_row
from fjormcord.bot.artping.util.message_util import MESSAGE_ONE_NAME_ONLY, MissingArgument, get_first, has_extra_entries
from fjormcord.bot.artping.util.user_util import get_username


def add_character(client: discord.Client, message: discord.Message):
    entry = get_first(message.content)

    if entry is None:
        raise MissingArgument("character name")

    if has_extra_entries(message.content):
        logging.warning(MESSAGE_ONE_NAME_ONLY)
        return MESSAGE_ONE_NAME_ONLY

    existing = get_character_row(entry)
    if existing:
        out = f"Character {existing['NAME']} already exists"
        logging.warning(out)
        return out

    character_repository.add_character(entry)

    out = f"Character {entry} has been added"
    logging.info(out)
    return out


def remove_character(client: discord.Client, message: discord.Message):
    entry = get_first(message.content)

    if entry is None:
        raise MissingArgument("character name")

    if has_extra_entries(message.content):
        logging.warning(MESSAGE_ONE_NAME_ONLY)
        return MESSAGE_ONE_NAME_ONLY

    character = get_character_row(entry)

    if character is None:
        out = f"Character {entry} doesn't exist"
        logging.warning(out)
        return out

    character_repository.remove_character(character['CHARACTER_ID'])

    out = f"Character {character['NAME']} has been removed"
    logging.info(out)
    return out


async def check_character(client: discord.Client, message: discord.Message):
    entry = get_first(message.content)

    if entry is None:
        raise MissingArgument("character name")

    if has_extra_entries(message.content):
        logging.warning(MESSAGE_ONE_NAME_ONLY)
        return MESSAGE_ONE_NAME_ONLY

    character = get_character_row(entry)

    if character is None:
        out = f"Character {entry} doesn't exist"
        logging.warning(out)
        return out

    usernames = [await get_username(client, user_id) for user_id in get_art_ping_users((character['CHARACTER_ID'],))]

    return f"Character entry found for {character['NAME']}\n" \
        + f"Users: {', '.join(usernames)}"
