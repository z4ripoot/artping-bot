import configparser
import shutil

import pytest

from fjormcord.bot.artping.config import PROJECT_ROOT, load_settings


@pytest.fixture
def directory(tmp_path):
    # A copy of the committed defaults, without the developer's own config.ini
    shutil.copy(PROJECT_ROOT / "config.example.ini", tmp_path)
    return tmp_path


def test_defaults_come_from_the_example(directory):
    settings = load_settings(directory)

    assert settings.discord_token == ""
    assert settings.database_path == directory / "test.db"
    assert settings.art_ping_cooldown_seconds == 1
    assert settings.coliseum_channel_id is None
    assert settings.emoji['lorenz_smile'].startswith("<:LorenzSmile:")


def test_config_ini_overrides_the_example(directory):
    (directory / "config.ini").write_text("[discord]\ntoken=secret\n\n"
                                          "[art_ping]\ncooldown_seconds=2.5\n\n"
                                          "[tasks]\ncoliseum_notification_channel_id=123\n")

    settings = load_settings(directory)

    assert settings.discord_token == "secret"
    assert settings.art_ping_cooldown_seconds == 2.5
    assert settings.coliseum_channel_id == 123
    assert settings.database_path == directory / "test.db"


def test_missing_setting_fails_when_loading(tmp_path):
    (tmp_path / "config.example.ini").write_text("[discord]\ntoken=\n")

    with pytest.raises(configparser.Error):
        load_settings(tmp_path)
