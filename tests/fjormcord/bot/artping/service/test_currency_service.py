import asyncio

from fjormcord.bot.artping.service.currency_service import add_currency, remove_currency, set_currency, clear_currency, check_wallet, \
    get_scoreboard
from tests.fakes import make_message


def test_set_currency_creates_then_updates_wallet(client):
    add_currency(client, make_message("~addcurrency Orbs"))

    assert set_currency(client, make_message("~setcurrency orbs 10")) == "Your Orbs has been set to 10"
    assert set_currency(client, make_message("~setcurrency orbs 25")) == "Your Orbs has been set to 25"
    assert check_wallet(client, make_message("~checkwallet")) == "User user1's wallet:\nOrbs: 25\n"


def test_set_currency_rejects_invalid_amount(client):
    add_currency(client, make_message("~addcurrency Orbs"))

    assert set_currency(client, make_message("~setcurrency orbs lots")) == \
        "Failed to set currency. Please enter a valid amount for your orbs."


def test_clear_currency(client):
    add_currency(client, make_message("~addcurrency Orbs"))
    set_currency(client, make_message("~setcurrency orbs 10"))

    assert clear_currency(client, make_message("~clearcurrency orbs")) == "Your Orbs has been cleared"
    assert clear_currency(client, make_message("~clearcurrency orbs")) == \
        "Failed to clear currency Orbs for user. Currency Orbs for user doesn't exist"


def test_remove_currency_cascades_to_wallets(client, database):
    add_currency(client, make_message("~addcurrency Orbs"))
    set_currency(client, make_message("~setcurrency orbs 10"))

    assert remove_currency(client, make_message("~removecurrency orbs")) == "Currency Orbs has been removed"
    assert database.execute("SELECT COUNT(*) FROM GACHA_CURRENCY_WALLET").fetchone()[0] == 0


def test_scoreboard_orders_by_amount(client):
    add_currency(client, make_message("~addcurrency Orbs"))
    set_currency(client, make_message("~setcurrency orbs 10", user_id=1))
    set_currency(client, make_message("~setcurrency orbs 30", user_id=2))

    out = asyncio.run(get_scoreboard(client, make_message("~scoreboard orbs")))

    assert out == "Scoreboard for Orbs:\n1. Bob (30)\n2. Alice (10)\n"
