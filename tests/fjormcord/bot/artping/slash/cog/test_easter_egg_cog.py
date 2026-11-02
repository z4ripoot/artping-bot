from fjormcord.bot.artping import easter_eggs
from fjormcord.bot.artping.slash.cog.easter_egg_cog import EasterEggCog
from tests.fakes import FakeInteraction, invoke


def test_lorenz_and_chromk_post_the_easter_eggs():
    cog = EasterEggCog()
    lorenz, chromk = FakeInteraction(), FakeInteraction()

    invoke(cog.lorenz, lorenz, cog)
    invoke(cog.chromk, chromk, cog)

    assert [(content, ephemeral) for content, ephemeral, _ in lorenz.sent] == [(easter_eggs.lorenz_smile(), False)]
    assert [(content, ephemeral) for content, ephemeral, _ in chromk.sent] == [(easter_eggs.chromk(), False)]
