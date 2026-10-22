import inspect
import logging

import discord

from fjormcord.bot.artping import config
from fjormcord.bot.artping.coliseum import start_coliseum_notification
from fjormcord.bot.artping.commands import COMMAND_PREFIX, COMMANDS_BY_NAME, MESSAGE_DENIED, format_usage
from fjormcord.bot.artping.util.message_util import MissingArgument, split_message
from fjormcord.bot.artping.util.user_util import is_administrator

# Replies echo user input, so never let a message trigger @everyone/@here or role pings
ALLOWED_MENTIONS = discord.AllowedMentions(everyone=False, roles=False, users=True, replied_user=True)

CONFIG = config.read_config()

LORENZ_SMILE = CONFIG.get('emoji', 'lorenz_smile')

CHROMK_1 = CONFIG.get('emoji', 'chromk_1')
CHROMK_2 = CONFIG.get('emoji', 'chromk_2')
CHROMK_3 = CONFIG.get('emoji', 'chromk_3')
CHROMK_4 = CONFIG.get('emoji', 'chromk_4')
CHROMK_5 = CONFIG.get('emoji', 'chromk_5')
CHROMK_6 = CONFIG.get('emoji', 'chromk_6')
CHROMK_7 = CONFIG.get('emoji', 'chromk_7')
CHROMK_8 = CONFIG.get('emoji', 'chromk_8')
CHROMK_9 = CONFIG.get('emoji', 'chromk_9')
CHROMK_10 = CONFIG.get('emoji', 'chromk_10')
CHROMK_11 = CONFIG.get('emoji', 'chromk_11')
CHROMK_12 = CONFIG.get('emoji', 'chromk_12')
CHROMK = f'{CHROMK_1}{CHROMK_2}{CHROMK_3}{CHROMK_4}\n{CHROMK_5}{CHROMK_6}{CHROMK_7}{CHROMK_8}\n{CHROMK_9}{CHROMK_10}{CHROMK_11}{CHROMK_12}'


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

        lowered = content.lower()
        if lowered == "thank you lorenz" or lowered == "thanks lorenz":
            await message.channel.send(LORENZ_SMILE)

        if lowered == "chromk":
            await message.channel.send(CHROMK)

        if not content.startswith(COMMAND_PREFIX):
            return

        command = COMMANDS_BY_NAME.get(lowered.split()[0])
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

