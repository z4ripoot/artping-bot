from fjormcord.bot.artping.repository import alias_repository, character_repository, character_vote_repository
from fjormcord.bot.artping.slash.character_cog import CharacterCog
from fjormcord.bot.artping.vote_view import VoteView
from tests.fakes import FakeInteraction, click, invoke

ADMIN_ONLY_COMMANDS = ["remove_character", "add_alias", "remove_alias", "set_primary_name"]


def test_admin_add_character():
    cog = CharacterCog(None)
    interaction = FakeInteraction(administrator=True)

    invoke(cog.add_character, interaction, cog, character="black knight")

    assert interaction.response.deferred == [{}]
    assert interaction.sent[0][0] == "Character Black_Knight has been added"
    assert character_repository.get_character("Black_Knight") is not None


def test_non_admin_add_character_starts_a_button_vote():
    cog = CharacterCog(None)
    interaction = FakeInteraction(user_id=7)

    invoke(cog.add_character, interaction, cog, character="Lucina")

    vote_message = interaction.channel.last_message()
    assert isinstance(vote_message.view, VoteView)
    vote = character_vote_repository.get_vote(str(vote_message.id))
    assert (vote.character_name, vote.proposer) == ("Lucina", "7")
    assert character_repository.get_character("Lucina") is None
    click(interaction.client, vote_message, 2)
    assert character_vote_repository.count_voters(str(vote_message.id)) == 1


def test_add_character_vote_refused_in_dms():
    cog = CharacterCog(None)
    interaction = FakeInteraction(in_guild=False)

    invoke(cog.add_character, interaction, cog, character="Lucina")

    assert interaction.sent == [("Votes can only be started in a server", True, interaction.sent[0][2])]
    assert character_repository.get_character("Lucina") is None


def test_admin_commands_hidden_and_checked():
    cog = CharacterCog(None)
    for name in ADMIN_ONLY_COMMANDS:
        command = getattr(cog, name)
        assert command.default_permissions.administrator, name
        assert command.guild_only, name
    character_repository.add_character("Lucina")
    interaction = FakeInteraction()

    invoke(cog.remove_character, interaction, cog, character="Lucina")

    assert interaction.sent[0][:2] == ("This command is for admins only", True)
    assert character_repository.get_character("Lucina") is not None


def test_add_alias_with_spaces():
    character_repository.add_character("Black_Knight")
    cog = CharacterCog(None)
    interaction = FakeInteraction(administrator=True)

    invoke(cog.add_alias, interaction, cog, character="black knight", alias="zelgius the knight")

    character = character_repository.get_character("Black_Knight")
    assert alias_repository.has_alias(character.id, "Zelgius_The_Knight")
    assert "Zelgius_The_Knight" in interaction.sent[0][0]


def test_check_remove_alias_and_primary_name():
    character_repository.add_character("Lucina")
    cog = CharacterCog(None)
    admin = FakeInteraction(administrator=True)
    invoke(cog.add_alias, admin, cog, character="Lucina", alias="Marth_Mask")

    primary, check, remove = FakeInteraction(administrator=True), FakeInteraction(), FakeInteraction(administrator=True)
    invoke(cog.set_primary_name, primary, cog, alias="marth mask")
    invoke(cog.check_character, check, cog, character="Lucina")
    invoke(cog.remove_alias, remove, cog, character="Marth_Mask", alias="Lucina")

    assert "Marth_Mask" in primary.sent[0][0]
    assert check.sent[0][0].startswith("Character entry found for Marth_Mask")
    assert "has been removed" in remove.sent[0][0]
