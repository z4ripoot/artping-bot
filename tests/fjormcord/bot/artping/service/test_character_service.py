import asyncio

from fjormcord.bot.artping.repository.art_ping_repository import add_ping
from fjormcord.bot.artping.repository.character_repository import get_character_row
from fjormcord.bot.artping.service.character_service import add_character, remove_character, check_character
from tests.fakes import make_message


def test_add_character_rejects_duplicates_case_insensitively(client):
    assert add_character(client, make_message("~addcharacter Lucina")) == "Lucina has been added"
    assert add_character(client, make_message("~addcharacter lucina")) == \
        "Failed to add character lucina. Character lucina already exists"


def test_remove_character_cascades_to_pings(client, database):
    add_character(client, make_message("~addcharacter Lucina"))
    add_ping(get_character_row("Lucina")['CHARACTER_ID'], "1")

    assert remove_character(client, make_message("~removecharacter lucina")) == "Lucina has been removed"
    assert database.execute("SELECT COUNT(*) FROM PINGS").fetchone()[0] == 0


def test_check_character_lists_usernames_and_survives_unknown_users(client):
    add_character(client, make_message("~addcharacter Lucina"))
    character_id = get_character_row("Lucina")['CHARACTER_ID']
    add_ping(character_id, "1")
    add_ping(character_id, "99")

    out = asyncio.run(check_character(client, make_message("~checkcharacter lucina")))

    assert out == "Character entry found for Lucina\nUsers: Alice, Unknown user (99)"
