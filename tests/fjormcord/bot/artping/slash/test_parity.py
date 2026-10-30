from fjormcord.bot.artping.legacy.commands import COMMANDS
from fjormcord.bot.artping.slash.runner import is_admin_command
from tests.fakes import registered_slash_commands

# Slash-only: /resource posts a resource where ~(resource name) did, and the easter eggs are words in legacy
SLASH_ONLY = {"resource", "lorenz", "chromk"}


def test_every_legacy_command_has_a_slash_command():
    slash_names = {command.name for command in registered_slash_commands()}
    legacy_names = {command.name.removeprefix("~") for command in COMMANDS}

    assert legacy_names == slash_names - SLASH_ONLY


def test_admin_commands_are_the_same_in_both_syntaxes():
    admin_commands = [command for command in registered_slash_commands() if is_admin_command(command)]
    legacy_admin_names = {command.name.removeprefix("~") for command in COMMANDS if command.admin_only}

    assert {command.name for command in admin_commands} == legacy_admin_names
    # Hidden in DMs, where nobody is a server admin
    assert all(command.guild_only for command in admin_commands)
