import logging


def get_entries(content):
    # Everything after the command
    entries = content.split(" ")[1:]

    if not entries:
        logging.warning("No entries found")
        return None

    return entries


def get_first(content):
    entries = get_entries(content)
    return entries[0] if entries else None
