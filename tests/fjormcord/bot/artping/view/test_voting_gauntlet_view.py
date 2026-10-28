import asyncio

from fjormcord.bot.artping.model.voting_gauntlet import Entrant
from fjormcord.bot.artping.service import voting_gauntlet_service
from fjormcord.bot.artping.view.voting_gauntlet_view import TrackButton, TrackView
from tests.fakes import FakeInteraction

MATCHUP = (Entrant("Edelgard", 2, behind=False), Entrant("Dimitri", 1, behind=True))


def button_after_restart(button):
    # Rebuilt from its custom_id, as discord.py does for a click on a message sent before a restart
    match = TrackButton.__discord_ui_compiled_template__.fullmatch(button.custom_id)
    return asyncio.run(TrackButton.from_custom_id(FakeInteraction(), button.item, match))


def click(button, user_id=1):
    interaction = FakeInteraction(user_id)
    asyncio.run(button.callback(interaction))
    return interaction.sent


def test_view_is_persistent():
    view = TrackView(112, MATCHUP)

    assert view.is_persistent()
    assert [button.item.label for button in view.children] == ["Track Edelgard", "Track Dimitri"]


def test_button_is_rebuilt_from_its_custom_id():
    button = button_after_restart(TrackView(112, MATCHUP).children[1])

    assert (button.tournament_id, button.name, button.opponent) == (112, "Dimitri", "Edelgard")
    assert button.item.label == "Track Dimitri"


def test_click_tracks_the_character_and_answers_privately():
    voting_gauntlet_service.start_gauntlet(112)

    sent = click(button_after_restart(TrackView(112, MATCHUP).children[1]), user_id=7)

    assert sent == [("You now track Dimitri. You'll be pinged every hour Dimitri is Weaker", True, None)]
    assert voting_gauntlet_service.get_trackers(112, "Dimitri") == ["7"]


def test_failed_click_is_answered_privately(monkeypatch, caplog):
    def failing_toggle_tracking(tournament_id, user_id, name, opponent):
        raise RuntimeError("database is locked")

    monkeypatch.setattr(voting_gauntlet_service, "toggle_tracking", failing_toggle_tracking)

    assert click(TrackView(112, MATCHUP).children[0]) == [("Something went wrong while tracking", True, None)]
    assert "database is locked" in caplog.text
