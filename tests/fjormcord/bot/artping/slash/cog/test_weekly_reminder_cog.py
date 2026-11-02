import pytest

from fjormcord.bot.artping.slash.cog.weekly_reminder_cog import WeeklyReminderCog
from tests.fakes import FakeChannel, FakeInteraction, invoke, use_settings


@pytest.fixture
def cog():
    return WeeklyReminderCog()


def test_closing_times_are_public(cog):
    interaction = FakeInteraction()

    invoke(cog.closing_times, interaction, cog)

    assert interaction.sent[0].content.startswith("### Closing times\n")
    assert interaction.sent[0].ephemeral is False


def test_send_reminders_answers_the_admin_privately(monkeypatch, cog):
    channel = FakeChannel(channel_id=20)
    use_settings(monkeypatch, coliseum_channel_id=20, divine_games_channel_id=None)
    interaction = FakeInteraction(administrator=True, channel=channel)

    invoke(cog.send_reminders, interaction, cog)

    assert interaction.response.deferred == [{"ephemeral": True}]
    assert interaction.sent[0].content == (
        "Coliseum notification: sent to <#20>\nDivine Games notification: no channel is configured"
    )
    assert interaction.sent[0].ephemeral is True
    assert len(channel.sent) == 1
