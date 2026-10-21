import asyncio

from fjormcord.bot.artping.service.currency_service import add_currency, remove_currency, set_currency, clear_currency, check_wallet, \
    get_scoreboard
from fjormcord.bot.artping.util.message_util import MESSAGE_ONE_NAME_ONLY
from tests.fakes import FakeClient, make_message


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


def test_currency_commands_reject_spaces_in_names(client):
    add_currency(client, make_message("~addcurrency Fire"))
    set_currency(client, make_message("~setcurrency Fire 10"))

    assert add_currency(client, make_message("~addcurrency Fire Orbs")) == MESSAGE_ONE_NAME_ONLY
    assert set_currency(client, make_message("~setcurrency Fire Orbs 50")) == MESSAGE_ONE_NAME_ONLY
    assert clear_currency(client, make_message("~clearcurrency Fire Orbs")) == MESSAGE_ONE_NAME_ONLY
    assert asyncio.run(get_scoreboard(client, make_message("~scoreboard Fire Orbs"))) == MESSAGE_ONE_NAME_ONLY
    assert remove_currency(client, make_message("~removecurrency Fire Orbs")) == MESSAGE_ONE_NAME_ONLY
    assert check_wallet(client, make_message("~checkwallet")) == "User user1's wallet:\nFire: 10\n"


def scoreboard_of_25_users():
    # User n has n * 10 Orbs, so User25 ranks first
    client = FakeClient({user_id: f"User{user_id}" for user_id in range(1, 26)})
    add_currency(client, make_message("~addcurrency Orbs"))
    for user_id in range(1, 26):
        set_currency(client, make_message(f"~setcurrency orbs {user_id * 10}", user_id=user_id))
    return client


def test_scoreboard_shows_first_page_of_ten(client):
    client = scoreboard_of_25_users()

    out = asyncio.run(get_scoreboard(client, make_message("~scoreboard orbs")))

    assert out == "Scoreboard for Orbs (page 1/3):\n" \
        + "".join(f"{rank}. User{26 - rank} ({(26 - rank) * 10})\n" for rank in range(1, 11)) \
        + "Use ~scoreboard Orbs 2 for the next page"
    assert len(client.fetched) == 10


def test_scoreboard_last_page_continues_ranking(client):
    client = scoreboard_of_25_users()

    out = asyncio.run(get_scoreboard(client, make_message("~scoreboard orbs 3")))

    assert out == "Scoreboard for Orbs (page 3/3):\n" \
        + "".join(f"{rank}. User{26 - rank} ({(26 - rank) * 10})\n" for rank in range(21, 26))
    assert len(client.fetched) == 5


def test_scoreboard_rejects_page_out_of_range(client):
    client = scoreboard_of_25_users()

    assert asyncio.run(get_scoreboard(client, make_message("~scoreboard orbs 4"))) == \
        "Page 4 doesn't exist. The scoreboard for Orbs has 3 pages"
    assert asyncio.run(get_scoreboard(client, make_message("~scoreboard orbs 0"))) == \
        "Page 0 doesn't exist. The scoreboard for Orbs has 3 pages"


def test_scoreboard_without_entries(client):
    add_currency(client, make_message("~addcurrency Orbs"))

    assert asyncio.run(get_scoreboard(client, make_message("~scoreboard orbs"))) == \
        "Nobody has set their Orbs yet"


def test_scoreboard_rejects_more_than_name_and_page(client):
    add_currency(client, make_message("~addcurrency Orbs"))

    assert asyncio.run(get_scoreboard(client, make_message("~scoreboard orbs 1 2"))) == MESSAGE_ONE_NAME_ONLY


def test_scoreboard_page_must_be_a_number(client):
    add_currency(client, make_message("~addcurrency Orbs"))

    for page in ("--1", "²", "two"):
        assert asyncio.run(get_scoreboard(client, make_message(f"~scoreboard orbs {page}"))) == MESSAGE_ONE_NAME_ONLY
