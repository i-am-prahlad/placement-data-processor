"""Name cleaning for export. Never invent a name."""

from __future__ import annotations

import math
from typing import Any


def _is_blank(value: Any) -> bool:
    if value is None:
        return True
    if isinstance(value, float) and (math.isnan(value) or math.isinf(value)):
        return True
    text = str(value).strip()
    return text == "" or text.lower() in {"nan", "none", "nat"}


def _cap_token(token: str) -> str:
    if not token:
        return token
    pieces = []
    for part in token.split("'"):
        if not part:
            pieces.append(part)
            continue
        pieces.append(part[0].upper() + part[1:].lower() if len(part) > 1 else part.upper())
    return "'".join(pieces)


def to_proper_case(value: Any) -> str:
    if _is_blank(value):
        return ""
    text = " ".join(str(value).split())
    return " ".join(_cap_token(token) for token in text.split(" "))
