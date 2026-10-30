from fjormcord.bot.artping.legacy.handler.voting_gauntlet_handlers import send_voting_gauntlet
from tests.fakes import FakeClient, make_message, reply, use_settings


def test_send_voting_gauntlet_replies_what_it_did(monkeypatch):
    use_settings(monkeypatch, voting_gauntlet_channel_id=None)

    out = reply(send_voting_gauntlet, FakeClient(), make_message("~sendvotinggauntlet", administrator=True))

    assert out == "No channel is configured for the Voting Gauntlet scores"
