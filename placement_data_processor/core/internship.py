"""Internship matching and optional removal. Never remove unless the drive rule says so."""

from __future__ import annotations

import pandas as pd

from config.settings import DriveRules
from core.matcher import match_values
from core.removal_logger import RemovalLogger


def apply_internship(
    students: pd.DataFrame,
    internship: pd.DataFrame | None,
    rules: DriveRules,
    logger: RemovalLogger,
) -> pd.DataFrame:
    work = students.copy()
    if internship is None or internship.empty:
        work["internship"] = False
        work["internship_status"] = "No internship file"
        work["internship_match_method"] = "none"
        return work

    ref = internship.copy()
    if "has_internship" not in ref.columns:
        ref["has_internship"] = True
    flags, methods = match_values(work, ref, "has_internship", default=False)
    work["internship"] = flags.fillna(False).astype(bool)
    work["internship_match_method"] = methods
    work["internship_status"] = work["internship"].map(lambda x: "Has internship" if x else "No internship")

    if not rules.internship.remove:
        return work

    fail = work["internship"].astype(bool)
    for idx in work.index[fail]:
        row = work.loc[idx]
        reason = "Existing internship student removed per drive rule"
        logger.log(row, "Internship", reason)
        work.at[idx, "eligibility_status"] = "Removed"
        work.at[idx, "removal_reason"] = reason
        work.at[idx, "internship_status"] = "Fail"
    return work.loc[~fail].copy()
