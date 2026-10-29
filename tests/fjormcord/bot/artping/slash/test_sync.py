import asyncio

import discord
from discord import app_commands

from fjormcord.bot.artping.slash.sync import registered_commands, sync_commands
from tests.fakes import http_error


class FakeTree:
    # Records the calls in order; sync raises error when one is given
    def __init__(self, error=None):
        self.calls = []
        self.error = error

    def copy_global_to(self, guild):
        self.calls.append(("copy_global_to", guild.id))

    def clear_commands(self, guild):
        self.calls.append(("clear_commands", guild))

    async def sync(self, guild=None):
        self.calls.append(("sync", guild.id if guild else None))
        if self.error:
            raise self.error


def test_sync_to_guild_clears_global():
    tree = FakeTree()

    asyncio.run(sync_commands(tree, 42))

    assert tree.calls == [("copy_global_to", 42), ("sync", 42), ("clear_commands", None), ("sync", None)]


def test_sync_without_guild_is_global():
    tree = FakeTree()

    asyncio.run(sync_commands(tree, None))

    assert tree.calls == [("sync", None)]


def test_sync_failure_is_logged(caplog):
    tree = FakeTree(http_error(discord.Forbidden, 403))

    asyncio.run(sync_commands(tree, 42))

    assert "Syncing the slash commands failed" in caplog.text


def test_sync_network_failure_is_logged(caplog):
    tree = FakeTree(ConnectionResetError("connection lost"))

    asyncio.run(sync_commands(tree, 42))

    assert "Syncing the slash commands failed" in caplog.text


def test_registered_commands_are_read_where_sync_left_them():
    tree = app_commands.CommandTree(discord.Client(intents=discord.Intents.none()))
    tree.add_command(app_commands.Command(name="ping", description="Ping", callback=_callback))
    assert [command.name for command in registered_commands(tree, None)] == ["ping"]

    # Synced to a development guild: copied there and cleared globally
    tree.copy_global_to(guild=discord.Object(id=42))
    tree.clear_commands(guild=None)

    assert [command.name for command in registered_commands(tree, 42)] == ["ping"]
    assert registered_commands(tree, None) == []


async def _callback(interaction: discord.Interaction):
    pass
