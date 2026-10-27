import re

# Characters that start a new part of a name: Black_Knight, M!Robin, L'Arachel
_NAME_PART = re.compile(r"[^_!']+")


def normalize_name(name: str) -> str:
    # Each part of the name starts with a capital and the rest is lowercase, e.g. black_KNIGHT -> Black_Knight
    return _NAME_PART.sub(lambda part: part.group().capitalize(), name)
