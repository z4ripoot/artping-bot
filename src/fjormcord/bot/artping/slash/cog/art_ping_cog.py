import inspect

import discord
from discord import app_commands
from discord.ext import commands

from fjormcord.bot.artping import config
from fjormcord.bot.artping.service import art_ping_service
from fjormcord.bot.artping.slash.options import (
    CHARACTER_DESCRIPTION,
    character_choices,
    subscribed_character_choices,
    to_name,
)
from fjormcord.bot.artping.slash.runner import run


def build_art_ping_command(max_characters: int) -> app_commands.Command:
    # /artping takes up to max_characters characters, as options character, character2, character3, ...; Discord
    # needs one option per character, so the callback's signature is generated from the setting
    names = ["character"] + [f"character{number}" for number in range(2, max_characters + 1)]

    async def art_ping(interaction: discord.Interaction, **characters: str | None):
        values = [value for value in characters.values() if value is not None]
        await run(interaction, lambda: art_ping_service.do_art_ping([to_name(value) for value in values]))

    keyword_only = inspect.Parameter.KEYWORD_ONLY
    parameters = [
        inspect.Parameter("interaction", inspect.Parameter.POSITIONAL_OR_KEYWORD, annotation=discord.Interaction),
        # The first character is required, the others are optional
        inspect.Parameter(names[0], keyword_only, annotation=str),
        *(inspect.Parameter(name, keyword_only, default=None, annotation=str | None) for name in names[1:]),
    ]
    art_ping.__signature__ = inspect.Signature(parameters)
    art_ping.__annotations__ = {parameter.name: parameter.annotation for parameter in parameters}

    art_ping = app_commands.describe(**{name: CHARACTER_DESCRIPTION for name in names})(art_ping)
    art_ping = app_commands.autocomplete(**{name: character_choices for name in names})(art_ping)
    return app_commands.Command(name="artping", description="Ping users for art of these characters", callback=art_ping)


class ArtPingCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self._art_ping = None

    async def cog_load(self):
        # Built here as its options depend on the settings
        self._art_ping = build_art_ping_command(config.read_settings().art_ping_slash_max_characters)
        self.bot.tree.add_command(self._art_ping)

    async def cog_unload(self):
        self.bot.tree.remove_command(self._art_ping.name)

    @app_commands.command(name="addping", description="Add yourself to the ping list for when this character is pinged")
    @app_commands.describe(character=CHARACTER_DESCRIPTION)
    @app_commands.autocomplete(character=character_choices)
    async def add_ping(self, interaction: discord.Interaction, character: str):
        await run(interaction, lambda: art_ping_service.add_ping(str(interaction.user.id), to_name(character)))

    @app_commands.command(name="removeping", description="Remove yourself from the ping list of this character")
    @app_commands.describe(character=CHARACTER_DESCRIPTION)
    @app_commands.autocomplete(character=subscribed_character_choices)
    async def remove_ping(self, interaction: discord.Interaction, character: str):
        await run(interaction, lambda: art_ping_service.remove_ping(str(interaction.user.id), to_name(character)))

    @app_commands.command(name="checkping", description="See which characters you are being pinged for")
    async def check_ping(self, interaction: discord.Interaction):
        # Private, so only the user sees their pings and turns the pages; deferred, as the user's name may be fetched
        await run(
            interaction,
            lambda: art_ping_service.check_ping(interaction.client, str(interaction.user.id)),
            defer=True,
            ephemeral=True,
        )
