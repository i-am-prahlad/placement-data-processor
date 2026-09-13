from core.processor import process
from tests.conftest import excel_bytes, open_rules, placement_row, response


def test_same_roll_keeps_latest_timestamp():
    responses = excel_bytes(
        [
            response(Timestamp="2026-01-01 09:00:00", **{"BTech CGPA": 8.0}),
            response(Timestamp="2026-01-02 09:00:00", **{"BTech CGPA": 9.5, "Email address": "later@college.edu"}),
        ]
    )
    placement = excel_bytes([placement_row("R001")])
    _validation, result = process(responses, placement, open_rules())
    assert result is not None
    assert result.summary.duplicate_count == 1
    assert result.summary.final_eligible_count == 1
    assert result.eligible.iloc[0]["email"] == "later@college.edu"
    assert result.eligible.iloc[0]["be_cgpa"] == 9.5
    assert result.removals.iloc[0]["Removal Category"] == "Duplicate"


def test_earlier_submission_is_removed():
    responses = excel_bytes(
        [
            response(**{"Full Name": "EARLY BIRD", "Timestamp": "2026-01-01 08:00:00"}),
            response(**{"Full Name": "LATE BIRD", "Timestamp": "2026-01-03 08:00:00"}),
        ]
    )
    placement = excel_bytes([placement_row("R001")])
    _, result = process(responses, placement, open_rules())
    assert result.eligible.iloc[0]["name"] == "Late Bird"
    assert "Earlier submission" in result.removals.iloc[0]["Removal Reason"]


def test_duplicate_email_after_roll_dedup():
    responses = excel_bytes(
        [
            response(**{"College Roll No.": "R001", "Email address": "same@x.com", "Timestamp": "2026-01-01"}),
            response(**{"College Roll No.": "R002", "Email address": "same@x.com", "Timestamp": "2026-01-05", "Full Name": "OTHER PERSON"}),
        ]
    )
    placement = excel_bytes([placement_row("R001"), placement_row("R002")])
    _, result = process(responses, placement, open_rules())
    assert result.summary.duplicate_count == 1
    assert result.summary.final_eligible_count == 1
    assert result.eligible.iloc[0]["roll_no"] == "R002"


def test_name_only_match_is_flagged_not_removed():
    responses = excel_bytes(
        [
            response(**{"College Roll No.": "R001", "Full Name": "JOHN SMITH", "Email address": "a@x.com", "Mobile No": "9876543210"}),
            response(**{"College Roll No.": "R002", "Full Name": "JOHN SMITH", "Email address": "b@x.com", "Mobile No": "9123456780"}),
        ]
    )
    placement = excel_bytes([placement_row("R001"), placement_row("R002")])
    _, result = process(responses, placement, open_rules())
    assert result.summary.duplicate_count == 0
    assert result.summary.final_eligible_count == 2
    assert any("flagged for review" in w.lower() or "name" in w.lower() for w in result.warnings)
    flagged = result.audit["Duplicate Status"].astype(str)
    assert flagged.str.contains("Name match flagged").any()
