import discord

from fjormcord.bot.artping.exception.missing_argument import MissingArgument
from fjormcord.bot.artping.service import art_ping_service
from fjormcord.bot.artping.util.message_util import get_entries, get_single_name


def do_art_ping(client: discord.Client, message: discord.Message) -> str:
    entries = get_entries(message.content)

    if not entries:
        raise MissingArgument("character name")

    return art_ping_service.do_art_ping(entries)


def add_ping(client: discord.Client, message: discord.Message) -> str:
    return art_ping_service.add_ping(str(message.author.id), get_single_name(message.content, "character name"))


def remove_ping(client: discord.Client, message: discord.Message) -> str:
    return art_ping_service.remove_ping(str(message.author.id), get_single_name(message.content, "character name"))


def check_ping(client: discord.Client, message: discord.Message) -> str:
    return art_ping_service.check_ping(str(message.author.id))
