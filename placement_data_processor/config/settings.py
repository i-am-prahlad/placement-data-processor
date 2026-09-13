"""Drive-specific eligibility rules. Do not hard-code drive thresholds in core modules."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass
class PlacementRule:
    """Maximum offer count the student may already have and still remain eligible."""

    max_offers: int = 0


@dataclass
class AcademicRule:
    """Open = no academic cuts. Threshold applies 10th, 12th, and CGPA independently."""

    mode: str = "open"  # "open" | "threshold"
    tenth: float | None = None
    twelfth: float | None = None
    cgpa: float | None = None


@dataclass
class LiveKtRule:
    allowed: bool = True


@dataclass
class InternshipRule:
    remove: bool = False


@dataclass
class OutputRule:
    include_job_role: bool = True


@dataclass
class DriveRules:
    placement: PlacementRule = field(default_factory=PlacementRule)
    academic: AcademicRule = field(default_factory=AcademicRule)
    live_kt: LiveKtRule = field(default_factory=LiveKtRule)
    internship: InternshipRule = field(default_factory=InternshipRule)
    output: OutputRule = field(default_factory=OutputRule)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any] | None) -> "DriveRules":
        data = data or {}
        placement = data.get("placement") or {}
        academic = data.get("academic") or {}
        live_kt = data.get("live_kt") or {}
        internship = data.get("internship") or {}
        output = data.get("output") or {}
        return cls(
            placement=PlacementRule(max_offers=int(placement.get("max_offers", 0))),
            academic=AcademicRule(
                mode=str(academic.get("mode", "open")).lower(),
                tenth=_optional_float(academic.get("tenth")),
                twelfth=_optional_float(academic.get("twelfth")),
                cgpa=_optional_float(academic.get("cgpa")),
            ),
            live_kt=LiveKtRule(allowed=bool(live_kt.get("allowed", True))),
            internship=InternshipRule(remove=bool(internship.get("remove", False))),
            output=OutputRule(include_job_role=bool(output.get("include_job_role", True))),
        )

    def validate(self) -> list[str]:
        errors: list[str] = []
        if self.placement.max_offers < 0:
            errors.append("Maximum offers allowed cannot be negative.")
        if self.academic.mode not in {"open", "threshold"}:
            errors.append("Academic mode must be 'open' or 'threshold'.")
        if self.academic.mode == "threshold":
            if self.academic.tenth is None:
                errors.append("10th percentage threshold is required.")
            elif not 0 <= self.academic.tenth <= 100:
                errors.append("10th percentage threshold must be between 0 and 100.")
            if self.academic.twelfth is None:
                errors.append("12th/Diploma percentage threshold is required.")
            elif not 0 <= self.academic.twelfth <= 100:
                errors.append("12th/Diploma percentage threshold must be between 0 and 100.")
            if self.academic.cgpa is None:
                errors.append("BTech/BE CGPA threshold is required.")
            elif not 0 <= self.academic.cgpa <= 10:
                errors.append("BTech/BE CGPA threshold must be between 0 and 10.")
        return errors


def _optional_float(value: Any) -> float | None:
    if value is None or value == "":
        return None
    return float(value)


def default_rules() -> DriveRules:
    return DriveRules()
