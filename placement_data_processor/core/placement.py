"""Offer-count classification and placement eligibility."""

from __future__ import annotations

import pandas as pd

from config.settings import DriveRules
from core.matcher import match_values
from core.removal_logger import RemovalLogger


def classify_offer_count(count: int) -> str:
    if count <= 0:
        return "No offer"
    if count == 1:
        return "Single-placed"
    if count == 2:
        return "Double-placed"
    return "More than 2 offers"


def placement_category(offer_count: int) -> str:
    if offer_count == 1:
        return "Single placed"
    if offer_count == 2:
        return "Double placed"
    return "Placement"


def apply_placement(
    students: pd.DataFrame,
    placement: pd.DataFrame,
    rules: DriveRules,
    logger: RemovalLogger,
) -> tuple[pd.DataFrame, pd.Series]:
    work = students.copy()
    offers, methods = match_values(work, placement, "offer_count", default=0)
    offers = pd.to_numeric(offers, errors="coerce").fillna(0).astype(int)
    work["offer_count"] = offers
    work["placement_match_method"] = methods
    work["placement_class"] = work["offer_count"].map(classify_offer_count)

    max_offers = rules.placement.max_offers
    exceeded = work["offer_count"] > max_offers
    reasons = work.loc[exceeded].apply(
        lambda row: (
            f"{classify_offer_count(int(row['offer_count']))}: "
            f"{int(row['offer_count'])} offer(s) > maximum allowed {max_offers}"
        ),
        axis=1,
    )
    for idx, reason in reasons.items():
        row = work.loc[idx]
        logger.log(row, category=placement_category(int(row["offer_count"])), reason=reason)

    work.loc[exceeded, "eligibility_status"] = "Removed"
    work.loc[exceeded, "removal_reason"] = reasons
    work.loc[exceeded, "placement_status"] = "Fail"
    work.loc[~exceeded, "placement_status"] = "Pass"
    return work.loc[~exceeded].copy(), work["placement_status"]
