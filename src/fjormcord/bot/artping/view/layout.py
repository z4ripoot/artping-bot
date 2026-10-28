import discord

from fjormcord.bot.artping.model.layout import Layout
from fjormcord.bot.artping.util.message_util import split_layout, split_message

# The bar on the left of every layout
ACCENT_COLOUR = discord.Colour.blurple()


def to_view(layout: Layout) -> discord.ui.LayoutView:
    # Without a timeout, so its controls keep working; they are DynamicItems, which work after a restart too
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
    # The text of a layout message, for logs and tests
    return "\n".join(item.content for item in view.walk_children() if isinstance(item, discord.ui.TextDisplay))


def message_options(reply: str | Layout) -> list[dict]:
    # The keyword arguments of each message a reply is sent as: a string split to Discord's length limit, a layout
    # split to its own limit, as views without content. An empty reply sends nothing
    if isinstance(reply, Layout):
        return [{"view": to_view(part)} for part in split_layout(reply)]
    return [{"content": chunk} for chunk in split_message(reply)]
