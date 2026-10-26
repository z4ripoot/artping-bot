import asyncio

import discord

from fjormcord.bot.artping.slash.sync import sync_commands
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
