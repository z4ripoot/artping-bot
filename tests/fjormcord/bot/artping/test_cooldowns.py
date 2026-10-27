import pytest

from fjormcord.bot.artping.cooldowns import Cooldowns
from fjormcord.bot.artping.exception.command_error import CommandError
from tests.fakes import FakeClock


def test_nothing_remains_without_a_cooldown():
    assert Cooldowns(30, FakeClock()).remaining(1) == 0


def test_remaining_counts_down_to_zero():
    clock = FakeClock()
    cooldowns = Cooldowns(30, clock)
    cooldowns.start(1)

    clock.advance(10)
    assert cooldowns.remaining(1) == 20

    clock.advance(25)
    assert cooldowns.remaining(1) == 0


def test_cooldowns_are_kept_per_user():
    cooldowns = Cooldowns(30, FakeClock())
    cooldowns.start(1)

    assert cooldowns.remaining(2) == 0


def test_zero_seconds_means_no_cooldown():
    cooldowns = Cooldowns(0, FakeClock())
    cooldowns.start(1)

    assert cooldowns.remaining(1) == 0


def test_check_turns_down_a_user_on_cooldown():
    clock = FakeClock()
    cooldowns = Cooldowns(30, clock)
    cooldowns.start(1)
    clock.advance(10)

    with pytest.raises(CommandError, match="^You used a command recently. Try again in 20 seconds$"):
        cooldowns.check(1)
    cooldowns.check(2)
