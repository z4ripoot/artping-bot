import asyncio
import inspect
import itertools
from types import SimpleNamespace

import discord

from fjormcord.bot.artping.service import character_vote_service
from fjormcord.bot.artping.util.message_util import CommandError


# The bot's own user, e.g. on the reaction it added to vote messages before they had a button
BOT_USER = SimpleNamespace(id=999, bot=True)

_message_ids = itertools.count(1000)

# Stands for an argument left out of an edit, as discord.py's MISSING does
_UNCHANGED = object()


def make_user(user_id, bot=False):
    # A user as reactions list them when the member isn't cached: without guild permissions
    return SimpleNamespace(id=user_id, bot=bot)


def make_member(user_id, administrator=False):
    return SimpleNamespace(id=user_id, bot=False, guild_permissions=SimpleNamespace(administrator=administrator))


def http_error(error, status):
    return error(SimpleNamespace(status=status, reason=error.__name__), error.__name__)


class FakeGuild:
    # administrators: IDs of the members with administrator permissions; members: everyone still in the server
    def __init__(self, members=(), administrators=()):
        self.members = set(members) | set(administrators)
        self.administrators = set(administrators)

    async def fetch_member(self, user_id):
        if user_id not in self.members:
            raise http_error(discord.NotFound, 404)
        return make_member(user_id, administrator=user_id in self.administrators)


class FakeReaction:
    def __init__(self, emoji):
        self.emoji = emoji
        self.reactors = []

    async def users(self):
        for user in self.reactors:
            yield user


class FakeSentMessage:
    # A message the bot sent: users can react to it, the bot can edit its content and its view (the vote button)
    def __init__(self, content, guild, view=None):
        self.id = next(_message_ids)
        self.content = content
        self.guild = guild
        self.view = view
        self.reactions = []

    def react(self, emoji, user):
        reaction = next((reaction for reaction in self.reactions if reaction.emoji == emoji), None)
        if reaction is None:
            reaction = FakeReaction(emoji)
            self.reactions.append(reaction)
        reaction.reactors.append(user)

    async def add_reaction(self, emoji):
        self.react(emoji, BOT_USER)

    async def edit(self, content=_UNCHANGED, view=_UNCHANGED):
        if content is not _UNCHANGED:
            self.content = content
        if view is not _UNCHANGED:
            self.view = view


class FakeChannel:
    # forbidden: the bot lacks the permissions to read the channel's messages
    def __init__(self, channel_id=10, forbidden=False, guild=None):
        self.id = channel_id
        self.forbidden = forbidden
        self.guild = guild or FakeGuild()
        self.sent = []
        # The allowed_mentions each message was sent with, None for the client's default
        self.sent_allowed_mentions = []
        self.messages = {}

    async def send(self, content, allowed_mentions=None, view=None):
        self.sent.append(content)
        self.sent_allowed_mentions.append(allowed_mentions)
        return self.post(content, view)

    def post(self, content, view=None):
        # A message in the channel, e.g. one a user wrote earlier
        message = FakeSentMessage(content, self.guild, view)
        self.messages[message.id] = message
        return message

    async def fetch_message(self, message_id):
        if self.forbidden:
            raise http_error(discord.Forbidden, 403)
        if message_id not in self.messages:
            raise http_error(discord.NotFound, 404)
        return self.messages[message_id]

    def last_message(self):
        return list(self.messages.values())[-1]


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
    def __init__(self, users=None, cached_users=None, channels=()):
        self.users = users or {}
        self.cached_users = cached_users or {}
        self.channels = {channel.id: channel for channel in channels}
        self.fetched = []
        self.user = BOT_USER

    def get_channel(self, channel_id):
        return self.channels.get(channel_id)

    async def fetch_channel(self, channel_id):
        if channel_id not in self.channels:
            raise http_error(discord.NotFound, 404)
        return self.channels[channel_id]

    def get_partial_messageable(self, channel_id):
        # Like Discord's, it exists for any ID; fetching from an unknown channel fails
        return self.channels.get(channel_id) or FakeChannel(channel_id)

    def get_user(self, user_id):
        if user_id not in self.cached_users:
            return None
        return SimpleNamespace(global_name=self.cached_users[user_id], name=f"name{user_id}")

    async def fetch_user(self, user_id):
        self.fetched.append(user_id)
        if user_id not in self.users:
            raise http_error(discord.NotFound, 404)
        return SimpleNamespace(global_name=self.users[user_id], name=f"name{user_id}")


def make_message(content, user_id=1, administrator=False, channel=None, bot=False):
    author = SimpleNamespace(id=user_id, display_name=f"user{user_id}", bot=bot,
                             guild_permissions=SimpleNamespace(administrator=administrator))
    return SimpleNamespace(content=content, author=author, channel=channel or FakeChannel(),
                           guild=SimpleNamespace(id=1))


def click(client, message, user_id, administrator=False):
    # A click on a vote message's button by a server member; returns the ephemeral reply
    return asyncio.run(character_vote_service.toggle_vote(client, message, make_member(user_id, administrator)))


def reply(handler, client, message):
    # Runs a handler as the bot does: awaited when it is async, and a CommandError's message is the reply
    try:
        out = handler(client, message)
        return asyncio.run(out) if inspect.isawaitable(out) else out
    except CommandError as e:
        return str(e)
