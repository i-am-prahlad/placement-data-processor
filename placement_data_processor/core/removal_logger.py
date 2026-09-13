"""Record every removal. Never silently discard a student."""

from __future__ import annotations

from dataclasses import dataclass, field

import pandas as pd


@dataclass
class RemovalLogger:
    rows: list[dict] = field(default_factory=list)
    _kept_from_duplicate_groups: set[int] = field(default_factory=set)

    def log(
        self,
        student: pd.Series | dict,
        category: str,
        reason: str,
        company: str = "",
    ) -> None:
        record = dict(student if isinstance(student, dict) else student.to_dict())
        comp = company or record.get("company", "") or record.get("placement_companies", "") or record.get("internship_company", "")
        self.rows.append(
            {
                "Name": record.get("name", ""),
                "College Roll No.": record.get("roll_no", ""),
                "Branch": record.get("branch", ""),
                "Removal Category": category,
                "Removal Reason": reason,
                "Offer Count": record.get("offer_count", 0),
                "Company": comp,
                "row_id": record.get("row_id"),
                "_student_record": record,
            }
        )

    def mark_kept_duplicate(self, row_id: int) -> None:

        self._kept_from_duplicate_groups.add(int(row_id))

    def duplicate_kept_hint(self) -> set[int]:
        return set(self._kept_from_duplicate_groups)

    def to_dataframe(self) -> pd.DataFrame:
        if not self.rows:
            return pd.DataFrame(
                columns=[
                    "Sr No",
                    "Name",
                    "College Roll No.",
                    "Branch",
                    "Removal Category",
                    "Removal Reason",
                    "Offer Count",
                    "Company",
                ]
            )
        df = pd.DataFrame(self.rows)
        df = df.drop(columns=["row_id", "_student_record"], errors="ignore")
        df.insert(0, "Sr No", range(1, len(df) + 1))
        return df[
            [
                "Sr No",
                "Name",
                "College Roll No.",
                "Branch",
                "Removal Category",
                "Removal Reason",
                "Offer Count",
                "Company",
            ]
        ]

    def counts_by_category(self) -> dict[str, int]:
        if not self.rows:
            return {}
        series = pd.Series([r["Removal Category"] for r in self.rows])
        return series.value_counts().to_dict()
