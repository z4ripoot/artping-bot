from fjormcord.bot.artping.repository.character_repository import add_character, get_character
from fjormcord.bot.artping.service.alias_service import add_alias, remove_alias, set_primary_name
from fjormcord.bot.artping.util.message_util import MESSAGE_ONE_NAME_ONLY
from tests.fakes import make_message, reply


def test_add_alias_makes_the_alias_find_the_character(client):
    add_character("Furina")

    assert reply(add_alias, client, make_message("~addalias furina Focalors")) == \
        "Alias Focalors has been added to Furina"
    assert get_character("focalors") == get_character("Furina")


def test_add_alias_for_unknown_character(client):
    assert reply(add_alias, client, make_message("~addalias Furina Focalors")) == "Character Furina doesn't exist"


def test_add_alias_rejects_an_existing_alias_of_any_character(client):
    add_character("Furina")
    add_character("Neuvillette")
    add_alias(client, make_message("~addalias Furina Focalors"))

    assert reply(add_alias, client, make_message("~addalias Neuvillette FOCALORS")) == \
        "FOCALORS is already an alias of Furina"
    assert reply(add_alias, client, make_message("~addalias Furina focalors")) == \
        "focalors is already an alias of Furina"


def test_add_alias_rejects_a_character_name(client):
    add_character("Furina")
    add_character("Neuvillette")

    assert reply(add_alias, client, make_message("~addalias Furina neuvillette")) == \
        "Character Neuvillette already exists"
    assert reply(add_alias, client, make_message("~addalias Furina Furina")) == "Character Furina already exists"


def test_add_alias_checks_its_arguments(client):
    add_character("Furina")

    assert reply(add_alias, client, make_message("~addalias Furina Focalors Archon")) == MESSAGE_ONE_NAME_ONLY
    assert get_character("Focalors") is None


def test_remove_alias(client):
    add_character("Furina")
    add_alias(client, make_message("~addalias Furina Focalors"))

    assert reply(remove_alias, client, make_message("~removealias furina focalors")) == \
        "Alias focalors has been removed from Furina"
    assert get_character("Focalors") is None


def test_remove_alias_of_another_character(client):
    add_character("Furina")
    add_character("Neuvillette")
    add_alias(client, make_message("~addalias Furina Focalors"))

    assert reply(remove_alias, client, make_message("~removealias Neuvillette Focalors")) == \
        "Focalors is not an alias of Neuvillette"
    assert get_character("Focalors") is not None


def test_remove_alias_rejects_the_character_name(client):
    add_character("Furina")

    assert reply(remove_alias, client, make_message("~removealias Furina Furina")) == \
        "Furina is not an alias of Furina"
    assert get_character("Furina") is not None


def test_set_primary_name_swaps_the_alias_and_the_name(client):
    add_character("Furina")
    character_id = get_character("Furina").id
    add_alias(client, make_message("~addalias Furina Focalors"))

    assert reply(set_primary_name, client, make_message("~setprimaryname focalors")) == \
        "Focalors is now the primary name; Furina has become an alias"
    assert get_character("Focalors").name == "Focalors"
    assert get_character("Furina").name == "Focalors"
    assert get_character("Focalors").id == character_id


def test_set_primary_name_rejects_the_current_name(client):
    add_character("Furina")

    assert reply(set_primary_name, client, make_message("~setprimaryname furina")) == \
        "Furina is already the primary name"


def test_set_primary_name_rejects_unknown_names(client):
    assert reply(set_primary_name, client, make_message("~setprimaryname Focalors")) == \
        "Character Focalors doesn't exist"
