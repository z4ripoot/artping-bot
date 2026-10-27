from fjormcord.bot.artping.legacy.commands import COMMANDS, show_help
from fjormcord.bot.artping.util.message_util import MULTI_WORD_HINT
from tests.fakes import make_message


def test_help_hides_admin_commands_from_non_admins():
    out = show_help(None, make_message("~help"))

    assert "~artping (character name): Ping users for art of this character" in out
    assert "Gacha Currency Commands:" in out
    assert "~removecharacter" not in out


def test_help_lists_every_command_for_admins():
    out = show_help(None, make_message("~help", administrator=True))

    assert "Admin Commands:" in out
    for command in COMMANDS:
        assert command.name in out


def test_help_explains_underscores_for_multi_word_names():
    assert "Use underscores for multi-word names, e.g. Black_Knight" in show_help(None, make_message("~help"))


def test_help_shows_add_character_to_non_admins():
    assert "~addcharacter (character name): " in show_help(None, make_message("~help"))


def test_help_mentions_slash_commands():
    lines = show_help(None, make_message("~help")).splitlines()

    assert lines[lines.index(MULTI_WORD_HINT) + 1] == "All commands are also available as slash commands, type /"
