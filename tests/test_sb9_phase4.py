"""
SB9 Phase 4 accuracy tests

Focus: Environmental exclusions and protected housing constraints cause
categorical ineligibility in proposal helpers.
"""
from app.rules import sb9


def base_parcel(**overrides):
    p = {
        "zone": "R1",
        "lot_area_sf": 6000,
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


def test_prime_farmland_ineligible():
    parcel = base_parcel(overlays={"prime_farmland": True})
    proposal = base_proposal()
    res = sb9.can_apply(parcel, proposal)
    assert res["eligible"] is False
    assert any("farmland" in r.lower() for r in res["reasons"])  # explanation present


def test_wetlands_ineligible():
    parcel = base_parcel(overlays={"wetlands": True})
    proposal = base_proposal()
    res = sb9.can_apply(parcel, proposal)
    assert res["eligible"] is False
    assert any("wetlands" in r.lower() for r in res["reasons"])  # explanation present


def test_rent_controlled_ineligible():
    parcel = base_parcel(rent_controlled=True)
    proposal = base_proposal()
    res = sb9.can_apply(parcel, proposal)
    assert res["eligible"] is False
    assert any("rent-controlled" in r.lower() for r in res["reasons"])  # explanation present

