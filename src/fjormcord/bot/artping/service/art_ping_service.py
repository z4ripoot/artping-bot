import logging

import discord

from fjormcord.bot.artping.exception.command_error import CommandError
from fjormcord.bot.artping.model.character import Character
from fjormcord.bot.artping.model.layout import Layout
from fjormcord.bot.artping.repository import art_ping_repository, character_repository
from fjormcord.bot.artping.service import (  # Modules: they import this one too, via the views
    character_service,
    character_vote_service,
)
from fjormcord.bot.artping.util.message_util import log_info
from fjormcord.bot.artping.util.name_util import normalize_name
from fjormcord.bot.artping.util.page_util import get_page, paged_header
from fjormcord.bot.artping.util.user_util import get_username, mentions
from fjormcord.bot.artping.view import page_view  # A module: it imports this one too

MESSAGE_NO_PINGS = "You are not subscribed to any characters"


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
    return mentions(user_ids)


def _add_character_hint(name: str, administrator: bool, prefix: str) -> str:
    # A non-admin's addcharacter starts a vote, unless voting is off; an admin's adds the character
    if administrator or not character_vote_service.is_voting_enabled():
        return f"Use {prefix}addcharacter {name} to add it"
    return f"Use {prefix}addcharacter {name} to start a vote to add it"


def do_art_ping(names: list[str], administrator: bool, slash: bool = False) -> Layout:
    # The header names the characters that exist; the body reports the unknown names, then pings. The footer reminds of
    # addping for the first character and hints at addcharacter for the first unknown name, in the syntax used
    prefix = "/" if slash else "~"
    characters, missing_names = _find_characters(names)

    body = []
    footer = []
    if missing_names:
        body.append(f"No character entry for {', '.join(missing_names)}")
    if characters:
        first = characters[0].name
        body.append(_ping(characters))
        footer.append(f"Want to be pinged for {first}? Use {prefix}addping {first}")
    if missing_names:
        footer.append(_add_character_hint(missing_names[0], administrator, prefix))

    if not characters:
        # Turned down, so it starts no cooldown and stays private for slash, but laid out with its hint
        raise CommandError(body[0], layout=Layout((body[0], "\n".join(footer))))

    header = "### " + ", ".join(character.name for character in characters)
    return Layout(("\n".join([header, *body]), "\n".join(footer)))


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


async def check_ping(client: discord.Client, user_id: str, page: int = 1) -> str | Layout:
    # The user's characters, one per line, 10 per page; the user is named as on the scoreboard, so a page turned after a
    # restart, which only has the user's ID, shows the same header
    characters = art_ping_repository.get_pings_from_user(user_id)

    if not characters:
        return MESSAGE_NO_PINGS

    name = await get_username(client, user_id)
    entries, page_count = get_page(characters, page, f"The list of {name}'s pings")
    header = paged_header(f"### {name}'s pings", page, page_count)
    buttons = page_view.page_buttons("pings", int(user_id), page, page_count)
    return Layout((header, "\n".join(character.name for character in entries)), (buttons,) if buttons else ())


async def check_ping_page(client: discord.Client, user_id: int, page: int) -> Layout:
    # A click on Previous or Next; the user may have unsubscribed from everything since
    out = await check_ping(client, str(user_id), page)
    if isinstance(out, str):
        raise CommandError(out)
    return out
