from fjormcord.bot.artping.config import load_config


def write(path, text):
    path.write_text(text)


def test_config_ini_overrides_example(tmp_path):
    write(tmp_path / "config.example.ini", "[discord]\ntoken=\n\n[database]\npath=test.db\n")
    write(tmp_path / "config.ini", "[discord]\ntoken=secret\n")

    config = load_config(tmp_path)

    assert config.get('discord', 'token') == "secret"
    assert config.get('database', 'path') == "test.db"


def test_example_is_used_without_config_ini(tmp_path):
    write(tmp_path / "config.example.ini", "[discord]\ntoken=\n")

    assert load_config(tmp_path).get('discord', 'token') == ""
