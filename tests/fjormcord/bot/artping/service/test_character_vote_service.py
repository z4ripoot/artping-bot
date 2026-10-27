import asyncio
from dataclasses import replace

import pytest

from fjormcord.bot.artping import config
from fjormcord.bot.artping.legacy.handler.character_handlers import add_character
from fjormcord.bot.artping.model.character_vote import CharacterVote
from fjormcord.bot.artping.repository import character_vote_repository
from fjormcord.bot.artping.repository.art_ping_repository import get_art_ping_users
from fjormcord.bot.artping.repository.character_repository import get_character
from fjormcord.bot.artping.repository.character_vote_repository import count_voters, get_votes
from fjormcord.bot.artping.service.character_vote_service import check_open_votes, drop_deleted_vote
from tests.fakes import BOT_USER, FakeChannel, FakeClient, FakeGuild, click, make_member, make_message, make_user, reply

EMOJI = "⭐"
# An administrator of the server the votes are in
ADMIN_ID = 9


def set_votes_needed(monkeypatch, votes_needed):
    monkeypatch.setattr(
        config,
        "_settings",
        replace(config.read_settings(), character_votes_needed=votes_needed, character_vote_emoji=EMOJI),
    )


@pytest.fixture(autouse=True)
def settings(monkeypatch):
    set_votes_needed(monkeypatch, 2)


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
        click(client, vote_message, user_id)


def reaction_vote(channel, name, *reactors):
    # A vote started before votes had a button: counted by its ⭐ reactions, the bot's own among them
    vote_message = channel.post(f"Vote to add {name}: react with {EMOJI}. Votes needed: 2")
    vote_message.react(EMOJI, BOT_USER)
    for reactor in reactors:
        vote_message.react(EMOJI, reactor)
    character_vote_repository.add_vote(
        CharacterVote(str(vote_message.id), str(channel.id), name, "7", uses_button=False)
    )
    return vote_message


def check_votes(client):
    asyncio.run(check_open_votes(client))


def label(vote_message):
    [button] = vote_message.view.children
    return button.label


def subscribers(name):
    return set(get_art_ping_users((get_character(name).id,)))


def test_non_admin_add_character_starts_a_vote(client, channel):
    out = reply(add_character, client, make_message("~addcharacter black_knight", user_id=7, channel=channel))

    vote_message = channel.last_message()
    assert out == ""
    assert channel.sent == ["Vote to add Black_Knight. Votes needed: 2"]
    assert label(vote_message) == "Vote (0/2)"
    assert vote_message.reactions == []
    assert get_votes() == [CharacterVote(str(vote_message.id), "10", "Black_Knight", "7")]
    assert get_character("Black_Knight") is None


def test_vote_button_shows_the_emoji(client, channel):
    vote_message = start_vote(client, channel, "Lucina")

    [button] = vote_message.view.children
    assert str(button.emoji) == EMOJI


def test_vote_is_not_started_for_a_name_in_use(client, channel):
    reply(add_character, client, make_message("~addcharacter Lucina", administrator=True))

    assert (
        reply(add_character, client, make_message("~addcharacter lucina", channel=channel))
        == "Character Lucina already exists"
    )
    assert channel.sent == []
    assert get_votes() == []


def test_vote_is_not_started_in_dms(client, channel):
    message = make_message("~addcharacter Lucina", channel=channel)
    message.guild = None

    assert reply(add_character, client, message) == "Votes can only be started in a server"
    assert get_votes() == []


def test_click_adds_a_vote_and_updates_the_count(client, channel):
    vote_message = start_vote(client, channel, "Black_Knight")

    assert click(client, vote_message, 1) == "Your vote for Black_Knight has been added"
    assert label(vote_message) == "Vote (1/2)"
    assert get_character("Black_Knight") is None
    assert len(get_votes()) == 1


def test_second_click_takes_the_vote_back(client, channel):
    vote_message = start_vote(client, channel, "Black_Knight")
    click(client, vote_message, 1)

    assert click(client, vote_message, 1) == "Your vote for Black_Knight has been taken back"
    assert label(vote_message) == "Vote (0/2)"
    assert count_voters(str(vote_message.id)) == 0


def test_vote_passes_and_subscribes_the_voters(client, channel):
    vote_message = start_vote(client, channel, "Black_Knight")

    vote(client, vote_message, 1, 2)

    assert subscribers("Black_Knight") == {"1", "2"}
    assert vote_message.content == "Character Black_Knight has been added"
    assert vote_message.view is None
    assert get_votes() == []


def test_taken_back_vote_is_not_subscribed(client, channel):
    vote_message = start_vote(client, channel, "Lucina")
    vote(client, vote_message, 3, 3)

    vote(client, vote_message, 1, 2)

    assert subscribers("Lucina") == {"1", "2"}


