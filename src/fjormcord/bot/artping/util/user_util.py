import logging

import discord


def is_administrator(author):
    # Users in DMs have no guild permissions
    permissions = getattr(author, 'guild_permissions', None)
    return permissions is not None and permissions.administrator


async def get_username(client: discord.Client, user_id):
    # The cache costs no request to Discord, but only holds users the bot has seen since it started
    user = client.get_user(int(user_id))
    if user is None:
        try:
            user = await client.fetch_user(int(user_id))
        except (discord.NotFound, discord.HTTPException) as e:
            logging.warning("Failed to fetch user %s. %s", user_id, e)
            return f"Unknown user ({user_id})"

    # global_name is None for users who never set a display name
    return user.global_name or user.name
