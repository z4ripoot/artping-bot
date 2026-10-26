import asyncio
from dataclasses import replace

from fjormcord.bot.artping import config
from fjormcord.bot.artping.model.character_vote import CharacterVote
from fjormcord.bot.artping.repository import character_vote_repository
from fjormcord.bot.artping.slash.character_vote_cog import CharacterVoteCog
from fjormcord.bot.artping.vote_view import VOTE_BUTTON_ID, VoteView
from tests.fakes import FakeChannel, FakeClient, FakeInteraction


class FakeBot:
    def __init__(self):
        self.views = []

    def add_view(self, view):
        self.views.append(view)


def test_vote_view_is_persistent():
    view = VoteView()

    assert view.is_persistent()
    assert [button.custom_id for button in view.children] == [VOTE_BUTTON_ID]


def test_cog_registers_the_view():
    bot = FakeBot()

    asyncio.run(CharacterVoteCog(bot).cog_load())

    [view] = bot.views
    assert isinstance(view, VoteView)


def test_click_is_deferred_and_answered_privately(monkeypatch):
    monkeypatch.setattr(config, "_settings", replace(config.read_settings(), character_votes_needed=2))
    channel = FakeChannel()
    vote_message = channel.post("Vote to add Lucina. Votes needed: 2")
    character_vote_repository.add_vote(CharacterVote(str(vote_message.id), str(channel.id), "Lucina", "7"))
    view = VoteView()
    interaction = FakeInteraction(1, channel=channel, client=FakeClient(channels=[channel]), message=vote_message)

    asyncio.run(view.vote.callback(interaction))

    assert interaction.response.deferred == [{"ephemeral": True, "thinking": True}]
    assert interaction.sent == [("Your vote for Lucina has been added", True, None)]
    assert character_vote_repository.count_voters(str(vote_message.id)) == 1
