from fjormcord.bot.artping.repository.art_ping_repository import add_ping
from fjormcord.bot.artping.repository.character_repository import get_character
from fjormcord.bot.artping.service.character_service import add_character, remove_character, check_character
from fjormcord.bot.artping.util.message_util import MESSAGE_ONE_NAME_ONLY
from tests.fakes import make_message, reply


def test_add_character_rejects_duplicates_case_insensitively(client):
    assert reply(add_character, client, make_message("~addcharacter Lucina")) == "Character Lucina has been added"
    assert reply(add_character, client, make_message("~addcharacter lucina")) == \
        "Character Lucina already exists"


def test_remove_character_cascades_to_pings(client, database):
    add_character(client, make_message("~addcharacter Lucina"))
    add_ping(get_character("Lucina").id, "1")

    assert reply(remove_character, client, make_message("~removecharacter lucina")) == \
        "Character Lucina has been removed"
    assert database.execute("SELECT COUNT(*) FROM PINGS").fetchone()[0] == 0


def test_check_character_lists_usernames_and_survives_unknown_users(client):
    add_character(client, make_message("~addcharacter Lucina"))
    character_id = get_character("Lucina").id
    add_ping(character_id, "1")
    add_ping(character_id, "99")

    out = reply(check_character, client, make_message("~checkcharacter lucina"))

    assert out == "Character entry found for Lucina\nUsers: Alice, Unknown user (99)"


def test_add_character_rejects_spaces_with_underscore_hint(client):
    assert reply(add_character, client, make_message("~addcharacter Black Knight")) == MESSAGE_ONE_NAME_ONLY
    assert get_character("Black") is None


def test_remove_and_check_character_reject_spaces(client):
    add_character(client, make_message("~addcharacter Black"))

    assert reply(remove_character, client, make_message("~removecharacter Black Knight")) == MESSAGE_ONE_NAME_ONLY
    assert reply(check_character, client, make_message("~checkcharacter Black Knight")) == MESSAGE_ONE_NAME_ONLY
    assert get_character("Black") is not None


def test_check_unknown_character(client):
    assert reply(check_character, client, make_message("~checkcharacter Marth")) == \
        "Character Marth doesn't exist"
