import asyncio
from datetime import datetime, timedelta, timezone
from types import SimpleNamespace

import discord

from fjormcord.bot.artping import divine_games
from tests.fakes import FakeChannel, fake_datetime, http_error, use_settings

CHANNEL_ID = 123


def run_divine_games_task(monkeypatch, utc_now, host_offset=timedelta(hours=2), channel_id=CHANNEL_ID, channel=None):
    channel = channel or FakeChannel()
    client = SimpleNamespace(get_channel=lambda channel_id: channel if channel_id == CHANNEL_ID else None)
    use_settings(monkeypatch, divine_games_channel_id=channel_id)
    monkeypatch.setattr(divine_games, "datetime", fake_datetime(utc_now, host_offset))

    asyncio.run(divine_games.task_divine_games_before_closing_notification.coro(client))
    return channel


def test_divine_games_notification_uses_utc_regardless_of_host_timezone(monkeypatch):
    # Saturday 21:59 UTC is already Saturday 23:59 on a UTC+2 host, and Sunday 01:59 on a UTC+4 one
    channel = run_divine_games_task(
        monkeypatch, datetime(2026, 10, 31, 21, 59, tzinfo=timezone.utc), host_offset=timedelta(hours=4)
    )

    # 23:59 GMT+1
    closing_time = int(datetime(2026, 10, 31, 22, 59, tzinfo=timezone.utc).timestamp())
    assert channel.sent == [f"Divine Games ends <t:{closing_time}:R> at <t:{closing_time}:f>"]
    # Laid out: the text in a container, no content
    assert isinstance(channel.last_message().view, discord.ui.LayoutView)


def test_divine_games_notification_skipped_outside_saturday(monkeypatch):
    # Friday 21:59 UTC is already Saturday 01:59 on a UTC+4 host
    channel = run_divine_games_task(
        monkeypatch, datetime(2026, 10, 30, 21, 59, tzinfo=timezone.utc), host_offset=timedelta(hours=4)
    )

    assert channel.sent == []


def test_divine_games_notification_skipped_for_unknown_channel(monkeypatch, caplog):
    sent = run_divine_games_task(monkeypatch, datetime(2026, 10, 31, 21, 59, tzinfo=timezone.utc), channel_id=456).sent

    assert sent == []
    assert "456" in caplog.text


def test_divine_games_notification_failure_is_logged_and_skipped(monkeypatch, caplog):
    # discord.py's loop only survives network errors; a missing permission must not stop the weekly reminder
    class ForbiddenChannel(FakeChannel):
        async def send(self, content=None, allowed_mentions=None, view=None):
            raise http_error(discord.Forbidden, 403)

    run_divine_games_task(monkeypatch, datetime(2026, 10, 31, 21, 59, tzinfo=timezone.utc), channel=ForbiddenChannel())

    assert "Sending the Divine Games notification failed" in caplog.text


def test_divine_games_notification_not_started_without_channel_id(monkeypatch, caplog):
    use_settings(monkeypatch, divine_games_channel_id=None)

    divine_games.start_divine_games_notification(SimpleNamespace())

    assert "No channel ID is configured" in caplog.text
    assert not divine_games.task_divine_games_before_closing_notification.is_running()
