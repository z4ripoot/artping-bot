import inspect
import logging

import discord

from fjormcord.bot.artping.coliseum import start_coliseum_notification
from fjormcord.bot.artping.commands import COMMAND_PREFIX, COMMANDS_BY_NAME, MESSAGE_DENIED, format_usage
from fjormcord.bot.artping.easter_eggs import get_easter_egg_reply
from fjormcord.bot.artping.util.message_util import MissingArgument, split_message
from fjormcord.bot.artping.util.user_util import is_administrator

# Replies echo user input, so never let a message trigger @everyone/@here or role pings
ALLOWED_MENTIONS = discord.AllowedMentions(everyone=False, roles=False, users=True, replied_user=True)


class ArtPingClient(discord.Client):
    def __init__(self, **options):
        options.setdefault('allowed_mentions', ALLOWED_MENTIONS)
        super().__init__(**options)

    async def on_ready(self):
        logging.info("Initiating tasks")
        start_coliseum_notification(self)
        logging.info("Tasks are initiated")

    async def on_message(self, message: discord.Message):
        if message.author == self.user:
            return

        content = message.content
        if not content:
            return

        easter_egg_reply = get_easter_egg_reply(content)
        if easter_egg_reply:
            await message.channel.send(easter_egg_reply)

        if not content.startswith(COMMAND_PREFIX):
            return

        command = COMMANDS_BY_NAME.get(content.split()[0].lower())
        if command is None:
            return

        logging.info(f"Received message from {message.author.display_name}: {content}")

        if command.admin_only and not is_administrator(message.author):
            await message.channel.send(MESSAGE_DENIED)
            return

        try:
            out = command.handler(self, message)
            if inspect.isawaitable(out):
                out = await out
        except MissingArgument as e:
            out = f"{e.argument.capitalize()} is missing. Usage: {format_usage(command)}"
            logging.warning(out)
        except Exception:
            logging.exception("Command %s failed", command.name)
            out = f"Something went wrong while running {command.name}"

        for chunk in split_message(out):
            await message.channel.send(chunk)

