import asyncio
import inspect
from types import SimpleNamespace

import discord

from fjormcord.bot.artping.util.message_util import CommandError


class FakeChannel:
    def __init__(self):
        self.sent = []

    async def send(self, content):
        self.sent.append(content)


class FakeClock:
    # Stands in for time.monotonic; the test moves it forward by hand
    def __init__(self, now=1000.0):
        self.now = now

    def __call__(self):
        return self.now

    def advance(self, seconds):
        self.now += seconds


class FakeClient:
    # users can be fetched from Discord; cached_users are also in the client's cache
    def __init__(self, users=None, cached_users=None):
        self.users = users or {}
        self.cached_users = cached_users or {}
        self.fetched = []

    def get_user(self, user_id):
        if user_id not in self.cached_users:
            return None
        return SimpleNamespace(global_name=self.cached_users[user_id], name=f"name{user_id}")

    async def fetch_user(self, user_id):
        self.fetched.append(user_id)
        if user_id not in self.users:
            raise discord.NotFound(SimpleNamespace(status=404, reason="Not Found"), "Unknown User")
        return SimpleNamespace(global_name=self.users[user_id], name=f"name{user_id}")


def make_message(content, user_id=1, administrator=False):
    author = SimpleNamespace(id=user_id, display_name=f"user{user_id}",
                             guild_permissions=SimpleNamespace(administrator=administrator))
    return SimpleNamespace(content=content, author=author, channel=FakeChannel())


def reply(handler, client, message):
    # Runs a handler as the bot does: awaited when it is async, and a CommandError's message is the reply
    try:
        out = handler(client, message)
        return asyncio.run(out) if inspect.isawaitable(out) else out
    except CommandError as e:
        return str(e)
