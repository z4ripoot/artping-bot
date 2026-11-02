import asyncio
import inspect
import itertools
from dataclasses import replace
from datetime import datetime
from types import SimpleNamespace
from typing import NamedTuple
from unittest.mock import AsyncMock, patch

import discord

from fjormcord.bot.artping import config
from fjormcord.bot.artping.bot import ArtPingClient
from fjormcord.bot.artping.cooldowns import Cooldowns
from fjormcord.bot.artping.exception.command_error import CommandError
from fjormcord.bot.artping.service import character_vote_service
from fjormcord.bot.artping.view.layout import layout_text

# The bot's own user
BOT_USER = SimpleNamespace(id=999, bot=True)

_message_ids = itertools.count(1000)

# Stands for an argument left out of an edit, as discord.py's MISSING does
_UNCHANGED = object()


def sent_content(content, view):
    # What a sent message shows: a layout's text, which it must carry without content, as in Discord
    if isinstance(view, discord.ui.LayoutView):
        if content is not None:
            raise AssertionError("A layout message can't have content")
        return layout_text(view)
    return content


def buttons(view):
    # A message's buttons, in order, also those wrapped in a DynamicItem; [] without a view
    if view is None:
        return []
    items = view.walk_children() if isinstance(view, discord.ui.LayoutView) else view.children
    items = [getattr(item, "item", item) for item in items]
    return [item for item in items if isinstance(item, discord.ui.Button)]


def button_labels(view):
    return [button.label for button in buttons(view)]


def select_options(view):
    # The labels of the options of a message's dropdown
    selects = [getattr(item, "item", item) for item in view.walk_children()]
    [select] = [item for item in selects if isinstance(item, discord.ui.Select)]
    return [option.label for option in select.options]


def items_of_type(view, item_type):
    # The view's controls of this type, in order; DynamicItems are matched by their own class
    return [item for item in view.walk_children() if isinstance(item, item_type)]


def text_length(view):
    # The characters across a layout's text displays, of which Discord allows 4000 per message
    return sum(len(item.content) for item in view.walk_children() if isinstance(item, discord.ui.TextDisplay))


def after_restart(item):
    # A DynamicItem rebuilt from its custom_id, as discord.py does for a click on a message sent before a restart
    item_type = type(item)
    match = item_type.__discord_ui_compiled_template__.fullmatch(item.custom_id)
    return asyncio.run(item_type.from_custom_id(FakeInteraction(), item.item, match))


def registered_slash_commands():
    # Every slash command, as setup_hook registers them (without syncing), so no test keeps its own list of cogs
    bot = ArtPingClient(intents=discord.Intents.none())
    with patch("fjormcord.bot.artping.bot.sync_commands", AsyncMock()):
        asyncio.run(bot.setup_hook())
    return bot.tree.get_commands()


def use_settings(monkeypatch, **changes):
    # Runs the test with these settings changed from the example's
    monkeypatch.setattr(config, "_settings", replace(config.read_settings(), **changes))


def fake_datetime(utc_now, host_offset):
    # Simulates a host whose local timezone is UTC + host_offset
    class FakeDatetime(datetime):
        @classmethod
        def now(cls, tz=None):
            if tz is None:
                return (utc_now + host_offset).replace(tzinfo=None)
            return utc_now.astimezone(tz)

    return FakeDatetime


def make_member(user_id, administrator=False):
    return SimpleNamespace(
        id=user_id,
        bot=False,
        display_name=f"user{user_id}",
        guild_permissions=SimpleNamespace(administrator=administrator),
    )


def http_error(error, status):
    return error(SimpleNamespace(status=status, reason=error.__name__), error.__name__)


class FakeSentMessage:
    # A message the bot sent: the bot can edit its content and its view (the vote button)
    def __init__(self, content, view=None, channel=None):
        self.id = next(_message_ids)
        self.content = content
        self.view = view
        self.channel = channel

    @property
    def components(self):
        # The message's controls, flat; each has the custom_id the message was sent with, as Discord's components do
        if self.view is None:
            return []
        return list(self.view.walk_children() if isinstance(self.view, discord.ui.LayoutView) else self.view.children)

    async def edit(self, content=_UNCHANGED, view=_UNCHANGED):
        if isinstance(view, discord.ui.LayoutView):
            # As in Discord, a message that becomes a layout must lose its content, explicitly
            if content is not None:
                raise AssertionError("A layout message can't have content")
            content = layout_text(view)
        if content is not _UNCHANGED:
            self.content = content
        if view is not _UNCHANGED:
            self.view = view


