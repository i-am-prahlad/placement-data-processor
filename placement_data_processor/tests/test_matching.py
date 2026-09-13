from core.processor import process
from tests.conftest import excel_bytes, open_rules, placement_row, response


def test_exact_roll_number_match():
    responses = excel_bytes([response(**{"College Roll No.": "R100"})])
    placement = excel_bytes([placement_row("R100", ["Acme"])])
    _, result = process(responses, placement, open_rules(placement={"max_offers": 0}))
    assert result.summary.placement_removals == 1
    assert int(result.audit.iloc[0]["Offer Count"] or 0) == 1


def test_email_fallback_when_roll_missing_on_response():
    responses = excel_bytes(
        [response(**{"College Roll No.": "", "Email address": "unique@college.edu"})]
    )
    placement = excel_bytes(
        [placement_row("PX", ["Acme"], email="unique@college.edu")]
    )
    _, result = process(responses, placement, open_rules(placement={"max_offers": 0}))
    assert result.summary.placement_removals == 1


def test_mobile_fallback():
    responses = excel_bytes(
        [response(**{"College Roll No.": "", "Email address": "none@x.com", "Mobile No": "9988776655"})]
    )
    placement = excel_bytes(
        [placement_row("PX", ["Acme"], email="other@x.com", mobile="9988776655")]
    )
    _, result = process(responses, placement, open_rules(placement={"max_offers": 0}))
    assert result.summary.placement_removals == 1


def test_ambiguous_name_is_not_used_for_matching():
    responses = excel_bytes(
        [response(**{"College Roll No.": "", "Email address": "z@x.com", "Mobile No": "9000000001", "Full Name": "ALEX JONES"})]
    )
    placement = excel_bytes(
        [
            placement_row("P1", ["Acme"], name="ALEX JONES", email="a1@x.com", mobile="9111111111"),
            placement_row("P2", ["Beta"], name="ALEX JONES", email="a2@x.com", mobile="9222222222"),
        ]
    )
    _, result = process(responses, placement, open_rules(placement={"max_offers": 0}))
    assert result.summary.placement_removals == 0
    assert result.summary.final_eligible_count == 1
