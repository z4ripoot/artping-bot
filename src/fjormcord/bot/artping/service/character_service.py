import logging

import discord

from fjormcord.bot.artping.model.character import Character
from fjormcord.bot.artping.repository import alias_repository, art_ping_repository, character_repository
# Imported as a module, since character_vote_service imports this one too
from fjormcord.bot.artping.service import character_vote_service
from fjormcord.bot.artping.util.message_util import CommandError, get_single_name
from fjormcord.bot.artping.util.name_util import normalize_name
from fjormcord.bot.artping.util.user_util import get_username, is_administrator


def require_character(name: str) -> Character:
    character = character_repository.get_character(name)
    if character is None:
        raise CommandError(f"Character {normalize_name(name)} doesn't exist")
    return character


def require_unused_name(name: str):
    # A name may belong to only one character, as its name or as one of its aliases
    existing = character_repository.get_character(name)
    if existing is None:
        return
    if alias_repository.has_alias(existing.id, name):
        raise CommandError(f"{name} is already an alias of {existing.name}")
    raise CommandError(f"Character {existing.name} already exists")


async def add_character(client: discord.Client, message: discord.Message) -> str:
    entry = normalize_name(get_single_name(message.content, "character name"))

    require_unused_name(entry)

    # Non-admins start a vote instead; the character is added once enough users, or an admin, react to it
    if not is_administrator(message.author) and character_vote_service.is_voting_enabled():
        return await character_vote_service.start_vote(message, entry)

    character_repository.add_character(entry)
    await character_vote_service.close_votes(client, entry)

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
