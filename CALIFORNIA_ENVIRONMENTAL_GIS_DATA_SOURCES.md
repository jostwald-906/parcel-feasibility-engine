# California Environmental GIS Data Sources
## SB35 and AB2011 Eligibility Hazard Layers

**Document Version:** 1.0
**Last Updated:** October 6, 2025
**Geographic Focus:** Santa Monica / Los Angeles County
**Purpose:** Integration into Parcel Feasibility Engine web application

---

## Table of Contents
1. [Wetlands (Clean Water Act)](#1-wetlands-clean-water-act)
2. [Conservation Areas / Protected Habitat](#2-conservation-areas--protected-habitat)
3. [Fire Hazard Severity Zones](#3-fire-hazard-severity-zones-cal-fire)
4. [Cortese List Hazardous Waste Sites](#4-cortese-list-hazardous-waste-sites-dtsc)
5. [Alquist-Priolo Earthquake Fault Zones](#5-alquist-priolo-earthquake-fault-zones)
6. [Integration Summary](#integration-summary)

---

## 1. Wetlands (Clean Water Act)

### Primary Data Sources

#### Option A: U.S. Fish & Wildlife Service - National Wetlands Inventory (NWI)
**Primary Agency:** U.S. Fish & Wildlife Service (USFWS)
**Coverage:** California-wide (nationwide)
**Authority Level:** Federal

**API/GIS Service URL:**
```
REST Service: https://fwspublicservices.wim.usgs.gov/wetlandsmapservice/rest
```

**Data Format:**
- ESRI REST API
- OGC WMS
- OGC WFS
- Downloadable: Geodatabase, GeoPackage, Shapefile

**Update Frequency:** Biannually (services updated with Wetlands Mapper)

**Access Requirements:**
- Public, no authentication required
- No API key needed
- Open access for all users

**Key Field Names:**
- `ATTRIBUTE` - Wetland classification code
- `WETLAND_TYPE` - Type of wetland
- `ACRES` - Acreage

**Integration Notes:**
- Most comprehensive federal wetlands dataset
- Nationwide coverage includes all California regions
- Well-maintained and regularly updated
- Ideal for compliance with Clean Water Act requirements

---

#### Option B: California Aquatic Resource Inventory (CARI)
**Primary Agency:** San Francisco Estuary Institute (SFEI) / California State Water Resources Control Board
**Coverage:** California-wide
**Authority Level:** State

**API/GIS Service URL:**
```
REST Service (FeatureServer): https://services2.arcgis.com/Uq9r85Potqm3MfRV/arcgis/rest/services/biosds2835_fpu/FeatureServer/0

Water Board GIS Services: http://gispublic.waterboards.ca.gov/arcgis/rest/services
```

**Data Format:**
- ESRI REST API (FeatureServer)
- OGC WMS
- OGC KML
- Downloadable from SFEI Data Center

**Update Frequency:** Periodic updates (version 3.2 as of 2025)

**Access Requirements:**
- Public access, no authentication required
- Contact: GIS@waterboards.ca.gov

**Key Field Names:**

*Classification Fields:*
- `clickcode` - Alphanumeric wetland classification code
- `clicklabel` - Detailed wetland type description (most detailed)
- `major_class` - Major classification (e.g., "Depressional")
- `wetland_class` - Specific wetland classification
- `anthropogenic_modification` - Human impact classification
- `wetland_type` - Wetland type consistent with CRAM modules
- `vegetation` - Vegetation classification

*Salinity Fields:*
- `salinity` - Six-class salinity (Fresh, Oligohaline, Mesohaline, Saline, Bar-Built, Undefined)
- `salinity_additional_information` - Detailed salinity source data

*Source Data Fields:*
- `name` - Wetland feature name
- `orig_dataset` - Original source dataset
- `orig_class` - Original classification from source
- `organization` - Mapping agency/organization
- `source_data` - Primary imagery/data source description
- `source_year` - Most recent source data year

*Administrative Fields:*
- `CARI_id` - Unique CARI feature ID
- `lastupdate` - Last integration script run date

*Legend/Display Fields:*
- `legcode` - 1-3 letter major wetland class code
- `leglabellevel1` - Common wetland type terminology (legend value)
- `leglabellevel2` - Major classification (legend detail)
- `legend_headings` - Legend heading value

**Integration Notes:**
- CARI is a standardized statewide compilation of best available local, regional, and statewide maps
- Includes National Wetlands Inventory (NWI) and National Hydrography Dataset (NHD)
- Accessible via EcoAtlas web interface (https://ecoatlas.org)
- More detailed California-specific classification than NWI
- Integrated with California Water Boards' Clean Water Act Section 401 certification program

---

### Recommended Approach for Wetlands
**Primary:** Use NWI for federal compliance and broad coverage
**Secondary:** Cross-reference with CARI for California-specific detail and state regulatory context

---

## 2. Conservation Areas / Protected Habitat

### California Protected Areas Database (CPAD)

**Primary Agency:** GreenInfo Network (maintained for California Natural Resources Agency)
**Coverage:** California-wide
**Authority Level:** State (authoritative database)

**API/GIS Service URL:**
```
REST Service (MapServer): https://services.gis.ca.gov/arcgis/rest/services/Boundaries/CA_Protected_Areas_Database/MapServer

California State Geoportal: https://gis.data.ca.gov/
Search for "CPAD" or "California Protected Areas"

Multiple themed services available at:
https://gis.cnra.ca.gov/arcgis/rest/services/Boundaries/
- CPAD_AccessType/MapServer
- CPAD_AgencyLevel/MapServer
- CPAD_AgencyClassification/MapServer
```

**Data Format:**
- ESRI REST API (MapServer, FeatureServer)
- OGC WMS
- OGC WFS
- GeoServices
- Downloadable: Shapefiles, Geodatabase

**Update Frequency:** Twice annually (CPAD 2025a published June 2025)

**Access Requirements:**
- Public access, no authentication required
- No API key needed

**Key Field Names:**

*Agency Information:*
- `AGNCY_LEV` - Agency Level (Federal, State, Non Profit, Special District, City, County)
- `AGNCY_TYP` - Agency Type
- `AGNCY_WEB` - Agency Website
- `LAYER` - Owning agency classification
- `MNG_AG_ID` - Managing Agency ID
- `MNG_AGENCY` (or `MNG_AGNCY`) - Managing Agency
- `MNG_AG_LEV` - Managing Agency Level
- `MNG_AG_TYP` - Managing Agency Type

*Access and Use:*
- `ACCESS_TYP` - Access Type (Open Access, Restricted Access, No Public Access)
- `SPEC_USE` - Special Use designation

*Identification:*
- `UNIT_NAME` - Unit Name
- `SITE_NAME` - Site Name
- `LABEL_NAME` - Label Name
- `PARK_URL` - Park URL

*Geographic:*
- `COUNTY` - County
- `CITY` - City
- `LAND_WATER` - Land or Water designation
- `ACRES` - Acreage

*Metadata:*
- `DATE_REVIS` - Date Revised
- `SRC_ALIGN` - Source Alignment
- `SRC_ATTR` - Source Attributes

**Database Structure:**
CPAD contains three types of spatial features:
- **Holdings** - Individual land parcels owned by agencies
- **Units** - Aggregated public park/open space units (may contain multiple holdings)
- **SuperUnits** - Multi-unit complexes (e.g., national parks spanning multiple units)

**Integration Notes:**
- Authoritative GIS database of parks and open space in California
- Maintained by GreenInfo Network, published by California Natural Resources Agency
- Over 1,000 public agencies and non-profit organizations represented
- Companion database: California Conservation Easement Database (CCED) for conservation easements
- Excellent documentation available in CPAD Database Manual (updated with each release)
- Ideal for identifying protected habitat and conservation areas for regulatory exclusions

**Documentation:**
- CPAD 2025a Database Manual: https://www.calands.org/wp-content/uploads/2024/06/CPAD-2024a-Database-Manual.pdf
- Website: https://calands.org/

---

## 3. Fire Hazard Severity Zones (CAL FIRE)

### CAL FIRE Fire Hazard Severity Zones (FHSZ)

**Primary Agency:** CAL FIRE (California Department of Forestry and Fire Protection) / Office of the State Fire Marshal
**Coverage:** California-wide
**Authority Level:** State (regulatory)

**API/GIS Service URL:**

*Los Angeles County Specific:*
```
REST Service (MapServer): https://public.gis.lacounty.gov/public/rest/services/LACounty_Dynamic/Hazards/MapServer/2

LA County Open Data:
- https://egis-lacounty.hub.arcgis.com/datasets/lacounty::fire-hazard-severity-zones
- https://data.lacounty.gov/datasets/bf87f4b1e6954f4697006ff41420c083_0
```

*Statewide CAL FIRE:*
```
Fire Hazard Severity Zone Viewer: https://experience.arcgis.com/experience/03beab8511814e79a0e4eabf0d3e7247

CAL FIRE FRAP GIS Data: https://www.fire.ca.gov/what-we-do/fire-resource-assessment-program/gis-mapping-and-data-analytics
```

**Data Format:**
- ESRI REST API (MapServer, FeatureServer)
- ArcGIS Hub datasets
- Downloadable: Shapefiles, PDF maps

**Update Frequency:**
- Major update cycle: 10+ years
- Last comprehensive update: 2007 (SRA) / 2008-2011 (LRA)
- **March 2025**: New FHSZ maps released for Local Responsibility Areas (LRA)
- Maps designed to remain stable for 10+ years

**Access Requirements:**
- Public access, no authentication required
- LA County REST API is publicly accessible

**Responsibility Areas:**
- **SRA (State Responsibility Area)** - CAL FIRE has fire suppression responsibility
- **LRA (Local Responsibility Area)** - Local fire departments have responsibility
- **FRA (Federal Responsibility Area)** - Federal agencies have responsibility

**Hazard Classifications:**
- Moderate
- High
- Very High (VHFHSZ - Very High Fire Hazard Severity Zone)

**Model Factors:**

*For Wildland Areas:*
- Fire history
- Flame length
- Terrain
- Local weather
- Potential fuel over 50-year period

*For Non-Wildland Areas:*
- Terrain
- Weather
- Urban vegetation cover
- Blowing embers
- Proximity to wildland
- Fire history
- Fire hazard in nearby wildlands

**Key Field Names (LA County):**
The specific field names vary by jurisdiction, but typically include:
- `HAZ_CLASS` or `FHSZ_CLASS` - Hazard classification (Moderate, High, Very High)
- `RESP_AREA` or `SRA_LRA` - Responsibility area designation (SRA/LRA)
- `ZONE` - Zone identifier

**Integration Notes:**
- March 2025 update represents first comprehensive LRA revision since 2007
- Los Angeles County must adopt new 2025 maps by ordinance within 120 days of March 24, 2025 issuance
- LA County REST API endpoint provides direct programmatic access
- Critical for SB35/AB2011 eligibility as development restrictions apply in Very High FHSZ
- Based on Public Resources Code 4201-4204 statutory requirements
- Model considers fuel loading, slope, fire weather, winds, and other relevant factors

**Official Resources:**
- CAL FIRE FHSZ Maps (2022): https://osfm.fire.ca.gov/what-we-do/community-wildfire-preparedness-and-mitigation/fire-hazard-severity-zones/fire-hazard-severity-zones-maps-2022
- Fire Hazard Severity Zones Hub: https://fire-hazard-severity-zones-rollout-calfire-forestry.hub.arcgis.com/

---

## 4. Cortese List Hazardous Waste Sites (DTSC)

### DTSC's Hazardous Waste and Substances Site List (Cortese List)

**Primary Agency:** California Department of Toxic Substances Control (DTSC) / California Environmental Protection Agency (CalEPA)
**Coverage:** California-wide
**Authority Level:** State (regulatory, required by Government Code Section 65962.5)

**API/GIS Service URL:**
```
California State Geoportal Dataset:
https://gis-california.opendata.arcgis.com/datasets/DTSC::dtsc-hazardous-waste-and-substances-site-list-cortese-list

California State Geoportal (search "DTSC" or "Cortese"):
https://gis.data.ca.gov/

DTSC EnviroStor Database (web interface):
https://www.envirostor.dtsc.ca.gov/public/

California Open Data Portal:
https://data.ca.gov/dataset/department-of-toxic-substances-control-envirostor-public-data-export
```

**Data Format:**
- ESRI REST API (FeatureServer/MapServer) - available via California State Geoportal
- OGC WMS
- OGC WFS
- GeoServices
- Downloadable: CSV, KML, Zip, GeoJSON, Shapefile

**Update Frequency:**
- EnviroStor database: Updated continuously/daily
- Annual Cortese List compilation: At least annually (per Government Code requirement)
- Public data export: Daily updates

**Access Requirements:**
- Public access, no authentication required
- No API key needed for basic access
- API links available through California State Geoportal (GeoServices, WMS, WFS)

**What is the Cortese List:**
The Cortese List is a planning document used by state and local agencies and developers to comply with CEQA (California Environmental Quality Act) requirements. It provides information about the location of hazardous materials release sites. Government Code Section 65962.5 requires CalEPA to develop an updated Cortese List at least annually.

**Data Systems:**

*Primary Database - EnviroStor:*
DTSC's Brownfields and Environmental Restoration Program (Cleanup Program) uses the EnviroStor database to provide DTSC's component of Cortese List data, identifying:
- State Response sites
- Federal Superfund sites
- Voluntary Cleanup sites
- School cleanup sites
- Military evaluation sites
- Corrective Action sites

*Site Types in EnviroStor:*
- Annual Workplan sites (now State Response and/or Federal Superfund)
- Backlog sites (listed under Health and Safety Code Section 25356)
- Cleanup sites
- Hazardous waste sites
- Inspection, Compliance and Enforcement (ICE) sites

**Key Field Names:**
Field names vary by dataset export, but typically include:
- `SITE_NAME` - Name of the site
- `ADDRESS` - Street address
- `CITY` - City
- `COUNTY` - County
- `ZIP` - ZIP code
- `SITE_TYPE` - Type of site (cleanup, hazardous waste, etc.)
- `STATUS` - Current status (Active, Inactive, Completed, etc.)
- `SITE_ID` or `ENVIROSTOR_ID` - Unique site identifier
- `LATITUDE` / `LONGITUDE` - Geographic coordinates
- `PROGRAM` - Regulatory program

**Integration Notes:**
- Critical for CEQA compliance and SB35/AB2011 eligibility screening
- Multiple data sources contribute to complete Cortese List (DTSC, SWRCB, CalRecycle, etc.)
- EnviroStor provides DTSC's official component
- Los Angeles County has integrated this data into their GIS systems
- API access through California State Geoportal provides standardized REST endpoints
- Data updated daily ensures current information for development eligibility checks

**Official Resources:**
- DTSC Cortese List: https://dtsc.ca.gov/dtscs-cortese-list/
- CalEPA Cortese List Data Resources: https://calepa.ca.gov/sitecleanup/corteselist/
- CalEPA Section 65962.5(a): https://calepa.ca.gov/sitecleanup/corteselist/section-65962-5a/

---

## 5. Alquist-Priolo Earthquake Fault Zones

### California Geological Survey (CGS) Alquist-Priolo Fault Hazard Zones

**Primary Agency:** California Department of Conservation - California Geological Survey (CGS)
**Coverage:** California-wide (zones delineated where active faults exist)
**Authority Level:** State (regulatory, per Alquist-Priolo Earthquake Fault Zoning Act)

**API/GIS Service URL:**
```
Fault Zones (FeatureServer):
https://gis.conservation.ca.gov/server/rest/services/CGS_Earthquake_Hazard_Zones/SHP_Fault_Zones/FeatureServer

Fault Zones Layer 0:
https://gis.conservation.ca.gov/server/rest/services/CGS_Earthquake_Hazard_Zones/SHP_Fault_Zones/FeatureServer/0

Fault Traces (MapServer):
https://gis.conservation.ca.gov/server/rest/services/CGS_Earthquake_Hazard_Zones/SHP_Fault_Traces/MapServer

Fault Traces Layer 0:
https://gis.conservation.ca.gov/server/rest/services/CGS_Earthquake_Hazard_Zones/SHP_Fault_Traces/MapServer/0
```

*Los Angeles City Specific:*
```
REST Service: http://maps.lacity.org/arcgis/rest/services/Mapping/NavigateLA/MapServer/97

LA City GeoHub: https://geohub.lacity.org/datasets/alquist-priolo-earthquake-fault-zones
```

*California State Geoportal:*
```
Dataset: https://gis.data.ca.gov/maps/ee92a5f9f4ee4ec5aa731d3245ed9f53/about

Alternative URL: https://maps-cnra-cadoc.opendata.arcgis.com/datasets/cadoc::cgs-seismic-hazards-program-alquist-priolo-fault-hazard-zones
```

**Data Format:**
- ESRI REST API (FeatureServer, MapServer)
- OGC WMS
- OGC WFS
- GeoServices
- Downloadable: Shapefile, KML, GeoJSON
- Output formats: JSON, geoJSON, PBF

**Maximum Record Count:** 1000 per query (FeatureServer/0)

**Update Frequency:**
- Official maps updated as new fault studies are completed
- Regulatory zones established through formal map adoption process
- Periodic updates based on new geologic research

**Access Requirements:**
- Public access, no authentication required
- No API key needed

**Layer Types:**

*Fault Zones (Polygons):*
- Regulatory zone boundaries forming Alquist-Priolo Earthquake Fault Zones
- Define areas where construction setbacks and disclosure requirements apply

*Fault Traces (Lines):*
- Identified fault traces used in delineating Alquist-Priolo zones
- Label points and leader lines for fault trace annotation

**Key Field Names:**
Specific field names from the services include:
- `ZONE_NAME` - Name of the fault zone
- `FAULT_NAME` - Name of the fault
- `FAULT_TYPE` - Type of fault
- `QUAD_NAME` - USGS quadrangle map name
- `MAP_DATE` - Date of official map publication
- `COUNTY` - County name
- `SCALE` - Map scale (typically 1:24,000)

**Regulatory Context:**
The Alquist-Priolo Earthquake Fault Zoning Act (Public Resources Code, Chapter 7.5, Division 2) was passed in 1972 to mitigate the hazard of surface faulting to structures for human occupancy. The Act:
- Prohibits location of most structures for human occupancy across active faults
- Requires special studies in zones to demonstrate sites are not threatened by surface displacement
- Applies to "active" faults (those with surface displacement within Holocene time - last 11,000 years)
- Requires seller disclosure when property lies within an Alquist-Priolo zone

**Integration Notes:**
- Essential for SB35/AB2011 eligibility (development restrictions in fault zones)
- Official maps produced by California Geological Survey are the governing documents
- Multiple service endpoints available (FeatureServer for queries, MapServer for display)
- Los Angeles area well-covered due to numerous active faults (San Andreas, Newport-Inglewood, etc.)
- Both zone boundaries and fault trace data available
- FeatureServer supports advanced queries in JSON, geoJSON, and PBF formats

**Official Resources:**
- CGS Alquist-Priolo Program: https://www.conservation.ca.gov/cgs/alquist-priolo
- Official Maps: https://www.conservation.ca.gov/cgs/alquist-priolo
- EQ Zapp (Earthquake Zones Application): https://www.conservation.ca.gov/cgs/geohazards/eq-zapp

**Interactive Map Viewer:**
- EQ Zapp Portal: https://maps.conservation.ca.gov/cgs/informationwarehouse/eqzapp/

---

## Integration Summary

### Coverage for Santa Monica / Los Angeles County
All five hazard layers provide comprehensive coverage for the Santa Monica / Los Angeles County area:

| Layer | Coverage | LA County Specific API |
|-------|----------|----------------------|
| Wetlands (NWI) | Nationwide | Same as statewide |
| Wetlands (CARI) | Statewide | Same as statewide |
| Protected Areas (CPAD) | Statewide | Same as statewide |
| Fire Hazard Zones | Statewide + County-specific | **Yes** - LA County REST API available |
| Cortese List | Statewide | Statewide data includes LA County |
| Earthquake Faults | Statewide + City-specific | **Yes** - LA City API available |

### Access Requirements Summary

| Layer | API Key Required | Authentication | Public Access |
|-------|-----------------|----------------|---------------|
| NWI Wetlands | No | None | Yes - Fully public |
| CARI Wetlands | No | None | Yes - Fully public |
| CPAD | No | None | Yes - Fully public |
| Fire Hazard Zones | No | None | Yes - Fully public |
| Cortese List | No | None | Yes - Fully public |
| Earthquake Faults | No | None | Yes - Fully public |

**Result:** All required data sources are publicly accessible with no authentication requirements, making them ideal for web application integration.

### Data Format Summary
All services support:
- **ESRI REST API** (MapServer and/or FeatureServer)
- **OGC WMS** (Web Map Service)
- **OGC WFS** (Web Feature Service) - in most cases
- **Downloadable formats** - Shapefiles, GeoJSON, KML, etc.

### Update Frequency Summary

| Layer | Update Frequency | Last Major Update | Next Expected Update |
|-------|-----------------|-------------------|---------------------|
| NWI Wetlands | Biannually | Continuous | Ongoing |
| CARI Wetlands | Periodic | Version 3.2 (2025) | TBD |
| CPAD | Twice annually | CPAD 2025a (June 2025) | December 2025 (2025b) |
| Fire Hazard Zones | 10+ year cycle | March 2025 (LRA) | ~2035 |
| Cortese List | Daily (EnviroStor) | Continuous | Daily |
| Earthquake Faults | As studies complete | Ongoing | Ongoing |

### Recommended Integration Approach

1. **Use REST APIs** - All services provide ESRI REST API endpoints for programmatic access
2. **Query by Geometry** - Use parcel coordinates/boundaries to query each service
3. **No Authentication** - No API keys or tokens needed (simplifies implementation)
4. **Caching Strategy** - Consider caching results given update frequencies:
   - High priority for daily caching: Cortese List
   - Medium priority: CPAD (twice yearly updates)
   - Low priority: Fire Hazard Zones, Earthquake Faults (infrequent updates)
5. **Fallback Sources** - Multiple endpoints available for most layers (state + local)

### Example Query Pattern
For a given parcel in Santa Monica, CA (approximate coordinates):

```javascript
// Example coordinates (Santa Monica area)
const latitude = 34.0195;
const longitude = -118.4912;

// Query each service using geometry intersection
// Most services support queries like:
// {serviceURL}/query?geometry={longitude},{latitude}&geometryType=esriGeometryPoint&spatialRel=esriSpatialRelIntersects&f=json
```

### Technical Integration Notes

1. **Geometry Format:** Services typically accept:
   - Points (lat/lon)
   - Polygons (for parcel boundaries)
   - ESRI JSON format
   - WKT (Well-Known Text) in some cases

2. **Response Format:** JSON is universally supported and recommended

3. **Rate Limiting:** No explicit rate limits found for public services, but implement reasonable throttling

4. **Error Handling:** All services return standard HTTP status codes and error messages

5. **CORS:** California State services generally support CORS for web application access

### Contact Information

| Agency | Contact | Purpose |
|--------|---------|---------|
| CA Water Boards GIS | GIS@waterboards.ca.gov | CARI/Wetlands questions |
| GreenInfo Network | info@greeninfo.org | CPAD questions |
| CAL FIRE | Contact via website | Fire hazard zones |
| DTSC | Contact via EnviroStor | Cortese List questions |
| CA Dept of Conservation | Contact via CGS | Earthquake fault zones |

---

## Additional Resources

### California State Geoportal
**URL:** https://gis.data.ca.gov/
**Description:** Central hub for California GIS data with search, download, and API access

### California Natural Resources Agency Open Data
**URL:** https://data.cnra.ca.gov/
**Description:** Open data portal with environmental and natural resource datasets

### EcoAtlas
**URL:** https://www.ecoatlas.org/
**Description:** California wetlands and aquatic resources mapping and tracking

### CAL FIRE FRAP
**URL:** https://www.fire.ca.gov/what-we-do/fire-resource-assessment-program/
**Description:** Fire Resource Assessment Program with GIS data and analytics

### Los Angeles County GIS Portal
**URL:** https://egis-lacounty.hub.arcgis.com/
**Description:** LA County-specific GIS datasets and services

---

## Document Changelog

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | 2025-10-06 | Initial documentation with comprehensive research on all five hazard layers |

---

## Notes for Developers

1. **Testing Endpoints:** All REST API URLs can be tested directly in a browser by appending `?f=pjson` to get service metadata

2. **Service Health:** Monitor service availability; government services occasionally undergo maintenance

3. **Coordinate Systems:** Most services support multiple coordinate systems (Web Mercator, WGS84, etc.)

4. **Query Limits:** Be aware of maximum record count limits (typically 1000-2000 records per query)

5. **Pagination:** For large result sets, implement pagination using `resultOffset` and `resultRecordCount` parameters

6. **Field Validation:** Always validate that expected fields exist in API responses (field names may change with updates)

7. **Version Tracking:** Consider tracking dataset versions (e.g., CPAD 2025a) in your application for audit purposes

8. **Local Caching:** Download and cache static layers locally for improved performance and reduced API calls

9. **Spatial Queries:** All services support spatial relationship queries (intersects, contains, within, etc.)

10. **Metadata:** Each service provides metadata endpoints for detailed field descriptions and data source information