def test_admin_click_passes_the_vote(client, channel):
    vote_message = start_vote(client, channel, "Lucina")

    click(client, vote_message, ADMIN_ID, administrator=True)

    assert subscribers("Lucina") == {str(ADMIN_ID)}
    assert vote_message.content == "Character Lucina has been added"
    assert vote_message.view is None


def test_admin_click_subscribes_the_other_voters_too(client, channel):
    vote_message = start_vote(client, channel, "Lucina")
    click(client, vote_message, 1)

    click(client, vote_message, ADMIN_ID, administrator=True)

    assert subscribers("Lucina") == {"1", str(ADMIN_ID)}


def test_only_the_voters_of_the_passing_vote_are_subscribed(client, channel):
    first = start_vote(client, channel, "Lucina", user_id=3)
    second = start_vote(client, channel, "lucina", user_id=1)
    vote(client, first, 3)

    vote(client, second, 1, 2)

    assert subscribers("Lucina") == {"1", "2"}
    assert first.content == "Character Lucina has already been added"
    assert first.view is None
    assert get_votes() == []


def test_admin_add_closes_open_votes(client, channel):
    vote_message = start_vote(client, channel, "Lucina")

    assert (
        reply(add_character, client, make_message("~addcharacter Lucina", administrator=True))
        == "Character Lucina has been added"
    )
    assert vote_message.content == "Character Lucina has already been added"
    assert vote_message.view is None
    assert get_votes() == []


def test_click_on_a_closed_vote(client, channel):
    vote_message = start_vote(client, channel, "Lucina")
    reply(add_character, client, make_message("~addcharacter Lucina", administrator=True))

    assert click(client, vote_message, 1) == "This vote has already been closed"
    assert vote_message.view is None
    assert subscribers("Lucina") == set()


def test_click_on_a_dropped_vote_removes_the_button(client, channel):
    vote_message = start_vote(client, channel, "Lucina")
    drop_deleted_vote(str(vote_message.id))

    assert click(client, vote_message, 1) == "This vote has already been closed"
    assert vote_message.view is None


def test_click_on_a_vote_for_a_name_that_became_an_alias_drops_it(client, channel, database):
    vote_message = start_vote(client, channel, "Focalors")
    reply(add_character, client, make_message("~addcharacter Furina", administrator=True))
    database.execute("INSERT INTO ALIAS (CHARACTER_ID, ALIAS) VALUES (?, 'Focalors')", (get_character("Furina").id,))

    assert click(client, vote_message, 1) == "Focalors is already an alias of Furina"
    assert vote_message.content == "Focalors is already an alias of Furina"
    assert vote_message.view is None
    assert get_votes() == []
    assert subscribers("Furina") == set()


def test_clicking_a_passed_vote_again_is_harmless(client, channel, database):
    vote_message = start_vote(client, channel, "Lucina")
    vote(client, vote_message, 1, 2)

    assert click(client, vote_message, 3) == "This vote has already been closed"
    assert database.execute("SELECT COUNT(*) FROM CHARACTERS").fetchone()[0] == 1
    assert subscribers("Lucina") == {"1", "2"}


def test_non_admin_adds_directly_when_fewer_than_two_votes_are_needed(client, channel, monkeypatch):
    set_votes_needed(monkeypatch, 1)

    assert (
        reply(add_character, client, make_message("~addcharacter Lucina", channel=channel))
        == "Character Lucina has been added"
    )
    assert channel.sent == []
    assert get_votes() == []


def test_deleted_vote_message_drops_the_vote(client, channel):
    vote_message = start_vote(client, channel, "Lucina")

    drop_deleted_vote(str(vote_message.id))

    assert get_votes() == []


# At startup: the open votes are checked, and the votes counted by reactions get the button


def test_open_votes_are_checked_at_startup(client, channel, monkeypatch):
    set_votes_needed(monkeypatch, 3)
    passing = start_vote(client, channel, "Lucina")
    waiting = start_vote(client, channel, "Marth")
    vote(client, passing, 1, 2)
    vote(client, waiting, 1)
    set_votes_needed(monkeypatch, 2)

    check_votes(client)

    assert subscribers("Lucina") == {"1", "2"}
    assert passing.content == "Character Lucina has been added"
    assert passing.view is None
    assert get_character("Marth") is None
    assert [open_vote.character_name for open_vote in get_votes()] == ["Marth"]


def test_open_votes_follow_a_changed_votes_needed_at_startup(client, channel, monkeypatch):
    vote_message = start_vote(client, channel, "Lucina")
    vote(client, vote_message, 1)
    set_votes_needed(monkeypatch, 3)

    check_votes(client)

    assert vote_message.content == "Vote to add Lucina. Votes needed: 3"
    assert label(vote_message) == "Vote (1/3)"


def test_vote_whose_message_is_gone_is_dropped_at_startup(client, channel):
    vote_message = start_vote(client, channel, "Lucina")
    del channel.messages[vote_message.id]

    check_votes(client)

    assert get_votes() == []


