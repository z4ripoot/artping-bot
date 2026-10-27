class MissingArgument(Exception):
    # Raised by a handler; the client answers with what is missing and the command's usage from ~help
    def __init__(self, argument):
        super().__init__(f"{argument} is missing")
        self.argument = argument
