from fjormcord.bot.artping.legacy.handler.weekly_reminder_handlers import get_closing_times, send_reminders
from tests.fakes import FakeClient, make_message, reply, use_settings


def test_closing_times_lists_every_reminder():
    out = reply(get_closing_times, FakeClient(), make_message("~closingtimes"))

    assert out.texts[0] == "### Closing times"
    assert len(out.texts[1].splitlines()) == 2


def test_send_reminders_reports_each_reminder(monkeypatch):
    use_settings(monkeypatch, coliseum_channel_id=None, divine_games_channel_id=None)

    out = reply(send_reminders, FakeClient(), make_message("~sendreminders", administrator=True))

    assert out == (
        "Coliseum notification: no channel is configured\nDivine Games notification: no channel is configured"
    )
