import discord

from fjormcord.bot.artping.model.layout import Layout
from fjormcord.bot.artping.util.message_util import split_layout, split_message

ACCENT_COLOUR = discord.Colour.blurple()


def to_view(layout: Layout) -> discord.ui.LayoutView:
    items = []
    for text in layout.texts:
        if items:
            items.append(discord.ui.Separator())
        items.append(discord.ui.TextDisplay(text))
    if layout.rows and items:
        items.append(discord.ui.Separator())
    items += [discord.ui.ActionRow(*row) for row in layout.rows]

    view = discord.ui.LayoutView(timeout=None)
    view.add_item(discord.ui.Container(*items, accent_colour=ACCENT_COLOUR))
    return view


def layout_text(view: discord.ui.LayoutView) -> str:
    return "\n".join(item.content for item in view.walk_children() if isinstance(item, discord.ui.TextDisplay))


def message_options(reply: str | Layout) -> list[dict]:
    if isinstance(reply, Layout):
        return [{"view": to_view(part)} for part in split_layout(reply)]
    return [{"content": chunk} for chunk in split_message(reply)]
