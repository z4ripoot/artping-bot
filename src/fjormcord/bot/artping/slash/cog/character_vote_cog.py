import logging

import discord
from discord.ext import commands

from fjormcord.bot.artping.service.character_vote_service import check_open_votes, drop_deleted_vote


class CharacterVoteCog(commands.Cog):
    # No commands: the vote listeners (the client registers the Vote button). Votes are started by ~addcharacter and
    # /addcharacter.
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_ready(self):
        # Also runs after a reconnect, which is harmless: it only re-renders the open votes, or passes or drops them
        try:
            await check_open_votes(self.bot)
        except Exception:
            logging.exception("Checking the open votes failed")

    @commands.Cog.listener()
    async def on_raw_message_delete(self, payload: discord.RawMessageDeleteEvent):
        # The raw event also fires for messages sent before the bot started, such as older vote messages
        try:
            drop_deleted_vote(str(payload.message_id))
        except Exception:
            logging.exception("Dropping vote %s failed", payload.message_id)
