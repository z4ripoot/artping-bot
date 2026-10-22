import asyncio
from types import SimpleNamespace

import discord
import pytest

from fjormcord.bot.artping import commands
from fjormcord.bot.artping.bot import ArtPingClient
from fjormcord.bot.artping.commands import Command
from fjormcord.bot.artping.easter_eggs import LORENZ_SMILE
from tests.fakes import make_message


@pytest.fixture
def bot():
    return ArtPingClient(intents=discord.Intents.default())


def dispatch(bot, message):
    asyncio.run(bot.on_message(message))
    return message.channel.sent


def test_commands_are_case_insensitive(bot):
    assert dispatch(bot, make_message("~CheckPing")) == ["You are not subscribed to any characters"]


def test_command_must_match_exactly(bot):
    assert dispatch(bot, make_message("~checkpingx")) == []


def test_admin_command_ignored_for_non_admin(bot):
    assert dispatch(bot, make_message("~addcharacter Lucina")) == []


def test_admin_command_allowed_for_admin(bot):
    assert dispatch(bot, make_message("~addcharacter Lucina", administrator=True)) == \
        ["Character Lucina has been added"]


def test_admin_command_ignored_in_dms(bot):
    message = make_message("~addcharacter Lucina")
    message.author = SimpleNamespace(id=1, display_name="user1")

    assert dispatch(bot, message) == []


def test_failing_command_still_replies(bot, monkeypatch):
    def broken(client, message):
        raise RuntimeError("database is gone")

    command = commands.COMMANDS_BY_NAME["~checkping"]
    monkeypatch.setitem(commands.COMMANDS_BY_NAME, "~checkping", Command(command.name, broken, command.description))

    assert dispatch(bot, make_message("~checkping")) == ["Something went wrong while running ~checkping"]


# The alias commands only reply that aliases aren't supported yet
COMMANDS_WITH_ARGUMENTS = [command for command in commands.COMMANDS
                           if command.usage and command.name not in ("~addalias", "~removealias")]


@pytest.mark.parametrize("command", COMMANDS_WITH_ARGUMENTS, ids=lambda command: command.name)
def test_missing_argument_is_answered_with_usage(bot, command):
    [reply] = dispatch(bot, make_message(command.name, administrator=True))

    assert reply.endswith(f" is missing. Usage: {command.name} ({') ('.join(command.usage)})")


def test_missing_argument_names_what_is_missing(bot):
    assert dispatch(bot, make_message("~addcharacter", administrator=True)) == \
        ["Character name is missing. Usage: ~addcharacter (character name)"]
    assert dispatch(bot, make_message("~setcurrency Orbs")) == \
        ["Amount is missing. Usage: ~setcurrency (currency name) (amount)"]


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
    assert dispatch(bot, make_message("Thanks Lorenz")) == [LORENZ_SMILE]
