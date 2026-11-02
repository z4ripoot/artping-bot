import asyncio

from fjormcord.bot.artping.legacy.dispatch import handle_message
from fjormcord.bot.artping.legacy.handler.art_ping_handlers import add_ping, check_ping, do_art_ping, remove_ping
from fjormcord.bot.artping.repository import alias_repository
from fjormcord.bot.artping.repository.art_ping_repository import add_ping as insert_ping
from fjormcord.bot.artping.repository.character_repository import add_character, get_character
from fjormcord.bot.artping.util.message_util import MESSAGE_ONE_NAME_ONLY
from tests.fakes import make_message, reply, use_settings


def subscribe(character_name, user_id):
    insert_ping(get_character(character_name).id, str(user_id))


def test_art_ping_mentions_subscribers_case_insensitively(client):
    add_character("Lucina")
    subscribe("Lucina", 1)
    subscribe("Lucina", 2)

    assert reply(do_art_ping, client, make_message("~artping lucina")).texts == (
        "### Lucina\n<@1> <@2>",
        "Want to be pinged for Lucina? Use ~addping Lucina",
    )


def test_art_ping_of_several_characters_reminds_of_the_first(client):
    for name in ("Lucina", "Chrom"):
        add_character(name)
    subscribe("Lucina", 1)
    subscribe("Chrom", 2)

    assert reply(do_art_ping, client, make_message("~artping lucina chrom")).texts == (
        "### Chrom, Lucina\n<@1> <@2>",
        "Want to be pinged for Chrom? Use ~addping Chrom",
    )


def test_art_ping_reports_missing_characters_in_same_reply(client):
    add_character("Lucina")
    subscribe("Lucina", 1)

    out = reply(do_art_ping, client, make_message("~artping Lucina Marth"))

    assert out.texts == (
        "### Lucina\nNo character entry for Marth\n<@1>",
        "Want to be pinged for Lucina? Use ~addping Lucina\nUse ~addcharacter Marth to start a vote to add it",
    )


def test_art_ping_hint_for_an_admin_adds_directly(client):
    add_character("Lucina")

    out = reply(do_art_ping, client, make_message("~artping Lucina Marth", administrator=True))

    assert out.texts[1] == "Want to be pinged for Lucina? Use ~addping Lucina\nUse ~addcharacter Marth to add it"


def test_art_ping_hint_adds_directly_when_voting_is_off(client, monkeypatch):
    use_settings(monkeypatch, character_votes_needed=1)
    add_character("Lucina")

    out = reply(do_art_ping, client, make_message("~artping Lucina Marth"))

    assert out.texts[1] == "Want to be pinged for Lucina? Use ~addping Lucina\nUse ~addcharacter Marth to add it"


def test_art_ping_with_only_unknown_characters(client):
    assert reply(do_art_ping, client, make_message("~artping Marth")).texts == (
        "No character entry for Marth",
        "Use ~addcharacter Marth to start a vote to add it",
    )


def test_art_ping_with_only_unknown_characters_starts_no_cooldown(client):
    message = make_message("~artping Marth")

    asyncio.run(handle_message(client, message))

    assert message.channel.sent == ["No character entry for Marth\nUse ~addcharacter Marth to start a vote to add it"]
    assert client.cooldowns.remaining(1) == 0


def test_art_ping_with_many_subscribers_is_split(client):
    add_character("Lucina")
    user_ids = [10**17 + number for number in range(300)]
    for user_id in user_ids:
        subscribe("Lucina", user_id)
    message = make_message("~artping Lucina")

    asyncio.run(handle_message(client, message))

    sent = message.channel.sent
    assert len(sent) > 1
    assert sent[0].startswith("### Lucina\n<@")
    assert sent[-1].endswith("\nWant to be pinged for Lucina? Use ~addping Lucina")
    mentioned = " ".join(sent).split()
    assert all(mentioned.count(f"<@{user_id}>") == 1 for user_id in user_ids)
    # The client's allowed mentions, which let the users be pinged
    assert message.channel.sent_allowed_mentions == [None] * len(sent)


