import discord

from fjormcord.bot.artping.service import alias_service
from fjormcord.bot.artping.util.message_util import get_single_name, get_two_entries


def add_alias(client: discord.Client, message: discord.Message) -> str:
    return alias_service.add_alias(*get_two_entries(message.content, "character name", "alias"))


def remove_alias(client: discord.Client, message: discord.Message) -> str:
    return alias_service.remove_alias(*get_two_entries(message.content, "character name", "alias"))


def set_primary_name(client: discord.Client, message: discord.Message) -> str:
    return alias_service.set_primary_name(get_single_name(message.content, "alias"))
