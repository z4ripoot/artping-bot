import pytest

from fjormcord.bot.artping import __main__ as main_module, config, database


class RecordingClient:
    started_with = None

    def __init__(self, **options):
        pass

    def run(self, token):
        RecordingClient.started_with = token


@pytest.fixture(autouse=True)
def reset_recording_client(monkeypatch):
    monkeypatch.setattr(RecordingClient, "started_with", None)


def test_missing_token_exits_with_setup_hint(tmp_path, monkeypatch):
    (tmp_path / "config.example.ini").write_text("[discord]\ntoken=\n")
    monkeypatch.setattr(config, "read_config", lambda: config.load_config(tmp_path))
    monkeypatch.setattr(main_module, "ArtPingClient", RecordingClient)

    with pytest.raises(SystemExit, match="config.ini"):
        main_module.main()

    assert RecordingClient.started_with is None


def test_database_is_opened_before_connecting_to_discord(tmp_path, monkeypatch):
    # A failing migration then stops the bot at startup instead of failing every command
    (tmp_path / "config.example.ini").write_text("[discord]\ntoken=secret\n")
    monkeypatch.setattr(config, "read_config", lambda: config.load_config(tmp_path))
    monkeypatch.setattr(main_module, "ArtPingClient", RecordingClient)

    def broken_database():
        raise RuntimeError("migration failed")

    monkeypatch.setattr(database, "get_database_connection", broken_database)

    with pytest.raises(RuntimeError, match="migration failed"):
        main_module.main()

    assert RecordingClient.started_with is None
