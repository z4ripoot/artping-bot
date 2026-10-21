import asyncio
from datetime import datetime, timedelta, timezone
from types import SimpleNamespace

import discord
import pytest

from fjormcord.bot.artping import bot as bot_module, commands
from fjormcord.bot.artping.bot import ArtPingClient
from fjormcord.bot.artping.commands import Command, MESSAGE_DENIED
from tests.fakes import FakeChannel, make_message


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
    assert dispatch(bot, make_message("~addcharacter Lucina", administrator=True)) == ["Character Lucina has been added"]


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


# The alias commands only reply that aliases aren't supported yet
COMMANDS_WITH_ARGUMENTS = [command for command in commands.COMMANDS
                           if command.usage and command.name not in ("~addalias", "~removealias")]


@pytest.mark.parametrize("command", COMMANDS_WITH_ARGUMENTS, ids=lambda command: command.name)
def test_missing_argument_is_answered_with_usage(bot, command):
    [reply] = dispatch(bot, make_message(command.name, administrator=True))

    assert reply.endswith(f" is missing. Usage: {command.name} ({command.usage})")


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


def fake_datetime(utc_now, host_offset):
    # Simulates a host whose local timezone is UTC + host_offset
    class FakeDatetime(datetime):
        @classmethod
        def now(cls, tz=None):
            if tz is None:
                return (utc_now + host_offset).replace(tzinfo=None)
            return utc_now.astimezone(tz)

    return FakeDatetime


CHANNEL_ID = 123


def run_coliseum_task(bot, monkeypatch, utc_now, host_offset=timedelta(hours=2), channel_id=CHANNEL_ID):
    channel = FakeChannel()
    monkeypatch.setattr(bot_module, "COLISEUM_NOTIFICATION_CHANNEL_ID", channel_id)
    monkeypatch.setattr(bot_module, "datetime", fake_datetime(utc_now, host_offset))
    monkeypatch.setattr(bot, "get_channel", lambda channel_id: channel if channel_id == CHANNEL_ID else None)

    asyncio.run(bot.task_coliseum_before_closing_notification.coro(bot))
    return channel.sent


def test_coliseum_notification_uses_utc_regardless_of_host_timezone(bot, monkeypatch):
    # Monday 22:00 UTC is already Tuesday 00:00 on a UTC+2 host
    sent = run_coliseum_task(bot, monkeypatch, datetime(2026, 10, 19, 22, 0, tzinfo=timezone.utc))

    closing_time = int(datetime(2026, 10, 19, 23, 0, tzinfo=timezone.utc).timestamp())
    assert sent == [f"Coliseum/Aether Raids closes <t:{closing_time}:R> at <t:{closing_time}:f>"]


def test_coliseum_notification_skipped_outside_monday(bot, monkeypatch):
    # Sunday 22:00 UTC is already Monday 00:00 on a UTC+2 host
    assert run_coliseum_task(bot, monkeypatch, datetime(2026, 10, 18, 22, 0, tzinfo=timezone.utc)) == []


def test_long_reply_is_split_into_messages_within_discord_limit(bot):
    dispatch(bot, make_message("~addcharacter Lucina", administrator=True))
    user_ids = range(10**17, 10**17 + 200)
    for user_id in user_ids:
        dispatch(bot, make_message("~addping Lucina", user_id=user_id))

    sent = dispatch(bot, make_message("~artping Lucina"))

    assert len(sent) > 1
    assert all(len(chunk) <= 2000 for chunk in sent)
    assert all(f"<@{user_id}>" in " ".join(sent) for user_id in user_ids)


def test_coliseum_notification_skipped_for_unknown_channel(bot, monkeypatch, caplog):
    sent = run_coliseum_task(bot, monkeypatch, datetime(2026, 10, 19, 22, 0, tzinfo=timezone.utc), channel_id=456)

    assert sent == []
    assert "456" in caplog.text


def test_old_channel_name_setting_is_reported(bot, monkeypatch, caplog):
    monkeypatch.setattr(bot_module, "COLISEUM_NOTIFICATION_CHANNEL_ID", None)
    monkeypatch.setattr(bot_module, "OLD_COLISEUM_NOTIFICATION_CHANNEL_NAME", "general")

    asyncio.run(bot.on_ready())

    assert "coliseum_notification_channel_id" in caplog.text
    assert not bot.task_coliseum_before_closing_notification.is_running()
