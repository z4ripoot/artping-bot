import discord
from discord import app_commands
from discord.ext import commands

from fjormcord.bot.artping.service import resource_service
from fjormcord.bot.artping.slash.options import resource_choices
from fjormcord.bot.artping.slash.runner import admin_command, run

RESOURCE_DESCRIPTION = "The resource's name"


class ResourceCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(name="resource", description="Post a resource; /resources lists them")
    @app_commands.describe(name=RESOURCE_DESCRIPTION)
    @app_commands.autocomplete(name=resource_choices)
    async def resource(self, interaction: discord.Interaction, name: str):
        # The copied text may mention users
        await run(interaction, "resource", lambda: resource_service.post_resource(name),
                  allowed_mentions=discord.AllowedMentions.none())

    @app_commands.command(name="resources", description="See which resources there are; /resource posts one")
    async def resources(self, interaction: discord.Interaction):
        await run(interaction, "resources", lambda: resource_service.list_resources(slash=True))

    @admin_command(name="setresource",
                   description="Save the text of a Discord message, or a website link, to post with /resource")
    @app_commands.describe(name="The new resource's name: letters, digits, _ and -",
                           link="A Discord message link or a website")
    async def set_resource(self, interaction: discord.Interaction, name: str, link: str):
        await run(interaction, "setresource", lambda: resource_service.set_resource(interaction.client, name, link),
                  defer=True)

    @admin_command(name="removeresource", description="Remove a resource")
    @app_commands.describe(name=RESOURCE_DESCRIPTION)
    @app_commands.autocomplete(name=resource_choices)
    async def remove_resource(self, interaction: discord.Interaction, name: str):
        await run(interaction, "removeresource", lambda: resource_service.remove_resource(name))
