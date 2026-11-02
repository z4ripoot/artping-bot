import asyncio
from types import SimpleNamespace

from fjormcord.bot.artping.model.character_vote import CharacterVote
from fjormcord.bot.artping.repository import character_vote_repository
from fjormcord.bot.artping.slash.cog import character_vote_cog
from fjormcord.bot.artping.slash.cog.character_vote_cog import CharacterVoteCog


def delete_message(message_id):
    # Discord's raw delete event, which also fires for messages sent before the bot started
    asyncio.run(CharacterVoteCog(None).on_raw_message_delete(SimpleNamespace(message_id=message_id)))


def test_deleting_a_vote_message_drops_the_vote():
    character_vote_repository.add_vote(CharacterVote("5", "10", "Lucina", "7"))
    character_vote_repository.add_vote(CharacterVote("6", "10", "Chrom", "7"))

    delete_message(5)

    assert [vote.message_id for vote in character_vote_repository.get_votes()] == ["6"]


def test_deleting_another_message_changes_nothing():
    character_vote_repository.add_vote(CharacterVote("5", "10", "Lucina", "7"))

    delete_message(99)

    assert len(character_vote_repository.get_votes()) == 1


def test_failure_is_logged(monkeypatch, caplog):
    # There is nobody to answer, so the error is only logged
    def failing_drop(message_id):
        raise RuntimeError("database is locked")

    monkeypatch.setattr(character_vote_cog, "drop_deleted_vote", failing_drop)

    delete_message(5)

    assert "Dropping vote 5 failed" in caplog.text
    assert "database is locked" in caplog.text
