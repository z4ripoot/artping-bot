import pytest

from fjormcord.bot.artping.exception.command_error import CommandError
from fjormcord.bot.artping.util.page_util import get_page


def test_page_holds_ten_entries_and_counts_the_pages():
    assert get_page(list(range(1, 26)), 2, "The list") == (list(range(11, 21)), 3)


def test_last_page_holds_the_rest():
    assert get_page(list(range(1, 26)), 3, "The list") == ([21, 22, 23, 24, 25], 3)


def test_page_out_of_range_is_refused():
    with pytest.raises(CommandError, match="^Page 4 doesn't exist. The scoreboard for Orbs has 3 pages$"):
        get_page(list(range(1, 26)), 4, "The scoreboard for Orbs")
    with pytest.raises(CommandError, match="^Page 0 doesn't exist"):
        get_page(list(range(1, 26)), 0, "The scoreboard for Orbs")


def test_a_single_page_is_named_in_the_singular():
    with pytest.raises(CommandError, match="^Page 2 doesn't exist. The list has 1 page$"):
        get_page([1], 2, "The list")
