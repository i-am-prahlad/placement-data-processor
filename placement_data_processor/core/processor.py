"""Pipeline orchestration. UI must call this module; do not put business rules in Streamlit."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, BinaryIO

import pandas as pd

from config.settings import DriveRules
from core.deduplicator import deduplicate
from core.eligibility import evaluate_academic
from core.internship import apply_internship
from core.loader import LoadedInputs, load_inputs
from core.matcher import ambiguous_name_matches, match_values
from core.normalizer import normalize_internship, normalize_placement, normalize_responses
from core.placement import classify_offer_count, placement_category
from core.removal_logger import RemovalLogger
from core.validator import ValidationResult, validate_inputs
from utils.logging import get_logger

logger = get_logger(__name__)


@dataclass
class ProcessSummary:
    processing_date: str
    input_response_count: int
    duplicate_count: int
    placement_removals: int
    academic_removals: int
    kt_removals: int
    internship_removals: int
    final_eligible_count: int

    def as_display_lines(self) -> list[str]:
        return [
            f"Total responses: {self.input_response_count:,}",
            f"Duplicates removed: {self.duplicate_count:,}",
            f"Placement removals: {self.placement_removals:,}",
            f"Academic removals: {self.academic_removals:,}",
            f"KT removals: {self.kt_removals:,}",
            f"Internship removals: {self.internship_removals:,}",
            "",
            f"Final eligible: {self.final_eligible_count:,}",
        ]

    def as_run_info(self) -> dict[str, Any]:
        return {
            "Processing Date": self.processing_date,
            "Input Response Count": self.input_response_count,
            "Duplicate Count": self.duplicate_count,
            "Placement Removals": self.placement_removals,
            "Academic Removals": self.academic_removals,
            "KT Removals": self.kt_removals,
            "Internship Removals": self.internship_removals,
            "Final Eligible Count": self.final_eligible_count,
        }


@dataclass
class ProcessResult:
    eligible: pd.DataFrame
    removals: pd.DataFrame
    audit: pd.DataFrame
    summary: ProcessSummary
    warnings: list[str] = field(default_factory=list)
    rules: DriveRules | None = None
    removal_logger: RemovalLogger | None = None


def run_pipeline(inputs: LoadedInputs, rules: DriveRules) -> ProcessResult:
    rule_errors = rules.validate()
    if rule_errors:
        raise ValueError("Invalid drive configuration: " + "; ".join(rule_errors))

    all_responses = normalize_responses(inputs.responses)
    placement = normalize_placement(inputs.placement)
    internship_df = normalize_internship(inputs.internship) if inputs.internship is not None else None
    input_count = len(all_responses)
    warnings: list[str] = list(inputs.warnings)

    removal_log = RemovalLogger()
    remaining, dup_warnings = deduplicate(all_responses, removal_log)
    warnings.extend(dup_warnings)
    duplicate_ids = {row["row_id"] for row in removal_log.rows if row.get("row_id") is not None}

    offers, methods = match_values(remaining, placement, "offer_count", default=0)
    placement_comps, _ = match_values(remaining, placement, "placement_companies", default="")
    remaining = remaining.copy()
    remaining["offer_count"] = pd.to_numeric(offers, errors="coerce").fillna(0).astype(int)
    remaining["placement_companies"] = placement_comps.fillna("").astype(str)
    remaining["placement_match_method"] = methods
    remaining["placement_class"] = remaining["offer_count"].map(classify_offer_count)

    remaining = evaluate_academic(remaining, rules)
    remaining = apply_internship(
        remaining,
        internship_df,
        DriveRules.from_dict({"internship": {"remove": False}}),
        RemovalLogger(),
    )
    if internship_df is not None and "internship_company" in internship_df.columns:
        intern_comps, _ = match_values(remaining, internship_df, "internship_company", default="")
        remaining["internship_company"] = intern_comps.fillna("").astype(str)
    else:
        remaining["internship_company"] = ""

    warnings.extend(ambiguous_name_matches(remaining, placement))

    if rules.live_kt.allowed:
        remaining["kt_status"] = remaining["has_live_kt"].map(
            lambda x: "Live KT present (allowed)" if x else "No live KT"
        )
    else:
        remaining["kt_status"] = remaining["has_live_kt"].map(lambda x: "Fail" if x else "Pass")

    max_offers = rules.placement.max_offers
    remaining["placement_status"] = remaining["offer_count"].map(
        lambda n: "Fail" if int(n) > max_offers else "Pass"
    )

    first_fail_category = pd.Series("", index=remaining.index)
    first_fail_reason = pd.Series("", index=remaining.index)

    place_fail = remaining["placement_status"].eq("Fail")
    first_fail_category = first_fail_category.mask(
        place_fail, remaining["offer_count"].map(lambda n: placement_category(int(n)))
    )
    first_fail_reason = first_fail_reason.mask(
        place_fail,
        remaining["offer_count"].map(
            lambda n: f"{classify_offer_count(int(n))}: {int(n)} offer(s) > maximum allowed {max_offers}"
        ),
    )

    if rules.academic.mode == "threshold":
        tenth_fail = remaining["tenth_status"].eq("Fail") & first_fail_category.eq("")
        twelfth_fail = remaining["twelfth_status"].eq("Fail") & first_fail_category.eq("")
        twelfth_fail = twelfth_fail & remaining["tenth_status"].ne("Fail")
        cgpa_fail = (
            remaining["cgpa_status"].eq("Fail")
            & first_fail_category.eq("")
            & remaining["tenth_status"].ne("Fail")
            & remaining["twelfth_status"].ne("Fail")
        )
        first_fail_category = first_fail_category.mask(tenth_fail, "10th eligibility")
        first_fail_reason = first_fail_reason.mask(tenth_fail, remaining["tenth_fail_reason"])
        first_fail_category = first_fail_category.mask(twelfth_fail, "12th eligibility")
        first_fail_reason = first_fail_reason.mask(twelfth_fail, remaining["twelfth_fail_reason"])
        first_fail_category = first_fail_category.mask(cgpa_fail, "CGPA eligibility")
        first_fail_reason = first_fail_reason.mask(cgpa_fail, remaining["cgpa_fail_reason"])

    if not rules.live_kt.allowed:
        kt_fail = remaining["has_live_kt"].astype(bool) & first_fail_category.eq("")
        first_fail_category = first_fail_category.mask(kt_fail, "Live KT / backlog")
        first_fail_reason = first_fail_reason.mask(
            kt_fail,
            remaining["live_kt_raw"].map(
                lambda raw: f"Live KT / backlog not allowed (reported: {raw or 'Yes'})"
            ),
        )

    if rules.internship.remove:
        intern_fail = remaining["internship"].astype(bool) & first_fail_category.eq("")
        first_fail_category = first_fail_category.mask(intern_fail, "Internship")
        first_fail_reason = first_fail_reason.mask(
            intern_fail, "Existing internship student removed per drive rule"
        )

    remaining["first_fail_category"] = first_fail_category
    remaining["first_fail_reason"] = first_fail_reason
    remaining["final_status"] = remaining["first_fail_category"].map(lambda c: "Removed" if c else "Eligible")
    remaining["final_reason"] = remaining["first_fail_reason"]
    remaining["eligibility_status"] = remaining["final_status"]
    remaining.loc[remaining["final_status"].eq("Removed"), "removal_reason"] = remaining["first_fail_reason"]

    for _, row in remaining.loc[remaining["final_status"].eq("Removed")].iterrows():
        removal_log.log(row, category=row["first_fail_category"], reason=row["first_fail_reason"])

    eligible = remaining.loc[remaining["final_status"].eq("Eligible")].copy()
    eligible = eligible.sort_values(by=["name", "roll_no"], kind="mergesort")

    counts = removal_log.counts_by_category()
    placement_removals = (
        counts.get("Single placed", 0) + counts.get("Double placed", 0) + counts.get("Placement", 0)
    )
    academic_removals = (
        counts.get("10th eligibility", 0)
        + counts.get("12th eligibility", 0)
        + counts.get("CGPA eligibility", 0)
    )

    summary = ProcessSummary(
        processing_date=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        input_response_count=input_count,
        duplicate_count=int(counts.get("Duplicate", 0)),
        placement_removals=int(placement_removals),
        academic_removals=int(academic_removals),
        kt_removals=int(counts.get("Live KT / backlog", 0)),
        internship_removals=int(counts.get("Internship", 0)),
        final_eligible_count=int(len(eligible)),
    )

    audit = _build_audit(all_responses, remaining, duplicate_ids, removal_log)
    logger.info("Processing complete. Eligible count logged without student identifiers.")
    return ProcessResult(
        eligible=eligible,
        removals=removal_log.to_dataframe(),
        audit=audit,
        summary=summary,
        warnings=warnings,
        rules=rules,
        removal_logger=removal_log,
    )


def _build_audit(
    all_responses: pd.DataFrame,
    remaining: pd.DataFrame,
    duplicate_ids: set,
    removal_log: RemovalLogger,
) -> pd.DataFrame:
    dup_reasons = {
        row["row_id"]: row["Removal Reason"]
        for row in removal_log.rows
        if row.get("Removal Category") == "Duplicate"
    }
    remaining_idx = remaining.set_index("row_id")
    rows = []
    for _, src in all_responses.iterrows():
        rid = src["row_id"]
        if rid in duplicate_ids:
            rows.append(
                {
                    "Name": src.get("name", ""),
                    "College Roll No.": src.get("roll_no", ""),
                    "Initial Status": "Submitted",
                    "Duplicate Status": "Removed as duplicate",
                    "Offer Count": "",
                    "Placement Status": "Not evaluated",
                    "10th Status": "Not evaluated",
                    "12th Status": "Not evaluated",
                    "CGPA Status": "Not evaluated",
                    "KT Status": "Not evaluated",
                    "Internship Status": "Not evaluated",
                    "Final Status": "Removed",
                    "Final Reason": dup_reasons.get(rid, "Duplicate"),
                }
            )
            continue
        rec = remaining_idx.loc[rid]
        if isinstance(rec, pd.DataFrame):
            rec = rec.iloc[0]
        rows.append(
            {
                "Name": rec.get("name", ""),
                "College Roll No.": rec.get("roll_no", ""),
                "Initial Status": "Submitted",
                "Duplicate Status": rec.get("duplicate_status", "Unique"),
                "Offer Count": rec.get("offer_count", 0),
                "Placement Status": rec.get("placement_status", ""),
                "10th Status": rec.get("tenth_status", ""),
                "12th Status": rec.get("twelfth_status", ""),
                "CGPA Status": rec.get("cgpa_status", ""),
                "KT Status": rec.get("kt_status", ""),
                "Internship Status": rec.get("internship_status", ""),
                "Final Status": rec.get("final_status", ""),
                "Final Reason": rec.get("final_reason", "") or "",
            }
        )
    return pd.DataFrame(rows)


def process(
    responses: bytes | BinaryIO | str,
    placement: bytes | BinaryIO | str,
    rules: DriveRules,
    internship: bytes | BinaryIO | str | None = None,
) -> tuple[ValidationResult, ProcessResult | None]:
    inputs = load_inputs(responses, placement, internship)
    validation = validate_inputs(inputs)
    if not validation.ok:
        return validation, None
    return validation, run_pipeline(inputs, rules)
