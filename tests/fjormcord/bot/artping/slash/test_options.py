import asyncio

import pytest

from fjormcord.bot.artping.exception.command_error import CommandError
from fjormcord.bot.artping.model.resource import Resource
from fjormcord.bot.artping.repository import (
    alias_repository,
    art_ping_repository,
    character_repository,
    currency_repository,
    resource_repository,
)
from fjormcord.bot.artping.slash.options import (
    character_choices,
    currency_choices,
    resource_choices,
    subscribed_character_choices,
    to_name,
)
from tests.fakes import FakeInteraction


def names(choices):
    return [choice.name for choice in choices]


def test_to_name_turns_spaces_into_underscores():
    assert to_name("  black   knight ") == "black_knight"


def test_to_name_refuses_blank():
    with pytest.raises(CommandError, match="A name can't be empty"):
        to_name("   ")


def test_character_choices_match_prefix_and_aliases():
    character_repository.add_character("Marth")
    character_repository.add_character("Lucina")
    marth = character_repository.get_character("Marth")
    alias_repository.add_alias(marth.id, "Marth_Mask")

    assert names(asyncio.run(character_choices(None, "mar"))) == ["Marth", "Marth_Mask"]
    assert names(asyncio.run(character_choices(None, "mask"))) == []
    assert names(asyncio.run(character_choices(None, "marth m"))) == ["Marth_Mask"]
    assert names(asyncio.run(character_choices(None, ""))) == ["Lucina", "Marth", "Marth_Mask"]


def test_subscribed_character_choices_are_the_users_subscriptions():
    for name in ["Marth", "Lucina", "Chrom"]:
        character_repository.add_character(name)
    marth = character_repository.get_character("Marth")
    lucina = character_repository.get_character("Lucina")
    chrom = character_repository.get_character("Chrom")
    alias_repository.add_alias(marth.id, "Marth_Mask")
    art_ping_repository.add_ping(marth.id, "1")
    art_ping_repository.add_ping(lucina.id, "1")
    art_ping_repository.add_ping(chrom.id, "2")
    interaction = FakeInteraction(user_id=1)

    assert names(asyncio.run(subscribed_character_choices(interaction, ""))) == ["Lucina", "Marth"]
    assert names(asyncio.run(subscribed_character_choices(interaction, "MA"))) == ["Marth"]
    assert names(asyncio.run(subscribed_character_choices(FakeInteraction(user_id=3), ""))) == []


def test_currency_choices_match_prefix():
    currency_repository.add_currency("Orbs")
    currency_repository.add_currency("Gems")

    assert names(asyncio.run(currency_choices(None, "O"))) == ["Orbs"]


def test_resource_choices_match_prefix():
    resource_repository.set_resource(Resource("hof", "text", "link"))

    assert names(asyncio.run(resource_choices(None, "HO"))) == ["hof"]


def test_choices_are_the_first_20_matches():
    character_repository.add_character("Lucina")
    for number in range(30):
        character_repository.add_character(f"Hero{number:02}")

    choices = asyncio.run(character_choices(None, "hero"))

    assert names(choices) == [f"Hero{number:02}" for number in range(20)]


def test_underscore_in_prefix_is_not_a_wildcard():
    character_repository.add_character("Black_Knight")
    character_repository.add_character("Blackx")

    assert names(asyncio.run(character_choices(None, "black_"))) == ["Black_Knight"]
