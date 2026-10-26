import discord

from fjormcord.bot.artping.service import alias_service
from fjormcord.bot.artping.util.message_util import MESSAGE_ONE_NAME_ONLY, CommandError, MissingArgument, \
    get_entries, get_single_name


def _get_name_and_alias(content: str) -> tuple[str, str]:
    entries = get_entries(content)

    if not entries:
        raise MissingArgument("character name")
    if len(entries) > 2:
        raise CommandError(MESSAGE_ONE_NAME_ONLY)
    if len(entries) == 1:
        raise MissingArgument("alias")

    name, alias = entries
    return name, alias


def add_alias(client: discord.Client, message: discord.Message) -> str:
    return alias_service.add_alias(*_get_name_and_alias(message.content))


def remove_alias(client: discord.Client, message: discord.Message) -> str:
    return alias_service.remove_alias(*_get_name_and_alias(message.content))


def set_primary_name(client: discord.Client, message: discord.Message) -> str:
    return alias_service.set_primary_name(get_single_name(message.content, "alias"))
