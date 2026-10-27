from fjormcord.bot.artping.slash.cog.art_ping_cog import ArtPingCog, build_art_ping_command
from fjormcord.bot.artping.slash.cog.character_cog import CharacterCog
from fjormcord.bot.artping.slash.cog.currency_cog import CurrencyCog
from fjormcord.bot.artping.slash.cog.easter_egg_cog import EasterEggCog
from fjormcord.bot.artping.slash.cog.resource_cog import ResourceCog

MAX_DESCRIPTION = 100


def test_descriptions_fit_discord():
    # Extend this as cogs are added
    cogs = (ArtPingCog(None), CharacterCog(None), CurrencyCog(None), ResourceCog(None), EasterEggCog(None))
    commands = [command for cog in cogs for command in cog.get_app_commands()]
    commands.append(build_art_ping_command(3))

    assert len(commands) == 22
    for command in commands:
        assert 0 < len(command.description) <= MAX_DESCRIPTION, command.name
        for parameter in command.parameters:
            assert 0 < len(parameter.description) <= MAX_DESCRIPTION, f"{command.name} {parameter.name}"
