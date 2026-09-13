"""Exact output worksheet schemas. Column order is part of the contract."""

RAIT_COLUMNS: list[str] = [
    "Sr No",
    "College Roll No.",
    "Name",
    "Email Address",
    "Mobile Number",
    "Gender",
    "Branch",
    "College Name",
    "Job Role",
    "10th Percentage",
    "10th Year of Passing",
    "12th/Diploma?",
    "12th/Diploma Percentage",
    "12th Year of Passing",
    "BE CGPA",
    "BE Percentage",
    "MTech CGPA",
    "MTech Percentage",
    "MTech Year of Passing",
    "Resume",
]

REMOVE_COLUMNS: list[str] = list(RAIT_COLUMNS)

REMOVE_SECTIONS: list[str] = [
    "Placed Student",
    "Internship Students",
    "Removed due to 10th Percentage",
    "Removed due to 12th Percentage",
    "Removed due to BE CGPA",
    "Removed due to KT",
]

AUDIT_COLUMNS: list[str] = [
    "Name",
    "College Roll No.",
    "Initial Status",
    "Duplicate Status",
    "Offer Count",
    "Placement Status",
    "10th Status",
    "12th Status",
    "CGPA Status",
    "KT Status",
    "Internship Status",
    "Final Status",
    "Final Reason",
]

RUN_INFO_FIELDS: list[str] = [
    "Processing Date",
    "Input Response Count",
    "Duplicate Count",
    "Placement Removals",
    "Academic Removals",
    "KT Removals",
    "Internship Removals",
    "Final Eligible Count",
]

REMOVAL_CATEGORIES = (
    "Duplicate",
    "Single placed",
    "Double placed",
    "Placement",
    "10th eligibility",
    "12th eligibility",
    "CGPA eligibility",
    "Live KT / backlog",
    "Internship",
    "Other",
)
