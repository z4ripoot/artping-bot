import asyncio
from dataclasses import replace

import pytest

from fjormcord.bot.artping import config
from fjormcord.bot.artping.model.character_vote import CharacterVote
from fjormcord.bot.artping.repository.art_ping_repository import get_art_ping_users
from fjormcord.bot.artping.repository.character_repository import get_character
from fjormcord.bot.artping.repository.character_vote_repository import get_votes
from fjormcord.bot.artping.legacy.character_handlers import add_character
from fjormcord.bot.artping.service.character_vote_service import check_open_votes, check_vote, drop_deleted_vote
from tests.fakes import BOT_USER, FakeChannel, FakeClient, FakeGuild, make_member, make_message, make_user, reply

EMOJI = "⭐"
# An administrator of the server the votes are in
ADMIN_ID = 9


@pytest.fixture(autouse=True)
def settings(monkeypatch):
    # Two votes needed, whatever a local config.ini sets
    monkeypatch.setattr(config, "_settings", replace(config.read_settings(), character_votes_needed=2,
                                                     character_vote_emoji=EMOJI))


@pytest.fixture
def channel():
    return FakeChannel(guild=FakeGuild(members={1, 2, 3}, administrators={ADMIN_ID}))


@pytest.fixture
def client(channel):
    return FakeClient(channels=[channel])


def start_vote(client, channel, name, user_id=1):
    reply(add_character, client, make_message(f"~addcharacter {name}", user_id=user_id, channel=channel))
    return channel.last_message()


def vote(client, vote_message, *user_ids):
    for user_id in user_ids:
        vote_message.react(EMOJI, make_user(user_id))
    asyncio.run(check_vote(client, str(vote_message.id)))


def subscribers(name):
    return set(get_art_ping_users((get_character(name).id,)))


def test_non_admin_add_character_starts_a_vote(client, channel):
    out = reply(add_character, client, make_message("~addcharacter black_knight", user_id=7, channel=channel))

    vote_message = channel.last_message()
    assert out == ""
    assert channel.sent == [f"Vote to add Black_Knight: react with {EMOJI}. Votes needed: 2"]
    assert [(reaction.emoji, reaction.reactors) for reaction in vote_message.reactions] == [(EMOJI, [BOT_USER])]
    assert get_votes() == [CharacterVote(str(vote_message.id), "10", "Black_Knight", "7")]
    assert get_character("Black_Knight") is None


def test_vote_is_not_started_for_a_name_in_use(client, channel):
    reply(add_character, client, make_message("~addcharacter Lucina", administrator=True))

    assert reply(add_character, client, make_message("~addcharacter lucina", channel=channel)) == \
        "Character Lucina already exists"
    assert channel.sent == []
    assert get_votes() == []


def test_vote_is_not_started_in_dms(client, channel):
    message = make_message("~addcharacter Lucina", channel=channel)
    message.guild = None

    assert reply(add_character, client, message) == "Votes can only be started in a server"
    assert get_votes() == []


def test_vote_waits_for_enough_votes(client, channel):
    vote_message = start_vote(client, channel, "Lucina")

    vote(client, vote_message, 1)

    assert get_character("Lucina") is None
    assert len(get_votes()) == 1


def test_vote_passes_and_subscribes_the_voters(client, channel):
    vote_message = start_vote(client, channel, "Lucina")

    vote(client, vote_message, 1, 2)

    assert subscribers("Lucina") == {"1", "2"}
    assert vote_message.content == "Character Lucina has been added"
    assert get_votes() == []


def test_bots_and_other_emoji_are_not_counted(client, channel):
    vote_message = start_vote(client, channel, "Lucina")
    vote_message.react("👍", make_user(2))
    vote_message.react(EMOJI, make_user(3, bot=True))

    vote(client, vote_message, 1)

    assert get_character("Lucina") is None


def test_only_the_voters_of_the_passing_vote_are_subscribed(client, channel):
    first = start_vote(client, channel, "Lucina", user_id=3)
    second = start_vote(client, channel, "lucina", user_id=1)
    vote(client, first, 3)

    vote(client, second, 1, 2)

    assert subscribers("Lucina") == {"1", "2"}
    assert first.content == "Character Lucina has already been added"
    assert get_votes() == []


