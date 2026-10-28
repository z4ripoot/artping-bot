import asyncio

import pytest

from fjormcord.bot.artping.exception.command_error import CommandError
from fjormcord.bot.artping.model.character_vote import VoteChannel
from fjormcord.bot.artping.repository.character_repository import add_character
from fjormcord.bot.artping.service import character_vote_service
from fjormcord.bot.artping.service.alias_service import add_alias
from fjormcord.bot.artping.service.art_ping_service import add_ping, do_art_ping
from fjormcord.bot.artping.service.currency_service import add_currency, check_wallet, get_scoreboard, set_currency
from fjormcord.bot.artping.service.resource_service import list_resources, post_resource, set_resource
from fjormcord.bot.artping.view.layout import to_view
from fjormcord.bot.artping.view.scoreboard_view import CurrencySelect
from tests.fakes import FakeClient, button_labels, select_options


def test_add_ping_takes_user_and_name():
    add_character("Lucina")

    assert add_ping("5", "lucina") == "Ping for Lucina has been added"


def test_do_art_ping_takes_names():
    add_character("Lucina")

    with pytest.raises(CommandError) as error:
        do_art_ping(["Nobody"], administrator=False)
    assert str(error.value) == "No character entry for Nobody"
    assert error.value.layout.texts == (
        "No character entry for Nobody",
        "Use ~addcharacter Nobody to start a vote to add it",
    )
    assert (
        do_art_ping(["Lucina", "Nobody"], administrator=False)
        .texts[0]
        .startswith("### Lucina\nNo character entry for Nobody")
    )


def test_art_ping_names_the_slash_commands():
    add_character("Lucina")

    assert do_art_ping(["Lucina", "Nobody"], administrator=False, slash=True).texts[1] == (
        "Want to be pinged for Lucina? Use /addping Lucina\nUse /addcharacter Nobody to start a vote to add it"
    )


def test_add_alias_normalizes():
    add_character("Lucina")

    assert add_alias("lucina", "marth_mask") == "Alias Marth_Mask has been added to Lucina"


def test_start_vote_refuses_outside_a_server():
    async def send(content, view):
        raise AssertionError("nothing should be sent")

    vote_channel = VoteChannel("1", False, send)

    with pytest.raises(CommandError, match="Votes can only be started in a server"):
        asyncio.run(character_vote_service.start_vote(vote_channel, "1", "Lucina"))


def test_check_wallet_names_the_slash_command():
    assert check_wallet("5", "user5", slash=True) == "Your wallet is empty. Use /setcurrency to add a currency"


def test_scoreboard_of_several_pages_has_buttons_to_turn_them():
    add_currency("Orbs")
    for user_id in range(1, 12):
        set_currency(str(user_id), "Orbs", user_id)

    out = asyncio.run(get_scoreboard(FakeClient({n: f"user{n}" for n in range(1, 12)}), "Orbs"))

    assert out.texts == (
        "### Scoreboard for Orbs (page 1/2)",
        "\n".join(f"{rank}. user{12 - rank} ({12 - rank})" for rank in range(1, 11)),
    )
    assert button_labels(to_view(out)) == ["◀ Previous", "Next ▶"]
    # One currency: nothing to switch to
    assert all(not isinstance(item, CurrencySelect) for item in to_view(out).walk_children())


def test_scoreboard_offers_the_other_currencies():
    add_currency("Orbs")
    add_currency("Gems")
    set_currency("1", "Orbs", 5)

    assert select_options(to_view(asyncio.run(get_scoreboard(FakeClient(), "Orbs")))) == ["Gems", "Orbs"]


def test_empty_scoreboard_keeps_its_header_and_dropdown():
    add_currency("Orbs")
    add_currency("Gems")

    out = asyncio.run(get_scoreboard(FakeClient(), "Orbs"))

    assert out.texts == ("### Scoreboard for Orbs", "Nobody has set their Orbs yet")
    assert select_options(to_view(out)) == ["Gems", "Orbs"]


def test_scoreboard_of_one_page_has_no_buttons():
    add_currency("Orbs")
    set_currency("1", "Orbs", 5)

    out = asyncio.run(get_scoreboard(FakeClient({1: "Alice"}), "Orbs"))

    assert out.texts == ("### Scoreboard for Orbs", "1. Alice (5)")
    assert out.rows == ()


def test_set_currency_takes_an_int():
    add_currency("Orbs")

    assert set_currency("5", "Orbs", 3) == "Your Orbs has been set to 3"


def test_list_resources_in_slash_syntax():
    asyncio.run(set_resource(FakeClient(), "hof", "https://example.com/hof"))
    asyncio.run(set_resource(FakeClient(), "faq", "https://example.com/faq"))

    assert list_resources(slash=True) == "Resources: faq, hof (post one with /resource)"


def test_post_resource_refuses_unknown():
    with pytest.raises(CommandError, match="Resource hof doesn't exist"):
        post_resource("hof")


def test_set_resource_takes_name_and_link():
    assert asyncio.run(set_resource(FakeClient(), "hof", "https://example.com/hof")) == "Resource hof has been set"
