from fjormcord.bot.artping.repository.art_ping_repository import add_ping as insert_ping
from fjormcord.bot.artping.repository.character_repository import add_character, get_character_row
from fjormcord.bot.artping.service.art_ping_service import do_art_ping, add_ping, remove_ping, check_ping
from tests.fakes import make_message


def subscribe(character_name, user_id):
    insert_ping(get_character_row(character_name)['CHARACTER_ID'], str(user_id))


def test_art_ping_mentions_subscribers_case_insensitively(client):
    add_character("Lucina")
    subscribe("Lucina", 1)
    subscribe("Lucina", 2)

    assert do_art_ping(client, make_message("~artping lucina")) == "Lucina: <@1> <@2>"


def test_art_ping_reports_missing_characters_in_same_reply(client):
    add_character("Lucina")
    subscribe("Lucina", 1)

    out = do_art_ping(client, make_message("~artping Lucina Marth"))

    assert out == "No character entry for Marth\nLucina: <@1>"


def test_art_ping_with_only_unknown_characters(client):
    assert do_art_ping(client, make_message("~artping Marth")) == "No character entry for Marth"


def test_art_ping_without_subscribers(client):
    add_character("Lucina")

    assert do_art_ping(client, make_message("~artping Lucina")) == "Nobody is subscribed to Lucina"


def test_art_ping_ignores_repeated_spaces(client):
    add_character("Lucina")
    subscribe("Lucina", 1)

    assert do_art_ping(client, make_message("~artping  Lucina ")) == "Lucina: <@1>"


def test_add_and_remove_ping(client):
    add_character("Lucina")

    assert add_ping(client, make_message("~addping lucina")) == "A ping for Lucina has been added"
    assert add_ping(client, make_message("~addping lucina")) == "Ping for Lucina already exists"
    assert check_ping(client, make_message("~checkping")) == "Lucina"
    assert remove_ping(client, make_message("~removeping lucina")) == "Ping for Lucina has been removed"
    assert remove_ping(client, make_message("~removeping lucina")) == "Ping for Lucina doesn't exist"


def test_add_ping_for_unknown_character(client):
    assert add_ping(client, make_message("~addping Marth")) == "Character Marth doesn't exist"


def test_check_ping_without_pings_is_not_empty(client):
    assert check_ping(client, make_message("~checkping")) == "You are not subscribed to any characters"
