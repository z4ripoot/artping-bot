import logging

import discord

from fjormcord.bot.artping.repository import character_repository
from fjormcord.bot.artping.repository.art_ping_repository import get_art_ping_users
from fjormcord.bot.artping.repository.character_repository import get_character_row
from fjormcord.bot.artping.util.message_util import get_first
from fjormcord.bot.artping.util.user_util import get_username


def add_character(client: discord.Client, message: discord.Message):
    entry = get_first(message.content)

    if entry is None:
        out = "Failed to add character"
        logging.warning(out)
        return out

    if get_character_row(entry):
        out = f"Failed to add character {entry}. Character {entry} already exists"
        logging.warning(out)
        return out

    character_repository.add_character(entry)

    out = f"{entry} has been added"
    logging.info(out)
    return out


def remove_character(client: discord.Client, message: discord.Message):
    entry = get_first(message.content)

    if entry is None:
        out = "Failed to remove character"
        logging.warning(out)
        return out

    character = get_character_row(entry)

    if character is None:
        out = f"Character {entry} doesn't exist"
        logging.warning(out)
        return out

    character_repository.remove_character(character['CHARACTER_ID'])

    out = f"{character['NAME']} has been removed"
    logging.info(out)
    return out


async def check_character(client: discord.Client, message: discord.Message):
    entry = get_first(message.content)

    if entry is None:
        out = "Failed to check character"
        logging.warning(out)
        return out

    character = get_character_row(entry)

    if character is None:
        out = f"Failed to check character {entry}"
        logging.warning(out)
        return out

    usernames = [await get_username(client, user_id) for user_id in get_art_ping_users((character['CHARACTER_ID'],))]

    return f"Character entry found for {character['NAME']}\n" \
        + f"Users: {', '.join(usernames)}"
