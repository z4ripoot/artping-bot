import re

_NAME_PART = re.compile(r"[^_!']+")


def normalize_name(name: str) -> str:
    return _NAME_PART.sub(lambda part: part.group().capitalize(), name)
