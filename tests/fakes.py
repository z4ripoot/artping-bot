from types import SimpleNamespace

import discord


class FakeChannel:
    def __init__(self):
        self.sent = []

    async def send(self, content):
        self.sent.append(content)


class FakeClient:
    def __init__(self, users=None):
        self.users = users or {}

    async def fetch_user(self, user_id):
        if user_id not in self.users:
            raise discord.NotFound(SimpleNamespace(status=404, reason="Not Found"), "Unknown User")
        return SimpleNamespace(global_name=self.users[user_id], name=f"name{user_id}")


def make_message(content, user_id=1, administrator=False):
    author = SimpleNamespace(id=user_id, display_name=f"user{user_id}",
                             guild_permissions=SimpleNamespace(administrator=administrator))
    return SimpleNamespace(content=content, author=author, channel=FakeChannel())
