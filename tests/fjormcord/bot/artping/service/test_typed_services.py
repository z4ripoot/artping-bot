import asyncio

import pytest

from fjormcord.bot.artping.model.character_vote import VoteChannel
from fjormcord.bot.artping.repository.character_repository import add_character
from fjormcord.bot.artping.service import character_vote_service
from fjormcord.bot.artping.service.alias_service import add_alias
from fjormcord.bot.artping.service.art_ping_service import add_ping, do_art_ping
from fjormcord.bot.artping.util.message_util import CommandError


def test_add_ping_takes_user_and_name():
    add_character("Lucina")

    assert add_ping("5", "lucina") == "Ping for Lucina has been added"


def test_do_art_ping_takes_names():
    add_character("Lucina")

    with pytest.raises(CommandError) as error:
        do_art_ping(["Nobody"])
    assert str(error.value).startswith("No character entry for Nobody")
    assert do_art_ping(["Lucina", "Nobody"]).startswith("No character entry for Nobody")


def test_add_alias_normalizes():
    add_character("Lucina")

    assert add_alias("lucina", "marth_mask") == "Alias Marth_Mask has been added to Lucina"


def test_start_vote_refuses_outside_a_server():
    async def send(content, view):
        raise AssertionError("nothing should be sent")

    vote_channel = VoteChannel("1", False, send)

    with pytest.raises(CommandError, match="Votes can only be started in a server"):
        asyncio.run(character_vote_service.start_vote(vote_channel, "1", "Lucina"))
