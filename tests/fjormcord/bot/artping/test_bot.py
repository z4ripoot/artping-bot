import asyncio
from dataclasses import replace
from types import SimpleNamespace

import discord
import pytest
from discord.ext import commands as discord_commands

from fjormcord.bot.artping import config
from fjormcord.bot.artping.bot import ArtPingClient
from fjormcord.bot.artping.cooldowns import Cooldowns
from fjormcord.bot.artping.easter_eggs import lorenz_smile
from fjormcord.bot.artping.legacy import commands
from fjormcord.bot.artping.legacy.commands import Command
from fjormcord.bot.artping.voting_gauntlet_view import TrackButton
from tests.fakes import FakeClock, make_message


@pytest.fixture
def bot():
    client = ArtPingClient(intents=discord.Intents.default())
    # No cooldown, so a test can send one user's commands in a row
    client.cooldowns = Cooldowns(0)
    return client


def dispatch(bot, message):
    asyncio.run(bot.on_message(message))
    return message.channel.sent


def test_commands_are_case_insensitive(bot):
    assert dispatch(bot, make_message("~CheckPing")) == ["You are not subscribed to any characters"]


def test_command_must_match_exactly(bot):
    assert dispatch(bot, make_message("~checkpingx")) == []


def test_messages_from_other_bots_are_ignored(bot):
    assert dispatch(bot, make_message("~checkping", bot=True)) == []
    assert dispatch(bot, make_message("~addcharacter Lucina", administrator=True, bot=True)) == []
    assert dispatch(bot, make_message("Thanks Lorenz", bot=True)) == []


def set_hof(bot):
    dispatch(bot, make_message("~setresource hof https://example.com/hof", administrator=True))


def test_resource_is_posted_without_mentions(bot):
    set_hof(bot)
    message = make_message("~HoF please")

    assert dispatch(bot, message) == ["https://example.com/hof"]
    [mentions] = message.channel.sent_allowed_mentions
    assert (mentions.everyone, mentions.users, mentions.roles, mentions.replied_user) == (False, False, False, False)


def test_unknown_resource_gets_no_reply(bot):
    assert dispatch(bot, make_message("~faq")) == []


def test_command_wins_over_a_resource_of_the_same_name(bot, database):
    database.execute("INSERT INTO RESOURCE (NAME, CONTENT, SOURCE) VALUES ('checkping', 'Resource', 'x')")

    assert dispatch(bot, make_message("~checkping")) == ["You are not subscribed to any characters"]


def test_long_resource_is_split_into_messages_within_discord_limit(bot, database):
    database.execute("INSERT INTO RESOURCE (NAME, CONTENT, SOURCE) VALUES ('hof', ?, 'x')", ("line\n" * 1000,))

    sent = dispatch(bot, make_message("~hof"))

    assert len(sent) > 1
    assert all(len(chunk) <= 2000 for chunk in sent)


def test_admin_command_ignored_for_non_admin(bot):
    assert dispatch(bot, make_message("~removecharacter Lucina")) == []


def test_add_character_by_non_admin_posts_a_vote(bot):
    [vote] = dispatch(bot, make_message("~addcharacter Lucina"))

    assert vote.startswith("Vote to add Lucina. Votes needed: ")


def test_setup_adds_the_vote_cog_and_the_buttons(bot, monkeypatch):
    synced = []

    async def sync_commands(tree, guild_id):
        synced.append((tree, guild_id))

    dynamic_items = []
    monkeypatch.setattr("fjormcord.bot.artping.bot.sync_commands", sync_commands)
    monkeypatch.setattr(bot, "add_dynamic_items", lambda *items: dynamic_items.extend(items))

    asyncio.run(bot.setup_hook())

    assert bot.get_cog("CharacterVoteCog") is not None
    assert [type(view).__name__ for view in bot.persistent_views] == ["VoteView"]
    # Routes clicks on the Voting Gauntlet buttons, also those of messages sent before a restart
    assert dynamic_items == [TrackButton]
    # The sync comes last, so it registers the commands of every cog
    assert synced == [(bot.tree, config.read_settings().guild_id)]


def test_admin_command_allowed_for_admin(bot):
    assert dispatch(bot, make_message("~addcharacter Lucina", administrator=True)) == [
        "Character Lucina has been added"
    ]


def test_admin_command_ignored_in_dms(bot):
    message = make_message("~removecharacter Lucina")
    message.author = SimpleNamespace(id=1, display_name="user1", bot=False)

    assert dispatch(bot, message) == []


def test_failing_command_still_replies(bot, monkeypatch):
    def broken(client, message):
        raise RuntimeError("database is gone")

    command = commands.COMMANDS_BY_NAME["~checkping"]
    monkeypatch.setitem(commands.COMMANDS_BY_NAME, "~checkping", Command(command.name, broken, command.description))

    assert dispatch(bot, make_message("~checkping")) == ["Something went wrong while running ~checkping"]


