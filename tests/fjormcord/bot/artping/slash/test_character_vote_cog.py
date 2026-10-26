import asyncio

from fjormcord.bot.artping.slash.character_vote_cog import CharacterVoteCog
from fjormcord.bot.artping.vote_view import VOTE_BUTTON_ID, VoteView


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