def test_admin_add_closes_open_votes(client, channel):
    vote_message = start_vote(client, channel, "Lucina")

    assert reply(add_character, client, make_message("~addcharacter Lucina", administrator=True)) == \
        "Character Lucina has been added"
    assert vote_message.content == "Character Lucina has already been added"
    assert get_votes() == []


def test_vote_for_a_name_that_became_an_alias_is_dropped(client, channel, database):
    vote_message = start_vote(client, channel, "Focalors")
    reply(add_character, client, make_message("~addcharacter Furina", administrator=True))
    database.execute("INSERT INTO ALIAS (CHARACTER_ID, ALIAS) VALUES (?, 'Focalors')", (get_character("Furina").id,))

    vote(client, vote_message, 1, 2)

    assert vote_message.content == "Focalors is already an alias of Furina"
    assert get_votes() == []
    assert subscribers("Furina") == set()


def test_vote_whose_message_is_gone_is_dropped(client, channel):
    vote_message = start_vote(client, channel, "Lucina")
    del channel.messages[vote_message.id]

    vote(client, vote_message)

    assert get_votes() == []


def test_deleted_vote_message_drops_the_vote(client, channel):
    vote_message = start_vote(client, channel, "Lucina")

    drop_deleted_vote(str(vote_message.id))

    assert get_votes() == []


def test_vote_is_kept_when_the_bot_may_not_read_the_channel(client, channel):
    vote_message = start_vote(client, channel, "Lucina")
    channel.forbidden = True

    vote(client, vote_message, 1, 2)

    assert get_character("Lucina") is None
    assert len(get_votes()) == 1


def test_open_votes_are_checked_at_startup(client, channel):
    passing = start_vote(client, channel, "Lucina")
    waiting = start_vote(client, channel, "Marth")
    passing.react(EMOJI, make_user(1))
    passing.react(EMOJI, make_user(2))
    waiting.react(EMOJI, make_user(1))

    asyncio.run(check_open_votes(client))

    assert subscribers("Lucina") == {"1", "2"}
    assert get_character("Marth") is None
    assert [open_vote.character_name for open_vote in get_votes()] == ["Marth"]


def test_checking_a_passed_vote_again_is_harmless(client, channel, database):
    vote_message = start_vote(client, channel, "Lucina")
    vote(client, vote_message, 1, 2)

    vote(client, vote_message, 3)

    assert database.execute("SELECT COUNT(*) FROM CHARACTERS").fetchone()[0] == 1
    assert subscribers("Lucina") == {"1", "2"}


def test_non_admin_adds_directly_when_fewer_than_two_votes_are_needed(client, channel, monkeypatch):
    monkeypatch.setattr(config, "_settings", replace(config.read_settings(), character_votes_needed=1))

    assert reply(add_character, client, make_message("~addcharacter Lucina", channel=channel)) ==         "Character Lucina has been added"
    assert channel.sent == []
    assert get_votes() == []


def test_admin_reaction_passes_the_vote(client, channel):
    vote_message = start_vote(client, channel, "Lucina")
    vote_message.react(EMOJI, make_member(ADMIN_ID, administrator=True))

    vote(client, vote_message)

    assert subscribers("Lucina") == {str(ADMIN_ID)}
    assert vote_message.content == "Character Lucina has been added"


def test_admin_reaction_passes_the_vote_when_the_member_is_not_cached(client, channel):
    vote_message = start_vote(client, channel, "Lucina")

    vote(client, vote_message, ADMIN_ID)

    assert subscribers("Lucina") == {str(ADMIN_ID)}


def test_admin_reaction_with_another_emoji_does_not_pass_the_vote(client, channel):
    vote_message = start_vote(client, channel, "Lucina")
    vote_message.react("👍", make_member(ADMIN_ID, administrator=True))

    vote(client, vote_message)

    assert get_character("Lucina") is None


def test_reaction_of_a_user_who_left_the_server_still_counts_as_a_vote(client, channel):
    vote_message = start_vote(client, channel, "Lucina")

    vote(client, vote_message, 1, 42)

    assert subscribers("Lucina") == {"1", "42"}
