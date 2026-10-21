from fjormcord.bot.artping.commands import COMMANDS, show_help
from tests.fakes import make_message


def test_help_hides_admin_commands_from_non_admins():
    out = show_help(None, make_message("~help"))

    assert "~artping (character name): Ping users for art of this character" in out
    assert "Gacha Currency Commands:" in out
    assert "~addcharacter" not in out


def test_help_lists_every_command_for_admins():
    out = show_help(None, make_message("~help", administrator=True))

    assert "Admin Commands:" in out
    for command in COMMANDS:
        assert command.name in out


def test_help_explains_underscores_for_multi_word_names():
    assert "Use underscores for multi-word names, e.g. Black_Knight" in show_help(None, make_message("~help"))