class FakeChannel:
    # forbidden: the bot lacks the permissions to read the channel's messages
    def __init__(self, channel_id=10, forbidden=False):
        self.id = channel_id
        self.forbidden = forbidden
        self.sent = []
        # The allowed_mentions each message was sent with, None for the client's default
        self.sent_allowed_mentions = []
        self.messages = {}

    async def send(self, content=None, allowed_mentions=None, view=None):
        # A layout's text is recorded as its content, so tests compare both kinds of message the same way
        content = sent_content(content, view)
        self.sent.append(content)
        self.sent_allowed_mentions.append(allowed_mentions)
        return self.post(content, view)

    def post(self, content, view=None):
        # A message in the channel, e.g. one a user wrote earlier
        message = FakeSentMessage(content, view, channel=self)
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
        self.cooldowns = Cooldowns(1, FakeClock())

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
    author = SimpleNamespace(
        id=user_id,
        display_name=f"user{user_id}",
        bot=bot,
        guild_permissions=SimpleNamespace(administrator=administrator),
    )
    return SimpleNamespace(
        content=content, author=author, channel=channel or FakeChannel(), guild=SimpleNamespace(id=1)
    )


def click(client, message, user_id, administrator=False):
    # A click on a vote message's button by a server member; returns the ephemeral reply
    return asyncio.run(character_vote_service.toggle_vote(client, message, make_member(user_id, administrator)))


class Sent(NamedTuple):
    # A message sent in answer to an interaction; allowed_mentions is None for the client's default
    content: str
    ephemeral: bool
    allowed_mentions: discord.AllowedMentions | None


class FakeInteractionResponse:
    def __init__(self, interaction):
        self._interaction = interaction
        # The keyword arguments of each defer
        self.deferred = []
        self._done = False

    async def send_message(self, content=None, ephemeral=False, allowed_mentions=None, view=None):
        self._done = True
        self._interaction.record(content, ephemeral, allowed_mentions, view)

    async def defer(self, **options):
        self._done = True
        self.deferred.append(options)
        # As in Discord, a click's defer without thinking shows nothing: the clicked message is edited later
        if self._interaction.message is None or options.get("thinking"):
            self._interaction.placeholder = options

    def is_done(self):
        return self._done

    async def edit_message(self, content=_UNCHANGED, view=_UNCHANGED):
        self._done = True
        await self._interaction.message.edit(content=content, view=view)


class FakeFollowup:
    def __init__(self, interaction):
        self._interaction = interaction

    async def send(self, content=None, ephemeral=False, allowed_mentions=None, view=None, wait=False):
        # As in Discord, a follow-up needs the interaction to be answered or deferred first
        if not self._interaction.response.is_done():
            raise RuntimeError("Follow-up sent before the interaction was responded to or deferred")
        # As in Discord, the first follow-up after a defer replaces its placeholder and keeps the defer's visibility
        if self._interaction.placeholder is not None:
            ephemeral = self._interaction.placeholder.get("ephemeral", False)
            self._interaction.placeholder = None
        message = self._interaction.record(content, ephemeral, allowed_mentions, view)
        return message if wait else None


class FakeInteraction:
    # A slash command or component click by a user; message is the message a component belongs to
    def __init__(self, user_id=1, administrator=False, channel=None, client=None, in_guild=True, message=None):
        self.user = make_member(user_id, administrator)
        self.channel = channel or FakeChannel()
        self.channel_id = self.channel.id
        self.client = client or FakeClient(channels=[self.channel])
        self.guild = SimpleNamespace(id=1) if in_guild else None
        self.message = message
        self.response = FakeInteractionResponse(self)
        self.followup = FakeFollowup(self)
        # The app command being run, set by invoke; None for a component click
        self.command = None
        # Everything sent, as response or follow-up
        self.sent: list[Sent] = []
        # The defer's options while its "is thinking" placeholder is the original response, else None
        self.placeholder = None
        self.original_deleted = False

    async def original_response(self):
        return SimpleNamespace(flags=discord.MessageFlags(loading=self.placeholder is not None))

    async def edit_original_response(self, content=_UNCHANGED, view=_UNCHANGED):
        # After a click's defer, the original response is the clicked message
        await self.message.edit(content=content, view=view)

    async def delete_original_response(self):
        self.placeholder = None
        self.original_deleted = True

    def record(self, content, ephemeral, allowed_mentions, view):
        content = sent_content(content, view)
        self.sent.append(Sent(content, ephemeral, allowed_mentions))
        return self.channel.post(content, view)


def invoke(command, interaction, cog=None, **options):
    # Runs an app command's callback as discord.py does after parsing the options
    interaction.command = command
    arguments = (interaction,) if cog is None else (cog, interaction)
    return asyncio.run(command.callback(*arguments, **options))


def reply(handler, client, message):
    # Runs a handler as the bot does: awaited when it is async, and a CommandError's message, or layout, is the reply.
    # A Layout is returned as it is, so tests compare its texts
    try:
        out = handler(client, message)
        out = asyncio.run(out) if inspect.isawaitable(out) else out
    except CommandError as e:
        return e.layout or str(e)
    return out
