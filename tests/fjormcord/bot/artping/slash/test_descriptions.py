from fjormcord.bot.artping.slash.art_ping_cog import ArtPingCog, build_art_ping_command
from fjormcord.bot.artping.slash.character_cog import CharacterCog
from fjormcord.bot.artping.slash.easter_egg_cog import EasterEggCog

MAX_DESCRIPTION = 100


def test_descriptions_fit_discord():
    # Extend this as cogs are added
    commands = [command for cog in (ArtPingCog(None), CharacterCog(None), EasterEggCog(None)) for command in cog.get_app_commands()]
    commands.append(build_art_ping_command(3))

    assert len(commands) == 12
    for command in commands:
        assert 0 < len(command.description) <= MAX_DESCRIPTION, command.name
        for parameter in command.parameters:
            assert 0 < len(parameter.description) <= MAX_DESCRIPTION, f"{command.name} {parameter.name}"
