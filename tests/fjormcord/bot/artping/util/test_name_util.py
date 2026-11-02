import pytest

from fjormcord.bot.artping.util.name_util import normalize_name


@pytest.mark.parametrize(
    "name, expected",
    [
        ("furina", "Furina"),
        ("fURINA", "Furina"),
        ("black_knight", "Black_Knight"),
        ("hu_TAO", "Hu_TAO"),
        ("FGO", "FGO"),
        ("jade_HSR", "Jade_HSR"),
        ("selena_FE8", "Selena_FE8"),
        ("kos-mos", "Kos-Mos"),
        ("Spider-Man", "Spider-Man"),
        ("l'arachel", "L'Arachel"),
        ("m!robin", "M!Robin"),
        ("DeathKnight", "Deathknight"),
        ("2b", "2b"),
    ],
)
def test_every_part_of_a_name_starts_with_a_capital(name, expected):
    assert normalize_name(name) == expected
