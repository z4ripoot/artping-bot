import logging

import discord

from fjormcord.bot.artping.model.character import Character
from fjormcord.bot.artping.repository import alias_repository, art_ping_repository, character_repository
from fjormcord.bot.artping.util.message_util import CommandError, get_single_name
from fjormcord.bot.artping.util.user_util import get_username


def require_character(name: str) -> Character:
    character = character_repository.get_character(name)
    if character is None:
        raise CommandError(f"Character {name} doesn't exist")
    return character


def require_unused_name(name: str):
    # A name may belong to only one character, as its name or as one of its aliases
    existing = character_repository.get_character(name)
    if existing is None:
        return
    if alias_repository.has_alias(existing.id, name):
        raise CommandError(f"{name} is already an alias of {existing.name}")
    raise CommandError(f"Character {existing.name} already exists")


def add_character(client: discord.Client, message: discord.Message) -> str:
    entry = get_single_name(message.content, "character name")

    require_unused_name(entry)

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

    lines = [f"Character entry found for {character.name}"]

    aliases = alias_repository.get_aliases(character.id)
    if aliases:
        lines.append(f"Aliases: {', '.join(aliases)}")

    user_ids = art_ping_repository.get_art_ping_users((character.id,))
    usernames = [await get_username(client, user_id) for user_id in user_ids]
    lines.append(f"Users: {', '.join(usernames)}")

    return "\n".join(lines)
