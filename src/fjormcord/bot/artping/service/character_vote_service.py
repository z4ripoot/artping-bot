import logging
from collections.abc import Iterable

import discord

from fjormcord.bot.artping import config
from fjormcord.bot.artping.exception.command_error import CommandError
from fjormcord.bot.artping.model.character import Character
from fjormcord.bot.artping.model.character_vote import CharacterVote, VoteChannel
from fjormcord.bot.artping.model.layout import Layout
from fjormcord.bot.artping.repository import character_vote_repository
from fjormcord.bot.artping.service import character_service  # A module: it imports this one too
from fjormcord.bot.artping.util.interaction_util import walk_components
from fjormcord.bot.artping.util.user_util import is_administrator
from fjormcord.bot.artping.view import subscribe_view, vote_view  # Modules: vote_view imports this one too
from fjormcord.bot.artping.view.layout import to_view


def is_voting_enabled() -> bool:
    # With fewer than 2 votes needed a vote decides nothing, so non-admins add characters directly
    return config.read_settings().character_votes_needed >= 2


async def start_vote(vote_channel: VoteChannel, proposer_id: str, name: str) -> str:
    # The vote message is sent here instead of being the reply, since the vote is stored by its ID
    if not vote_channel.in_guild:
        raise CommandError("Votes can only be started in a server")

    # The proposer's vote is counted from the start, which saves them a click. Votes are only started when at least
    # 2 are needed, so it can't pass the vote on its own
    vote_message = await vote_channel.send(to_view(_vote_layout(name, 1)))
    character_vote_repository.add_vote(
        CharacterVote(str(vote_message.id), vote_channel.channel_id, name, proposer_id),
        [proposer_id],
    )

    # An empty reply sends nothing more
    return ""


async def toggle_vote(client: discord.Client, vote_message: discord.Message, user: discord.abc.User) -> str:
    # A click on the vote button adds the user's vote or takes it back; an admin's click passes the vote.
    # Returns the reply only the clicker sees.
    message_id = str(vote_message.id)
    vote = character_vote_repository.get_vote(message_id)
    if vote is None:
        # Closed while its message kept the button, e.g. when editing the message failed: it gets a text without the
        # button, as a layout message has no content to keep. Unless the message has been edited since: a click that
        # raced the one that passed the vote must not overwrite its announcement and Subscribe button
        if await _shows_vote_button(vote_message):
            await _edit(vote_message, Layout(("This vote has already been closed",)))
        return "This vote has already been closed"

    dropped = await _drop_if_name_taken(vote_message, vote)
    if dropped is not None:
        return dropped

    # Nothing awaits from reading the vote to the commit, so other clicks and events can't interleave
    name = vote.character_name
    user_id = str(user.id)
    # The click comes from a server member, so the permissions are there without fetching the member
    administrator = is_administrator(user)
    if not administrator and character_vote_repository.has_voter(message_id, user_id):
        character_vote_repository.remove_voter(message_id, user_id)
        out = f"Your vote for {name} has been taken back"
    else:
        # An admin is subscribed along with the other voters
        character_vote_repository.add_voter(message_id, user_id)
        out = f"Your vote for {name} has been added"

    await _pass_or_show_count(client, vote_message, vote, administrator)
    return out


async def close_votes(client: discord.Client, character: Character):
    # The character has been added without them, so the open votes for its name have nothing left to decide
    votes = character_vote_repository.get_votes_for(character.name)
    character_vote_repository.remove_votes_for(character.name)
    await _close(client, votes, character)


def drop_deleted_vote(message_id: str):
    # Called for every deleted message, most of which aren't votes
    if character_vote_repository.get_vote(message_id) is not None:
        character_vote_repository.remove_vote(message_id)


def _vote_layout(name: str, count: int) -> Layout:
    return Layout((_vote_text(name),), ((vote_view.VoteButton(count),),))


def _added_layout(text: str, character: Character) -> Layout:
    # The Vote button makes way for Subscribe, for those who didn't vote
    return Layout((text,), ((subscribe_view.SubscribeButton.for_character(character),),))


def _vote_text(name: str) -> str:
    return f"Vote to add {name}. Votes needed: {config.read_settings().character_votes_needed}"


async def _drop_if_name_taken(vote_message: discord.Message, vote: CharacterVote) -> str | None:
    # A name taken another way, e.g. as an alias, leaves the vote nothing to decide: it is dropped and its message
    # says why. Returns that reason, or None when the vote stays open; then it awaits nothing, so the caller's
    # vote can't change underneath it
    try:
        character_service.require_unused_name(vote.character_name)
    except CommandError as e:
        logging.info("Dropping vote %s: %s", vote.message_id, e)
        character_vote_repository.remove_vote(vote.message_id)
        await _edit(vote_message, Layout((str(e),)))
        return str(e)
    return None


async def _pass_or_show_count(
    client: discord.Client, vote_message: discord.Message, vote: CharacterVote, by_administrator: bool
):
    # Adds the character when an admin voted or enough users did; otherwise renders the message with the current count
    count = character_vote_repository.count_voters(vote.message_id)
    if by_administrator or count >= config.read_settings().character_votes_needed:
        await _pass(client, vote_message, vote)
    else:
        await _edit(vote_message, _vote_layout(vote.character_name, count))


async def _pass(client: discord.Client, vote_message: discord.Message, vote: CharacterVote):
    # The caller has awaited nothing since it read the vote, so it is still open
    other_votes = [
        other
        for other in character_vote_repository.get_votes_for(vote.character_name)
        if other.message_id != vote.message_id
    ]
    character_id = character_vote_repository.pass_vote(vote.message_id, vote.character_name)
    character = Character(character_id, vote.character_name)
    await _edit(vote_message, _added_layout(f"Character {character.name} has been added", character))
    await _close(client, other_votes, character)


async def _fetch_vote_message(client: discord.Client, vote: CharacterVote) -> discord.Message:
    channel_id = int(vote.channel_id)
    # The cache costs no request to Discord
    channel = client.get_channel(channel_id) or await client.fetch_channel(channel_id)
    return await channel.fetch_message(int(vote.message_id))


async def _close(client: discord.Client, votes: Iterable[CharacterVote], character: Character):
    # The votes are already gone from the database; this only tells their messages, and swaps their Vote button for
    # Subscribe
    for vote in votes:
        try:
            vote_message = await _fetch_vote_message(client, vote)
        except discord.HTTPException as e:
            logging.warning("Failed to fetch the message of closed vote %s. %s", vote.message_id, e)
            continue
        await _edit(vote_message, _added_layout(f"Character {character.name} has already been added", character))


async def _shows_vote_button(vote_message: discord.Message) -> bool:
    # Whether the message, as it is now rather than as it was clicked, still has the Vote button, at any depth of its
    # layout
    try:
        current = await vote_message.channel.fetch_message(vote_message.id)
    except discord.HTTPException as e:
        logging.warning("Failed to fetch vote message %s. %s", vote_message.id, e)
        return False
    return any(
        getattr(component, "custom_id", None) == vote_view.VOTE_BUTTON_ID
        for component in walk_components(current.components)
    )


async def _edit(vote_message: discord.Message, layout: Layout):
    # content=None: a layout message can't have content
    try:
        await vote_message.edit(content=None, view=to_view(layout))
    except discord.HTTPException as e:
        logging.warning("Failed to edit vote message %s. %s", vote_message.id, e)
