import discord

from fjormcord.bot.artping.exception.command_error import CommandError
from fjormcord.bot.artping.model.character import Character
from fjormcord.bot.artping.model.character_vote import VoteChannel
from fjormcord.bot.artping.model.layout import Layout
from fjormcord.bot.artping.repository import alias_repository, art_ping_repository, character_repository
from fjormcord.bot.artping.service import character_vote_service  # A module: it imports this one too
from fjormcord.bot.artping.util.message_util import log_info
from fjormcord.bot.artping.util.name_util import normalize_name
from fjormcord.bot.artping.util.page_util import get_page, paged_header
from fjormcord.bot.artping.util.user_util import get_username, is_administrator
from fjormcord.bot.artping.view import page_view, subscribe_view  # Modules: they import this one too


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


async def add_character(
    client: discord.Client, user: discord.abc.User, name: str, vote_channel: VoteChannel
) -> str | Layout:
    entry = normalize_name(name)

    require_unused_name(entry)

    # Non-admins start a vote instead; the character is added once enough users, or an admin, click its button
    if not is_administrator(user) and character_vote_service.is_voting_enabled():
        return await character_vote_service.start_vote(vote_channel, str(user.id), entry)

    character = Character(character_repository.add_character(entry), entry)
    await character_vote_service.close_votes(client, character)

    text = log_info(f"Character {entry} has been added")
    return Layout((text,), ((subscribe_view.SubscribeButton.for_character(character),),))


def remove_character(name: str) -> str:
    character = require_character(name)

    character_repository.remove_character(character.id)

    return log_info(f"Character {character.name} has been removed")


async def check_character(client: discord.Client, name: str, page: int = 1) -> Layout:
    return await _render_character(client, require_character(name), page)


async def check_character_page(client: discord.Client, character_id: int, page: int) -> Layout:
    # A click on Previous or Next; the character may have been removed since
    character = character_repository.get_character_by_id(character_id)
    if character is None:
        raise CommandError("This character doesn't exist anymore")
    return await _render_character(client, character, page)


async def _render_character(client: discord.Client, character: Character, page: int) -> Layout:
    # The header with the aliases, then the subscribers' names, one per line, 10 per page
    user_ids = art_ping_repository.get_art_ping_users((character.id,))
    aliases = alias_repository.get_aliases(character.id)
    aliases_line = f"\nAliases: {', '.join(aliases)}" if aliases else ""

    if not user_ids:
        return Layout((f"### {character.name}'s pings{aliases_line}", f"Nobody is subscribed to {character.name}"))

    entries, page_count = get_page(user_ids, page, f"The list of {character.name}'s pings")
    header = paged_header(f"### {character.name}'s pings", page, page_count) + aliases_line
    # Only the users on this page are looked up
    usernames = [await get_username(client, user_id) for user_id in entries]
    buttons = page_view.page_buttons("character", character.id, page, page_count)
    return Layout((header, "\n".join(usernames)), (buttons,) if buttons else ())
