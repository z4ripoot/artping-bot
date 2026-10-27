from fjormcord.bot.artping.legacy.handler.character_handlers import add_character, check_character, remove_character
from fjormcord.bot.artping.repository.art_ping_repository import add_ping
from fjormcord.bot.artping.repository.character_repository import get_character
from fjormcord.bot.artping.util.message_util import MESSAGE_ONE_NAME_ONLY
from tests.fakes import make_message, reply


def test_add_character_rejects_duplicates_case_insensitively(client):
    assert (
        reply(add_character, client, make_message("~addcharacter Lucina", administrator=True))
        == "Character Lucina has been added"
    )
    assert (
        reply(add_character, client, make_message("~addcharacter lucina", administrator=True))
        == "Character Lucina already exists"
    )


def test_remove_character_cascades_to_pings(client, database):
    reply(add_character, client, make_message("~addcharacter Lucina", administrator=True))
    add_ping(get_character("Lucina").id, "1")

    assert (
        reply(remove_character, client, make_message("~removecharacter lucina")) == "Character Lucina has been removed"
    )
    assert database.execute("SELECT COUNT(*) FROM PINGS").fetchone()[0] == 0


def test_check_character_lists_usernames_and_survives_unknown_users(client):
    reply(add_character, client, make_message("~addcharacter Lucina", administrator=True))
    character_id = get_character("Lucina").id
    add_ping(character_id, "1")
    add_ping(character_id, "99")

    out = reply(check_character, client, make_message("~checkcharacter lucina"))

    assert out == "Character entry found for Lucina\nUsers: Alice, Unknown user (99)"


def test_add_character_rejects_an_alias(client, database):
    reply(add_character, client, make_message("~addcharacter Furina", administrator=True))
    database.execute("INSERT INTO ALIAS (CHARACTER_ID, ALIAS) VALUES (?, 'Focalors')", (get_character("Furina").id,))

    assert (
        reply(add_character, client, make_message("~addcharacter focalors", administrator=True))
        == "Focalors is already an alias of Furina"
    )


def test_add_character_normalizes_the_name(client):
    assert (
        reply(add_character, client, make_message("~addcharacter m!ROBIN", administrator=True))
        == "Character M!Robin has been added"
    )
    assert get_character("m!robin").name == "M!Robin"


def test_unknown_character_is_named_normalized(client):
    assert (
        reply(check_character, client, make_message("~checkcharacter black_knight"))
        == "Character Black_Knight doesn't exist"
    )


def test_remove_character_by_alias_cascades_to_aliases(client, database):
    reply(add_character, client, make_message("~addcharacter Furina", administrator=True))
    database.execute("INSERT INTO ALIAS (CHARACTER_ID, ALIAS) VALUES (?, 'Focalors')", (get_character("Furina").id,))

    assert (
        reply(remove_character, client, make_message("~removecharacter Focalors"))
        == "Character Furina has been removed"
    )
    assert database.execute("SELECT COUNT(*) FROM ALIAS").fetchone()[0] == 0


def test_check_character_lists_aliases(client, database):
    reply(add_character, client, make_message("~addcharacter Furina", administrator=True))
    character_id = get_character("Furina").id
    database.execute("INSERT INTO ALIAS (CHARACTER_ID, ALIAS) VALUES (?, 'Focalors')", (character_id,))
    database.execute("INSERT INTO ALIAS (CHARACTER_ID, ALIAS) VALUES (?, 'Archon')", (character_id,))
    add_ping(character_id, "1")

    out = reply(check_character, client, make_message("~checkcharacter focalors"))

    assert out == "Character entry found for Furina\nAliases: Archon, Focalors\nUsers: Alice"


def test_add_character_rejects_spaces_with_underscore_hint(client):
    assert (
        reply(add_character, client, make_message("~addcharacter Black Knight", administrator=True))
        == MESSAGE_ONE_NAME_ONLY
    )
    assert get_character("Black") is None


def test_remove_and_check_character_reject_spaces(client):
    reply(add_character, client, make_message("~addcharacter Black", administrator=True))

    assert reply(remove_character, client, make_message("~removecharacter Black Knight")) == MESSAGE_ONE_NAME_ONLY
    assert reply(check_character, client, make_message("~checkcharacter Black Knight")) == MESSAGE_ONE_NAME_ONLY
    assert get_character("Black") is not None


def test_check_unknown_character(client):
    assert reply(check_character, client, make_message("~checkcharacter Marth")) == "Character Marth doesn't exist"
