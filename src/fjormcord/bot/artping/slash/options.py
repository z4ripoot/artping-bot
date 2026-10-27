import discord
from discord import app_commands

from fjormcord.bot.artping import config
from fjormcord.bot.artping.exception.command_error import CommandError
from fjormcord.bot.artping.repository import character_repository, currency_repository, resource_repository

# The description of an option that takes a character
CHARACTER_DESCRIPTION = "The character's name or an alias; spaces are fine"


def _underscore_spaces(value: str) -> str:
    # Slash options can contain spaces, names can't: "black knight" is the name Black_Knight
    return "_".join(value.split())


def to_name(value: str) -> str:
    name = _underscore_spaces(value)
    if not name:
        raise CommandError("A name can't be empty")
    return name


def _choices(get_names, current: str) -> list[app_commands.Choice[str]]:
    # get_names(prefix, limit) is a repository query; current is what the user typed so far
    names = get_names(_underscore_spaces(current), config.read_settings().autocomplete_max_choices)
    return [app_commands.Choice(name=name, value=name) for name in names]


async def character_choices(interaction: discord.Interaction, current: str) -> list[app_commands.Choice[str]]:
    return _choices(character_repository.get_all_names, current)


async def currency_choices(interaction: discord.Interaction, current: str) -> list[app_commands.Choice[str]]:
    return _choices(currency_repository.get_currency_names, current)


async def resource_choices(interaction: discord.Interaction, current: str) -> list[app_commands.Choice[str]]:
    return _choices(resource_repository.get_resource_names, current)
