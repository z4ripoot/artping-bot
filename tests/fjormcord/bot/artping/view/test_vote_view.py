import asyncio
from dataclasses import replace

from fjormcord.bot.artping import config
from fjormcord.bot.artping.model.character_vote import CharacterVote
from fjormcord.bot.artping.repository import character_vote_repository
from fjormcord.bot.artping.service import character_vote_service
from fjormcord.bot.artping.view.vote_view import VoteButton
from tests.fakes import FakeChannel, FakeClient, FakeInteraction


def test_vote_button_keeps_the_custom_id_of_old_vote_messages():
    # Vote messages posted before the layouts carry this custom_id; their clicks must still reach the vote
    assert VoteButton(1).custom_id == "character_vote"
    assert VoteButton.__discord_ui_compiled_template__.fullmatch("character_vote")


def test_vote_button_shows_the_count():
    assert VoteButton(1).item.label == "Vote (1/5)"


def test_click_is_deferred_and_answered_privately(monkeypatch):
    monkeypatch.setattr(config, "_settings", replace(config.read_settings(), character_votes_needed=2))
    channel = FakeChannel()
    vote_message = channel.post("Vote to add Lucina. Votes needed: 2")
    character_vote_repository.add_vote(CharacterVote(str(vote_message.id), str(channel.id), "Lucina", "7"))
    interaction = FakeInteraction(1, channel=channel, client=FakeClient(channels=[channel]), message=vote_message)

    asyncio.run(VoteButton().callback(interaction))

    assert interaction.response.deferred == [{"ephemeral": True, "thinking": True}]
    assert interaction.sent == [("Your vote for Lucina has been added", True, None)]
    assert character_vote_repository.count_voters(str(vote_message.id)) == 1


def test_failed_click_is_answered_privately(monkeypatch, caplog):
    async def failing_toggle_vote(client, vote_message, user):
        raise RuntimeError("database is locked")

    monkeypatch.setattr(character_vote_service, "toggle_vote", failing_toggle_vote)
    channel = FakeChannel()
    interaction = FakeInteraction(
        1,
        channel=channel,
        client=FakeClient(channels=[channel]),
        message=channel.post("Vote to add Lucina. Votes needed: 2"),
    )

    asyncio.run(VoteButton().callback(interaction))

    assert interaction.sent == [("Something went wrong while voting", True, None)]
    assert "database is locked" in caplog.text
