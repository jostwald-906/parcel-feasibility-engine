"""
SB9 Phase 2 accuracy tests

Focus: Hazard overlays handled with mitigation, not categorical denial.
"""
from app.rules import sb9


def base_parcel(**overrides):
    p = {
        "zone": "R1",
        "lot_area_sf": 5000,
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


def test_flood_zone_is_eligible_with_mitigation_flag():
    parcel = base_parcel(overlays={"coastal": False, "historic": False, "very_high_fire": False, "flood": True})
    proposal = base_proposal()

    res = sb9.can_apply(parcel, proposal)
    assert res["eligible"] is True
    assert any("flood" in r.lower() for r in res["reasons"])  # explanation present

    out = sb9.apply(parcel, proposal)
    assert out["eligible"] is True
    assert out["standards_overrides"].get("hazard_mitigation_required") is True
    assert any("flood" in r.lower() and "mitigation" in r.lower() for r in out["reasons"])  # mitigation noted


def test_vhfhsz_is_eligible_with_mitigation_flag():
    parcel = base_parcel(overlays={"coastal": False, "historic": False, "very_high_fire": True, "flood": False})
    proposal = base_proposal()

    res = sb9.can_apply(parcel, proposal)
    assert res["eligible"] is True
    assert any("fire" in r.lower() for r in res["reasons"])  # explanation present

    out = sb9.apply(parcel, proposal)
    assert out["eligible"] is True
    assert out["standards_overrides"].get("hazard_mitigation_required") is True
    assert any("fire" in r.lower() and "mitigation" in r.lower() for r in out["reasons"])  # mitigation noted

