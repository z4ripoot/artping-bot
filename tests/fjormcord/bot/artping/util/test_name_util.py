import pytest

from fjormcord.bot.artping.util.name_util import normalize_name


@pytest.mark.parametrize(
    "name, expected",
    [
        ("furina", "Furina"),
        ("FURINA", "Furina"),
        ("black_knight", "Black_Knight"),
        ("HU_TAO", "Hu_Tao"),
        ("l'arachel", "L'Arachel"),
        ("m!robin", "M!Robin"),
        ("DeathKnight", "Deathknight"),
        ("2b", "2b"),
    ],
)
def test_every_part_of_a_name_starts_with_a_capital(name, expected):
    assert normalize_name(name) == expected
