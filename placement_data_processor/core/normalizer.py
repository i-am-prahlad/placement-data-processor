"""Convert raw workbooks into the canonical student DataFrame."""

from __future__ import annotations

import math
import re
from typing import Any

import pandas as pd

from core.loader import LoadedWorkbook
from utils.headers import HeaderMapping
from utils.names import to_proper_case
from utils.phones import format_mobile_text, normalize_mobile

CANONICAL_COLUMNS = [
    "row_id",
    "timestamp",
    "roll_no",
    "name",
    "name_key",
    "email",
    "raw_mobile",
    "mobile",
    "mobile_flag",
    "gender",
    "branch",
    "college",
    "job_role",
    "degree",
    "tenth_percentage",
    "tenth_year",
    "twelfth_or_diploma",
    "twelfth_percentage",
    "twelfth_year",
    "be_cgpa",
    "be_percentage",
    "btech_year",
    "live_kt_raw",
    "has_live_kt",
    "dead_kt",
    "drop",
    "gap",
    "resume",
    "mtech_cgpa",
    "mtech_percentage",
    "mtech_year",
    "offer_count",
    "internship",
    "eligibility_status",
    "removal_reason",
]


def _blank(value: Any) -> bool:
    if value is None:
        return True
    if isinstance(value, float) and (math.isnan(value) or math.isinf(value)):
        return True
    text = str(value).strip()
    return text == "" or text.lower() in {"nan", "none", "nat", "-"}


def _as_text(value: Any) -> str:
    if _blank(value):
        return ""
    if isinstance(value, float) and value.is_integer():
        return str(int(value))
    if isinstance(value, int):
        return str(value)
    return str(value).strip()


def normalize_roll(value: Any) -> str:
    text = _as_text(value)
    if not text:
        return ""
    if re.fullmatch(r"\d+\.0", text):
        text = text[:-2]
    return text.strip().upper()


def parse_percentage(value: Any) -> float | None:
    if _blank(value):
        return None
    text = str(value).strip().replace(",", "")
    text = text.replace("%", "")
    try:
        number = float(text)
    except ValueError:
        return None
    if math.isnan(number) or math.isinf(number):
        return None
    if 0 <= number <= 1:
        return round(number * 100, 4)
    if 0 <= number <= 100:
        return number
    return None


def parse_cgpa(value: Any) -> float | None:
    if _blank(value):
        return None
    text = str(value).strip().replace(",", "")
    text = text.replace("%", "")
    try:
        number = float(text)
    except ValueError:
        return None
    if math.isnan(number) or math.isinf(number):
        return None
    if 0 <= number <= 10:
        return number
    return None


def parse_year(value: Any) -> str:
    text = _as_text(value)
    if re.fullmatch(r"\d+\.0", text):
        text = text[:-2]
    return text


def has_live_kt(value: Any) -> bool:
    if _blank(value):
        return False
    text = str(value).strip().lower()
    if text in {"no", "n", "none", "0", "0.0", "false", "nil", "na", "n/a", "not applicable"}:
        return False
    if text in {"yes", "y", "true"}:
        return True
    try:
        return float(text) > 0
    except ValueError:
        return True


def parse_timestamp(series: pd.Series) -> pd.Series:
    return pd.to_datetime(series, errors="coerce")


def _series_from_mapping(df: pd.DataFrame, mapping: HeaderMapping, field: str) -> pd.Series:
    column = mapping.field_to_column.get(field)
    if column is None:
        return pd.Series([None] * len(df), index=df.index)
    return df[column]


def normalize_responses(workbook: LoadedWorkbook) -> pd.DataFrame:
    df = workbook.dataframe
    mapping = workbook.mapping

    email = _series_from_mapping(df, mapping, "email")
    if "email" not in mapping.field_to_column:
        email = _series_from_mapping(df, mapping, "email_id")

    raw_mobile = _series_from_mapping(df, mapping, "mobile").map(format_mobile_text)
    mobiles = _series_from_mapping(df, mapping, "mobile").map(lambda v: normalize_mobile(v))
    mobile_values = mobiles.map(lambda pair: pair[0])
    mobile_flags = mobiles.map(lambda pair: pair[1])

    names = _series_from_mapping(df, mapping, "name").map(_as_text)
    out = pd.DataFrame({
        "row_id": range(len(df)),
        "timestamp": parse_timestamp(_series_from_mapping(df, mapping, "timestamp")),
        "roll_no": _series_from_mapping(df, mapping, "roll_no").map(normalize_roll),
        "name": names.map(to_proper_case),
        "name_key": names.map(lambda v: " ".join(_as_text(v).lower().split())),
        "email": email.map(lambda v: _as_text(v).lower()),
        "raw_mobile": raw_mobile,
        "mobile": mobile_values,
        "mobile_flag": mobile_flags,
        "gender": _series_from_mapping(df, mapping, "gender").map(_as_text),
        "branch": _series_from_mapping(df, mapping, "branch").map(_as_text),
        "college": _series_from_mapping(df, mapping, "college").map(_as_text),
        "job_role": _series_from_mapping(df, mapping, "job_role").map(_as_text),
        "degree": _series_from_mapping(df, mapping, "degree").map(_as_text),
        "tenth_percentage": _series_from_mapping(df, mapping, "tenth_percentage").map(parse_percentage),
        "tenth_year": _series_from_mapping(df, mapping, "tenth_year").map(parse_year),
        "twelfth_or_diploma": _series_from_mapping(df, mapping, "twelfth_or_diploma").map(_as_text),
        "twelfth_percentage": _series_from_mapping(df, mapping, "twelfth_percentage").map(parse_percentage),
        "twelfth_year": _series_from_mapping(df, mapping, "twelfth_year").map(parse_year),
        "be_cgpa": _series_from_mapping(df, mapping, "be_cgpa").map(parse_cgpa),
        "be_percentage": _series_from_mapping(df, mapping, "be_percentage").map(parse_percentage),
        "btech_year": _series_from_mapping(df, mapping, "btech_year").map(parse_year),
        "live_kt_raw": _series_from_mapping(df, mapping, "live_kt").map(_as_text),
        "has_live_kt": _series_from_mapping(df, mapping, "live_kt").map(has_live_kt),
        "dead_kt": _series_from_mapping(df, mapping, "dead_kt").map(_as_text),
        "drop": _series_from_mapping(df, mapping, "drop").map(_as_text),
        "gap": _series_from_mapping(df, mapping, "gap").map(_as_text),
        "resume": _series_from_mapping(df, mapping, "resume").map(_as_text),
        "mtech_cgpa": _series_from_mapping(df, mapping, "mtech_cgpa").map(parse_cgpa),
        "mtech_percentage": _series_from_mapping(df, mapping, "mtech_percentage").map(parse_percentage),
        "mtech_year": _series_from_mapping(df, mapping, "mtech_year").map(parse_year),
        "offer_count": 0,
        "internship": False,
        "eligibility_status": "Pending",
        "removal_reason": "",
    })
    return out


