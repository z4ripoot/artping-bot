import asyncio
import logging
from types import SimpleNamespace

import discord

from fjormcord.bot.artping.exception.command_error import CommandError
from fjormcord.bot.artping.slash.runner import admin_command, run
from fjormcord.bot.artping.util.message_util import ALLOWED_MENTIONS
from tests.fakes import FakeInteraction


def run_command(interaction, call, command_name="checkping", **options):
    # run takes the name from the app command being run; a stand-in, unless the test set a command
    if interaction.command is None:
        interaction.command = SimpleNamespace(name=command_name)
    asyncio.run(run(interaction, call, **options))


def replies(interaction):
    return [(content, ephemeral) for content, ephemeral, _ in interaction.sent]


def test_reply_is_public():
    interaction = FakeInteraction()

    run_command(interaction, lambda: "hi")

    assert interaction.sent == [("hi", False, ALLOWED_MENTIONS)]


def test_async_call_is_awaited():
    interaction = FakeInteraction()

    async def call():
        return "later"

    run_command(interaction, call)

    assert interaction.sent == [("later", False, ALLOWED_MENTIONS)]


def test_command_error_is_ephemeral():
    interaction = FakeInteraction()

    def call():
        raise CommandError("Nope")

    run_command(interaction, call)

    assert replies(interaction) == [("Nope", True)]


def test_unexpected_error_is_logged_and_ephemeral(caplog):
    interaction = FakeInteraction()

    def call():
        raise ValueError("boom")

    with caplog.at_level(logging.ERROR):
        run_command(interaction, call)

    assert replies(interaction) == [("Something went wrong while running /checkping", True)]
    assert "boom" in caplog.text


@admin_command(name="removecurrency", description="An admin command")
async def admin_only(interaction: discord.Interaction):
    pass


def test_admin_command_is_hidden_from_non_admins_and_dms():
    assert admin_only.default_permissions.administrator
    assert admin_only.guild_only


def test_admin_command_refuses_non_admin():
    interaction = FakeInteraction()
    interaction.command = admin_only
    calls = []

    run_command(interaction, lambda: calls.append(1) or "done")

    assert replies(interaction) == [("This command is for admins only", True)]
    assert calls == []


def test_admin_command_allows_admin():
    interaction = FakeInteraction(administrator=True)
    interaction.command = admin_only

    run_command(interaction, lambda: "done")

    assert interaction.sent == [("done", False, ALLOWED_MENTIONS)]


def test_cooldown_turns_down_and_is_shared_with_legacy():
    interaction = FakeInteraction()
    # As a ~ command of the same user does
    interaction.client.cooldowns.start(interaction.user.id)
    calls = []

    run_command(interaction, lambda: calls.append(1) or "pinged", "artping")

    assert replies(interaction) == [("You used a command recently. Try again in 1 second", True)]
    assert calls == []


def test_success_starts_cooldown_for_every_command():
    interaction = FakeInteraction()
    run_command(interaction, lambda: "pinged", "artping")

    run_command(interaction, lambda: "subscribed", "checkping")

    assert replies(interaction) == [("pinged", False), ("You used a command recently. Try again in 1 second", True)]


def test_failure_does_not_start_cooldown():
    interaction = FakeInteraction()

    def call():
        raise CommandError("Nope")

    run_command(interaction, call, "artping")
    run_command(interaction, lambda: "pinged", "artping")

    assert interaction.sent[-1] == ("pinged", False, ALLOWED_MENTIONS)


def test_admins_skip_cooldown():
    interaction = FakeInteraction(administrator=True)

    run_command(interaction, lambda: "one", "artping")
    run_command(interaction, lambda: "two", "checkping")

    assert [content for content, _, _ in interaction.sent] == ["one", "two"]


def test_long_reply_is_split():
    interaction = FakeInteraction()
    text = "\n".join("x" * 99 for _ in range(45))

    run_command(interaction, lambda: text)

    assert len(interaction.sent) == 3
    assert all(len(content) <= 2000 for content, _, _ in interaction.sent)
    assert "\n".join(content for content, _, _ in interaction.sent) == text


def test_empty_reply_sends_nothing():
    interaction = FakeInteraction()

    run_command(interaction, lambda: "")

    assert interaction.sent == []


def test_deferred_reply_goes_to_followup():
    interaction = FakeInteraction()

    run_command(interaction, lambda: "hi", defer=True)

    assert interaction.response.deferred == [{}]
    assert interaction.sent == [("hi", False, ALLOWED_MENTIONS)]
