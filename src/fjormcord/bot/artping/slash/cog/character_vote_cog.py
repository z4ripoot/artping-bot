import logging

import discord
from discord.ext import commands

from fjormcord.bot.artping.service.character_vote_service import drop_deleted_vote


class CharacterVoteCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_raw_message_delete(self, payload: discord.RawMessageDeleteEvent):
        try:
            drop_deleted_vote(str(payload.message_id))
        except Exception:
            logging.exception("Dropping vote %s failed", payload.message_id)
