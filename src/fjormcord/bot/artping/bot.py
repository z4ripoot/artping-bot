import logging

import discord
from discord.ext import commands

from fjormcord.bot.artping import config
from fjormcord.bot.artping.coliseum import start_coliseum_notification
from fjormcord.bot.artping.cooldowns import Cooldowns
from fjormcord.bot.artping.legacy.dispatch import handle_message
from fjormcord.bot.artping.slash.art_ping_cog import ArtPingCog
from fjormcord.bot.artping.slash.character_cog import CharacterCog
from fjormcord.bot.artping.slash.character_vote_cog import CharacterVoteCog
from fjormcord.bot.artping.slash.easter_egg_cog import EasterEggCog
from fjormcord.bot.artping.slash.sync import sync_commands
from fjormcord.bot.artping.util.message_util import ALLOWED_MENTIONS


class ArtPingClient(commands.Bot):
    def __init__(self, **options):
        # The ~ commands are handled by legacy.dispatch, so the prefix is never used
        options.setdefault('command_prefix', commands.when_mentioned)
        options.setdefault('help_command', None)
        options.setdefault('allowed_mentions', ALLOWED_MENTIONS)
        super().__init__(**options)
        self.cooldowns = Cooldowns()

    async def setup_hook(self):
        await self.add_cog(CharacterVoteCog(self))
        await self.add_cog(ArtPingCog(self))
        await self.add_cog(CharacterCog(self))
        await self.add_cog(EasterEggCog(self))
        await sync_commands(self.tree, config.read_settings().guild_id)

    async def on_ready(self):
        logging.info("Initiating tasks")
        start_coliseum_notification(self)
        logging.info("Tasks are initiated")

    async def on_message(self, message: discord.Message):
        # The ~ commands are dispatched by hand; process_commands is never called, as there are no prefix commands
        await handle_message(self, message)
