"""Academic and Live KT eligibility. Dead KT / Drop / Gap are not applied unless configured."""

from __future__ import annotations

import pandas as pd

from config.settings import DriveRules
from core.removal_logger import RemovalLogger


def _fmt(value) -> str:
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return "missing"
    if isinstance(value, float) and value.is_integer():
        return str(int(value))
    return str(value)


def evaluate_academic(students: pd.DataFrame, rules: DriveRules) -> pd.DataFrame:
    work = students.copy()
    if rules.academic.mode != "threshold":
        work["tenth_status"] = "Open"
        work["twelfth_status"] = "Open"
        work["cgpa_status"] = "Open"
        work["tenth_fail_reason"] = ""
        work["twelfth_fail_reason"] = ""
        work["cgpa_fail_reason"] = ""
        return work

    tenth_need = rules.academic.tenth
    twelfth_need = rules.academic.twelfth
    cgpa_need = rules.academic.cgpa

    tenth = work["tenth_percentage"]
    twelfth = work["twelfth_percentage"]
    cgpa = work["be_cgpa"]

    tenth_missing = tenth.isna()
    twelfth_missing = twelfth.isna()
    cgpa_missing = cgpa.isna()
    tenth_fail = tenth_missing | (tenth < tenth_need)
    twelfth_fail = twelfth_missing | (twelfth < twelfth_need)
    cgpa_fail = cgpa_missing | (cgpa < cgpa_need)

    work["tenth_status"] = tenth_fail.map(lambda x: "Fail" if x else "Pass")
    work["twelfth_status"] = twelfth_fail.map(lambda x: "Fail" if x else "Pass")
    work["cgpa_status"] = cgpa_fail.map(lambda x: "Fail" if x else "Pass")

    work["tenth_fail_reason"] = _fail_reason(
        tenth, tenth_missing, tenth_need, "10th percentage", suffix="%"
    )
    work["twelfth_fail_reason"] = _fail_reason(
        twelfth, twelfth_missing, twelfth_need, "12th/Diploma percentage", suffix="%"
    )
    work["cgpa_fail_reason"] = _fail_reason(
        cgpa, cgpa_missing, cgpa_need, "BTech/BE CGPA", suffix=""
    )
    return work


def _fail_reason(series: pd.Series, missing: pd.Series, need, label: str, suffix: str) -> pd.Series:
    reasons = pd.Series("", index=series.index)
    reasons.loc[missing] = f"{label} missing; required {need}{suffix}"
    below = (~missing) & (series < need)
    reasons.loc[below] = series.loc[below].map(lambda v: f"{label} {_fmt(v)}{suffix} < required {need}{suffix}")
    return reasons


def apply_academic(
    students: pd.DataFrame,
    rules: DriveRules,
    logger: RemovalLogger,
) -> pd.DataFrame:
    work = evaluate_academic(students, rules)
    if rules.academic.mode != "threshold":
        return work

    # Independent thresholds; first failing dimension is the removal category.
    tenth_fail = work["tenth_status"].eq("Fail")
    twelfth_fail = work["twelfth_status"].eq("Fail") & ~tenth_fail
    cgpa_fail = work["cgpa_status"].eq("Fail") & ~tenth_fail & ~twelfth_fail

    for idx in work.index[tenth_fail]:
        row = work.loc[idx]
        logger.log(row, "10th eligibility", row["tenth_fail_reason"])
    for idx in work.index[twelfth_fail]:
        row = work.loc[idx]
        logger.log(row, "12th eligibility", row["twelfth_fail_reason"])
    for idx in work.index[cgpa_fail]:
        row = work.loc[idx]
        logger.log(row, "CGPA eligibility", row["cgpa_fail_reason"])

    failed = tenth_fail | work["twelfth_status"].eq("Fail") | work["cgpa_status"].eq("Fail")
    work.loc[failed, "eligibility_status"] = "Removed"
    work.loc[tenth_fail, "removal_reason"] = work.loc[tenth_fail, "tenth_fail_reason"]
    work.loc[twelfth_fail, "removal_reason"] = work.loc[twelfth_fail, "twelfth_fail_reason"]
    work.loc[cgpa_fail, "removal_reason"] = work.loc[cgpa_fail, "cgpa_fail_reason"]
    return work.loc[~failed].copy()


def apply_live_kt(
    students: pd.DataFrame,
    rules: DriveRules,
    logger: RemovalLogger,
) -> pd.DataFrame:
    work = students.copy()
    if rules.live_kt.allowed:
        work["kt_status"] = work["has_live_kt"].map(lambda x: "Live KT present (allowed)" if x else "No live KT")
        return work

    fail = work["has_live_kt"].astype(bool)
    work["kt_status"] = fail.map(lambda x: "Fail" if x else "Pass")
    for idx in work.index[fail]:
        row = work.loc[idx]
        raw = row.get("live_kt_raw") or "Yes"
        reason = f"Live KT / backlog not allowed (reported: {raw})"
        logger.log(row, "Live KT / backlog", reason)
        work.at[idx, "eligibility_status"] = "Removed"
        work.at[idx, "removal_reason"] = reason
    return work.loc[~fail].copy()
