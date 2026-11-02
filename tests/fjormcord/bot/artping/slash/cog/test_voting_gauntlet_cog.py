from fjormcord.bot.artping.slash.cog.voting_gauntlet_cog import VotingGauntletCog
from tests.fakes import FakeInteraction, invoke, use_settings


def test_send_voting_gauntlet_answers_the_admin_privately(monkeypatch):
    cog = VotingGauntletCog()
    use_settings(monkeypatch, voting_gauntlet_channel_id=None)
    interaction = FakeInteraction(administrator=True)

    invoke(cog.send_voting_gauntlet, interaction, cog)

    assert interaction.response.deferred == [{"ephemeral": True}]
    assert interaction.sent[0].content == "No channel is configured for the Voting Gauntlet scores"
    assert interaction.sent[0].ephemeral is True
