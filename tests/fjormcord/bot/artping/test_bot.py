import asyncio
from types import SimpleNamespace

import discord
import pytest

from fjormcord.bot.artping import commands
from fjormcord.bot.artping.bot import ArtPingClient
from fjormcord.bot.artping.commands import Command, MESSAGE_DENIED
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


def test_admin_command_denied_for_non_admin(bot):
    assert dispatch(bot, make_message("~addcharacter Lucina")) == [MESSAGE_DENIED]


def test_admin_command_allowed_for_admin(bot):
    assert dispatch(bot, make_message("~addcharacter Lucina", administrator=True)) == ["Lucina has been added"]


def test_admin_command_denied_in_dms(bot):
    message = make_message("~addcharacter Lucina")
    message.author = SimpleNamespace(id=1, display_name="user1")

    assert dispatch(bot, message) == [MESSAGE_DENIED]


def test_failing_command_still_replies(bot, monkeypatch):
    def broken(client, message):
        raise RuntimeError("database is gone")

    command = commands.COMMANDS_BY_NAME["~checkping"]
    monkeypatch.setitem(commands.COMMANDS_BY_NAME, "~checkping", Command(command.name, broken, command.description))

    assert dispatch(bot, make_message("~checkping")) == ["Something went wrong while running ~checkping"]
