import inspect
import logging
import math
from time import monotonic

import discord

from fjormcord.bot.artping.coliseum import start_coliseum_notification
from fjormcord.bot.artping.commands import COMMAND_PREFIX, COMMANDS_BY_NAME, format_usage, Command
from fjormcord.bot.artping.easter_eggs import get_easter_egg_reply
from fjormcord.bot.artping.util.message_util import CommandError, MissingArgument, split_message
from fjormcord.bot.artping.util.user_util import is_administrator

# Replies echo user input, so never let a message trigger @everyone/@here or role pings
ALLOWED_MENTIONS = discord.AllowedMentions(everyone=False, roles=False, users=True, replied_user=True)


class ArtPingClient(discord.Client):
    def __init__(self, **options):
        options.setdefault('allowed_mentions', ALLOWED_MENTIONS)
        super().__init__(**options)
        # (command name, user ID) -> monotonic() time from which the user can use the command again;
        # kept in memory, so cooldowns reset when the bot restarts
        self._cooldown_ends = {}

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

        logging.info("Received message from %s: %s", message.author.display_name, content)

        # Non-admins get no reply to admin commands to prevent bot spam
        if command.admin_only and not is_administrator(message.author):
            return

        out = await self.get_message(command, message)

        # Replies longer than Discord allows are sent as several messages
        for chunk in split_message(out):
            await message.channel.send(chunk)

    async def get_message(self, command: Command, message: discord.Message) -> str:
        now = monotonic()
        try:
            self._check_cooldown(command, message.author, now)
            out = command.handler(self, message)
            if inspect.isawaitable(out):
                out = await out
            # Only a command that succeeded starts the cooldown, so a mistake can be corrected right away
            self._start_cooldown(command, message.author, now)
        except MissingArgument as e:
            out = f"{e.argument.capitalize()} is missing. Usage: {format_usage(command)}"
            logging.warning(out)
        except CommandError as e:
            out = str(e)
            logging.warning(out)
        except Exception:
            logging.exception("Command %s failed", command.name)
            out = f"Something went wrong while running {command.name}"
        return out

    def _check_cooldown(self, command: Command, author: discord.abc.User, now: float):
        # Turns the command down while the user's cooldown for it runs
        remaining = self._cooldown_ends.get((command.name, author.id), now) - now
        if remaining > 0:
            seconds = math.ceil(remaining)
            raise CommandError(
                f"You used {command.name} recently. Try again in {seconds} second{'' if seconds == 1 else 's'}")

    def _start_cooldown(self, command: Command, author: discord.abc.User, now: float):
        # Admins never get a cooldown, so _check_cooldown doesn't have to exempt them
        if command.cooldown_seconds > 0 and not is_administrator(author):
            self._cooldown_ends[(command.name, author.id)] = now + command.cooldown_seconds
