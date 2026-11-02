import math
from typing import TypeVar

from fjormcord.bot.artping.exception.command_error import CommandError

PAGE_SIZE = 10

T = TypeVar("T")


def paged_header(header: str, page: int, page_count: int) -> str:
    return header if page_count == 1 else f"{header} (page {page}/{page_count})"


def get_page(entries: list[T], page: int, description: str) -> tuple[list[T], int]:
    page_count = math.ceil(len(entries) / PAGE_SIZE)
    if not 1 <= page <= page_count:
        pages = "page" if page_count == 1 else "pages"
        raise CommandError(f"Page {page} doesn't exist. {description} has {page_count} {pages}")
    start = (page - 1) * PAGE_SIZE
    return entries[start : start + PAGE_SIZE], page_count
