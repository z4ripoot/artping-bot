from fjormcord.bot.artping.util.message_util import split_message


def test_short_message_is_not_split():
    assert split_message("hello\nworld", limit=20) == ["hello\nworld"]


def test_splits_on_line_breaks():
    assert split_message("aaaa\nbbbb\ncccc", limit=9) == ["aaaa\nbbbb", "cccc"]


def test_splits_long_line_on_spaces():
    assert split_message("<@1> <@2> <@3> <@4>", limit=10) == ["<@1> <@2>", "<@3> <@4>"]


def test_cuts_word_longer_than_limit():
    assert split_message("abcdefghij", limit=4) == ["abcd", "efgh", "ij"]
