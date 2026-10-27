import discord
from discord import app_commands
from discord.ext import commands

from fjormcord.bot.artping.model.character_vote import VoteChannel
from fjormcord.bot.artping.service import alias_service, character_service
from fjormcord.bot.artping.slash.options import CHARACTER_DESCRIPTION, character_choices, to_name
from fjormcord.bot.artping.slash.runner import admin_command, run

ALIAS_DESCRIPTION = "The alias; spaces are fine"


class CharacterCog(commands.Cog):
    @app_commands.command(
        name="addcharacter", description="Add a character to ping for; non-admins start a vote, voters get subscribed"
    )
    @app_commands.describe(character="The new character's name; spaces are fine")
    @app_commands.autocomplete(character=character_choices)
    async def add_character(self, interaction: discord.Interaction, character: str):
        # A vote message is a follow-up to the deferred interaction; wait=True returns it, as its ID identifies the vote
        vote_channel = VoteChannel(
            str(interaction.channel_id),
            interaction.guild is not None,
            lambda content, view: interaction.followup.send(content, view=view, wait=True),
        )
        await run(
            interaction,
            lambda: character_service.add_character(
                interaction.client, interaction.user, to_name(character), vote_channel
            ),
            defer=True,
        )

    @app_commands.command(name="checkcharacter", description="See which users are pinged for this character")
    @app_commands.describe(character=CHARACTER_DESCRIPTION)
    @app_commands.autocomplete(character=character_choices)
    async def check_character(self, interaction: discord.Interaction, character: str):
        await run(
            interaction, lambda: character_service.check_character(interaction.client, to_name(character)), defer=True
        )

    @admin_command(name="removecharacter", description="Remove a character and unsubscribe all its users")
    @app_commands.describe(character=CHARACTER_DESCRIPTION)
    @app_commands.autocomplete(character=character_choices)
    async def remove_character(self, interaction: discord.Interaction, character: str):
        await run(interaction, lambda: character_service.remove_character(to_name(character)))

    @admin_command(name="addalias", description="Add an alias to a character")
    @app_commands.describe(character=CHARACTER_DESCRIPTION, alias=ALIAS_DESCRIPTION)
    @app_commands.autocomplete(character=character_choices)
    async def add_alias(self, interaction: discord.Interaction, character: str, alias: str):
        await run(interaction, lambda: alias_service.add_alias(to_name(character), to_name(alias)))

    @admin_command(name="removealias", description="Remove an alias from a character")
    @app_commands.describe(character=CHARACTER_DESCRIPTION, alias=ALIAS_DESCRIPTION)
    @app_commands.autocomplete(character=character_choices)
    async def remove_alias(self, interaction: discord.Interaction, character: str, alias: str):
        await run(interaction, lambda: alias_service.remove_alias(to_name(character), to_name(alias)))

    @admin_command(
        name="setprimaryname", description="Make an alias the character's name; the old name becomes an alias"
    )
    @app_commands.describe(alias=ALIAS_DESCRIPTION)
    @app_commands.autocomplete(alias=character_choices)
    async def set_primary_name(self, interaction: discord.Interaction, alias: str):
        await run(interaction, lambda: alias_service.set_primary_name(to_name(alias)))
