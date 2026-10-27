import configparser

import pytest

from fjormcord.bot.artping.config import EXAMPLE_CONFIG_FILE, load_settings


def write_config(directory, changes=None, encoding="utf-8"):
    # The example as directory/config.ini, with changes as {(section, key): value}
    parser = configparser.ConfigParser()
    parser.read(EXAMPLE_CONFIG_FILE, encoding="utf-8")
    for (section, key), value in (changes or {}).items():
        parser[section][key] = value
    path = directory / "config.ini"
    with path.open("w", encoding=encoding) as file:
        parser.write(file)
    return path


def test_example_is_a_complete_config():
    settings = load_settings(EXAMPLE_CONFIG_FILE)

    assert settings.discord_token == ""
    assert settings.database_path == EXAMPLE_CONFIG_FILE.parent / "test.db"
    assert settings.cooldown_seconds == 1
    assert settings.autocomplete_max_choices == 20
    assert settings.coliseum_channel_id is None
    assert settings.guild_id is None
    assert settings.art_ping_slash_max_characters == 10
    assert settings.character_votes_needed == 5
    assert settings.character_vote_emoji == "⭐"
    assert settings.emoji['lorenz_smile'].startswith("<:LorenzSmile:")


def test_settings_are_read_from_the_file(tmp_path):
    path = write_config(tmp_path, {("discord", "token"): "secret", ("discord", "guild_id"): "456",
                                   ("commands", "cooldown_seconds"): "2.5",
                                   ("commands", "autocomplete_max_choices"): "7",
                                   ("art_ping", "slash_max_characters"): "3",
                                   ("tasks", "coliseum_notification_channel_id"): "123",
                                   ("character_vote", "votes_needed"): "3",
                                   ("character_vote", "emoji"): "<:Vote:123>"})

    settings = load_settings(path)

    assert settings.discord_token == "secret"
    assert settings.cooldown_seconds == 2.5
    assert settings.autocomplete_max_choices == 7
    assert settings.coliseum_channel_id == 123
    assert settings.guild_id == 456
    assert settings.art_ping_slash_max_characters == 3
    assert settings.character_votes_needed == 3
    assert settings.character_vote_emoji == "<:Vote:123>"
    # Relative to the config file, not the working directory
    assert settings.database_path == tmp_path / "test.db"


@pytest.mark.parametrize("setting", [("art_ping", "slash_max_characters"), ("commands", "autocomplete_max_choices")])
@pytest.mark.parametrize("value", ["0", "26"])
def test_discord_limits_are_enforced(tmp_path, setting, value):
    path = write_config(tmp_path, {setting: value})

    with pytest.raises(ValueError, match=f"{setting[0]}.{setting[1]} must be between 1 and 25"):
        load_settings(path)


def test_missing_setting_fails_when_loading(tmp_path):
    # There are no defaults to fall back on
    (tmp_path / "config.ini").write_text("[discord]\ntoken=secret\n")

    with pytest.raises(configparser.Error):
        load_settings(tmp_path / "config.ini")


def test_missing_file_fails_with_setup_hint(tmp_path):
    with pytest.raises(FileNotFoundError, match="Copy config.example.ini to config.ini"):
        load_settings(tmp_path / "config.ini")


def test_config_ini_saved_with_a_byte_order_mark_is_read(tmp_path):
    path = write_config(tmp_path, {("discord", "token"): "secret"}, encoding="utf-8-sig")

    assert load_settings(path).discord_token == "secret"
