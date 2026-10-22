import logging

import discord

from fjormcord.bot.artping.model.character import Character
from fjormcord.bot.artping.repository import art_ping_repository, character_repository
from fjormcord.bot.artping.service.character_service import require_character
from fjormcord.bot.artping.util.message_util import CommandError, MissingArgument, get_entries, get_single_name


def _find_characters(names: list[str]) -> tuple[list[Character], list[str]]:
    # Returns the characters that exist, and the names that matched none
    characters = character_repository.get_characters(names)
    found_names = {character.name.lower() for character in characters}
    return characters, [name for name in names if name.lower() not in found_names]


def _ping(characters: list[Character]) -> str:
    # Mentions everyone subscribed to these characters
    character_names = ", ".join(character.name for character in characters)
    user_ids = art_ping_repository.get_art_ping_users([character.id for character in characters])

    logging.info("Pinged %s users for %s", len(user_ids), character_names)
    if not user_ids:
        return f"Nobody is subscribed to {character_names}"
    return f"{character_names}: " + " ".join(f"<@{user_id}>" for user_id in user_ids)


def do_art_ping(client: discord.Client, message: discord.Message) -> str:
    entries = get_entries(message.content)

    if not entries:
        raise MissingArgument("character name")

    # Unknown characters are reported in the same reply as the ping for the rest
    lines = []

    characters, missing_names = _find_characters(entries)
    if missing_names:
        lines.append(f"No character entry for {', '.join(missing_names)}")

    if not characters:
        raise CommandError("\n".join(lines))

    lines.append(_ping(characters))
    return "\n".join(lines)


def add_ping(client: discord.Client, message: discord.Message) -> str:
    character = require_character(get_single_name(message.content, "character name"))
    user_id = str(message.author.id)

    if art_ping_repository.has_ping(character.id, user_id):
        raise CommandError(f"Ping for {character.name} already exists")

    art_ping_repository.add_ping(character.id, user_id)

    out = f"Ping for {character.name} has been added"
    logging.info(out)
    return out


def remove_ping(client: discord.Client, message: discord.Message) -> str:
    character = require_character(get_single_name(message.content, "character name"))
    user_id = str(message.author.id)

    if not art_ping_repository.has_ping(character.id, user_id):
        raise CommandError(f"Ping for {character.name} doesn't exist")

    art_ping_repository.remove_ping(character.id, user_id)

    out = f"Ping for {character.name} has been removed"
    logging.info(out)
    return out


def check_ping(client: discord.Client, message: discord.Message) -> str:
    characters = art_ping_repository.get_pings_from_user(str(message.author.id))

    if not characters:
        return "You are not subscribed to any characters"

    return ", ".join(character.name for character in characters)
