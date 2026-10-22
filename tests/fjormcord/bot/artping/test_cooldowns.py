from fjormcord.bot.artping.cooldowns import Cooldowns
from tests.fakes import FakeClock


def test_nothing_remains_without_a_cooldown():
    assert Cooldowns(FakeClock()).remaining("~artping", 1) == 0


def test_remaining_counts_down_to_zero():
    clock = FakeClock()
    cooldowns = Cooldowns(clock)
    cooldowns.start("~artping", 1, 30)

    clock.advance(10)
    assert cooldowns.remaining("~artping", 1) == 20

    clock.advance(25)
    assert cooldowns.remaining("~artping", 1) == 0


def test_cooldowns_are_kept_per_command_and_user():
    cooldowns = Cooldowns(FakeClock())
    cooldowns.start("~artping", 1, 30)

    assert cooldowns.remaining("~artping", 2) == 0
    assert cooldowns.remaining("~checkping", 1) == 0
