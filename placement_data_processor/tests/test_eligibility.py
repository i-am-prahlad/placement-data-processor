from core.processor import process
from tests.conftest import excel_bytes, open_rules, placement_row, response


THRESHOLD = open_rules(
    academic={"mode": "threshold", "tenth": 70, "twelfth": 70, "cgpa": 7.0},
)


def test_exactly_at_threshold_is_eligible():
    responses = excel_bytes(
        [response(**{"10th Percentage": 70, "12th/Diploma Percentage": 70, "BTech CGPA": 7.0})]
    )
    placement = excel_bytes([placement_row("R001")])
    _, result = process(responses, placement, THRESHOLD)
    assert result.summary.final_eligible_count == 1


def test_below_tenth_threshold():
    responses = excel_bytes(
        [response(**{"10th Percentage": 62, "12th/Diploma Percentage": 80, "BTech CGPA": 8.0})]
    )
    placement = excel_bytes([placement_row("R001")])
    _, result = process(responses, placement, THRESHOLD)
    assert result.summary.academic_removals == 1
    assert result.removals.iloc[0]["Removal Category"] == "10th eligibility"
    assert "62" in result.removals.iloc[0]["Removal Reason"]
    assert "70" in result.removals.iloc[0]["Removal Reason"]


def test_open_eligibility_ignores_low_scores():
    responses = excel_bytes(
        [response(**{"10th Percentage": 40, "12th/Diploma Percentage": 40, "BTech CGPA": 5.0})]
    )
    placement = excel_bytes([placement_row("R001")])
    _, result = process(responses, placement, open_rules(academic={"mode": "open"}))
    assert result.summary.final_eligible_count == 1
    assert result.summary.academic_removals == 0


def test_missing_academic_values_fail_threshold():
    responses = excel_bytes(
        [response(**{"10th Percentage": None, "12th/Diploma Percentage": 80, "BTech CGPA": 8.0})]
    )
    placement = excel_bytes([placement_row("R001")])
    _, result = process(responses, placement, THRESHOLD)
    assert result.summary.academic_removals == 1
    assert "missing" in result.removals.iloc[0]["Removal Reason"].lower()


def test_live_kt_removed_when_not_allowed():
    responses = excel_bytes([response(**{"Live KT": "Yes"})])
    placement = excel_bytes([placement_row("R001")])
    _, result = process(responses, placement, open_rules(live_kt={"allowed": False}))
    assert result.summary.kt_removals == 1
    assert result.removals.iloc[0]["Removal Category"] == "Live KT / backlog"


def test_live_kt_kept_when_allowed():
    responses = excel_bytes([response(**{"Live KT": "Yes"})])
    placement = excel_bytes([placement_row("R001")])
    _, result = process(responses, placement, open_rules(live_kt={"allowed": True}))
    assert result.summary.kt_removals == 0
    assert result.summary.final_eligible_count == 1


def test_internship_removed_when_enabled():
    responses = excel_bytes([response()])
    placement = excel_bytes([placement_row("R001")])
    internship = excel_bytes([{"College Roll No.": "R001", "Internship": "Yes"}])
    _, result = process(responses, placement, open_rules(internship={"remove": True}), internship=internship)
    assert result.summary.internship_removals == 1
    assert result.removals.iloc[0]["Removal Category"] == "Internship"


def test_internship_kept_when_disabled():
    responses = excel_bytes([response()])
    placement = excel_bytes([placement_row("R001")])
    internship = excel_bytes([{"College Roll No.": "R001"}])
    _, result = process(responses, placement, open_rules(internship={"remove": False}), internship=internship)
    assert result.summary.internship_removals == 0
    assert result.summary.final_eligible_count == 1
