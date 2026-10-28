import asyncio

import pytest

from fjormcord.bot.artping.repository import art_ping_repository, character_repository, currency_repository
from fjormcord.bot.artping.service import art_ping_service, character_service, currency_service
from fjormcord.bot.artping.view.layout import to_view
from fjormcord.bot.artping.view.page_view import PageButton, page_buttons
from tests.fakes import FakeChannel, FakeClient, FakeInteraction, button_labels


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
    layout = asyncio.run(currency_service.get_scoreboard(client, "Orbs", page))
    return asyncio.run(FakeChannel().send(view=to_view(layout)))


def page_items(message):
    return [item for item in message.view.walk_children() if isinstance(item, PageButton)]


def button_after_restart(button):
    # Rebuilt from its custom_id, as discord.py does for a click on a message sent before a restart
    match = PageButton.__discord_ui_compiled_template__.fullmatch(button.custom_id)
    return asyncio.run(PageButton.from_custom_id(FakeInteraction(), button.item, match))


def click(client, message, label, user_id=100):
    # Clicks the button with this label; returns what was sent in answer, the clicked message is edited in place
    button = next(button for button in page_items(message) if button.item.label == label)
    interaction = FakeInteraction(user_id, client=client, message=message)
    asyncio.run(button_after_restart(button).callback(interaction))
    return interaction.sent


def pages(message):
    return [(button.item.label, button.page, button.item.disabled) for button in page_items(message)]


def test_page_buttons_hold_the_kind_the_subject_and_the_page():
    previous, following = page_buttons("scoreboard", 1, 2, 3)

    assert (previous.custom_id, following.custom_id) == ("page:scoreboard:1:1", "page:scoreboard:1:3")


def test_a_single_page_has_no_buttons():
    assert page_buttons("scoreboard", 1, 1, 1) == ()


def test_next_turns_the_message_to_the_next_page(client, orbs):
    message = post_scoreboard(client)

    assert click(client, message, "Next ▶") == []

    assert message.content.splitlines()[:2] == ["### Scoreboard for Orbs (page 2/3)", "11. User15 (15)"]
    assert pages(message) == [("◀ Previous", 1, False), ("Next ▶", 3, False)]


def test_buttons_are_disabled_at_the_ends(client, orbs):
    message = post_scoreboard(client, page=2)

    click(client, message, "Next ▶")

    assert message.content.splitlines()[0] == "### Scoreboard for Orbs (page 3/3)"
    assert pages(message) == [("◀ Previous", 2, False), ("Next ▶", 4, True)]
    assert pages(post_scoreboard(client))[0] == ("◀ Previous", 0, True)


def test_turning_a_page_has_the_cooldown(client, orbs):
    message = post_scoreboard(client)
    click(client, message, "Next ▶")

    sent = click(client, message, "◀ Previous")

    assert sent == [("You used a command recently. Try again in 1 second", True, None)]
    assert message.content.splitlines()[0] == "### Scoreboard for Orbs (page 2/3)"


def test_page_that_no_longer_exists_is_answered_privately(client, orbs):
    message = post_scoreboard(client, page=2)
    for user_id in range(11, 26):
        currency_repository.clear_currency(str(user_id), orbs.id)

    assert click(client, message, "Next ▶") == [
        ("Page 3 doesn't exist. The scoreboard for Orbs has 1 page", True, None)
    ]
    assert message.content.splitlines()[0] == "### Scoreboard for Orbs (page 2/3)"


def test_scoreboard_that_shrank_to_one_page_loses_its_buttons(client, orbs):
    message = post_scoreboard(client, page=2)
    for user_id in range(11, 26):
        currency_repository.clear_currency(str(user_id), orbs.id)

    click(client, message, "◀ Previous")

    assert message.content.splitlines()[0] == "### Scoreboard for Orbs"
    assert button_labels(message.view) == []


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


def post(layout):
    return asyncio.run(FakeChannel().send(view=to_view(layout)))


def test_next_turns_a_ping_list_to_the_next_page():
    client = FakeClient({1: "Alice"})
    for number in range(1, 13):
        character_id = character_repository.add_character(f"Hero{number:02d}")
        art_ping_repository.add_ping(character_id, "1")
    message = post(asyncio.run(art_ping_service.check_ping(client, "1")))

    click(client, message, "Next ▶")

    assert message.content == "### Alice's pings (page 2/2)\nHero11\nHero12"


def test_next_turns_a_character_list_to_the_next_page():
    client = FakeClient({user_id: f"User{user_id}" for user_id in range(1, 13)})
    character_id = character_repository.add_character("Lucina")
    for user_id in range(1, 13):
        art_ping_repository.add_ping(character_id, str(user_id))
    message = post(asyncio.run(character_service.check_character(client, "Lucina")))

    click(client, message, "Next ▶")

    assert message.content == "### Lucina's pings (page 2/2)\nUser11\nUser12"


def test_removed_character_is_answered_privately():
    client = FakeClient()
    character_id = character_repository.add_character("Lucina")
    for user_id in range(1, 13):
        art_ping_repository.add_ping(character_id, str(user_id))
    message = post(asyncio.run(character_service.check_character(client, "Lucina")))
    character_repository.remove_character(character_id)

    assert click(client, message, "Next ▶") == [("This character doesn't exist anymore", True, None)]
