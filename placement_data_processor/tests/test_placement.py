from core.placement import classify_offer_count
from core.processor import process
from tests.conftest import excel_bytes, open_rules, placement_row, response


def test_offer_classification():
    assert classify_offer_count(0) == "No offer"
    assert classify_offer_count(1) == "Single-placed"
    assert classify_offer_count(2) == "Double-placed"
    assert classify_offer_count(3) == "More than 2 offers"
    assert classify_offer_count(4) == "More than 2 offers"


def test_zero_offers_eligible_when_max_is_zero():
    responses = excel_bytes([response()])
    placement = excel_bytes([placement_row("R001", [])])
    _, result = process(responses, placement, open_rules(placement={"max_offers": 0}))
    assert result.summary.final_eligible_count == 1
    assert int(result.eligible.iloc[0]["offer_count"]) == 0


def test_single_offer_removed_when_no_offers_allowed():
    responses = excel_bytes([response()])
    placement = excel_bytes([placement_row("R001", ["TCS"])])
    _, result = process(responses, placement, open_rules(placement={"max_offers": 0}))
    assert result.summary.final_eligible_count == 0
    assert result.summary.placement_removals == 1
    assert result.removals.iloc[0]["Removal Category"] == "Single placed"


def test_single_offer_kept_when_max_is_one():
    responses = excel_bytes([response()])
    placement = excel_bytes([placement_row("R001", ["TCS"])])
    _, result = process(responses, placement, open_rules(placement={"max_offers": 1}))
    assert result.summary.final_eligible_count == 1


def test_double_offer_removed_when_max_is_one():
    responses = excel_bytes([response()])
    placement = excel_bytes([placement_row("R001", ["TCS", "Infosys"])])
    _, result = process(responses, placement, open_rules(placement={"max_offers": 1}))
    assert result.summary.final_eligible_count == 0
    assert result.removals.iloc[0]["Removal Category"] == "Double placed"


def test_more_than_two_offers():
    responses = excel_bytes([response()])
    placement = excel_bytes([placement_row("R001", ["A", "B", "C"])])
    _, result = process(responses, placement, open_rules(placement={"max_offers": 1}))
    assert result.removals.iloc[0]["Removal Category"] == "Placement"
    assert result.eligible.empty
