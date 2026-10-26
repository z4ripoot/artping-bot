import asyncio

from fjormcord.bot.artping.repository import alias_repository, art_ping_repository, character_repository
from fjormcord.bot.artping.slash.art_ping_cog import ArtPingCog, build_art_ping_command
from tests.fakes import FakeInteraction, invoke


class FakeBot:
    def __init__(self):
        self.tree = FakeTree()


class FakeTree:
    def __init__(self):
        self.commands = []

    def add_command(self, command):
        self.commands.append(command)

    def remove_command(self, name):
        self.commands = [command for command in self.commands if command.name != name]


def add_lucina_pinged_by(user_id):
    character_repository.add_character("Lucina")
    character = character_repository.get_character("Lucina")
    alias_repository.add_alias(character.id, "Marth_Mask")
    art_ping_repository.add_ping(character.id, str(user_id))


def test_art_ping_options_follow_the_setting():
    assert [p.name for p in build_art_ping_command(3).parameters] == ["character", "character2", "character3"]
    assert len(build_art_ping_command(10).parameters) == 10


def test_art_ping_pings_subscribers():
    add_lucina_pinged_by(5)
    interaction = FakeInteraction()

    invoke(build_art_ping_command(3), interaction, character="Lucina")

    assert [(content, ephemeral) for content, ephemeral, _ in interaction.sent] == [("Lucina: <@5>", False)]


def test_art_ping_pings_a_character_once():
    add_lucina_pinged_by(5)
    interaction = FakeInteraction()

    invoke(build_art_ping_command(3), interaction, character="Lucina", character2="marth mask")

    assert [content for content, _, _ in interaction.sent] == ["Lucina: <@5>"]


def test_art_ping_has_a_cooldown():
    add_lucina_pinged_by(5)
    command = build_art_ping_command(3)
    first, second = FakeInteraction(), FakeInteraction()
    second.client = first.client

    invoke(command, first, character="Lucina")
    invoke(command, second, character="Lucina")

    assert second.sent[0][1] is True


def test_add_ping_with_spaces():
    character_repository.add_character("Black_Knight")
    interaction = FakeInteraction()

    cog = ArtPingCog(FakeBot())

    invoke(cog.add_ping, interaction, cog, character="black knight")

    assert interaction.sent[0][0] == "Ping for Black_Knight has been added"


def test_remove_and_check_ping():
    add_lucina_pinged_by(1)
    cog = ArtPingCog(FakeBot())
    check, remove = FakeInteraction(), FakeInteraction()

    invoke(cog.check_ping, check, cog)
    invoke(cog.remove_ping, remove, cog, character="Lucina")

    assert "Lucina" in check.sent[0][0]
    assert remove.sent[0][0] == "Ping for Lucina has been removed"


def test_cog_adds_and_removes_the_art_ping_command():
    bot = FakeBot()
    cog = ArtPingCog(bot)

    asyncio.run(cog.cog_load())
    assert [command.name for command in bot.tree.commands] == ["artping"]

    asyncio.run(cog.cog_unload())
    assert bot.tree.commands == []
