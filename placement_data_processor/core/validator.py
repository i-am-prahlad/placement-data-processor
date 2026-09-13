"""Pre-processing validation. Fail clearly; never continue silently on missing critical fields."""

from __future__ import annotations

from dataclasses import dataclass, field

import pandas as pd

from core.loader import LoadedInputs
from utils.headers import REQUIRED_PLACEMENT_FIELDS, REQUIRED_RESPONSE_FIELDS, HeaderMapper, HeaderMatchError


@dataclass
class ValidationResult:
    ok: bool
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    detected_columns: dict[str, dict[str, str]] = field(default_factory=dict)
    record_counts: dict[str, int] = field(default_factory=dict)


def _format_header_error(exc: HeaderMatchError) -> str:
    available = ", ".join(exc.available[:20]) if exc.available else "(none)"
    return (
        "Cannot process\n\n"
        f"Missing required column:\n{exc.field}\n\n"
        "Please upload a workbook containing this field.\n\n"
        f"Detected headers: {available}"
    )


def validate_inputs(inputs: LoadedInputs) -> ValidationResult:
    mapper = HeaderMapper()
    errors: list[str] = []
    warnings = list(inputs.warnings)
    detected = {
        "responses": dict(inputs.responses.mapping.detected),
        "placement": dict(inputs.placement.mapping.detected),
    }
    if inputs.internship is not None:
        detected["internship"] = dict(inputs.internship.mapping.detected)

    try:
        mapper.require(inputs.responses.mapping, REQUIRED_RESPONSE_FIELDS, inputs.responses.headers)
    except HeaderMatchError as exc:
        errors.append(_format_header_error(exc))

    try:
        mapper.require(inputs.placement.mapping, REQUIRED_PLACEMENT_FIELDS, inputs.placement.headers)
    except HeaderMatchError as exc:
        errors.append(_format_header_error(exc))

    offer_fields = [f for f in ("offer_1", "offer_2", "offer_3", "offer_4") if f in inputs.placement.mapping.field_to_column]
    if not offer_fields:
        errors.append(
            "Cannot process\n\n"
            "Missing required column:\n1st Offer\n\n"
            "Please upload a Studentwise Placement workbook containing offer columns "
            "(1st Offer, 2nd Offer, 3rd Offer, 4th Offer)."
        )

    responses = inputs.responses.dataframe
    mapping = inputs.responses.mapping.field_to_column
    if "timestamp" in mapping:
        ts = pd.to_datetime(responses[mapping["timestamp"]], errors="coerce")
        if ts.notna().sum() == 0:
            errors.append("Timestamp column was found but no usable timestamps could be parsed for deduplication.")
        elif ts.isna().any():
            warnings.append(
                f"{int(ts.isna().sum())} response row(s) have missing/invalid timestamps. "
                "Those rows cannot use timestamp-based duplicate resolution."
            )

    if "roll_no" in mapping:
        rolls = responses[mapping["roll_no"]].astype(str).str.strip()
        blank = rolls.isin(["", "nan", "None", "NaT"]) | responses[mapping["roll_no"]].isna()
        if blank.all():
            warnings.append(
                "College Roll No. column was found but contains no usable roll numbers. "
                "Placement matching will use only safe email/mobile matches."
            )
        elif blank.any():
            warnings.append(f"{int(blank.sum())} response row(s) have a blank College Roll No.")

    if "email" not in mapping and "email_id" not in mapping:
        warnings.append("No email column was identified. Email-based matching and duplicate checks will be skipped.")
    if "mobile" not in mapping:
        warnings.append("No mobile column was identified. Mobile-based matching and duplicate checks will be skipped.")

    counts = {
        "responses": int(len(responses)),
        "placement": int(len(inputs.placement.dataframe)),
        "internship": int(len(inputs.internship.dataframe)) if inputs.internship is not None else 0,
    }
    return ValidationResult(
        ok=len(errors) == 0,
        errors=errors,
        warnings=warnings,
        detected_columns=detected,
        record_counts=counts,
    )
