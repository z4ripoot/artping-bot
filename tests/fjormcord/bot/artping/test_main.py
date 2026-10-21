import pytest

from fjormcord.bot.artping import __main__ as main_module, config


class RecordingClient:
    started_with = None

    def __init__(self, **options):
        pass

    def run(self, token):
        RecordingClient.started_with = token


def test_missing_token_exits_with_setup_hint(tmp_path, monkeypatch):
    (tmp_path / "config.example.ini").write_text("[discord]\ntoken=\n")
    monkeypatch.setattr(config, "read_config", lambda: config.load_config(tmp_path))
    monkeypatch.setattr(main_module, "ArtPingClient", RecordingClient)

    with pytest.raises(SystemExit, match="config.ini"):
        main_module.main()

    assert RecordingClient.started_with is None
