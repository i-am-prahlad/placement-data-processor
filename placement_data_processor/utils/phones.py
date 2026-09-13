"""Mobile number normalization. Never fabricate digits."""

from __future__ import annotations

import math
import re
from typing import Any


_NON_DIGIT = re.compile(r"\D+")


def _is_blank(value: Any) -> bool:
    if value is None:
        return True
    if isinstance(value, float) and (math.isnan(value) or math.isinf(value)):
        return True
    text = str(value).strip()
    return text == "" or text.lower() in {"nan", "none", "nat"}


def normalize_mobile(value: Any) -> tuple[str | None, str | None]:
    """Return (normalized_10_digit_or_none, flag_reason_or_none)."""
    if _is_blank(value):
        return None, "missing"

    if isinstance(value, float):
        if value.is_integer():
            raw = str(int(value))
        else:
            return None, "invalid"
    else:
        raw = str(value).strip()

    digits = _NON_DIGIT.sub("", raw)
    if not digits:
        return None, "no digits"

    if digits.startswith("91") and len(digits) >= 12:
        digits = digits[2:]
    if len(digits) == 11 and digits.startswith("0"):
        digits = digits[1:]

    if len(digits) != 10:
        return None, "not exactly 10 digits"
    if digits.startswith("0"):
        return None, "leading zero"
    return digits, None


def format_mobile_text(value: Any) -> str:
    """Format and preserve mobile number as clean text without scientific notation, decimal conversion, or loss of leading zeros."""
    if _is_blank(value):
        return ""
    if isinstance(value, float):
        if value.is_integer():
            return str(int(value))
        val_str = f"{value:.0f}" if value.is_integer() else str(value).strip()
        if val_str.endswith(".0"):
            val_str = val_str[:-2]
        return val_str
    if isinstance(value, int):
        return str(value)
    text = str(value).strip()
    if text.lower() in {"nan", "none", "nat", "-"}:
        return ""
    if re.fullmatch(r"\d+\.0", text):
        text = text[:-2]
    return text

