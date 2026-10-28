import discord

from fjormcord.bot.artping.model.character_vote import VoteChannel
from fjormcord.bot.artping.model.layout import Layout
from fjormcord.bot.artping.service import character_service
from fjormcord.bot.artping.util.message_util import get_single_name


async def add_character(client: discord.Client, message: discord.Message) -> str | Layout:
    name = get_single_name(message.content, "character name")
    vote_channel = VoteChannel(
        str(message.channel.id),
        message.guild is not None,
        lambda view: message.channel.send(view=view),
    )
    return await character_service.add_character(client, message.author, name, vote_channel)


def remove_character(client: discord.Client, message: discord.Message) -> str:
    return character_service.remove_character(get_single_name(message.content, "character name"))


async def check_character(client: discord.Client, message: discord.Message) -> str:
    return await character_service.check_character(client, get_single_name(message.content, "character name"))
