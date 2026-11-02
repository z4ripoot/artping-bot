import pytest

from fjormcord.bot.artping.repository import alias_repository, character_repository, character_vote_repository
from fjormcord.bot.artping.slash.cog.character_cog import CharacterCog
from tests.fakes import FakeInteraction, button_labels, invoke


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


def test_add_character_vote_refused_in_dms(cog):
    interaction = FakeInteraction(in_guild=False)

    invoke(cog.add_character, interaction, cog, character="Lucina")

    assert [(sent.content, sent.ephemeral) for sent in interaction.sent] == [
        ("Votes can only be started in a server", True)
    ]
    assert character_repository.get_character("Lucina") is None


def test_add_alias_with_spaces(cog):
    character_repository.add_character("Black_Knight")
    interaction = FakeInteraction(administrator=True)

    invoke(cog.add_alias, interaction, cog, character="black knight", alias="zelgius the knight")

    character = character_repository.get_character("Black_Knight")
    assert alias_repository.has_alias(character.id, "Zelgius_The_Knight")
    assert "Zelgius_The_Knight" in interaction.sent[0].content


def test_set_primary_name_with_spaces(cog):
    character_id = character_repository.add_character("Lucina")
    alias_repository.add_alias(character_id, "Marth_Mask")
    interaction = FakeInteraction(administrator=True)

    invoke(cog.set_primary_name, interaction, cog, alias="marth mask")

    assert interaction.sent[0].content == "Marth_Mask is now the primary name; Lucina has become an alias"


def test_check_character_is_public(cog):
    character_id = character_repository.add_character("Lucina")
    alias_repository.add_alias(character_id, "Marth_Mask")
    interaction = FakeInteraction()

    invoke(cog.check_character, interaction, cog, character="marth mask")

    assert interaction.sent[0].content == "### Lucina's pings\nAliases: Marth_Mask\nNobody is subscribed to Lucina"
    assert interaction.sent[0].ephemeral is False


def test_remove_alias(cog):
    character_id = character_repository.add_character("Lucina")
    alias_repository.add_alias(character_id, "Marth_Mask")
    interaction = FakeInteraction(administrator=True)

    invoke(cog.remove_alias, interaction, cog, character="Lucina", alias="marth mask")

    assert interaction.sent[0].content == "Alias Marth_Mask has been removed from Lucina"
    assert not alias_repository.has_alias(character_id, "Marth_Mask")
