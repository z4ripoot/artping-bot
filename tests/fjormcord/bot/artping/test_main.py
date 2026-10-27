from pathlib import Path

import pytest

from fjormcord.bot.artping import __main__ as main_module, config, database
from fjormcord.bot.artping.config import Settings


class RecordingClient:
    started_with = None

    def __init__(self, **options):
        pass

    def run(self, token):
        RecordingClient.started_with = token


@pytest.fixture(autouse=True)
def reset_recording_client(monkeypatch):
    monkeypatch.setattr(RecordingClient, "started_with", None)


def use_token(monkeypatch, token):
    settings = Settings(discord_token=token, database_path=Path("test.db"), cooldown_seconds=1,
                        autocomplete_max_choices=20, coliseum_channel_id=None, guild_id=None,
                        art_ping_slash_max_characters=10, character_votes_needed=5, character_vote_emoji="⭐",
                        emoji={})
    monkeypatch.setattr(config, "read_settings", lambda: settings)


def test_missing_token_exits_with_setup_hint(monkeypatch):
    use_token(monkeypatch, "")
    monkeypatch.setattr(main_module, "ArtPingClient", RecordingClient)

    with pytest.raises(SystemExit, match="config.ini"):
        main_module.main()

    assert RecordingClient.started_with is None


def test_missing_config_exits_with_setup_hint(monkeypatch, tmp_path):
    monkeypatch.setattr(config, "read_settings", lambda: config.load_settings(tmp_path / "config.ini"))
    monkeypatch.setattr(main_module, "ArtPingClient", RecordingClient)

    with pytest.raises(SystemExit, match="Invalid configuration: .* Copy config.example.ini to config.ini"):
        main_module.main()

    assert RecordingClient.started_with is None


def test_database_is_opened_before_connecting_to_discord(monkeypatch):
    # A failing migration then stops the bot at startup instead of failing every command
    use_token(monkeypatch, "secret")
    monkeypatch.setattr(main_module, "ArtPingClient", RecordingClient)

    def broken_database():
        raise RuntimeError("migration failed")

    monkeypatch.setattr(database, "get_database_connection", broken_database)

    with pytest.raises(RuntimeError, match="migration failed"):
        main_module.main()

    assert RecordingClient.started_with is None
