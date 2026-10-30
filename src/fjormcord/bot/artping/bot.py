import logging

import discord
from discord.ext import commands

from fjormcord.bot.artping import config
from fjormcord.bot.artping.cooldowns import Cooldowns
from fjormcord.bot.artping.legacy.dispatch import handle_message
from fjormcord.bot.artping.slash.cog.art_ping_cog import ArtPingCog
from fjormcord.bot.artping.slash.cog.character_cog import CharacterCog
from fjormcord.bot.artping.slash.cog.character_vote_cog import CharacterVoteCog
from fjormcord.bot.artping.slash.cog.currency_cog import CurrencyCog
from fjormcord.bot.artping.slash.cog.easter_egg_cog import EasterEggCog
from fjormcord.bot.artping.slash.cog.help_cog import HelpCog
from fjormcord.bot.artping.slash.cog.resource_cog import ResourceCog
from fjormcord.bot.artping.slash.cog.weekly_reminder_cog import WeeklyReminderCog
from fjormcord.bot.artping.slash.sync import sync_commands
from fjormcord.bot.artping.util.message_util import ALLOWED_MENTIONS
from fjormcord.bot.artping.view.page_view import PageButton
from fjormcord.bot.artping.view.scoreboard_view import CurrencySelect
from fjormcord.bot.artping.view.subscribe_view import SubscribeButton
from fjormcord.bot.artping.view.vote_view import VoteButton
from fjormcord.bot.artping.view.voting_gauntlet_view import TrackButton
from fjormcord.bot.artping.voting_gauntlet import start_voting_gauntlet_notification
from fjormcord.bot.artping.weekly_reminder import start_weekly_reminders


class ArtPingClient(commands.Bot):
    def __init__(self, **options):
        # The ~ commands are handled by legacy.dispatch, so the prefix is never used
        options.setdefault("command_prefix", commands.when_mentioned)
        options.setdefault("help_command", None)
        options.setdefault("allowed_mentions", ALLOWED_MENTIONS)
        super().__init__(**options)
        self.cooldowns = Cooldowns(config.read_settings().cooldown_seconds)

    async def setup_hook(self):
        await self.add_cog(CharacterVoteCog(self))
        await self.add_cog(ArtPingCog(self))
        await self.add_cog(CharacterCog())
        await self.add_cog(CurrencyCog())
        await self.add_cog(ResourceCog())
        await self.add_cog(EasterEggCog())
        await self.add_cog(HelpCog())
        await self.add_cog(WeeklyReminderCog())
        # Clicks on every control, also on messages sent before a restart: the Track buttons of the Voting Gauntlet
        # messages, the page buttons, the scoreboard's dropdown, Subscribe on new characters and Vote on the votes
        self.add_dynamic_items(TrackButton, PageButton, CurrencySelect, SubscribeButton, VoteButton)
        await sync_commands(self.tree, config.read_settings().guild_id)

    async def on_ready(self):
        logging.info("Initiating tasks")
        start_weekly_reminders(self)
        start_voting_gauntlet_notification(self)
        logging.info("Tasks are initiated")

    async def on_message(self, message: discord.Message):
        # The ~ commands are dispatched by hand; process_commands is never called, as there are no prefix commands
        await handle_message(self, message)
