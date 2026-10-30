from fjormcord.bot.artping.slash.cog.voting_gauntlet_cog import VotingGauntletCog
from tests.fakes import FakeInteraction, invoke, use_settings


def test_send_voting_gauntlet_is_for_admins_only():
    cog = VotingGauntletCog()
    interaction = FakeInteraction()

    invoke(cog.send_voting_gauntlet, interaction, cog)

    assert interaction.sent[0].content == "This command is for admins only"
    assert cog.send_voting_gauntlet.default_permissions.administrator
    assert cog.send_voting_gauntlet.guild_only


def test_send_voting_gauntlet_answers_the_admin_privately(monkeypatch):
    cog = VotingGauntletCog()
    use_settings(monkeypatch, voting_gauntlet_channel_id=None)
    interaction = FakeInteraction(administrator=True)

    invoke(cog.send_voting_gauntlet, interaction, cog)

    assert interaction.response.deferred == [{"ephemeral": True}]
    assert interaction.sent[0].content == "No channel is configured for the Voting Gauntlet scores"
    assert interaction.sent[0].ephemeral is True
