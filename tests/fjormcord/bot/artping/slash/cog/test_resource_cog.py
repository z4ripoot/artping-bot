import pytest

from fjormcord.bot.artping.model.resource import Resource
from fjormcord.bot.artping.repository import resource_repository
from fjormcord.bot.artping.slash.cog.resource_cog import ResourceCog
from tests.fakes import FakeInteraction, invoke


@pytest.fixture
def cog():
    return ResourceCog()


def test_resource_is_posted_without_mentions(cog):
    resource_repository.set_resource(Resource("hof", "Hello <@5>", "https://example.com"))
    interaction = FakeInteraction()

    invoke(cog.resource, interaction, cog, name="hof")

    content, ephemeral, allowed_mentions = interaction.sent[0]
    assert (content, ephemeral) == ("Hello <@5>", False)
    assert not (
        allowed_mentions.everyone or allowed_mentions.users or allowed_mentions.roles or allowed_mentions.replied_user
    )


def test_unknown_resource_is_refused(cog):
    interaction = FakeInteraction()

    invoke(cog.resource, interaction, cog, name="hof")

    assert interaction.sent[0].content == "Resource hof doesn't exist"
    assert interaction.sent[0].ephemeral is True


def test_long_resource_is_split(cog):
    resource_repository.set_resource(Resource("hof", "word " * 1000, "https://example.com"))
    interaction = FakeInteraction()

    invoke(cog.resource, interaction, cog, name="hof")

    assert len(interaction.sent) > 1
    assert all(len(content) <= 2000 for content, _, _ in interaction.sent)


def test_resource_name_with_space_is_refused(cog):
    interaction = FakeInteraction(administrator=True)

    invoke(cog.set_resource, interaction, cog, name="hall of fame", link="https://example.com")

    assert interaction.sent[0].content == "Resource names can only contain letters, digits, _ and -"
    assert interaction.sent[0].ephemeral is True


def test_set_list_and_remove_resource(cog):
    added, listed, removed = FakeInteraction(administrator=True), FakeInteraction(), FakeInteraction(administrator=True)

    invoke(cog.set_resource, added, cog, name="hof", link="https://example.com")
    invoke(cog.resources, listed, cog)
    invoke(cog.remove_resource, removed, cog, name="HOF")

    assert added.response.deferred == [{}]
    assert added.sent[0].content == "Resource hof has been set"
    assert listed.sent[0].content == "### Resources\nhof\nPost one with /resource"
    assert removed.sent[0].content == "Resource hof has been removed"
