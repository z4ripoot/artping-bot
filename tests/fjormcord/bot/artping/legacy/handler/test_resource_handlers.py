import pytest

from fjormcord.bot.artping.exception.missing_argument import MissingArgument
from fjormcord.bot.artping.legacy.handler.resource_handlers import list_resources, remove_resource, set_resource
from fjormcord.bot.artping.model.resource import Resource
from fjormcord.bot.artping.repository.resource_repository import get_resource, get_resource_names
from fjormcord.bot.artping.service.resource_service import get_resource_content
from fjormcord.bot.artping.util.message_util import MESSAGE_ONE_NAME_ONLY
from tests.fakes import FakeChannel, FakeClient, make_message, reply

WEBSITE = "https://feheroes.fandom.com/wiki/Hall_of_Forms"


@pytest.fixture
def channel():
    return FakeChannel(channel_id=20)


@pytest.fixture
def client(channel):
    return FakeClient(channels=[channel])


def link_to(message, channel_id=20):
    return f"https://discord.com/channels/1/{channel_id}/{message.id}"


def set_from(client, name, link):
    return reply(set_resource, client, make_message(f"~setresource {name} {link}", administrator=True))


def test_message_link_stores_the_message_text(client, channel):
    original = channel.post("Hall of Forms rotation:\n<@5> made a guide")
    link = link_to(original)

    assert set_from(client, "hof", link) == "Resource hof has been set"
    assert get_resource("hof") == Resource("hof", "Hall of Forms rotation:\n<@5> made a guide", link)


def test_later_edits_of_the_message_are_not_followed(client, channel):
    original = channel.post("Old text")
    set_from(client, "hof", link_to(original))
    original.content = "New text"

    assert get_resource_content("hof") == "Old text"


@pytest.mark.parametrize("host", ["discord.com", "ptb.discord.com", "canary.discord.com", "discordapp.com"])
def test_message_links_of_every_discord_host_are_read(client, channel, host):
    original = channel.post("Text")

    set_from(client, "hof", f"https://{host}/channels/1/20/{original.id}")

    assert get_resource_content("hof") == "Text"


def test_website_link_is_stored_as_the_content(client):
    assert set_from(client, "hof", WEBSITE) == "Resource hof has been set"
    assert get_resource("hof") == Resource("hof", WEBSITE, WEBSITE)


def test_link_without_embed_brackets_is_stored(client):
    set_from(client, "hof", f"<{WEBSITE}>")

    assert get_resource_content("hof") == WEBSITE


def test_setting_an_existing_name_replaces_it(client):
    set_from(client, "hof", WEBSITE)

    set_from(client, "HoF", "https://example.com")

    assert get_resource("hof") == Resource("HoF", "https://example.com", "https://example.com")
    assert get_resource_names() == ["HoF"]


def test_leading_tilde_of_the_name_is_dropped(client):
    set_from(client, "~hof", WEBSITE)

    assert get_resource_names() == ["hof"]


@pytest.mark.parametrize("name", ["help", "ArtPing", "~setresource", "resources"])
def test_name_of_a_command_is_refused(client, name):
    command = "~" + name.removeprefix("~").lower()

    assert set_from(client, name, WEBSITE) == f"{command} is a command, so it can't be a resource"
    assert get_resource_names() == []


@pytest.mark.parametrize("name", ["~", "h@f", "<@5>", "hôf"])
def test_invalid_name_is_refused(client, name):
    assert set_from(client, name, WEBSITE) == "Resource names can only contain letters, digits, _ and -"


@pytest.mark.parametrize("link", ["hof.com", "ftp://example.com", "https://"])
def test_text_that_is_not_a_link_is_refused(client, link):
    assert set_from(client, "hof", link) == "That isn't a link to a Discord message or a website"


def test_message_that_cannot_be_read_is_refused(client, channel):
    original = channel.post("Text")
    channel.forbidden = True
    unreadable = "Couldn't read that message. Check the link, and that the bot can read that channel"

    assert set_from(client, "hof", link_to(original)) == unreadable
    assert set_from(client, "hof", link_to(original, channel_id=99)) == unreadable
    assert get_resource_names() == []


def test_message_without_text_is_refused(client, channel):
    image_only = channel.post("")

    assert set_from(client, "hof", link_to(image_only)) == "That message has no text"


def test_missing_link_and_extra_words_are_refused(client):
    with pytest.raises(MissingArgument, match="link is missing"):
        reply(set_resource, client, make_message("~setresource hof", administrator=True))
    assert set_from(client, "hof", f"{WEBSITE} extra") == MESSAGE_ONE_NAME_ONLY


def test_remove_resource(client):
    set_from(client, "hof", WEBSITE)

    assert (
        reply(remove_resource, client, make_message("~removeresource HOF", administrator=True))
        == "Resource hof has been removed"
    )
    assert get_resource_names() == []


def test_remove_unknown_resource(client):
    assert (
        reply(remove_resource, client, make_message("~removeresource hof", administrator=True))
        == "Resource hof doesn't exist"
    )


def test_list_resources_alphabetically(client):
    set_from(client, "hof", WEBSITE)
    set_from(client, "FAQ", WEBSITE)

    assert reply(list_resources, client, make_message("~resources")).texts == ("### Resources", "~FAQ\n~hof")


def test_list_without_resources(client):
    assert reply(list_resources, client, make_message("~resources")) == "No resources have been set yet"


def test_content_is_found_ignoring_case_and_unknown_names_are_none(client):
    set_from(client, "hof", WEBSITE)

    assert get_resource_content("HOF") == WEBSITE
    assert get_resource_content("faq") is None
