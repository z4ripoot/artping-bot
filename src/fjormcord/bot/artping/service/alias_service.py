from fjormcord.bot.artping.exception.command_error import CommandError
from fjormcord.bot.artping.repository import alias_repository, character_repository
from fjormcord.bot.artping.service.character_service import require_character, require_unused_name
from fjormcord.bot.artping.util.message_util import log_info
from fjormcord.bot.artping.util.name_util import normalize_name


def add_alias(name: str, alias: str) -> str:
    character = require_character(name)
    alias = normalize_name(alias)

    require_unused_name(alias)

    alias_repository.add_alias(character.id, alias)

    return log_info(f"Alias {alias} has been added to {character.name}")


def remove_alias(name: str, alias: str) -> str:
    character = require_character(name)
    alias = normalize_name(alias)

    if not alias_repository.has_alias(character.id, alias):
        raise CommandError(f"{alias} is not an alias of {character.name}")

    alias_repository.remove_alias(character.id, alias)

    return log_info(f"Alias {alias} has been removed from {character.name}")


def set_primary_name(alias: str) -> str:
    alias = normalize_name(alias)
    character = require_character(alias)

    if not alias_repository.has_alias(character.id, alias):
        raise CommandError(f"{character.name} is already the primary name")

    alias_repository.set_primary_name(character.id, alias)

    renamed = character_repository.get_character(character.name)
    return log_info(f"{renamed.name} is now the primary name; {character.name} has become an alias")
