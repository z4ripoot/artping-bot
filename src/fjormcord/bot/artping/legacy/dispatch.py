import logging

import discord

from fjormcord.bot.artping.easter_eggs import get_easter_egg_reply
from fjormcord.bot.artping.exception.command_error import CommandError
from fjormcord.bot.artping.exception.missing_argument import MissingArgument
from fjormcord.bot.artping.legacy.commands import COMMAND_PREFIX, COMMANDS_BY_NAME, Command, format_usage
from fjormcord.bot.artping.model.layout import Layout
from fjormcord.bot.artping.service.resource_service import get_resource_content
from fjormcord.bot.artping.util.message_util import await_reply, split_message
from fjormcord.bot.artping.util.user_util import is_administrator
from fjormcord.bot.artping.view.layout import message_options


async def handle_message(client: discord.Client, message: discord.Message):
    # Bots, this one included, get no reply at all, so no bot can make this one spam
    if message.author.bot:
        return

    content = message.content
    if not content:
        return

    easter_egg_reply = get_easter_egg_reply(content)
    if easter_egg_reply:
        await message.channel.send(easter_egg_reply)

    if not content.startswith(COMMAND_PREFIX):
        return

    word = content.split()[0]
    command = COMMANDS_BY_NAME.get(word.lower())
    if command is None:
        # Commands are looked up first, so a resource never hides one
        await send_resource(client, message, word.removeprefix(COMMAND_PREFIX))
        return

    logging.info("Received message from %s: %s", message.author.display_name, content)

    # Non-admins get no reply to admin commands to prevent bot spam
    if command.admin_only and not is_administrator(message.author):
        return

    out = await get_message(client, command, message)

    # Replies longer than Discord allows are sent as several messages; an empty reply sends nothing
    for options in message_options(out):
        await message.channel.send(**options)


async def send_resource(client: discord.Client, message: discord.Message, name: str):
    content = get_resource_content(name)
    if content is None:
        return

    # Posting a resource is a command too, so it has the cooldown
    try:
        with client.cooldowns.command(message.author):
            logging.info("Posting resource %s for %s", name, message.author.display_name)
            # The copied text may mention users or roles; posting it again must not ping them
            for chunk in split_message(content):
                await message.channel.send(chunk, allowed_mentions=discord.AllowedMentions.none())
    except CommandError as e:
        logging.warning(str(e))
        await message.channel.send(str(e))


async def get_message(client: discord.Client, command: Command, message: discord.Message) -> str | Layout:
    try:
        with client.cooldowns.command(message.author):
            out = await await_reply(command.handler(client, message))
    except MissingArgument as e:
        out = f"{e.argument.capitalize()} is missing. Usage: {format_usage(command)}"
        logging.warning(out)
    except CommandError as e:
        logging.warning(str(e))
        out = e.layout or str(e)
    except Exception:
        logging.exception("Command %s failed", command.name)
        out = f"Something went wrong while running {command.name}"
    return out
