from typing import TYPE_CHECKING

if TYPE_CHECKING:
    # Only for the annotation, so exceptions still import nothing from the project when the bot runs
    from fjormcord.bot.artping.model.layout import Layout


class CommandError(Exception):
    # Raised by a handler to turn a command down; the client logs the message and sends it as the reply, or the layout
    # when there is one (a refusal that is laid out, e.g. an art ping of unknown characters with its hint)
    def __init__(self, message: str, layout: "Layout | None" = None):
        super().__init__(message)
        self.layout = layout
