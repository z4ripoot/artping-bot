import discord

from fjormcord.bot.artping.service import resource_service
from fjormcord.bot.artping.util.message_util import get_single_name, get_two_entries


async def set_resource(client: discord.Client, message: discord.Message) -> str:
    name, link = get_two_entries(message.content, "resource name", "link")
    return await resource_service.set_resource(client, name, link)


def remove_resource(client: discord.Client, message: discord.Message) -> str:
    return resource_service.remove_resource(get_single_name(message.content, "resource name"))


def list_resources(client: discord.Client, message: discord.Message) -> str:
    return resource_service.list_resources()
