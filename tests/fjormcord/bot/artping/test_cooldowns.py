import pytest

from fjormcord.bot.artping.cooldowns import Cooldowns
from fjormcord.bot.artping.exception.command_error import CommandError
from tests.fakes import FakeClock, make_member


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


def test_command_that_succeeds_starts_the_cooldown():
    cooldowns = Cooldowns(30, FakeClock())

    with cooldowns.command(make_member(1)):
        pass

    assert cooldowns.remaining(1) == 30


def test_command_that_fails_does_not_start_the_cooldown():
    cooldowns = Cooldowns(30, FakeClock())

    with pytest.raises(CommandError):
        with cooldowns.command(make_member(1)):
            raise CommandError("Turned down")

    assert cooldowns.remaining(1) == 0


def test_command_turns_down_a_user_on_cooldown_without_running():
    cooldowns = Cooldowns(30, FakeClock())
    cooldowns.start(1)
    ran = False

    with pytest.raises(CommandError):
        with cooldowns.command(make_member(1)):
            ran = True

    assert not ran


def test_command_of_an_admin_starts_no_cooldown():
    cooldowns = Cooldowns(30, FakeClock())

    with cooldowns.command(make_member(1, administrator=True)):
        pass

    assert cooldowns.remaining(1) == 0
