import logging


def get_entries(content):
    split_entries = content.split(" ")

    if len(split_entries) < 2:
        logging.warning("No entries found")
        return None

    entry_list = []

    logging.info("Getting entries")

    # Get all entries
    for entry in split_entries[1:]:
        entry_list.append(entry)

    logging.info("Found %d entries", len(entry_list))

    return entry_list


def get_first(content):
    split_entries = content.split(" ")

    if len(split_entries) < 2:
        logging.warning("No entries found")
        return None

    logging.info("Getting first entry")

    return split_entries[1]
