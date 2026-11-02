import os
import subprocess
import sys

import pytest

from fjormcord.bot.artping import __main__ as main_module
from fjormcord.bot.artping import config, database
from tests.fakes import use_settings


class RecordingClient:
    started_with = None

    def __init__(self, **options):
        pass

    def run(self, token):
        RecordingClient.started_with = token


@pytest.fixture(autouse=True)
def reset_recording_client(monkeypatch):
    monkeypatch.setattr(RecordingClient, "started_with", None)


def test_missing_token_exits_with_setup_hint(monkeypatch):
    use_settings(monkeypatch, discord_token="")
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


def test_missing_config_is_reported_before_any_module_reads_it(tmp_path):
    # In a fresh process, as a module that read the settings when imported would fail before main can report it
    script = (
        "from pathlib import Path\n"
        "from fjormcord.bot.artping import config\n"
        f"config.CONFIG_FILE = Path({str(tmp_path / 'config.ini')!r})\n"
        "from fjormcord.bot.artping.__main__ import main\n"
        "main()\n"
    )
    environment = {**os.environ, "PYTHONPATH": str(config.PROJECT_ROOT / "src")}

    result = subprocess.run([sys.executable, "-c", script], capture_output=True, text=True, env=environment)

    assert result.returncode == 1
    assert result.stderr.startswith("Invalid configuration: ")


def test_database_is_opened_before_connecting_to_discord(monkeypatch):
    # A failing migration then stops the bot at startup instead of failing every command
    use_settings(monkeypatch, discord_token="secret")
    monkeypatch.setattr(main_module, "ArtPingClient", RecordingClient)

    def broken_database():
        raise RuntimeError("migration failed")

    monkeypatch.setattr(database, "get_database_connection", broken_database)

    with pytest.raises(RuntimeError, match="migration failed"):
        main_module.main()

    assert RecordingClient.started_with is None
