import pytest

from fjormcord.bot.artping.legacy.handler.currency_handlers import (
    add_currency,
    check_wallet,
    clear_currency,
    get_scoreboard,
    remove_currency,
    set_currency,
)
from fjormcord.bot.artping.repository import currency_repository
from fjormcord.bot.artping.util.message_util import MESSAGE_ONE_NAME_ONLY
from tests.fakes import FakeClient, make_message, reply


@pytest.fixture
def orbs():
    currency_repository.add_currency("Orbs")
    return currency_repository.get_currency("Orbs")


def set_amount(currency, amount, user_id=1):
    currency_repository.set_currency(str(user_id), currency.id, amount)


def test_set_currency_creates_then_updates_wallet(client, orbs):
    assert reply(set_currency, client, make_message("~setcurrency orbs 10")) == "Your Orbs has been set to 10"
    assert reply(set_currency, client, make_message("~setcurrency orbs 25")) == "Your Orbs has been set to 25"
    assert reply(check_wallet, client, make_message("~checkwallet")) == "User user1's wallet:\nOrbs: 25"


def test_set_currency_rejects_invalid_amount(client, orbs):
    assert (
        reply(set_currency, client, make_message("~setcurrency orbs lots"))
        == "Failed to set currency. Please enter a valid amount for your orbs."
    )


def test_clear_currency(client, orbs):
    set_amount(orbs, 10)

    assert reply(clear_currency, client, make_message("~clearcurrency orbs")) == "Your Orbs has been cleared"
    assert reply(clear_currency, client, make_message("~clearcurrency orbs")) == "You don't have any Orbs set"


def test_remove_currency_cascades_to_wallets(client, database, orbs):
    set_amount(orbs, 10)

    assert reply(remove_currency, client, make_message("~removecurrency orbs")) == "Currency Orbs has been removed"
    assert database.execute("SELECT COUNT(*) FROM GACHA_CURRENCY_WALLET").fetchone()[0] == 0


def test_scoreboard_orders_by_amount(client, orbs):
    set_amount(orbs, 10, user_id=1)
    set_amount(orbs, 30, user_id=2)

    out = reply(get_scoreboard, client, make_message("~scoreboard orbs"))

    assert out.texts == ("### Scoreboard for Orbs", "1. Bob (30)\n2. Alice (10)")


def test_currency_commands_reject_spaces_in_names(client):
    currency_repository.add_currency("Fire")
    set_amount(currency_repository.get_currency("Fire"), 10)

    assert reply(add_currency, client, make_message("~addcurrency Fire Orbs")) == MESSAGE_ONE_NAME_ONLY
    assert reply(set_currency, client, make_message("~setcurrency Fire Orbs 50")) == MESSAGE_ONE_NAME_ONLY
    assert reply(clear_currency, client, make_message("~clearcurrency Fire Orbs")) == MESSAGE_ONE_NAME_ONLY
    assert reply(get_scoreboard, client, make_message("~scoreboard Fire Orbs")) == MESSAGE_ONE_NAME_ONLY
    assert reply(remove_currency, client, make_message("~removecurrency Fire Orbs")) == MESSAGE_ONE_NAME_ONLY
    assert reply(check_wallet, client, make_message("~checkwallet")) == "User user1's wallet:\nFire: 10"


def scoreboard_of_25_users(orbs):
    # User n has n * 10 Orbs, so User25 ranks first
    for user_id in range(1, 26):
        set_amount(orbs, user_id * 10, user_id=user_id)
    return FakeClient({user_id: f"User{user_id}" for user_id in range(1, 26)})


def test_scoreboard_shows_first_page_of_ten(orbs):
    client = scoreboard_of_25_users(orbs)

    out = reply(get_scoreboard, client, make_message("~scoreboard orbs"))

    assert out.texts == (
        "### Scoreboard for Orbs (page 1/3)",
        "\n".join(f"{rank}. User{26 - rank} ({(26 - rank) * 10})" for rank in range(1, 11)),
    )
    assert len(client.fetched) == 10


def test_scoreboard_last_page_continues_ranking(orbs):
    client = scoreboard_of_25_users(orbs)

    out = reply(get_scoreboard, client, make_message("~scoreboard orbs 3"))

    assert out.texts == (
        "### Scoreboard for Orbs (page 3/3)",
        "\n".join(f"{rank}. User{26 - rank} ({(26 - rank) * 10})" for rank in range(21, 26)),
    )
    assert len(client.fetched) == 5


def test_scoreboard_rejects_page_out_of_range(orbs):
    client = scoreboard_of_25_users(orbs)

    assert (
        reply(get_scoreboard, client, make_message("~scoreboard orbs 4"))
        == "Page 4 doesn't exist. The scoreboard for Orbs has 3 pages"
    )
    assert (
        reply(get_scoreboard, client, make_message("~scoreboard orbs 0"))
        == "Page 0 doesn't exist. The scoreboard for Orbs has 3 pages"
    )


def test_scoreboard_without_entries(client, orbs):
    assert reply(get_scoreboard, client, make_message("~scoreboard orbs")).texts == (
        "### Scoreboard for Orbs",
        "Nobody has set their Orbs yet",
    )


def test_scoreboard_rejects_more_than_name_and_page(client, orbs):
    assert reply(get_scoreboard, client, make_message("~scoreboard orbs 1 2")) == MESSAGE_ONE_NAME_ONLY


def test_scoreboard_page_must_be_a_number(client, orbs):
    for page in ("--1", "²", "two"):
        assert reply(get_scoreboard, client, make_message(f"~scoreboard orbs {page}")) == MESSAGE_ONE_NAME_ONLY


def test_set_currency_rejects_negative_amount(client, orbs):
    assert (
        reply(set_currency, client, make_message("~setcurrency orbs -500"))
        == "Failed to set currency. The amount can't be negative"
    )
    assert reply(set_currency, client, make_message("~setcurrency orbs 0")) == "Your Orbs has been set to 0"


def test_set_currency_rejects_amount_too_large_for_database(client, orbs):
    assert (
        reply(set_currency, client, make_message(f"~setcurrency orbs {2**63 - 1}"))
        == f"Your Orbs has been set to {2**63 - 1}"
    )
    assert (
        reply(set_currency, client, make_message(f"~setcurrency orbs {2**63}"))
        == "Failed to set currency. The amount is too large"
    )


def test_unknown_currency_is_reported_the_same_everywhere(client):
    expected = "Currency Gems doesn't exist"

    assert reply(set_currency, client, make_message("~setcurrency Gems 5")) == expected
    assert reply(clear_currency, client, make_message("~clearcurrency Gems")) == expected
    assert reply(remove_currency, client, make_message("~removecurrency Gems")) == expected
    assert reply(get_scoreboard, client, make_message("~scoreboard Gems")) == expected


def test_add_currency_rejects_duplicates_with_stored_name(client, orbs):
    assert reply(add_currency, client, make_message("~addcurrency orbs")) == "Currency Orbs already exists"


def test_empty_wallet(client):
    assert (
        reply(check_wallet, client, make_message("~checkwallet"))
        == "Your wallet is empty. Use ~setcurrency to add a currency"
    )
