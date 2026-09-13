"""Header detection by name, never by column position."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable


class HeaderMatchError(Exception):
    """A required field could not be identified from workbook headers."""

    def __init__(self, field: str, aliases: list[str], available: list[str]):
        self.field = field
        self.aliases = aliases
        self.available = available
        super().__init__(f"Missing required column: {field}")


def normalize_header(value: str) -> str:
    text = str(value or "").strip().lower()
    text = text.replace("\n", " ").replace("\r", " ")
    for ch in [".", ",", ":", ";", "/", "\\", "(", ")", "[", "]", "_", "-"]:
        text = text.replace(ch, " ")
    return " ".join(text.split())


# Canonical field -> accepted header variants (already conceptually normalized).
FIELD_ALIASES: dict[str, tuple[str, ...]] = {
    "timestamp": (
        "timestamp",
        "time stamp",
        "submission time",
        "submitted at",
        "response timestamp",
    ),
    "email": (
        "email address",
        "email",
        "email id",
        "emailid",
        "e mail",
        "student email",
        "mail id",
        "mail",
    ),
    "email_id": (
        "email id",
        "emailid",
        "email address",
        "email",
    ),
    "name": (
        "full name",
        "name",
        "student name",
        "candidate name",
        "student full name",
        "name of student",
    ),
    "mobile": (
        "candidate mobile number",
        "candidate mobile no",
        "candidate mobile",
        "student mobile number",
        "student mobile no",
        "mobile no",
        "mobile number",
        "mobile",
        "phone",
        "phone no",
        "phone number",
        "candidate phone number",
        "contact no",
        "contact number",
        "candidate contact number",
        "whatsapp no",
        "whatsapp number",
        "contact",
    ),
    "gender": ("gender", "sex"),
    "college": (
        "college name",
        "college",
        "institute",
        "institute name",
        "institution",
        "university",
        "college college name",
    ),
    "roll_no": (
        "college roll no",
        "college roll number",
        "college roll",
        "roll no",
        "roll number",
        "rollno",
        "university roll no",
        "prn",
        "prn no",
        "prn number",
        "registration no",
        "registration number",
    ),
    "branch": (
        "graduation branch",
        "btech branch",
        "be branch",
        "branch",
        "branch name",
        "department",
        "stream",
        "programme",
        "program",
    ),

    "major_minor": (
        "btech major minor subject",
        "major minor",
        "major minor subject",
        "btech major minor",
    ),
    "job_role": (
        "job role",
        "role",
        "position",
        "profile",
        "applied role",
        "job profile",
    ),
    "degree": ("degree", "qualification", "course"),
    "tenth_percentage": (
        "10th percentage",
        "10th percent",
        "10th %",
        "tenth percentage",
        "ssc percentage",
        "10th marks",
        "class 10 percentage",
        "x percentage",
    ),
    "tenth_year": (
        "10th year of passing",
        "10th yr of passing",
        "10th yop",
        "tenth year of passing",
        "10th year",
        "ssc year",
        "class 10 year",
    ),
    "twelfth_or_diploma": (
        "12th diploma",
        "12th diploma?",
        "12th or diploma",
        "12th diploma ?",
        "hsc diploma",
    ),
    "twelfth_percentage": (
        "12th diploma percentage",
        "12th percentage",
        "diploma percentage",
        "hsc percentage",
        "12th percent",
        "class 12 percentage",
        "xii percentage",
    ),
    "twelfth_year": (
        "12th diploma year of passing",
        "12th year of passing",
        "12th year",
        "diploma year of passing",
        "hsc year",
        "12th yop",
    ),
    "be_cgpa": (
        "btech cgpa",
        "be cgpa",
        "b e cgpa",
        "cgpa",
        "btech be cgpa",
        "ug cgpa",
        "aggregate cgpa",
        "current cgpa",
    ),
    "be_percentage": (
        "btech percentage",
        "be percentage",
        "b e percentage",
        "ug percentage",
        "engineering percentage",
    ),
    "btech_year": (
        "btech year of passing",
        "be year of passing",
        "year of passing",
        "graduation year",
        "btech yop",
    ),
    "live_kt": (
        "live kt",
        "live kts",
        "live backlog",
        "active backlog",
        "active kt",
        "current kt",
        "live backlogs",
    ),
    "dead_kt": ("dead kt", "dead kts", "dead backlog", "cleared backlog"),
    "drop": ("drop", "drops", "year drop"),
    "gap": ("gap", "gaps", "gap year", "education gap"),
    "placed": (
        "are you placed",
        "are you placed?",
        "placed",
        "placement status",
    ),
    "company_1": ("company 1 name", "company 1", "first company"),
    "company_2": ("company 2 name", "company 2", "second company"),
    "resume": (
        "resume",
        "resume link",
        "resume url",
        "cv",
        "cv link",
        "resume drive link",
    ),
    "acknowledgement": (
        "statement of acknowledgement",
        "acknowledgement",
        "acknowledgment",
    ),
    "offer_1": (
        "1st offer",
        "first offer",
        "offer 1",
        "offer1",
        "company 1",
        "placed company 1",
    ),
    "offer_2": (
        "2nd offer",
        "second offer",
        "offer 2",
        "offer2",
        "company 2",
        "placed company 2",
    ),
    "offer_3": (
        "3rd offer",
        "third offer",
        "offer 3",
        "offer3",
        "company 3",
    ),
    "offer_4": (
        "4th offer",
        "fourth offer",
        "offer 4",
        "offer4",
        "company 4",
    ),
    "mtech_cgpa": ("mtech cgpa", "m tech cgpa", "me cgpa", "pg cgpa"),
    "mtech_percentage": (
        "mtech percentage",
        "m tech percentage",
        "me percentage",
        "pg percentage",
    ),
    "mtech_year": (
        "mtech year of passing",
        "m tech year of passing",
        "mtech yop",
        "pg year of passing",
    ),
    "internship": (
        "internship",
        "internship status",
        "has internship",
        "intern",
        "current internship",
        "internship company",
    ),
}

REQUIRED_RESPONSE_FIELDS = ("timestamp", "name", "roll_no")
REQUIRED_PLACEMENT_FIELDS = ("roll_no",)


@dataclass
class HeaderMapping:
    field_to_column: dict[str, str]
    unmatched: list[str]
    detected: dict[str, str]


class HeaderMapper:
    def __init__(self, aliases: dict[str, tuple[str, ...]] | None = None):
        self.aliases = aliases or FIELD_ALIASES

    def map_headers(self, headers: Iterable[str]) -> HeaderMapping:
        original = [str(h) for h in headers if str(h).strip() != ""]
        normalized_to_original: dict[str, str] = {}
        for header in original:
            key = normalize_header(header)
            if key and key not in normalized_to_original:
                normalized_to_original[key] = header

        used_columns: set[str] = set()
        field_to_column: dict[str, str] = {}

        for field, variants in self.aliases.items():
            match = self._best_match(variants, normalized_to_original, used_columns)
            if match:
                field_to_column[field] = match
                used_columns.add(match)

        unmatched = [h for h in original if h not in field_to_column.values()]
        detected = dict(field_to_column)
        return HeaderMapping(
            field_to_column=field_to_column,
            unmatched=unmatched,
            detected=detected,
        )

    def require(
        self,
        mapping: HeaderMapping,
        fields: Iterable[str],
        available_headers: Iterable[str],
    ) -> None:
        available = [str(h) for h in available_headers]
        for field in fields:
            if field not in mapping.field_to_column:
                aliases = [a for a in self.aliases.get(field, (field,))]
                raise HeaderMatchError(field=_display_name(field), aliases=aliases, available=available)

    @staticmethod
    def _best_match(
        variants: tuple[str, ...],
        normalized_to_original: dict[str, str],
        used_columns: set[str],
    ) -> str | None:
        # Prefer earlier, more specific aliases. Never fuzzy-guess unknown headers.
        for variant in variants:
            target = normalize_header(variant)
            column = normalized_to_original.get(target)
            if column and column not in used_columns:
                return column
        # Token-set equality: "College Roll No." vs "college roll no"
        variant_sets = [frozenset(normalize_header(v).split()) for v in variants]
        for header_norm, original in normalized_to_original.items():
            if original in used_columns:
                continue
            header_set = frozenset(header_norm.split())
            if header_set in variant_sets:
                return original
        return None


def _display_name(field: str) -> str:
    return {
        "timestamp": "Timestamp",
        "roll_no": "College Roll No.",
        "name": "Full Name",
        "email": "Email address",
        "mobile": "Mobile No",
        "offer_1": "1st Offer",
        "tenth_percentage": "10th Percentage",
        "twelfth_percentage": "12th/Diploma Percentage",
        "be_cgpa": "BTech CGPA",
        "live_kt": "Live KT",
        "resume": "Resume",
    }.get(field, field)
