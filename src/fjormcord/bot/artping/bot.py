import inspect
import logging
import math

import discord

from fjormcord.bot.artping import config
from fjormcord.bot.artping.coliseum import start_coliseum_notification
from fjormcord.bot.artping.commands import COMMAND_PREFIX, COMMANDS_BY_NAME, format_usage, Command
from fjormcord.bot.artping.cooldowns import Cooldowns
from fjormcord.bot.artping.easter_eggs import get_easter_egg_reply
from fjormcord.bot.artping.service.character_vote_service import check_open_votes, check_vote, drop_deleted_vote
from fjormcord.bot.artping.service.resource_service import get_resource_content
from fjormcord.bot.artping.util.message_util import CommandError, MissingArgument, split_message
from fjormcord.bot.artping.util.user_util import is_administrator

# Replies echo user input, so never let a message trigger @everyone/@here or role pings
ALLOWED_MENTIONS = discord.AllowedMentions(everyone=False, roles=False, users=True, replied_user=True)


class ArtPingClient(discord.Client):
    def __init__(self, **options):
        options.setdefault('allowed_mentions', ALLOWED_MENTIONS)
        super().__init__(**options)
        self.cooldowns = Cooldowns()

    async def on_ready(self):
        logging.info("Initiating tasks")
        start_coliseum_notification(self)
        logging.info("Tasks are initiated")
        # Also runs after a reconnect, which is harmless: a vote is only added once
        await check_open_votes(self)

    # The raw events also fire for messages sent before the bot started, such as older vote messages
    async def on_raw_reaction_add(self, payload: discord.RawReactionActionEvent):
        if payload.user_id == self.user.id or str(payload.emoji) != config.read_settings().character_vote_emoji:
            return
        try:
            await check_vote(self, str(payload.message_id))
        except Exception:
            logging.exception("Checking vote %s failed", payload.message_id)

    async def on_raw_message_delete(self, payload: discord.RawMessageDeleteEvent):
        try:
            drop_deleted_vote(str(payload.message_id))
        except Exception:
            logging.exception("Dropping vote %s failed", payload.message_id)

    async def on_message(self, message: discord.Message):
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
            await self.send_resource(message, word.removeprefix(COMMAND_PREFIX))
            return

        logging.info("Received message from %s: %s", message.author.display_name, content)

        # Non-admins get no reply to admin commands to prevent bot spam
        if command.admin_only and not is_administrator(message.author):
            return

        out = await self.get_message(command, message)

        # Replies longer than Discord allows are sent as several messages; an empty reply sends nothing
        for chunk in split_message(out):
            await message.channel.send(chunk)

    async def send_resource(self, message: discord.Message, name: str):
        content = get_resource_content(name)
        if content is None:
            return

        logging.info("Posting resource %s for %s", name, message.author.display_name)
        # The copied text may mention users or roles; posting it again must not ping them
        for chunk in split_message(content):
            await message.channel.send(chunk, allowed_mentions=discord.AllowedMentions.none())

    async def get_message(self, command: Command, message: discord.Message) -> str:
        try:
            self._check_cooldown(command, message.author)
            out = command.handler(self, message)
            if inspect.isawaitable(out):
                out = await out
            # Only a command that succeeded starts the cooldown, so a mistake can be corrected right away
            self._start_cooldown(command, message.author)
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

    def _check_cooldown(self, command: Command, author: discord.abc.User):
        # Turns the command down while the user's cooldown for it runs
        remaining = self.cooldowns.remaining(command.name, author.id)
        if remaining > 0:
            seconds = math.ceil(remaining)
            raise CommandError(
                f"You used {command.name} recently. Try again in {seconds} second{'' if seconds == 1 else 's'}")

    def _start_cooldown(self, command: Command, author: discord.abc.User):
        # Admins never get a cooldown, so _check_cooldown doesn't have to exempt them
        if command.cooldown_seconds > 0 and not is_administrator(author):
            self.cooldowns.start(command.name, author.id, command.cooldown_seconds)
