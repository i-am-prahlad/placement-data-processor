from io import BytesIO

import pandas as pd

from config.settings import DriveRules


def excel_bytes(rows: list[dict]) -> bytes:
    frame = pd.DataFrame(rows)
    buffer = BytesIO()
    frame.to_excel(buffer, index=False, engine="openpyxl")
    return buffer.getvalue()


def open_rules(**overrides) -> DriveRules:
    base = {
        "placement": {"max_offers": 0},
        "academic": {"mode": "open"},
        "live_kt": {"allowed": True},
        "internship": {"remove": False},
        "output": {"include_job_role": True},
    }
    for key, value in overrides.items():
        if isinstance(value, dict) and key in base:
            base[key].update(value)
        else:
            base[key] = value
    return DriveRules.from_dict(base)


RESPONSE_BASE = {
    "Timestamp": "2026-01-01 10:00:00",
    "Full Name": "ADA LOVELACE",
    "Email address": "ada@college.edu",
    "Mobile No": "9876543210",
    "Gender": "Female",
    "College Name": "RAIT",
    "College Roll No.": "R001",
    "Branch": "CE",
    "Job Role": "SDE",
    "10th Percentage": 90,
    "10th Year of Passing": 2018,
    "12th/Diploma?": "12th",
    "12th/Diploma Percentage": 88,
    "12th/Diploma Year of Passing": 2020,
    "BTech CGPA": 9.1,
    "BTech Percentage": 85,
    "Live KT": "No",
    "Resume": "https://example.com/ada.pdf",
}


def response(**overrides) -> dict:
    row = dict(RESPONSE_BASE)
    row.update(overrides)
    return row


def placement_row(roll: str, offers: list[str] | None = None, **extra) -> dict:
    offers = offers or []
    padded = (offers + ["", "", "", ""])[:4]
    row = {
        "College Roll No.": roll,
        "1st Offer": padded[0],
        "2nd Offer": padded[1],
        "3rd Offer": padded[2],
        "4th Offer": padded[3],
        "Email address": extra.pop("email", ""),
        "Mobile No": extra.pop("mobile", ""),
        "Full Name": extra.pop("name", ""),
    }
    row.update(extra)
    return row
