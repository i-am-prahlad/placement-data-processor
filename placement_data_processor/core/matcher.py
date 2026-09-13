"""Safe student matching. College Roll No. is primary. Never match solely on an ambiguous name."""

from __future__ import annotations

import pandas as pd


def _unique_lookup(frame: pd.DataFrame, key: str, value_col: str) -> dict:
    usable = frame[key].notna() & (frame[key].astype(str).str.strip() != "") & (frame[key].astype(str) != "None")
    subset = frame.loc[usable, [key, value_col]]
    counts = subset[key].value_counts()
    unique_keys = counts[counts == 1].index
    paired = subset[subset[key].isin(unique_keys)]
    return dict(zip(paired[key], paired[value_col]))


def match_values(
    students: pd.DataFrame,
    reference: pd.DataFrame,
    value_col: str,
    default=None,
) -> tuple[pd.Series, pd.Series]:
    """
    Return (matched_values, match_method).
    Methods: roll_no, email, mobile, unmatched.
    Name is never used for silent matching.
    """
    n = len(students)
    values = pd.Series([default] * n, index=students.index)
    methods = pd.Series(["unmatched"] * n, index=students.index)

    by_roll = _unique_lookup(reference, "roll_no", value_col)
    roll_keys = students["roll_no"].astype(str)
    roll_hit = students["roll_no"].ne("") & roll_keys.isin(by_roll)
    values.loc[roll_hit] = roll_keys[roll_hit].map(by_roll)
    methods.loc[roll_hit] = "roll_no"

    remaining = methods.eq("unmatched")
    if remaining.any() and "email" in reference.columns and "email" in students.columns:
        by_email = _unique_lookup(reference, "email", value_col)
        email_hit = remaining & students["email"].astype(str).str.strip().ne("") & students["email"].isin(by_email)
        values.loc[email_hit] = students.loc[email_hit, "email"].map(by_email)
        methods.loc[email_hit] = "email"

    remaining = methods.eq("unmatched")
    if remaining.any() and "mobile" in reference.columns and "mobile" in students.columns:
        by_mobile = _unique_lookup(reference, "mobile", value_col)
        mobile_hit = remaining & students["mobile"].notna() & students["mobile"].isin(by_mobile)
        values.loc[mobile_hit] = students.loc[mobile_hit, "mobile"].map(by_mobile)
        methods.loc[mobile_hit] = "mobile"

    return values, methods


def ambiguous_name_matches(students: pd.DataFrame, reference: pd.DataFrame) -> list[str]:
    """Report name collisions that were not used for matching."""
    if "name_key" not in students.columns or "name_key" not in reference.columns:
        return []
    ref_counts = reference.loc[reference["name_key"].astype(str).str.strip().ne(""), "name_key"].value_counts()
    ambiguous = set(ref_counts[ref_counts > 1].index)
    if not ambiguous:
        return []
    hits = students["name_key"].isin(ambiguous)
    n = int(hits.sum())
    if not n:
        return []
    return [
        f"{n} student(s) share a name that is ambiguous in the placement/internship file. "
        "They were not matched by name."
    ]
