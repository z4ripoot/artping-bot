import asyncio

import pytest

from fjormcord.bot.artping.repository import currency_repository
from fjormcord.bot.artping.service import currency_service
from fjormcord.bot.artping.view.layout import to_view
from fjormcord.bot.artping.view.scoreboard_view import CurrencySelect
from tests.fakes import (
    FakeChannel,
    FakeClient,
    FakeInteraction,
    after_restart,
    button_labels,
    items_of_type,
    select_options,
)


@pytest.fixture
def currencies():
    # Orbs and Gems, user 1 has 5 of each
    for name in ("Orbs", "Gems"):
        currency_repository.add_currency(name)
        currency_repository.set_currency("1", currency_repository.get_currency(name).id, 5)
    return {name: currency_repository.get_currency(name) for name in ("Orbs", "Gems")}


@pytest.fixture
def client():
    return FakeClient({1: "Alice"})


def post_scoreboard(client, page=1):
    layout = asyncio.run(currency_service.get_scoreboard(client, "Orbs", page))
    return asyncio.run(FakeChannel().send(view=to_view(layout)))


def dropdown(message):
    [select] = items_of_type(message.view, CurrencySelect)
    return select


def selected(message):
    return [option.label for option in dropdown(message).item.options if option.default]


def pick(client, message, currency, user_id=100):
    # Picks a currency in the message's dropdown, rebuilt from its custom_id as after a restart; returns the answer
    rebuilt = after_restart(dropdown(message))
    # discord.py has no public way to pick: it fills _values from the interaction's data
    rebuilt.item._values = [str(currency.id)]
    interaction = FakeInteraction(user_id, client=client, message=message)
    asyncio.run(rebuilt.callback(interaction))
    return interaction.sent


def test_dropdown_lists_the_currencies_alphabetically_with_the_current_one_selected(client, currencies):
    message = post_scoreboard(client)

    assert select_options(message.view) == ["Gems", "Orbs"]
    assert selected(message) == ["Orbs"]


def test_empty_scoreboard_keeps_its_header_and_dropdown(client):
    currency_repository.add_currency("Orbs")
    currency_repository.add_currency("Gems")

    message = post_scoreboard(client)

    assert message.content == "### Scoreboard for Orbs\nNobody has set their Orbs yet"
    assert select_options(message.view) == ["Gems", "Orbs"]


def test_picking_a_currency_shows_its_scoreboard(client, currencies):
    message = post_scoreboard(client)

    assert pick(client, message, currencies["Gems"]) == []

    assert message.content.splitlines()[0] == "### Scoreboard for Gems"
    assert selected(message) == ["Gems"]


def test_picking_a_removed_currency_is_answered_privately(client, currencies):
    message = post_scoreboard(client)
    currency_repository.remove_currency(currencies["Gems"].id)

    assert pick(client, message, currencies["Gems"]) == [("This currency doesn't exist anymore", True, None)]
    assert message.content.splitlines()[0] == "### Scoreboard for Orbs"


def test_picking_a_currency_has_the_cooldown(client, currencies):
    message = post_scoreboard(client)
    pick(client, message, currencies["Gems"])

    sent = pick(client, message, currencies["Orbs"])

    assert sent == [("You used a command recently. Try again in 1 second", True, None)]
    assert message.content.splitlines()[0] == "### Scoreboard for Gems"


def test_refused_pick_redraws_the_scoreboard_so_the_dropdown_drops_it(client, currencies):
    message = post_scoreboard(client)
    pick(client, message, currencies["Gems"])
    shown = message.view

    pick(client, message, currencies["Orbs"])

    # Discord keeps showing a picked option until the message is edited, so the refused pick is drawn away
    assert message.view is not shown
    assert selected(message) == ["Gems"]
    assert message.content.splitlines()[0] == "### Scoreboard for Gems"


def test_refused_pick_keeps_the_page(currencies):
    for user_id in range(2, 13):
        currency_repository.set_currency(str(user_id), currencies["Orbs"].id, user_id)
    client = FakeClient({user_id: f"User{user_id}" for user_id in range(1, 13)})
    message = post_scoreboard(client, page=2)
    currency_repository.remove_currency(currencies["Gems"].id)
    shown = message.view

    pick(client, message, currencies["Gems"])

    assert message.view is not shown
    assert message.content.splitlines()[0] == "### Scoreboard for Orbs (page 2/2)"
    # Orbs is the only currency left, so the redrawn scoreboard has no dropdown, only its pages
    assert button_labels(message.view) == ["◀ Previous", "Next ▶"]
