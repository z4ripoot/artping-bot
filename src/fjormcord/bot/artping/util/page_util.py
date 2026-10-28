import math
from typing import TypeVar

from fjormcord.bot.artping.exception.command_error import CommandError

# The entries on one page of the scoreboard, a user's pings or a character's subscribers
PAGE_SIZE = 10

T = TypeVar("T")


def get_page(entries: list[T], page: int, description: str) -> tuple[list[T], int]:
    # The entries on the page, and the number of pages; entries isn't empty. description names the list in the error,
    # e.g. "The scoreboard for Orbs"
    page_count = math.ceil(len(entries) / PAGE_SIZE)
    if not 1 <= page <= page_count:
        pages = "page" if page_count == 1 else "pages"
        raise CommandError(f"Page {page} doesn't exist. {description} has {page_count} {pages}")
    start = (page - 1) * PAGE_SIZE
    return entries[start : start + PAGE_SIZE], page_count
