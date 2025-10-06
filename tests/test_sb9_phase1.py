"""
SB9 Phase 1 accuracy tests

Focus: proposal-based helpers
- Small-lot duplex eligibility (no hard minimum lot size)
- Side/rear setback override only
"""
from app.rules import sb9


def base_parcel(**overrides):
    p = {
        "zone": "R1",
        "lot_area_sf": 1500,  # below 2,000 sf; should still allow two-unit under SB9
        "overlays": {"coastal": False, "historic": False, "very_high_fire": False, "flood": False},
        "existing_units": 1,
        "had_rental_last_3y": False,
    }
    p.update(overrides)
    return p


def base_proposal(**overrides):
    pr = {"two_unit": True, "lot_split": False, "near_transit": False}
    pr.update(overrides)
    return pr


def test_small_lot_duplex_is_eligible():
    parcel = base_parcel()
    proposal = base_proposal(two_unit=True)

    res = sb9.can_apply(parcel, proposal)
    assert res["eligible"] is True
    assert any("two-unit" in r.lower() for r in res["reasons"])  # confirm rationale


def test_apply_sets_only_side_rear_min_setback():
    parcel = base_parcel()
    proposal = base_proposal()

    out = sb9.apply(parcel, proposal)
    assert out["eligible"] is True
    # Side/rear override surfaced as 4 ft
    assert out["standards_overrides"]["min_side_rear_setback"] == 4
    # Do not claim a front setback override here
    assert "front_setback_override" not in out["standards_overrides"]

