import logging

import discord

from fjormcord.bot.artping.repository import alias_repository, character_repository
from fjormcord.bot.artping.service.character_service import require_character, require_unused_name
from fjormcord.bot.artping.util.message_util import MESSAGE_ONE_NAME_ONLY, CommandError, MissingArgument, \
    get_entries, get_single_name


def _get_character_and_alias(content):
    entries = get_entries(content)

    if not entries:
        raise MissingArgument("character name")
    if len(entries) > 2:
        raise CommandError(MESSAGE_ONE_NAME_ONLY)
    if len(entries) == 1:
        raise MissingArgument("alias")

    name, alias = entries
    return require_character(name), alias


def add_alias(client: discord.Client, message: discord.Message) -> str:
    character, alias = _get_character_and_alias(message.content)

    require_unused_name(alias)

    alias_repository.add_alias(character.id, alias)

    out = f"Alias {alias} has been added to {character.name}"
    logging.info(out)
    return out


def remove_alias(client: discord.Client, message: discord.Message) -> str:
    character, alias = _get_character_and_alias(message.content)

    if not alias_repository.has_alias(character.id, alias):
        raise CommandError(f"{alias} is not an alias of {character.name}")

    alias_repository.remove_alias(character.id, alias)

    out = f"Alias {alias} has been removed from {character.name}"
    logging.info(out)
    return out


def set_primary_name(client: discord.Client, message: discord.Message) -> str:
    alias = get_single_name(message.content, "alias")
    character = require_character(alias)

    if not alias_repository.has_alias(character.id, alias):
        raise CommandError(f"{character.name} is already the primary name")

    alias_repository.set_primary_name(character.id, alias)

    renamed = character_repository.get_character(character.name)
    out = f"{renamed.name} is now the primary name; {character.name} has become an alias"
    logging.info(out)
    return out
