"""
Santa Monica City Configuration

Implements CityConfig for Santa Monica, California.
Includes all Santa Monica-specific:
- 31 zoning codes across 5 categories
- Downtown Community Plan (DCP) with tiered development
- Bergamot Area Plan
- GIS service connections
- Coastal zone considerations
"""

from typing import Dict, List, Optional, Any
from app.cities.base import (
    CityConfig,
    ZoningCode,
    GISServiceConfig,
    OverlayZone
)


class SantaMonicaConfig(CityConfig):
    """Santa Monica city configuration."""

    @property
    def city_name(self) -> str:
        return "Santa Monica"

    @property
    def city_code(self) -> str:
        return "SM"

    @property
    def state(self) -> str:
        return "CA"

    @property
    def municipal_code_url(self) -> str:
        return "https://library.municode.com/ca/santa_monica/codes/code_of_ordinances"

    # Zoning Codes

    def get_zoning_codes(self) -> List[ZoningCode]:
        """All 31 Santa Monica zoning codes."""
        return [
            # Residential Zones
            ZoningCode(code="R1", description="Single-Unit Residential", category="Residential", base_far=0.5, base_height_ft=28),
            ZoningCode(code="R2", description="Low Density Residential", category="Residential", base_far=0.75, base_height_ft=30),
            ZoningCode(code="R3", description="Medium Density Residential", category="Residential", base_far=1.25, base_height_ft=35),
            ZoningCode(code="R4", description="High Density Residential", category="Residential", base_far=1.5, base_height_ft=40),
            ZoningCode(code="RMH", description="Residential Mobile Home", category="Residential"),
            ZoningCode(code="OP1", description="Ocean Park 1", category="Residential"),
            ZoningCode(code="OP2", description="Ocean Park 2", category="Residential"),
            ZoningCode(code="OP3", description="Ocean Park 3", category="Residential"),
            ZoningCode(code="OP4", description="Ocean Park 4", category="Residential"),
            ZoningCode(code="OPD", description="Ocean Park D", category="Residential"),

            # Commercial & Mixed-Use
            ZoningCode(code="NC", description="Neighborhood Commercial", category="Commercial & Mixed-Use", base_far=1.0, base_height_ft=35),
            ZoningCode(code="GC", description="General Commercial", category="Commercial & Mixed-Use", base_far=1.5, base_height_ft=45),
            ZoningCode(code="MUB", description="Mixed-Use Boulevard", category="Commercial & Mixed-Use", base_far=2.0, base_height_ft=50),
            ZoningCode(code="MUBL", description="Mixed-Use Boulevard Low", category="Commercial & Mixed-Use", base_far=1.5, base_height_ft=40),
            ZoningCode(code="HMU", description="High Mixed-Use", category="Commercial & Mixed-Use", base_far=2.5, base_height_ft=55),
            ZoningCode(code="OC", description="Office Campus", category="Commercial & Mixed-Use", base_far=2.0, base_height_ft=50),
            ZoningCode(code="LT", description="Light Industrial/Technology", category="Commercial & Mixed-Use", base_far=1.5, base_height_ft=45),
            ZoningCode(code="WT", description="Waterfront", category="Commercial & Mixed-Use"),
            ZoningCode(code="OT", description="Ocean Transitional", category="Commercial & Mixed-Use"),

            # Downtown Community Plan Districts
            ZoningCode(code="TA", description="Transit Adjacent", category="Downtown Community Plan", base_far=2.25, base_height_ft=45),
            ZoningCode(code="NV", description="Neighborhood Village", category="Downtown Community Plan", base_far=2.0, base_height_ft=35),

            # Bergamot Area Plan Districts
            ZoningCode(code="BTV", description="Bergamot Transit Village", category="Bergamot Area Plan", base_far=3.0, base_height_ft=60),
            ZoningCode(code="MUC", description="Mixed Use Creative", category="Bergamot Area Plan", base_far=2.5, base_height_ft=50),
            ZoningCode(code="CAC", description="Conservation: Art Center", category="Bergamot Area Plan", base_far=1.5, base_height_ft=40),

            # Special Districts
            ZoningCode(code="OF", description="Office", category="Special Districts", base_far=1.5, base_height_ft=45),
            ZoningCode(code="BC", description="Bergamot Creative", category="Special Districts"),
            ZoningCode(code="CCS", description="Civic Center Specific Plan", category="Special Districts"),
            ZoningCode(code="IC", description="Industrial Creative", category="Special Districts"),
            ZoningCode(code="CC", description="Commercial Corridor", category="Special Districts"),
            ZoningCode(code="OS", description="Open Space", category="Special Districts"),
            ZoningCode(code="PL", description="Public Lands", category="Special Districts"),
        ]

    def get_zoning_categories(self) -> Dict[str, List[str]]:
        """Zoning codes organized by category."""
        return {
            "Residential": ["R1", "R2", "R3", "R4", "RMH", "OP1", "OP2", "OP3", "OP4", "OPD"],
            "Commercial & Mixed-Use": ["NC", "GC", "MUB", "MUBL", "HMU", "OC", "LT", "WT", "OT"],
            "Downtown Community Plan": ["TA", "NV"],
            "Bergamot Area Plan": ["BTV", "MUC", "CAC"],
            "Special Districts": ["OF", "BC", "CCS", "IC", "CC", "OS", "PL"],
        }

    # GIS Services

    def get_parcel_service(self) -> GISServiceConfig:
        return GISServiceConfig(
            url="https://gis.santamonica.gov/server/rest/services/Parcels_Public/FeatureServer/0",
            layer_name="Parcels Public",
            layer_id=0,
            geometry_type="esriGeometryPolygon",
            fields={
                "objectid": "esriFieldTypeOID",
                "ain": "esriFieldTypeString",
                "apn": "esriFieldTypeString",
                "situsaddress": "esriFieldTypeString",
                "usecode": "esriFieldTypeString",
                "usedescription": "esriFieldTypeString"
            },
            key_fields=["apn", "address"]
        )

    def get_zoning_service(self) -> GISServiceConfig:
        return GISServiceConfig(
            url="https://gis.santamonica.gov/server/rest/services/Zoning_Update/FeatureServer/0",
            layer_name="Zoning Parcel Based",
            layer_id=0,
            geometry_type="esriGeometryPolygon",
            fields={
                "objectid": "esriFieldTypeOID",
                "zoning": "esriFieldTypeString",
                "overlay": "esriFieldTypeString",
                "zonedesc": "esriFieldTypeString"
            },
            key_fields=["zone", "overlay"]
        )

    def get_historic_service(self) -> Optional[GISServiceConfig]:
        return GISServiceConfig(
            url="https://gis.santamonica.gov/server/rest/services/Historic_Preservation_Layers/FeatureServer/2",
            layer_name="Historic Resources Inventory",
            layer_id=2,
            geometry_type="esriGeometryPolygon",
            fields={
                "objectid": "esriFieldTypeOID",
                "ain": "esriFieldTypeString",
                "resource_evaluation": "esriFieldTypeString"
            },
            key_fields=["historic"]
        )

    def get_coastal_service(self) -> Optional[GISServiceConfig]:
        return GISServiceConfig(
            url="https://gis.santamonica.gov/server/rest/services/Coastal_Zone/FeatureServer/0",
            layer_name="Coastal Zone",
            layer_id=0,
            geometry_type="esriGeometryPolygon",
            fields={
                "objectid": "esriFieldTypeOID",
                "coastalzon": "esriFieldTypeDouble"
            },
            key_fields=[]
        )

    def get_flood_service(self) -> Optional[GISServiceConfig]:
        return GISServiceConfig(
            url="https://gis.santamonica.gov/server/rest/services/FEMA_National_Flood_Hazard_Area/MapServer/0",
            layer_name="FEMA Flood Hazard Area",
            layer_id=0,
            geometry_type="esriGeometryPolygon",
            fields={
                "objectid": "esriFieldTypeOID",
                "fld_zone": "esriFieldTypeString"
            },
            key_fields=["zone", "flood"]
        )

    def get_transit_service(self) -> Optional[GISServiceConfig]:
        return GISServiceConfig(
            url="https://gis.santamonica.gov/server/rest/services/Big_Blue_Bus_Stops_and_Routes/FeatureServer/0",
            layer_name="Big Blue Bus Stops",
            layer_id=0,
            geometry_type="esriGeometryPoint",
            fields={
                "objectid": "esriFieldTypeOID",
                "stop_name": "esriFieldTypeString"
            },
            key_fields=["transit"]
        )

    def get_overlay_services(self) -> List[GISServiceConfig]:
        return [
            # Bergamot Area Plan
            GISServiceConfig(
                url="https://gis.santamonica.gov/server/rest/services/Bergamot_Area_Plan/FeatureServer/1",
                layer_name="Bergamot Area Plan Districts",
                layer_id=1,
                geometry_type="esriGeometryPolygon",
                fields={
                    "objectid": "esriFieldTypeOID",
                    "area_name": "esriFieldTypeString",
                    "label": "esriFieldTypeString"
                },
                key_fields=["overlay"]
            ),
            # CNEL
            GISServiceConfig(
                url="https://gis.santamonica.gov/server/rest/services/Community_Noise_Equivalent_Levels_CNEL/FeatureServer/0",
                layer_name="Community Noise Equivalent Levels (CNEL)",
                layer_id=0,
                geometry_type="esriGeometryPolygon",
                fields={
                    "objectid": "esriFieldTypeOID",
                    "cnel": "esriFieldTypeString"
                },
                key_fields=[]
            ),
        ]

    def get_hazard_services(self) -> List[GISServiceConfig]:
        return [
            GISServiceConfig(
                url="https://gis.santamonica.gov/server/rest/services/Fault_Zones/FeatureServer/1",
                layer_name="Fault Zones",
                layer_id=1,
                geometry_type="esriGeometryPolygon",
                fields={"objectid": "esriFieldTypeOID"},
                key_fields=["hazard"]
            ),
            GISServiceConfig(
                url="https://gis.santamonica.gov/server/rest/services/Liquefaction_Risk_Areas/FeatureServer/0",
                layer_name="Liquefaction Risk Areas",
                layer_id=0,
                geometry_type="esriGeometryPolygon",
                fields={"objectid": "esriFieldTypeOID"},
                key_fields=[]
            ),
        ]

    # Overlay Zones

    def get_overlay_zones(self) -> List[OverlayZone]:
        return [
            OverlayZone(
                name="Downtown Community Plan",
                code="DCP",
                description="Tiered development standards with community benefits (TA and NV districts)",
                applies_by_zoning=True,
                affected_zones=["TA", "NV"]
            ),
            OverlayZone(
                name="Bergamot Area Plan",
                code="BERGAMOT",
                description="Creative/arts district with tiered FAR and height standards",
                applies_by_zoning=True,
                affected_zones=["BTV", "MUC", "CAC"]
            ),
            OverlayZone(
                name="Community Noise Equivalent Levels",
                code="CNEL",
                description="Noise impact overlay requiring mitigation for residential development"
            ),
        ]

    # Special Plan Areas

    def get_special_plan_areas(self) -> List[str]:
        return ["DCP", "BERGAMOT"]

    def supports_tiered_development(self) -> bool:
        return True

    def get_tier_standards(self, zone_code: str) -> Optional[Dict[str, Any]]:
        """
        Get tiered standards for DCP and Bergamot zones.

        For implementation details, see:
        - app/cities/santa_monica/rules/dcp_scenarios.py
        - app/cities/santa_monica/rules/bergamot_scenarios.py
        """
        from app.rules.tiered_standards import DCP_TA_STANDARDS, DCP_NV_STANDARDS, BERGAMOT_STANDARDS

        zone = zone_code.upper()
        if zone == "TA":
            return DCP_TA_STANDARDS
        elif zone == "NV":
            return DCP_NV_STANDARDS
        elif zone in ["BTV", "MUC", "CAC"]:
            return BERGAMOT_STANDARDS.get(zone)

        return None

    # Coastal Zone

    def is_in_coastal_zone(self) -> bool:
        return True  # Entire city is within CA Coastal Zone

    def get_coastal_boundary_reference(self) -> Optional[str]:
        return "Ocean Avenue"  # Stricter CDP requirements west of Ocean Ave


# Singleton instance
santa_monica = SantaMonicaConfig()
