import discord

from fjormcord.bot.artping.model.layout import Layout
from fjormcord.bot.artping.view.layout import layout_text, message_options, to_view


def item_types(view):
    [container] = view.children
    return [type(item).__name__ for item in container.children]


def test_layout_is_a_container_of_texts_separators_and_rows():
    button = discord.ui.Button(label="x", custom_id="x")

    view = to_view(Layout(("### Head", "Body"), ((button,),)))

    [container] = view.children
    assert isinstance(container, discord.ui.Container)
    assert container.accent_colour == discord.Colour.blurple()
    assert item_types(view) == ["TextDisplay", "Separator", "TextDisplay", "Separator", "ActionRow"]
    assert view.is_persistent()


def test_layout_without_rows_ends_with_its_text():
    assert item_types(to_view(Layout(("Only",)))) == ["TextDisplay"]


def test_layout_text_joins_the_text_displays():
    assert layout_text(to_view(Layout(("a", "b")))) == "a\nb"


def test_message_options_of_a_string_are_its_chunks():
    assert message_options("hi") == [{"content": "hi"}]


def test_message_options_of_a_layout_are_views():
    [options] = message_options(Layout(("hi",)))

    assert list(options) == ["view"]
    assert isinstance(options["view"], discord.ui.LayoutView)
    assert layout_text(options["view"]) == "hi"
