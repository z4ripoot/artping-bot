from fjormcord.bot.artping.easter_eggs import CHROMK, LORENZ_SMILE
from fjormcord.bot.artping.slash.cog.easter_egg_cog import EasterEggCog
from tests.fakes import FakeInteraction, invoke


def test_lorenz_and_chromk_post_the_easter_eggs():
    cog = EasterEggCog()
    lorenz, chromk = FakeInteraction(), FakeInteraction()

    invoke(cog.lorenz, lorenz, cog)
    invoke(cog.chromk, chromk, cog)

    assert [(content, ephemeral) for content, ephemeral, _ in lorenz.sent] == [(LORENZ_SMILE, False)]
    assert [(content, ephemeral) for content, ephemeral, _ in chromk.sent] == [(CHROMK, False)]
