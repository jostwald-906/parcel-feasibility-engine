"""
Focused tests for sb9.can_apply() and sb9.apply(parcel, proposal).

Inputs:
- parcel: {zone, lot_area_sf, overlays: {coastal, historic, very_high_fire, flood}, existing_units, had_rental_last_3y}
- proposal: {two_unit: bool, lot_split: bool, near_transit: bool}

Outputs (apply):
- {eligible: bool, reasons: [..], standards_overrides: {min_side_rear_setback: 4, ...},
   max_units_delta: 1 or 3, parking_required: 0|1 per unit}
"""
import pytest

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


class TestCanApply:
    def test_two_unit_standard_parcel_is_eligible(self):
        parcel = base_parcel()
        proposal = base_proposal(two_unit=True, lot_split=False)
        result = sb9.can_apply(parcel, proposal)
        assert result["eligible"] is True
        assert any("Two-unit" in r or "two-unit" in r for r in result["reasons"])  # messaging present

    def test_lot_split_on_adequate_lot_is_eligible(self):
        parcel = base_parcel(lot_area_sf=6000)
        proposal = base_proposal(two_unit=False, lot_split=True)
        result = sb9.can_apply(parcel, proposal)
        assert result["eligible"] is True
        assert any("lot split" in r.lower() for r in result["reasons"])  # mentions lot split sufficiency

    def test_lot_split_too_small_is_ineligible(self):
        parcel = base_parcel(lot_area_sf=2000)
        proposal = base_proposal(two_unit=False, lot_split=True)
        result = sb9.can_apply(parcel, proposal)
        assert result["eligible"] is False
        assert any("too small" in r.lower() for r in result["reasons"])  # size constraint reason

    def test_not_single_family_zone_is_ineligible(self):
        parcel = base_parcel(zone="R3")
        proposal = base_proposal(two_unit=True, lot_split=False)
        result = sb9.can_apply(parcel, proposal)
        assert result["eligible"] is False
        assert any("single-family" in r.lower() for r in result["reasons"])  # zoning reason


class TestApply:
    def test_near_transit_zero_parking(self):
        parcel = base_parcel()
        proposal = base_proposal(near_transit=True)
        out = sb9.apply(parcel, proposal)
        assert out["eligible"] is True
        assert out["parking_required"] == 0
        assert any("no parking" in r.lower() for r in out["reasons"])  # explain

    def test_coastal_overlay_requires_cdp_but_is_eligible(self):
        parcel = base_parcel(overlays={"coastal": True, "historic": False, "very_high_fire": False, "flood": False})
        proposal = base_proposal()
        out = sb9.apply(parcel, proposal)
        assert out["eligible"] is True
        assert out["standards_overrides"].get("coastal_cdp_required") is True
        assert any("coastal" in r.lower() and "cdp" in r.lower() for r in out["reasons"])  # CDP explained

    def test_standards_override_includes_min_setback(self):
        parcel = base_parcel()
        proposal = base_proposal()
        out = sb9.apply(parcel, proposal)
        assert out["standards_overrides"]["min_side_rear_setback"] == 4

    def test_lot_split_max_units_delta_is_three(self):
        parcel = base_parcel(lot_area_sf=6000)
        proposal = base_proposal(two_unit=False, lot_split=True)
        out = sb9.apply(parcel, proposal)
        assert out["eligible"] is True
        assert out["max_units_delta"] == 3
        assert any("lot split" in r.lower() for r in out["reasons"])  # explains path

