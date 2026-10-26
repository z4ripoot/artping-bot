import logging

import discord
from discord.ext import commands

from fjormcord.bot.artping import config
from fjormcord.bot.artping.coliseum import start_coliseum_notification
from fjormcord.bot.artping.cooldowns import Cooldowns
from fjormcord.bot.artping.legacy.dispatch import handle_message
from fjormcord.bot.artping.service.character_vote_service import check_open_votes, check_vote, drop_deleted_vote
from fjormcord.bot.artping.util.message_util import ALLOWED_MENTIONS


class ArtPingClient(commands.Bot):
    def __init__(self, **options):
        # The ~ commands are handled by legacy.dispatch, so the prefix is never used
        options.setdefault('command_prefix', commands.when_mentioned)
        options.setdefault('help_command', None)
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
        # The ~ commands are dispatched by hand; process_commands is never called, as there are no prefix commands
        await handle_message(self, message)
