import pytest

from fjormcord.bot.artping.service.voting_gauntlet_service import (MESSAGE_ENDED, end_gauntlet, get_trackers,
                                                                   start_gauntlet, toggle_tracking)


@pytest.fixture(autouse=True)
def running():
    start_gauntlet(112)


def test_track_a_character():
    assert toggle_tracking(112, "1", "Dimitri", "Edelgard") == \
        "You now track Dimitri. You'll be pinged every hour Dimitri is Weaker"
    assert get_trackers(112, "Dimitri") == ["1"]


def test_click_again_stops_tracking():
    toggle_tracking(112, "1", "Dimitri", "Edelgard")

    assert toggle_tracking(112, "1", "Dimitri", "Edelgard") == "You no longer track Dimitri"
    assert get_trackers(112, "Dimitri") == []


def test_tracking_the_opponent_switches_sides():
    toggle_tracking(112, "1", "Dimitri", "Edelgard")

    assert toggle_tracking(112, "1", "Edelgard", "Dimitri") == \
        "You now track Edelgard instead of Dimitri. You'll be pinged every hour Edelgard is Weaker"
    assert get_trackers(112, "Dimitri") == []
    assert get_trackers(112, "Edelgard") == ["1"]


def test_trackers_are_listed_per_character():
    toggle_tracking(112, "2", "Dimitri", "Edelgard")
    toggle_tracking(112, "1", "Dimitri", "Edelgard")
    toggle_tracking(112, "3", "Claude", "Yuri")

    assert get_trackers(112, "Dimitri") == ["1", "2"]


def test_ended_gauntlet_cannot_be_tracked():
    toggle_tracking(112, "1", "Dimitri", "Edelgard")

    end_gauntlet()

    assert get_trackers(112, "Dimitri") == []
    assert toggle_tracking(112, "1", "Dimitri", "Edelgard") == MESSAGE_ENDED


def test_older_gauntlet_cannot_be_tracked():
    assert toggle_tracking(111, "1", "Dimitri", "Edelgard") == MESSAGE_ENDED


def test_new_gauntlet_removes_the_trackers_of_the_old_one():
    toggle_tracking(112, "1", "Dimitri", "Edelgard")

    start_gauntlet(113)

    assert get_trackers(112, "Dimitri") == []
    assert toggle_tracking(113, "1", "Dimitri", "Edelgard").startswith("You now track Dimitri")


def test_starting_the_running_gauntlet_again_keeps_the_trackers():
    toggle_tracking(112, "1", "Dimitri", "Edelgard")

    start_gauntlet(112)

    assert get_trackers(112, "Dimitri") == ["1"]
