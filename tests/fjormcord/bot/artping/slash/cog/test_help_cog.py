from types import SimpleNamespace

from fjormcord.bot.artping.slash.cog.art_ping_cog import ArtPingCog, build_art_ping_command
from fjormcord.bot.artping.slash.cog.character_cog import CharacterCog
from fjormcord.bot.artping.slash.cog.currency_cog import CurrencyCog
from fjormcord.bot.artping.slash.cog.easter_egg_cog import EasterEggCog
from fjormcord.bot.artping.slash.cog.help_cog import HelpCog, show_slash_help
from fjormcord.bot.artping.slash.cog.resource_cog import ResourceCog
from fjormcord.bot.artping.slash.cog.voting_gauntlet_cog import VotingGauntletCog
from fjormcord.bot.artping.slash.cog.weekly_reminder_cog import WeeklyReminderCog
from tests.fakes import FakeInteraction, invoke


def all_commands(max_characters=10):
    # Every slash command, as the bot registers them
    cogs = [
        ArtPingCog(None),
        CharacterCog(),
        CurrencyCog(),
        ResourceCog(),
        EasterEggCog(),
        HelpCog(),
        WeeklyReminderCog(),
        VotingGauntletCog(),
    ]
    return [build_art_ping_command(max_characters), *(command for cog in cogs for command in cog.get_app_commands())]


def help_text(administrator=False):
    return "\n".join(show_slash_help(all_commands(), administrator).texts)


def test_help_starts_with_the_title_and_the_tips():
    out = show_slash_help(all_commands(), administrator=False)

    assert out.texts[0].splitlines() == [
        "## Commands",
        "Options in brackets are optional",
        "The same commands also work with ~, type ~help",
    ]


def test_help_lists_the_slash_commands_in_the_sections_of_legacy_help():
    out = show_slash_help(all_commands(), administrator=False)

    assert out.texts[1].splitlines()[:3] == [
        "### Art Ping Commands",
        "**/artping character [character2 … character10]**",
        "Ping users for art of these characters",
    ]
    assert out.texts[2].startswith("### Gacha Currency Commands\n**/setcurrency currency amount**\n")
    assert "**/scoreboard currency [page]**" in out.texts[2]


def test_help_lists_resource_after_resources_and_leaves_out_the_easter_eggs():
    text = help_text()

    assert text.index("**/resources**") < text.index("**/resource name**") < text.index("**/help**")
    assert "/lorenz" not in text
    assert "/chromk" not in text


def test_help_lists_the_optional_characters_of_a_short_artping_one_by_one():
    out = show_slash_help(all_commands(max_characters=3), administrator=False)

    assert "**/artping character [character2] [character3]**" in out.texts[1]


def test_help_hides_admin_commands_from_non_admins():
    out = show_slash_help(all_commands(), administrator=False)

    assert len(out.texts) == 4
    assert out.texts[3].startswith("### Reminder Commands\n**/closingtimes**\n")
    assert "/removecharacter" not in "\n".join(out.texts)


def test_help_lists_every_command_but_the_easter_eggs_for_admins():
    out = show_slash_help(all_commands(), administrator=True)

    assert out.texts[4].startswith("### Admin Commands\n")
    for command in all_commands():
        if command.name not in ("lorenz", "chromk"):
            assert f"**/{command.name}" in "\n".join(out.texts)


def test_admin_help_fits_one_message():
    assert sum(len(text) for text in show_slash_help(all_commands(25), administrator=True).texts) <= 4000


def test_help_is_private_and_reads_the_registered_commands():
    interaction = FakeInteraction(administrator=True)
    interaction.client.tree = SimpleNamespace(get_commands=lambda guild=None: all_commands())

    cog = HelpCog()
    invoke(cog.help, interaction, cog)

    [sent] = interaction.sent
    assert sent.ephemeral is True
    assert sent.content.startswith("## Commands\n")
    assert "Admin Commands" in sent.content
