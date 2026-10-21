import asyncio

from fjormcord.bot.artping.util.user_util import get_username
from tests.fakes import FakeClient


def test_cached_user_is_not_fetched():
    client = FakeClient(users={1: "Alice"}, cached_users={1: "Alice"})

    assert asyncio.run(get_username(client, "1")) == "Alice"
    assert client.fetched == []


def test_uncached_user_is_fetched():
    client = FakeClient(users={1: "Alice"})

    assert asyncio.run(get_username(client, "1")) == "Alice"
    assert client.fetched == [1]


def test_unknown_user():
    assert asyncio.run(get_username(FakeClient(), "99")) == "Unknown user (99)"
