import re

_NAME_PART = re.compile(r"[^_!'-]+")


def _normalize_part(part: str) -> str:
    return part if part.isupper() else part.capitalize()


def normalize_name(name: str) -> str:
    return _NAME_PART.sub(lambda part: _normalize_part(part.group()), name)
