from tests.fakes import registered_slash_commands, use_settings

MAX_DESCRIPTION = 100


def test_descriptions_fit_discord(monkeypatch):
    # /artping with every character option the setting allows, each with its description
    use_settings(monkeypatch, art_ping_slash_max_characters=25)

    for command in registered_slash_commands():
        assert 0 < len(command.description) <= MAX_DESCRIPTION, command.name
        for parameter in command.parameters:
            assert 0 < len(parameter.description) <= MAX_DESCRIPTION, f"{command.name} {parameter.name}"