# The alias commands only reply that aliases aren't supported yet
COMMANDS_WITH_ARGUMENTS = [
    command for command in commands.COMMANDS if command.usage and command.name not in ("~addalias", "~removealias")
]


@pytest.mark.parametrize("command", COMMANDS_WITH_ARGUMENTS, ids=lambda command: command.name)
def test_missing_argument_is_answered_with_usage(bot, command):
    [reply] = dispatch(bot, make_message(command.name, administrator=True))

    assert reply.endswith(f" is missing. Usage: {command.name} ({') ('.join(command.usage)})")


def test_missing_argument_names_what_is_missing(bot):
    assert dispatch(bot, make_message("~addcharacter", administrator=True)) == [
        "Character name is missing. Usage: ~addcharacter (character name)"
    ]
    assert dispatch(bot, make_message("~setcurrency Orbs")) == [
        "Amount is missing. Usage: ~setcurrency (currency name) (amount)"
    ]


def test_replies_cannot_mention_everyone_or_roles(bot):
    assert dispatch(bot, make_message("~artping @everyone")) == ["No character entry for @everyone"]
    assert bot.allowed_mentions.everyone is False
    assert bot.allowed_mentions.roles is False
    assert bot.allowed_mentions.users is True


def test_long_reply_is_split_into_messages_within_discord_limit(bot):
    dispatch(bot, make_message("~addcharacter Lucina", administrator=True))
    user_ids = range(10**17, 10**17 + 200)
    for user_id in user_ids:
        dispatch(bot, make_message("~addping Lucina", user_id=user_id))

    sent = dispatch(bot, make_message("~artping Lucina"))

    assert len(sent) > 1
    assert all(len(chunk) <= 2000 for chunk in sent)
    assert all(f"<@{user_id}>" in " ".join(sent) for user_id in user_ids)


def test_easter_egg_is_answered(bot):
    assert dispatch(bot, make_message("Thanks Lorenz")) == [lorenz_smile()]


@pytest.fixture
def clock(bot):
    clock = FakeClock()
    bot.cooldowns = Cooldowns(1, clock)
    return clock


@pytest.fixture
def lucina(bot, clock):
    # Lucina with user 1 subscribed; the admin starts no cooldown, and user 1's has run out
    dispatch(bot, make_message("~addcharacter Lucina", administrator=True))
    dispatch(bot, make_message("~addping Lucina", user_id=1))
    clock.advance(1)


def test_command_is_turned_down_during_cooldown(bot, clock, lucina):
    dispatch(bot, make_message("~artping Lucina", user_id=2))

    clock.advance(0.5)

    assert dispatch(bot, make_message("~artping Lucina", user_id=2)) == [
        "You used a command recently. Try again in 1 second"
    ]


def test_command_is_allowed_after_cooldown(bot, clock, lucina):
    dispatch(bot, make_message("~artping Lucina", user_id=2))

    clock.advance(1)

    assert dispatch(bot, make_message("~artping Lucina", user_id=2)) == ["Lucina: <@1>"]


def test_cooldown_only_holds_back_that_user(bot, clock, lucina):
    dispatch(bot, make_message("~artping Lucina", user_id=2))

    assert dispatch(bot, make_message("~artping Lucina", user_id=3)) == ["Lucina: <@1>"]


def test_cooldown_holds_back_every_command(bot, clock, lucina):
    dispatch(bot, make_message("~artping Lucina", user_id=1))

    assert dispatch(bot, make_message("~checkping", user_id=1)) == [
        "You used a command recently. Try again in 1 second"
    ]


def test_resource_has_the_cooldown(bot, clock, lucina):
    set_hof(bot)
    dispatch(bot, make_message("~hof", user_id=2))

    assert dispatch(bot, make_message("~checkping", user_id=2)) == [
        "You used a command recently. Try again in 1 second"
    ]
    clock.advance(1)
    assert dispatch(bot, make_message("~hof", user_id=2)) == ["https://example.com/hof"]


def test_turned_down_command_does_not_start_cooldown(bot, clock, lucina):
    dispatch(bot, make_message("~artping Lucin", user_id=2))

    assert dispatch(bot, make_message("~artping Lucina", user_id=2)) == ["Lucina: <@1>"]


def test_admins_are_not_held_back_by_cooldown(bot, clock, lucina):
    dispatch(bot, make_message("~artping Lucina", administrator=True))

    assert dispatch(bot, make_message("~artping Lucina", administrator=True)) == ["Lucina: <@1>"]


def test_cooldown_follows_the_configured_length(monkeypatch):
    settings = replace(config.read_settings(), cooldown_seconds=30)
    monkeypatch.setattr(config, "read_settings", lambda: settings)
    bot = ArtPingClient(intents=discord.Intents.default())
    dispatch(bot, make_message("~checkping", user_id=2))

    assert dispatch(bot, make_message("~checkping", user_id=2)) == [
        "You used a command recently. Try again in 30 seconds"
    ]


def test_client_is_a_bot_without_prefix_commands(bot):
    assert isinstance(bot, discord_commands.Bot)
    assert bot.help_command is None