def test_vote_is_kept_when_the_bot_may_not_read_the_channel(client, channel):
    reaction_vote(channel, "Lucina", make_user(1), make_user(2))
    channel.forbidden = True

    check_votes(client)

    assert get_character("Lucina") is None
    assert len(get_votes()) == 1
    assert not get_votes()[0].uses_button


def test_vote_for_a_name_that_became_an_alias_is_dropped_at_startup(client, channel, database):
    vote_message = start_vote(client, channel, "Focalors")
    reply(add_character, client, make_message("~addcharacter Furina", administrator=True))
    database.execute("INSERT INTO ALIAS (CHARACTER_ID, ALIAS) VALUES (?, 'Focalors')", (get_character("Furina").id,))

    check_votes(client)

    assert vote_message.content == "Focalors is already an alias of Furina"
    assert vote_message.view is None
    assert get_votes() == []


def test_reaction_vote_is_converted_at_startup(client, channel):
    vote_message = reaction_vote(channel, "Black_Knight", make_user(1))

    check_votes(client)

    assert count_voters(str(vote_message.id)) == 1
    assert vote_message.content == "Vote to add Black_Knight. Votes needed: 2"
    assert label(vote_message) == "Vote (1/2)"
    assert get_votes()[0].uses_button
    assert get_character("Black_Knight") is None


def test_failed_conversion_edit_is_repaired_at_the_next_startup(client, channel):
    vote_message = reaction_vote(channel, "Black_Knight", make_user(1))
    vote_message.failing_edits = 1
    check_votes(client)
    assert vote_message.view is None

    check_votes(client)

    assert vote_message.content == "Vote to add Black_Knight. Votes needed: 2"
    assert label(vote_message) == "Vote (1/2)"
    assert count_voters(str(vote_message.id)) == 1


def test_reaction_vote_passes_during_conversion(client, channel):
    vote_message = reaction_vote(channel, "Lucina", make_user(1), make_user(2))

    check_votes(client)

    assert subscribers("Lucina") == {"1", "2"}
    assert vote_message.content == "Character Lucina has been added"
    assert vote_message.view is None
    assert get_votes() == []


def test_reaction_vote_with_admin_passes_during_conversion(client, channel):
    vote_message = reaction_vote(channel, "Lucina", make_member(ADMIN_ID, administrator=True))

    check_votes(client)

    assert subscribers("Lucina") == {str(ADMIN_ID)}
    assert vote_message.content == "Character Lucina has been added"


def test_reaction_vote_with_admin_passes_when_the_member_is_not_cached(client, channel):
    reaction_vote(channel, "Lucina", make_user(ADMIN_ID))

    check_votes(client)

    assert subscribers("Lucina") == {str(ADMIN_ID)}


def test_bots_and_other_emoji_are_not_counted_during_conversion(client, channel):
    vote_message = reaction_vote(channel, "Lucina", make_user(1), make_user(3, bot=True))
    vote_message.react("👍", make_user(2))
    vote_message.react("👍", make_member(ADMIN_ID, administrator=True))

    check_votes(client)

    assert get_character("Lucina") is None
    assert label(vote_message) == "Vote (1/2)"


def test_reaction_of_a_user_who_left_the_server_still_counts(client, channel):
    reaction_vote(channel, "Lucina", make_user(1), make_user(42))

    check_votes(client)

    assert subscribers("Lucina") == {"1", "42"}


def test_conversion_happens_once(client, channel):
    vote_message = reaction_vote(channel, "Lucina", make_user(1))
    check_votes(client)
    # A reaction added after the conversion no longer counts
    vote_message.react(EMOJI, make_user(2))

    check_votes(client)

    assert count_voters(str(vote_message.id)) == 1
    assert click(client, vote_message, 3) == "Your vote for Lucina has been added"
    assert subscribers("Lucina") == {"1", "3"}


# The repository: the stored voters


def test_removing_a_vote_removes_its_voters():
    character_vote_repository.add_vote(CharacterVote("5", "10", "Lucina", "7"))
    character_vote_repository.add_voter("5", "1")

    character_vote_repository.remove_vote("5")

    assert character_vote_repository.count_voters("5") == 0


def test_pass_vote_subscribes_the_stored_voters():
    character_vote_repository.add_vote(CharacterVote("5", "10", "Lucina", "7"))
    character_vote_repository.add_voter("5", "1")
    character_vote_repository.add_voter("5", "2")

    character_vote_repository.pass_vote("5", "Lucina")

    assert subscribers("Lucina") == {"1", "2"}
    assert get_votes() == []


def test_convert_vote_stores_the_voters_and_marks_the_vote():
    character_vote_repository.add_vote(CharacterVote("5", "10", "Lucina", "7", uses_button=False))
    character_vote_repository.add_voter("5", "1")

    character_vote_repository.convert_vote("5", ["1", "2"])

    assert character_vote_repository.count_voters("5") == 2
    assert character_vote_repository.get_vote("5").uses_button