def offer_present(value: Any) -> bool:
    if _blank(value):
        return False
    text = str(value).strip().lower()
    return text not in {"no", "n", "none", "na", "n/a", "not placed", "nil", "0", "-"}


def normalize_placement(workbook: LoadedWorkbook) -> pd.DataFrame:
    df = workbook.dataframe
    mapping = workbook.mapping
    out = pd.DataFrame({
        "roll_no": _series_from_mapping(df, mapping, "roll_no").map(normalize_roll),
        "email": (_series_from_mapping(df, mapping, "email") if "email" in mapping.field_to_column else pd.Series([""] * len(df))).map(lambda v: _as_text(v).lower()),
        "mobile": _series_from_mapping(df, mapping, "mobile").map(lambda v: normalize_mobile(v)[0] if not _blank(v) else None)
        if "mobile" in mapping.field_to_column
        else pd.Series([None] * len(df)),
        "name_key": _series_from_mapping(df, mapping, "name").map(lambda v: " ".join(_as_text(v).lower().split()))
        if "name" in mapping.field_to_column
        else pd.Series([""] * len(df)),
        "offer_1": _series_from_mapping(df, mapping, "offer_1"),
        "offer_2": _series_from_mapping(df, mapping, "offer_2"),
        "offer_3": _series_from_mapping(df, mapping, "offer_3"),
        "offer_4": _series_from_mapping(df, mapping, "offer_4"),
    })
    out["offer_count"] = (
        out["offer_1"].map(offer_present).astype(int)
        + out["offer_2"].map(offer_present).astype(int)
        + out["offer_3"].map(offer_present).astype(int)
        + out["offer_4"].map(offer_present).astype(int)
    )

    def _extract_companies(row) -> str:
        companies = [
            str(row[col]).strip()
            for col in ["offer_1", "offer_2", "offer_3", "offer_4"]
            if offer_present(row[col])
        ]
        return ", ".join(companies)

    out["placement_companies"] = out.apply(_extract_companies, axis=1)
    return out


def normalize_internship(workbook: LoadedWorkbook) -> pd.DataFrame:
    df = workbook.dataframe
    mapping = workbook.mapping
    intern_flag = pd.Series([True] * len(df))
    if "internship" in mapping.field_to_column:
        intern_flag = df[mapping.field_to_column["internship"]].map(
            lambda v: False if _blank(v) else str(v).strip().lower() not in {"no", "n", "none", "0", "false", "na", "n/a"}
        )

    # If internship offers exist (like 1st Offer..4th Offer or internship column text), extract company name
    def _extract_intern_company(idx) -> str:
        row = df.iloc[idx]
        companies = []
        for col_name in ["offer_1", "offer_2", "offer_3", "offer_4"]:
            if col_name in mapping.field_to_column:
                val = row.get(mapping.field_to_column[col_name])
                if offer_present(val):
                    companies.append(str(val).strip())
        if not companies and "internship" in mapping.field_to_column:
            val = row.get(mapping.field_to_column["internship"])
            if not _blank(val) and str(val).strip().lower() not in {"yes", "y", "true"}:
                companies.append(str(val).strip())
        return ", ".join(companies)

    companies_series = pd.Series([_extract_intern_company(i) for i in range(len(df))])

    return pd.DataFrame({
        "roll_no": _series_from_mapping(df, mapping, "roll_no").map(normalize_roll)
        if "roll_no" in mapping.field_to_column
        else pd.Series([""] * len(df)),
        "email": _series_from_mapping(df, mapping, "email").map(lambda v: _as_text(v).lower())
        if "email" in mapping.field_to_column
        else pd.Series([""] * len(df)),
        "mobile": _series_from_mapping(df, mapping, "mobile").map(lambda v: normalize_mobile(v)[0] if not _blank(v) else None)
        if "mobile" in mapping.field_to_column
        else pd.Series([None] * len(df)),
        "has_internship": intern_flag,
        "internship_company": companies_series,
    })
