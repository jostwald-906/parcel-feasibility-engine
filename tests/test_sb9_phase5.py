"""
SB9 Phase 5 accuracy tests

Focus:
- Parking 0 when near transit OR within designated car-share area
- Note short-term rental prohibition (30+ day terms) in apply()
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


def test_car_share_area_zero_parking():
    parcel = base_parcel()
    # Not near transit, but within car-share area
    proposal = base_proposal(near_transit=False, car_share_area=True)
    out = sb9.apply(parcel, proposal)
    assert out["eligible"] is True
    assert out["parking_required"] == 0
    assert any("car-share" in r.lower() for r in out["reasons"])  # reason present
    assert out["standards_overrides"].get("parking_zero_allowed") is True


def test_default_parking_one_when_no_transit_or_car_share():
    parcel = base_parcel()
    proposal = base_proposal(near_transit=False, car_share_area=False)
    out = sb9.apply(parcel, proposal)
    assert out["parking_required"] == 1


def test_short_term_rental_prohibition_noted():
    parcel = base_parcel()
    proposal = base_proposal()
    out = sb9.apply(parcel, proposal)
    assert out["eligible"] is True
    assert out["standards_overrides"].get("short_term_rental_prohibited") is True
    assert any("short-term" in r.lower() and "30" in r for r in out["reasons"])  # note present

