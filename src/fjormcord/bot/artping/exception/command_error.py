class CommandError(Exception):
    # Raised by a handler to turn a command down; the client logs the message and sends it as the reply
    pass
