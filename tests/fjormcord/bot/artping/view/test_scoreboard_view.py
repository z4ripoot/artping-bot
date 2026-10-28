import asyncio

import pytest

from fjormcord.bot.artping.repository import currency_repository
from fjormcord.bot.artping.service import currency_service
from fjormcord.bot.artping.view.scoreboard_view import PageButton, ScoreboardView
from tests.fakes import FakeChannel, FakeClient, FakeInteraction


@pytest.fixture
def orbs():
    # 25 users, so 3 pages; user n has n Orbs
    currency_repository.add_currency("Orbs")
    currency = currency_repository.get_currency("Orbs")
    for user_id in range(1, 26):
        currency_repository.set_currency(str(user_id), currency.id, user_id)
    return currency


@pytest.fixture
def client():
    return FakeClient({user_id: f"User{user_id}" for user_id in range(1, 26)})


def post_scoreboard(client, page=1):
    reply = asyncio.run(currency_service.get_scoreboard(client, "Orbs", page))
    return FakeChannel().post(reply.content, reply.view)


def button_after_restart(button):
    # Rebuilt from its custom_id, as discord.py does for a click on a message sent before a restart
    match = PageButton.__discord_ui_compiled_template__.fullmatch(button.custom_id)
    return asyncio.run(PageButton.from_custom_id(FakeInteraction(), button.item, match))


def click(client, message, label, user_id=100):
    # Clicks the button with this label; returns what was sent in answer, the clicked message is edited in place
    button = next(button for button in message.view.children if button.item.label == label)
    interaction = FakeInteraction(user_id, client=client, message=message)
    asyncio.run(button_after_restart(button).callback(interaction))
    return interaction.sent


def pages(message):
    return [(button.item.label, button.page, button.item.disabled) for button in message.view.children]


def test_view_is_persistent():
    view = ScoreboardView(1, 2, 3)

    assert view.is_persistent()
    assert [button.item.custom_id for button in view.children] == ["scoreboard:1:1", "scoreboard:1:3"]


def test_next_turns_the_message_to_the_next_page(client, orbs):
    message = post_scoreboard(client)

    assert click(client, message, "Next ▶") == []

    assert message.content.splitlines()[:2] == ["Scoreboard for Orbs (page 2/3):", "11. User15 (15)"]
    assert pages(message) == [("◀ Previous", 1, False), ("Next ▶", 3, False)]


def test_buttons_are_disabled_at_the_ends(client, orbs):
    message = post_scoreboard(client, page=2)

    click(client, message, "Next ▶")

    assert message.content.splitlines()[0] == "Scoreboard for Orbs (page 3/3):"
    assert pages(message) == [("◀ Previous", 2, False), ("Next ▶", 4, True)]
    assert pages(post_scoreboard(client))[0] == ("◀ Previous", 0, True)


def test_turning_a_page_has_the_cooldown(client, orbs):
    message = post_scoreboard(client)
    click(client, message, "Next ▶")

    sent = click(client, message, "◀ Previous")

    assert sent == [("You used a command recently. Try again in 1 second", True, None)]
    assert message.content.splitlines()[0] == "Scoreboard for Orbs (page 2/3):"


def test_page_that_no_longer_exists_is_answered_privately(client, orbs):
    message = post_scoreboard(client, page=2)
    for user_id in range(11, 26):
        currency_repository.clear_currency(str(user_id), orbs.id)

    assert click(client, message, "Next ▶") == [
        ("Page 3 doesn't exist. The scoreboard for Orbs has 1 pages", True, None)
    ]


def test_scoreboard_that_shrank_to_one_page_loses_its_buttons(client, orbs):
    message = post_scoreboard(client, page=2)
    for user_id in range(11, 26):
        currency_repository.clear_currency(str(user_id), orbs.id)

    click(client, message, "◀ Previous")

    assert message.content.splitlines()[0] == "Scoreboard for Orbs:"
    assert message.view is None


def test_removed_currency_is_answered_privately(client, orbs):
    message = post_scoreboard(client)
    currency_repository.remove_currency(orbs.id)

    assert click(client, message, "Next ▶") == [("This currency doesn't exist anymore", True, None)]


def test_failed_click_is_answered_privately(client, orbs, monkeypatch, caplog):
    message = post_scoreboard(client)

    async def failing_get_scoreboard_page(client, currency_id, page):
        raise RuntimeError("database is locked")

    monkeypatch.setattr(currency_service, "get_scoreboard_page", failing_get_scoreboard_page)

    assert click(client, message, "Next ▶") == [("Something went wrong while turning the page", True, None)]
    assert "database is locked" in caplog.text
