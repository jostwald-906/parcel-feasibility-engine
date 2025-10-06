"""
SB9 Phase 3 accuracy tests

Focus: Lot split 40/60 ratio and 1,200 sf per child lot.
Applies to proposal helpers (can_apply/apply) without altering legacy scenario tests.
"""
from app.rules import sb9


def base_parcel(**overrides):
    p = {
        "zone": "R1",
        "lot_area_sf": 2400,  # exact minimum
        "overlays": {"coastal": False, "historic": False, "very_high_fire": False, "flood": False},
        "existing_units": 1,
        "had_rental_last_3y": False,
    }
    p.update(overrides)
    return p


def base_proposal(**overrides):
    pr = {"two_unit": False, "lot_split": True, "near_transit": False}
    pr.update(overrides)
    return pr


def test_ratio_and_min_child_area_at_minimum():
    parcel = base_parcel(lot_area_sf=2400)
    proposal = base_proposal(lot_split=True)

    res = sb9.can_apply(parcel, proposal)
    assert res["eligible"] is True
    assert any("40/60" in r for r in res["reasons"])  # ratio mentioned

    out = sb9.apply(parcel, proposal)
    assert out["eligible"] is True
    assert out["standards_overrides"]["lot_split_min_child_lot_pct"] == 0.4
    assert out["standards_overrides"]["lot_split_max_child_lot_pct"] == 0.6
    # 2400 * 0.4 = 960, but minimum per child lot is 1200 sf
    assert out["standards_overrides"]["lot_split_min_child_lot_area_sf"] == 1200


def test_ratio_and_min_child_area_on_larger_lot():
    parcel = base_parcel(lot_area_sf=3500)
    proposal = base_proposal(lot_split=True)

    out = sb9.apply(parcel, proposal)
    # 0.4 * 3500 = 1400, larger than 1200
    assert out["standards_overrides"]["lot_split_min_child_lot_area_sf"] == 1400


def test_narrow_lot_width_irrelevant_in_proposal_helpers():
    # Even if a separate geometric width would be narrow, proposal helpers ignore width
    parcel = base_parcel(lot_area_sf=5000)
    proposal = base_proposal(lot_split=True)
    res = sb9.can_apply(parcel, proposal)
    assert res["eligible"] is True

