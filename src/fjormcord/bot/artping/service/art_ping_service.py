import logging

from fjormcord.bot.artping.exception.command_error import CommandError
from fjormcord.bot.artping.model.character import Character
from fjormcord.bot.artping.repository import art_ping_repository, character_repository
from fjormcord.bot.artping.service import character_service  # A module: it imports this one too, via subscribe_view
from fjormcord.bot.artping.util.message_util import log_info
from fjormcord.bot.artping.util.name_util import normalize_name
from fjormcord.bot.artping.util.user_util import mentions


def _find_characters(names: list[str]) -> tuple[list[Character], list[str]]:
    # Returns the characters that exist, alphabetically and each once even when named by several aliases,
    # and the names that matched none
    characters = []
    missing_names = []
    for name in names:
        character = character_repository.get_character(name)
        if character is None:
            missing_names.append(normalize_name(name))
        elif character not in characters:
            characters.append(character)
    characters.sort(key=lambda character: character.name.casefold())
    return characters, missing_names


def _ping(characters: list[Character]) -> str:
    # Mentions everyone subscribed to these characters
    character_names = ", ".join(character.name for character in characters)
    user_ids = art_ping_repository.get_art_ping_users([character.id for character in characters])

    logging.info("Pinged %s users for %s", len(user_ids), character_names)
    if not user_ids:
        return f"Nobody is subscribed to {character_names}"
    return f"{character_names}: {mentions(user_ids)}"


def do_art_ping(names: list[str]) -> str:
    # Unknown characters are reported in the same reply as the ping for the rest
    lines = []

    characters, missing_names = _find_characters(names)
    if missing_names:
        lines.append(f"No character entry for {', '.join(missing_names)}")

    if not characters:
        raise CommandError("\n".join(lines))

    lines.append(_ping(characters))
    return "\n".join(lines)


def add_ping(user_id: str, name: str) -> str:
    return _add_ping(user_id, character_service.require_character(name))


def subscribe(user_id: str, character_id: int) -> str:
    # A click on the Subscribe button of a new character, which may have been removed since
    character = character_repository.get_character_by_id(character_id)
    if character is None:
        raise CommandError("This character doesn't exist anymore")
    return _add_ping(user_id, character)


def _add_ping(user_id: str, character: Character) -> str:
    if art_ping_repository.has_ping(character.id, user_id):
        raise CommandError(f"Ping for {character.name} already exists")

    art_ping_repository.add_ping(character.id, user_id)

    return log_info(f"Ping for {character.name} has been added")


def remove_ping(user_id: str, name: str) -> str:
    character = character_service.require_character(name)

    if not art_ping_repository.has_ping(character.id, user_id):
        raise CommandError(f"Ping for {character.name} doesn't exist")

    art_ping_repository.remove_ping(character.id, user_id)

    return log_info(f"Ping for {character.name} has been removed")


def check_ping(user_id: str) -> str:
    characters = art_ping_repository.get_pings_from_user(user_id)

    if not characters:
        return "You are not subscribed to any characters"

    return ", ".join(character.name for character in characters)
