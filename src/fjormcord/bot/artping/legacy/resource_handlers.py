import discord

from fjormcord.bot.artping.service import resource_service
from fjormcord.bot.artping.util.message_util import MESSAGE_ONE_NAME_ONLY, CommandError, MissingArgument, \
    get_entries, get_single_name


async def set_resource(client: discord.Client, message: discord.Message) -> str:
    entries = get_entries(message.content)

    if not entries:
        raise MissingArgument("resource name")
    if len(entries) > 2:
        raise CommandError(MESSAGE_ONE_NAME_ONLY)
    if len(entries) == 1:
        raise MissingArgument("link")

    name, link = entries
    return await resource_service.set_resource(client, name, link)


def remove_resource(client: discord.Client, message: discord.Message) -> str:
    return resource_service.remove_resource(get_single_name(message.content, "resource name"))


def list_resources(client: discord.Client, message: discord.Message) -> str:
    return resource_service.list_resources()
