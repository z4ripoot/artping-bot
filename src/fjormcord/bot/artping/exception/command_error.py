from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from fjormcord.bot.artping.model.layout import Layout


class CommandError(Exception):
    def __init__(self, message: str, layout: "Layout | None" = None):
        super().__init__(message)
        self.layout = layout
