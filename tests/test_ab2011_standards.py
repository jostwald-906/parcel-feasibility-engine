"""
Unit tests for AB2011 standards floors and precedence helpers.

Covers:
- State floors by tier for minimum density (30/50/80 u/ac)
- State floors by tier for minimum height (35/45/65 ft)
- Local-vs-state precedence helper (choose max of local and floor)
- Standards application to a parcel (min units by lot size)
"""
import math
import pytest

from app.rules.ab2011 import (
    ab2011_state_floors,
    ab2011_precedence,
    apply_ab2011_standards,
)
from app.models.parcel import ParcelBase


def make_parcel_acres(acres: float) -> ParcelBase:
    return ParcelBase(
        apn="AB2011-FLOOR-TEST",
        address="",
        city="",
        county="",
        zip_code="",
        lot_size_sqft=acres * 43560.0,
        zoning_code="C-1",
        existing_units=0,
        existing_building_sqft=20000.0,
        year_built=1980,
    )


class TestStateFloors:
    def test_low_tier_floors(self):
        floors = ab2011_state_floors("low")
        assert floors["min_density_u_ac"] == 30.0
        assert floors["min_height_ft"] == 35.0

    def test_mid_tier_floors(self):
        floors = ab2011_state_floors("mid")
        assert floors["min_density_u_ac"] == 50.0
        assert floors["min_height_ft"] == 45.0

    def test_high_tier_floors(self):
        floors = ab2011_state_floors("high")
        assert floors["min_density_u_ac"] == 80.0
        assert floors["min_height_ft"] == 65.0


class TestPrecedenceHelper:
    def test_density_uses_state_when_local_lower(self):
        final = ab2011_precedence(local_value=25, state_floor=30)
        assert final == 30

    def test_density_uses_local_when_local_higher(self):
        final = ab2011_precedence(local_value=60, state_floor=50)
        assert final == 60

    def test_height_uses_state_when_local_lower(self):
        final = ab2011_precedence(local_value=30, state_floor=35)
        assert final == 35

    def test_height_uses_local_when_local_higher(self):
        final = ab2011_precedence(local_value=55, state_floor=45)
        assert final == 55

    def test_none_local_uses_state(self):
        assert ab2011_precedence(local_value=None, state_floor=45) == 45


class TestApplyStandards:
    def test_min_units_low_tier_half_acre(self):
        parcel = make_parcel_acres(0.5)
        res = apply_ab2011_standards(parcel, tier="low", local_min_density_u_ac=None, local_max_height_ft=None)
        # 0.5 acres * 30 u/ac = 15 units (ceil)
        assert res["final_min_density_u_ac"] == 30
        assert res["final_min_units"] == 15
        assert res["final_min_height_ft"] == 35

    def test_mid_tier_local_more_permissive(self):
        parcel = make_parcel_acres(0.25)
        # Local is more permissive: density 60 u/ac and height 55 ft
        res = apply_ab2011_standards(parcel, tier="mid", local_min_density_u_ac=60, local_max_height_ft=55)
        assert res["state_min_density_u_ac"] == 50
        assert res["final_min_density_u_ac"] == 60
        assert res["state_min_height_ft"] == 45
        assert res["final_min_height_ft"] == 55
        # Units: 0.25 ac * 60 = 15
        assert res["final_min_units"] == 15

    def test_high_tier_local_below_floor(self):
        parcel = make_parcel_acres(1.0)
        # Local constraints below state floor
        res = apply_ab2011_standards(parcel, tier="high", local_min_density_u_ac=50, local_max_height_ft=50)
        assert res["final_min_density_u_ac"] == 80  # state floor prevails
        assert res["final_min_height_ft"] == 65     # state floor prevails
        # 1.0 ac * 80 = 80 units
        assert res["final_min_units"] == 80

