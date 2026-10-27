import discord
from discord import app_commands

from fjormcord.bot.artping.exception.command_error import CommandError
from fjormcord.bot.artping.repository import character_repository, currency_repository, resource_repository

# Discord shows at most this many autocomplete choices
MAX_CHOICES = 25


def to_name(value: str) -> str:
    # Slash options can contain spaces, names can't: "black knight" is the name Black_Knight
    name = "_".join(value.split())
    if not name:
        raise CommandError("A name can't be empty")
    return name


def _choices(names: list[str], current: str) -> list[app_commands.Choice[str]]:
    prefix = "_".join(current.split()).lower()
    return [app_commands.Choice(name=name, value=name) for name in names if name.lower().startswith(prefix)][
        :MAX_CHOICES]


async def character_choices(interaction: discord.Interaction, current: str) -> list[app_commands.Choice[str]]:
    return _choices(character_repository.get_all_names(), current)


async def currency_choices(interaction: discord.Interaction, current: str) -> list[app_commands.Choice[str]]:
    return _choices(currency_repository.get_currency_names(), current)


async def resource_choices(interaction: discord.Interaction, current: str) -> list[app_commands.Choice[str]]:
    return _choices(resource_repository.get_resource_names(), current)
