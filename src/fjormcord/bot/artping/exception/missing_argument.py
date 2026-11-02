class MissingArgument(Exception):
    def __init__(self, argument: str):
        super().__init__(f"{argument} is missing")
        self.argument = argument
