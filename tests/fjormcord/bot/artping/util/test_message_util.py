import discord

from fjormcord.bot.artping.model.layout import Layout
from fjormcord.bot.artping.util.message_util import split_layout, split_message


def test_short_message_is_not_split():
    assert split_message("hello\nworld", limit=20) == ["hello\nworld"]


def test_splits_on_line_breaks():
    assert split_message("aaaa\nbbbb\ncccc", limit=9) == ["aaaa\nbbbb", "cccc"]


def test_splits_long_line_on_spaces():
    assert split_message("<@1> <@2> <@3> <@4>", limit=10) == ["<@1> <@2>", "<@3> <@4>"]


def test_cuts_word_longer_than_limit():
    assert split_message("abcdefghij", limit=4) == ["abcd", "efgh", "ij"]


def test_split_layout_keeps_a_short_layout_whole():
    layout = Layout(("a", "b"))

    assert split_layout(layout) == [layout]


def test_split_layout_splits_a_long_text_and_keeps_the_rows_on_the_last_part():
    rows = ((discord.ui.Button(label="x", custom_id="x"),),)
    body = " ".join(f"<@{n:018d}>" for n in range(300))

    parts = split_layout(Layout(("### Head\n" + body, "Footer"), rows), limit=4000)

    assert len(parts) > 1
    assert parts[0].texts[0].startswith("### Head")
    assert parts[-1].texts[-1] == "Footer"
    assert parts[-1].rows == rows
    assert all(part.rows == () for part in parts[:-1])
    assert all(sum(map(len, part.texts)) <= 4000 for part in parts)
    words = " ".join(" ".join(part.texts) for part in parts).split()
    assert all(words.count(f"<@{n:018d}>") == 1 for n in range(300))
