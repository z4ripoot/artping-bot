import asyncio
from datetime import datetime, timedelta, timezone
from types import SimpleNamespace

import discord

from fjormcord.bot.artping import coliseum
from tests.fakes import FakeChannel, use_settings


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


def run_coliseum_task(monkeypatch, utc_now, host_offset=timedelta(hours=2), channel_id=CHANNEL_ID):
    channel = FakeChannel()
    client = SimpleNamespace(get_channel=lambda channel_id: channel if channel_id == CHANNEL_ID else None)
    use_settings(monkeypatch, coliseum_channel_id=channel_id)
    monkeypatch.setattr(coliseum, "datetime", fake_datetime(utc_now, host_offset))

    asyncio.run(coliseum.task_coliseum_before_closing_notification.coro(client))
    return channel


def test_coliseum_notification_uses_utc_regardless_of_host_timezone(monkeypatch):
    # Monday 22:00 UTC is already Tuesday 00:00 on a UTC+2 host
    channel = run_coliseum_task(monkeypatch, datetime(2026, 10, 19, 22, 0, tzinfo=timezone.utc))

    closing_time = int(datetime(2026, 10, 19, 23, 0, tzinfo=timezone.utc).timestamp())
    assert channel.sent == [f"Coliseum/Aether Raids closes <t:{closing_time}:R> at <t:{closing_time}:f>"]
    # Laid out: the text in a container, no content
    assert isinstance(channel.last_message().view, discord.ui.LayoutView)


def test_coliseum_notification_skipped_outside_monday(monkeypatch):
    # Sunday 22:00 UTC is already Monday 00:00 on a UTC+2 host
    assert run_coliseum_task(monkeypatch, datetime(2026, 10, 18, 22, 0, tzinfo=timezone.utc)).sent == []


def test_coliseum_notification_skipped_for_unknown_channel(monkeypatch, caplog):
    sent = run_coliseum_task(monkeypatch, datetime(2026, 10, 19, 22, 0, tzinfo=timezone.utc), channel_id=456).sent

    assert sent == []
    assert "456" in caplog.text


def test_coliseum_notification_not_started_without_channel_id(monkeypatch, caplog):
    use_settings(monkeypatch, coliseum_channel_id=None)

    coliseum.start_coliseum_notification(SimpleNamespace())

    assert "No channel ID is configured" in caplog.text
    assert not coliseum.task_coliseum_before_closing_notification.is_running()
