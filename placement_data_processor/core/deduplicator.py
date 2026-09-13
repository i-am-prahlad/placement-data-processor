"""Duplicate response handling. Primary key is College Roll No.; keep the latest timestamp."""

from __future__ import annotations

import pandas as pd

from core.removal_logger import RemovalLogger


def _sort_latest_first(df: pd.DataFrame) -> pd.DataFrame:
    ordered = df.copy()
    ordered["_ts_rank"] = ordered["timestamp"]
    # Missing timestamps sort last so a dated submission wins when possible.
    return ordered.sort_values(by=["_ts_rank", "row_id"], ascending=[False, False], na_position="last")


def _reason_earlier(kept: pd.Series, removed: pd.Series) -> str:
    kept_ts = kept["timestamp"]
    removed_ts = removed["timestamp"]
    kept_label = "unknown time" if pd.isna(kept_ts) else str(kept_ts)
    removed_label = "unknown time" if pd.isna(removed_ts) else str(removed_ts)
    return (
        f"Earlier submission removed; latest response kept "
        f"(removed timestamp: {removed_label}; kept timestamp: {kept_label})"
    )


def _drop_group_keep_latest(
    df: pd.DataFrame,
    key: str,
    logger: RemovalLogger,
    reason_prefix: str,
) -> pd.DataFrame:
    usable = df[key].notna() & (df[key].astype(str).str.strip() != "") & (df[key].astype(str) != "None")
    if key == "mobile":
        usable = df[key].notna()
    working = df.loc[usable].copy()
    if working.empty:
        return df

    working = _sort_latest_first(working)
    duplicate_keys = working[working.duplicated(subset=[key], keep=False)][key].unique()
    if len(duplicate_keys) == 0:
        return df

    keep_ids = set(working.drop_duplicates(subset=[key], keep="first")["row_id"].tolist())
    remove_mask = working[key].isin(duplicate_keys) & ~working["row_id"].isin(keep_ids)
    removed = working.loc[remove_mask]
    for kid in working.loc[working[key].isin(duplicate_keys) & working["row_id"].isin(keep_ids), "row_id"]:
        logger.mark_kept_duplicate(int(kid))
    kept_by_key = working.drop_duplicates(subset=[key], keep="first").set_index(key)

    for _, row in removed.iterrows():
        kept = kept_by_key.loc[row[key]]
        if isinstance(kept, pd.DataFrame):
            kept = kept.iloc[0]
        logger.log(
            row,
            category="Duplicate",
            reason=f"{reason_prefix}. {_reason_earlier(kept, row)}",
        )
    return df.loc[~df["row_id"].isin(set(removed["row_id"].tolist()))].copy()


def flag_name_collisions(df: pd.DataFrame) -> tuple[pd.DataFrame, list[str]]:
    """Name-only matches are flagged, never auto-removed."""
    warnings: list[str] = []
    out = df.copy()
    if "duplicate_status" not in out.columns:
        out["duplicate_status"] = "Unique"
    usable = out["name_key"].astype(str).str.strip() != ""
    counts = out.loc[usable, "name_key"].value_counts()
    collided = set(counts[counts > 1].index)
    if not collided:
        return out, warnings
    mask = out["name_key"].isin(collided)
    # Only flag when roll numbers differ — same student already handled by roll/email/mobile.
    different_rolls = out.loc[mask].groupby("name_key")["roll_no"].nunique()
    ambiguous_names = set(different_rolls[different_rolls > 1].index)
    flag_mask = out["name_key"].isin(ambiguous_names)
    out.loc[flag_mask, "duplicate_status"] = "Name match flagged for review"
    n = int(flag_mask.sum())
    unique_names = len(ambiguous_names)
    if n:
        warnings.append(
            f"{unique_names} student name(s) appear more than once with different roll numbers "
            f"({n} row(s) flagged for review). Name-only matches were not treated as duplicates."
        )
    return out, warnings


def deduplicate(students: pd.DataFrame, logger: RemovalLogger) -> tuple[pd.DataFrame, list[str]]:
    work = students.copy()
    work["duplicate_status"] = "Unique"
    original_ids = set(work["row_id"].tolist())

    work = _drop_group_keep_latest(work, "roll_no", logger, "Duplicate College Roll No.")
    work = _drop_group_keep_latest(work, "email", logger, "Duplicate email after roll-number deduplication")
    work = _drop_group_keep_latest(work, "mobile", logger, "Duplicate mobile number after roll-number deduplication")

    removed_ids = original_ids - set(work["row_id"].tolist())
    work.loc[~work["row_id"].isin(removed_ids), "duplicate_status"] = work["duplicate_status"].where(
        work["duplicate_status"] != "Unique", "Unique"
    )

    work, warnings = flag_name_collisions(work)

    survivors_from_dup_groups = logger.duplicate_kept_hint()
    if survivors_from_dup_groups:
        work.loc[work["row_id"].isin(survivors_from_dup_groups), "duplicate_status"] = work.loc[
            work["row_id"].isin(survivors_from_dup_groups), "duplicate_status"
        ].where(
            work.loc[work["row_id"].isin(survivors_from_dup_groups), "duplicate_status"] == "Name match flagged for review",
            "Kept latest of duplicates",
        )
    return work.reset_index(drop=True), warnings
