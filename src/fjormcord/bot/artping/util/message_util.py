import logging


def get_entries(content):
    # Everything after the command; split() also ignores repeated whitespace
    entries = content.split()[1:]

    if not entries:
        logging.warning("No entries found")
        return None

    return entries


def get_first(content):
    entries = get_entries(content)
    return entries[0] if entries else None


# Discord rejects messages longer than this
MAX_MESSAGE_LENGTH = 2000


def split_message(text, limit=MAX_MESSAGE_LENGTH):
    # Break at line breaks where possible, then at spaces (keeps mentions intact), and only cut words as a last resort
    chunks = []
    current = ""

    for separator, piece in _pieces(text, limit):
        if current and len(current) + len(separator) + len(piece) <= limit:
            current += separator + piece
        else:
            if current:
                chunks.append(current)
            current = piece

    if current:
        chunks.append(current)
    return chunks


def _pieces(text, limit):
    # Yields (separator, piece) pairs, each piece at most limit long
    for line_index, line in enumerate(text.split("\n")):
        line_separator = "\n" if line_index else ""
        if len(line) <= limit:
            yield line_separator, line
            continue

        for word_index, word in enumerate(line.split(" ")):
            separator = " " if word_index else line_separator
            for start in range(0, len(word), limit):
                yield separator if start == 0 else "", word[start:start + limit]
