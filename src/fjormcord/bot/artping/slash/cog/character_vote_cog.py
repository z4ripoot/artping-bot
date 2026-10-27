import logging

import discord
from discord.ext import commands

from fjormcord.bot.artping.service.character_vote_service import check_open_votes, drop_deleted_vote
from fjormcord.bot.artping.vote_view import VoteView


class CharacterVoteCog(commands.Cog):
    # No commands: the vote button and the vote listeners. Votes are started by ~addcharacter and /addcharacter.
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    async def cog_load(self):
        # Routes clicks on every vote message, also those sent before a restart, to the button's callback
        self.bot.add_view(VoteView())

    @commands.Cog.listener()
    async def on_ready(self):
        # Also runs after a reconnect, which is harmless: a vote is only added and converted once
        try:
            await check_open_votes(self.bot)
        except Exception:
            logging.exception("Checking the open votes failed")

    # The raw event also fires for messages sent before the bot started, such as older vote messages
    @commands.Cog.listener()
    async def on_raw_message_delete(self, payload: discord.RawMessageDeleteEvent):
        try:
            drop_deleted_vote(str(payload.message_id))
        except Exception:
            logging.exception("Dropping vote %s failed", payload.message_id)