def test_art_ping_without_subscribers(client):
    add_character("Lucina")

    assert reply(do_art_ping, client, make_message("~artping Lucina")).texts == (
        "### Lucina\nNobody is subscribed to Lucina",
        "Want to be pinged for Lucina? Use ~addping Lucina",
    )


def test_art_ping_ignores_repeated_spaces(client):
    add_character("Lucina")
    subscribe("Lucina", 1)

    assert reply(do_art_ping, client, make_message("~artping  Lucina ")).texts[0] == "### Lucina\n<@1>"


def test_add_and_remove_ping(client):
    add_character("Lucina")

    assert reply(add_ping, client, make_message("~addping lucina")) == "Ping for Lucina has been added"
    assert reply(add_ping, client, make_message("~addping lucina")) == "Ping for Lucina already exists"
    assert reply(check_ping, client, make_message("~checkping")).texts == ("### Alice's pings", "Lucina")
    assert reply(remove_ping, client, make_message("~removeping lucina")) == "Ping for Lucina has been removed"
    assert reply(remove_ping, client, make_message("~removeping lucina")) == "Ping for Lucina doesn't exist"


def test_add_ping_for_unknown_character(client):
    assert reply(add_ping, client, make_message("~addping Marth")) == "Character Marth doesn't exist"


def test_check_ping_lists_the_characters_one_per_line(client):
    for name in ("Marth", "Chrom", "Lucina"):
        add_character(name)
        subscribe(name, 1)

    out = reply(check_ping, client, make_message("~checkping"))

    assert out.texts == ("### Alice's pings", "Chrom\nLucina\nMarth")
    assert out.rows == ()


def test_check_ping_of_many_characters_has_pages(client):
    for number in range(1, 13):
        add_character(f"Hero{number:02d}")
        subscribe(f"Hero{number:02d}", 1)

    out = reply(check_ping, client, make_message("~checkping"))

    assert out.texts == ("### Alice's pings (page 1/2)", "\n".join(f"Hero{number:02d}" for number in range(1, 11)))
    [buttons] = out.rows
    assert [button.custom_id for button in buttons] == ["page:pings:1:0", "page:pings:1:2"]


def test_check_ping_without_pings_is_not_empty(client):
    assert reply(check_ping, client, make_message("~checkping")) == "You are not subscribed to any characters"


def test_add_and_remove_ping_hint_at_underscores_for_several_words(client):
    assert reply(add_ping, client, make_message("~addping Black Knight")) == MESSAGE_ONE_NAME_ONLY
    assert reply(remove_ping, client, make_message("~removeping Black Knight")) == MESSAGE_ONE_NAME_ONLY


def test_art_ping_by_alias_uses_the_character_name(client):
    add_character("Furina")
    alias_repository.add_alias(get_character("Furina").id, "Focalors")
    subscribe("Furina", 1)

    assert reply(do_art_ping, client, make_message("~artping focalors")).texts == (
        "### Furina\n<@1>",
        "Want to be pinged for Furina? Use ~addping Furina",
    )


def test_art_ping_by_name_and_alias_pings_once(client):
    add_character("Furina")
    alias_repository.add_alias(get_character("Furina").id, "Focalors")
    subscribe("Furina", 1)

    assert reply(do_art_ping, client, make_message("~artping Furina Focalors")).texts[0] == "### Furina\n<@1>"


def test_add_ping_by_alias(client):
    add_character("Furina")
    alias_repository.add_alias(get_character("Furina").id, "Focalors")

    assert reply(add_ping, client, make_message("~addping Focalors")) == "Ping for Furina has been added"
    assert reply(remove_ping, client, make_message("~removeping Furina")) == "Ping for Furina has been removed"


def test_art_ping_lists_characters_alphabetically(client):
    add_character("Marth")
    add_character("lucina")
    add_character("Chrom")
    subscribe("Marth", 1)

    out = reply(do_art_ping, client, make_message("~artping Marth lucina Chrom"))

    assert out.texts[0] == "### Chrom, lucina, Marth\n<@1>"


def test_art_ping_names_unknown_characters_normalized(client):
    add_character("Lucina")
    subscribe("Lucina", 1)

    out = reply(do_art_ping, client, make_message("~artping lucina marth"))

    assert out.texts[0] == "### Lucina\nNo character entry for Marth\n<@1>"
