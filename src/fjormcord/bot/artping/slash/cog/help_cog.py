from collections.abc import Iterable

import discord
from discord import app_commands
from discord.ext import commands

from fjormcord.bot.artping import config
from fjormcord.bot.artping.legacy.commands import COMMAND_PREFIX, COMMANDS, SECTION_ADMIN, help_layout
from fjormcord.bot.artping.model.layout import Layout
from fjormcord.bot.artping.slash.runner import is_admin_command, run
from fjormcord.bot.artping.slash.sync import registered_commands
from fjormcord.bot.artping.util.user_util import is_administrator

# The slash-only commands /help lists, each after the command it goes with; the easter eggs aren't listed
SLASH_ONLY_AFTER = {"resource": "resources"}

TIPS = [
    "Options in brackets are optional",
    "The same commands also work with ~, type ~help",
]


def format_slash_usage(command: app_commands.Command) -> str:
    # /scoreboard currency [page]; a run of optional options, as /artping's character2 ... character10, is shortened
    required = [parameter.name for parameter in command.parameters if parameter.required]
    optional = [parameter.name for parameter in command.parameters if not parameter.required]
    if len(optional) > 2:
        optional = [f"{optional[0]} … {optional[-1]}"]
    return " ".join([f"/{command.name}", *required, *(f"[{name}]" for name in optional)])


def show_slash_help(slash_commands: Iterable[app_commands.Command], administrator: bool) -> Layout:
    # As ~help: the sections and order of COMMANDS, the admin section only for admins, but in slash syntax with the
    # slash descriptions
    by_name = {command.name: command for command in slash_commands}
    entries = []
    for legacy in COMMANDS:
        name = legacy.name.removeprefix(COMMAND_PREFIX)
        names = [name, *(slash_only for slash_only, after in SLASH_ONLY_AFTER.items() if after == name)]
        for command in (by_name[name] for name in names if name in by_name):
            admin = is_admin_command(command)
            if admin and not administrator:
                continue
            section = SECTION_ADMIN if admin else legacy.section
            entries.append((section, format_slash_usage(command), command.description))
    return help_layout(TIPS, entries)


class HelpCog(commands.Cog):
    @app_commands.command(name="help", description="Shows an overview of all the available commands")
    async def help(self, interaction: discord.Interaction):
        # Private: the overview is only for the user who asked
        slash_commands = registered_commands(interaction.client.tree, config.read_settings().guild_id)
        administrator = is_administrator(interaction.user)
        await run(interaction, lambda: show_slash_help(slash_commands, administrator), ephemeral=True)
