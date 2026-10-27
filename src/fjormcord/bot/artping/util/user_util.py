import logging
from collections.abc import Iterable

import discord


def is_administrator(author: discord.abc.User) -> bool:
    # Users in DMs have no guild permissions
    permissions = getattr(author, "guild_permissions", None)
    return permissions is not None and permissions.administrator


def mentions(user_ids: Iterable[str]) -> str:
    # The users as mentions, which ping them, separated by spaces
    return " ".join(f"<@{user_id}>" for user_id in user_ids)


async def get_username(client: discord.Client, user_id: str) -> str:
    # The cache costs no request to Discord, but only holds users the bot has seen since it started
    user = client.get_user(int(user_id))
    if user is None:
        try:
            user = await client.fetch_user(int(user_id))
        except discord.HTTPException as e:
            logging.warning("Failed to fetch user %s. %s", user_id, e)
            return f"Unknown user ({user_id})"

    # global_name is None for users who never set a display name
    return user.global_name or user.name
