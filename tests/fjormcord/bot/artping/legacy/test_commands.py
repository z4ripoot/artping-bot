from fjormcord.bot.artping.legacy.commands import COMMANDS, show_help
from fjormcord.bot.artping.util.message_util import MULTI_WORD_HINT
from tests.fakes import make_message


def test_help_starts_with_the_title_and_the_tips():
    out = show_help(None, make_message("~help"))

    assert out.texts[0].splitlines() == [
        "## Commands",
        "Content in brackets is what to add when using a command",
        MULTI_WORD_HINT,
        "All commands are also available as slash commands, type /",
    ]


def test_help_gives_each_section_a_heading_and_each_command_two_lines():
    out = show_help(None, make_message("~help"))

    art_pings = out.texts[1].splitlines()
    assert art_pings[:3] == [
        "### Art Ping Commands",
        "**~artping (character name)**",
        "Ping users for art of this character",
    ]
    assert out.texts[2].startswith("### Gacha Currency Commands\n**~setcurrency (currency name) (amount)**\n")


def test_help_hides_admin_commands_from_non_admins():
    out = show_help(None, make_message("~help"))

    assert len(out.texts) == 3
    assert "~removecharacter" not in "\n".join(out.texts)


def test_help_lists_every_command_for_admins():
    out = show_help(None, make_message("~help", administrator=True))

    assert len(out.texts) == 4
    assert out.texts[3].startswith("### Admin Commands\n")
    for command in COMMANDS:
        assert f"**{command.name}" in "\n".join(out.texts)


def test_admin_help_fits_one_message():
    out = show_help(None, make_message("~help", administrator=True))

    assert sum(len(text) for text in out.texts) <= 4000


def test_help_shows_add_character_to_non_admins():
    assert "**~addcharacter (character name)**" in show_help(None, make_message("~help")).texts[1]
