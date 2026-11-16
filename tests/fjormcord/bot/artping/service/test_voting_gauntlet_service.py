import logging

import pytest

from fjormcord.bot.artping.model.voting_gauntlet import Entrant
from fjormcord.bot.artping.service.voting_gauntlet_service import (
    MESSAGE_ENDED,
    end_gauntlet,
    get_trackers,
    start_gauntlet,
    toggle_tracking,
)

DIMITRI, EDELGARD, CLAUDE, YURI = 8, 2, 4, 6
ENTRANTS = [
    Entrant(EDELGARD, "Edelgard", None, False),
    Entrant(DIMITRI, "Dimitri", None, False),
    Entrant(CLAUDE, "Claude", None, False),
    Entrant(YURI, "Yuri", None, False),
]


@pytest.fixture(autouse=True)
def running():
    start_gauntlet(112, ENTRANTS)


def test_track_a_character():
    assert (
        toggle_tracking(112, "1", DIMITRI, EDELGARD)
        == "You now track Dimitri. You'll be pinged every hour when Dimitri is Weaker"
    )
    assert get_trackers(112, DIMITRI) == ["1"]


def test_click_again_stops_tracking():
    toggle_tracking(112, "1", DIMITRI, EDELGARD)

    assert toggle_tracking(112, "1", DIMITRI, EDELGARD) == "You no longer track Dimitri"
    assert get_trackers(112, DIMITRI) == []


def test_tracking_the_opponent_switches_sides():
    toggle_tracking(112, "1", DIMITRI, EDELGARD)

    assert (
        toggle_tracking(112, "1", EDELGARD, DIMITRI)
        == "You now track Edelgard instead of Dimitri. You'll be pinged every hour when Edelgard is Weaker"
    )
    assert get_trackers(112, DIMITRI) == []
    assert get_trackers(112, EDELGARD) == ["1"]


def test_trackers_are_listed_per_character():
    toggle_tracking(112, "2", DIMITRI, EDELGARD)
    toggle_tracking(112, "1", DIMITRI, EDELGARD)
    toggle_tracking(112, "3", CLAUDE, YURI)

    assert get_trackers(112, DIMITRI) == ["1", "2"]


def test_ended_gauntlet_cannot_be_tracked():
    toggle_tracking(112, "1", DIMITRI, EDELGARD)

    end_gauntlet()

    assert get_trackers(112, DIMITRI) == []
    assert toggle_tracking(112, "1", DIMITRI, EDELGARD) == MESSAGE_ENDED


def test_ending_an_ended_gauntlet_again_logs_nothing(caplog):
    end_gauntlet()

    with caplog.at_level(logging.INFO):
        end_gauntlet()

    assert caplog.records == []


def test_older_gauntlet_cannot_be_tracked():
    assert toggle_tracking(111, "1", DIMITRI, EDELGARD) == MESSAGE_ENDED


def test_new_gauntlet_removes_the_trackers_of_the_old_one():
    toggle_tracking(112, "1", DIMITRI, EDELGARD)

    start_gauntlet(113, ENTRANTS)

    assert get_trackers(112, DIMITRI) == []
    assert toggle_tracking(113, "1", DIMITRI, EDELGARD).startswith("You now track Dimitri")


def test_starting_the_running_gauntlet_again_keeps_the_trackers():
    toggle_tracking(112, "1", DIMITRI, EDELGARD)

    start_gauntlet(112, ENTRANTS)

    assert get_trackers(112, DIMITRI) == ["1"]


def test_namesakes_are_tracked_apart():
    start_gauntlet(114, [Entrant(5, "Shez", None, False), Entrant(7, "Shez", None, False)])

    toggle_tracking(114, "1", 5, 7)

    assert toggle_tracking(114, "1", 7, 5) == (
        "You now track Shez instead of Shez. You'll be pinged every hour when Shez is Weaker"
    )
    assert get_trackers(114, 5) == []
    assert get_trackers(114, 7) == ["1"]


def test_unknown_entrant_cannot_be_tracked():
    assert toggle_tracking(112, "1", 1, DIMITRI) == MESSAGE_ENDED


def test_storing_the_entrants_again_keeps_their_trackers():
    toggle_tracking(112, "1", DIMITRI, EDELGARD)

    start_gauntlet(112, [Entrant(DIMITRI, "Dimitri", 5, True), *ENTRANTS[:1]])

    assert get_trackers(112, DIMITRI) == ["1"]
