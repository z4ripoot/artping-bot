from fjormcord.bot.artping.legacy.commands import COMMANDS
from fjormcord.bot.artping.slash.cog.art_ping_cog import ArtPingCog, build_art_ping_command
from fjormcord.bot.artping.slash.cog.character_cog import CharacterCog
from fjormcord.bot.artping.slash.cog.currency_cog import CurrencyCog
from fjormcord.bot.artping.slash.cog.easter_egg_cog import EasterEggCog
from fjormcord.bot.artping.slash.cog.help_cog import HelpCog
from fjormcord.bot.artping.slash.cog.resource_cog import ResourceCog

# Slash-only: /resource posts a resource where ~(resource name) did, and the easter eggs are words in legacy
SLASH_ONLY = {"resource", "lorenz", "chromk"}


def test_every_legacy_command_has_a_slash_command():
    cogs = [ArtPingCog(None), CharacterCog(), CurrencyCog(), ResourceCog(), EasterEggCog(), HelpCog()]
    slash_names = {command.name for cog in cogs for command in cog.get_app_commands()}
    slash_names.add(build_art_ping_command(1).name)

    legacy_names = {command.name.removeprefix("~") for command in COMMANDS}

    assert legacy_names == slash_names - SLASH_ONLY
