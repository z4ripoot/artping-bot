import logging

import discord

from fjormcord.bot.artping.repository import art_ping_repository, character_repository
from fjormcord.bot.artping.util.message_util import CommandError, get_single_name
from fjormcord.bot.artping.util.user_util import get_username


def require_character(name):
    character = character_repository.get_character(name)
    if character is None:
        raise CommandError(f"Character {name} doesn't exist")
    return character


def add_character(client: discord.Client, message: discord.Message) -> str:
    entry = get_single_name(message.content, "character name")

    existing = character_repository.get_character(entry)
    if existing:
        raise CommandError(f"Character {existing.name} already exists")

    character_repository.add_character(entry)

    out = f"Character {entry} has been added"
    logging.info(out)
    return out


def remove_character(client: discord.Client, message: discord.Message) -> str:
    character = require_character(get_single_name(message.content, "character name"))

    character_repository.remove_character(character.id)

    out = f"Character {character.name} has been removed"
    logging.info(out)
    return out


async def check_character(client: discord.Client, message: discord.Message) -> str:
    character = require_character(get_single_name(message.content, "character name"))

    user_ids = art_ping_repository.get_art_ping_users((character.id,))
    usernames = [await get_username(client, user_id) for user_id in user_ids]

    return f"Character entry found for {character.name}\nUsers: {', '.join(usernames)}"
