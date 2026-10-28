import pytest

from fjormcord.bot.artping.repository import alias_repository, character_repository, character_vote_repository
from fjormcord.bot.artping.slash.cog.character_cog import CharacterCog
from tests.fakes import FakeInteraction, button_labels, click, invoke

ADMIN_ONLY_COMMANDS = ["remove_character", "add_alias", "remove_alias", "set_primary_name"]


@pytest.fixture
def cog():
    return CharacterCog()


def test_admin_add_character(cog):
    interaction = FakeInteraction(administrator=True)

    invoke(cog.add_character, interaction, cog, character="black knight")

    assert interaction.response.deferred == [{}]
    assert interaction.sent[0].content == "Character Black_Knight has been added"
    assert character_repository.get_character("Black_Knight") is not None
    assert button_labels(interaction.channel.last_message().view) == ["Subscribe to Black_Knight"]


def test_non_admin_add_character_starts_a_button_vote(cog):
    interaction = FakeInteraction(user_id=7)

    invoke(cog.add_character, interaction, cog, character="Lucina")

    vote_message = interaction.channel.last_message()
    assert vote_message.content == "Vote to add Lucina. Votes needed: 5"
    assert button_labels(vote_message.view) == ["Vote (1/5)"]
    vote = character_vote_repository.get_vote(str(vote_message.id))
    assert (vote.character_name, vote.proposer) == ("Lucina", "7")
    assert character_repository.get_character("Lucina") is None
    assert character_vote_repository.has_voter(str(vote_message.id), "7")
    click(interaction.client, vote_message, 2)
    assert character_vote_repository.count_voters(str(vote_message.id)) == 2


def test_add_character_vote_refused_in_dms(cog):
    interaction = FakeInteraction(in_guild=False)

    invoke(cog.add_character, interaction, cog, character="Lucina")

    assert [(sent.content, sent.ephemeral) for sent in interaction.sent] == [
        ("Votes can only be started in a server", True)
    ]
    assert character_repository.get_character("Lucina") is None


def test_admin_commands_hidden_and_checked(cog):
    for name in ADMIN_ONLY_COMMANDS:
        command = getattr(cog, name)
        assert command.default_permissions.administrator, name
        assert command.guild_only, name
    character_repository.add_character("Lucina")
    interaction = FakeInteraction()

    invoke(cog.remove_character, interaction, cog, character="Lucina")

    assert interaction.sent[0].content == "This command is for admins only"
    assert interaction.sent[0].ephemeral is True
    assert character_repository.get_character("Lucina") is not None


def test_add_alias_with_spaces(cog):
    character_repository.add_character("Black_Knight")
    interaction = FakeInteraction(administrator=True)

    invoke(cog.add_alias, interaction, cog, character="black knight", alias="zelgius the knight")

    character = character_repository.get_character("Black_Knight")
    assert alias_repository.has_alias(character.id, "Zelgius_The_Knight")
    assert "Zelgius_The_Knight" in interaction.sent[0].content


def test_check_remove_alias_and_primary_name(cog):
    character_repository.add_character("Lucina")
    admin = FakeInteraction(administrator=True)
    invoke(cog.add_alias, admin, cog, character="Lucina", alias="Marth_Mask")

    primary, check, remove = FakeInteraction(administrator=True), FakeInteraction(), FakeInteraction(administrator=True)
    invoke(cog.set_primary_name, primary, cog, alias="marth mask")
    invoke(cog.check_character, check, cog, character="Lucina")
    invoke(cog.remove_alias, remove, cog, character="Marth_Mask", alias="Lucina")

    assert "Marth_Mask" in primary.sent[0].content
    assert check.sent[0].content.startswith("### Marth_Mask's pings")
    assert check.sent[0].ephemeral is False
    assert "has been removed" in remove.sent[0].content
