# Tier Standards Citations Needed

This document tracks all Santa Monica Municipal Code (SMMC) citations needed to replace placeholder values in the tiered development standards module.

**Status**: All values are currently PLACEHOLDERS and should NOT be used for production analysis without verification against current SMMC.

---

## 1. Downtown Community Plan (DCP) Tier Standards

### DCP Tier FAR Multipliers

**File**: `app/rules/tiered_standards.py`
**Constants**: `DCP_TIER_FAR_MULTIPLIER`

**Needed Citations**:
- [ ] SMMC § [TBD] - Downtown Community Plan FAR/Height Standards
- [ ] SMMC § [TBD] - DCP Tier 1 FAR (current: base zone FAR × 1.0)
- [ ] SMMC § [TBD] - DCP Tier 2 FAR (current: base zone FAR × 1.25)
- [ ] SMMC § [TBD] - DCP Tier 3 FAR (current: base zone FAR × 1.50)

**Current Placeholder Values**:
```python
DCP_TIER_FAR_MULTIPLIER = {
    '1': 1.0,      # Base tier - use zone FAR
    '2': 1.25,     # Tier 2 - 25% increase (PLACEHOLDER)
    '3': 1.5,      # Tier 3 - 50% increase (PLACEHOLDER)
}
```

**Assumptions**:
- Tier 1 uses base zoning FAR without modification
- Tier 2 provides 25% FAR increase over base
- Tier 3 provides 50% FAR increase over base
- Multipliers apply to base zone FAR, not fixed values

### DCP Tier Height Bonuses

**Needed Citations**:
- [ ] SMMC § [TBD] - DCP Tier 1 height limit (current: base zone height + 0 ft)
- [ ] SMMC § [TBD] - DCP Tier 2 height limit (current: base zone height + 10 ft)
- [ ] SMMC § [TBD] - DCP Tier 3 height limit (current: base zone height + 20 ft)

**Current Placeholder Values**:
```python
DCP_TIER_HEIGHT_BONUS = {
    '1': 0,        # Base tier - no bonus
    '2': 10,       # Tier 2 - +10 ft (PLACEHOLDER)
    '3': 20,       # Tier 3 - +20 ft (PLACEHOLDER)
}
```

**Assumptions**:
- Height bonuses are additive (base + bonus)
- Bonuses measured in feet
- Tier 1 receives no height bonus

---

## 2. Bergamot Area Plan Standards

### Bergamot District FAR

**File**: `app/rules/tiered_standards.py`
**Constants**: `BERGAMOT_FAR`

**Needed Citations**:
- [ ] SMMC § [TBD] - Bergamot Area Plan Development Standards
- [ ] Bergamot Area Plan Specific Plan (if adopted) § [TBD]
- [ ] SMMC § [TBD] - Bergamot sub-district boundaries and definitions
- [ ] SMMC § [TBD] - Default Bergamot FAR (current: 2.0)
- [ ] SMMC § [TBD] - Bergamot Core district FAR (current: 2.5)
- [ ] SMMC § [TBD] - Bergamot Edge district FAR (current: 1.75)

**Current Placeholder Values**:
```python
BERGAMOT_FAR = {
    'default': 2.0,     # Default district (PLACEHOLDER)
    'core': 2.5,        # Core district (PLACEHOLDER)
    'edge': 1.75,       # Edge district (PLACEHOLDER)
}
```

**Additional Requirements**:
- [ ] GIS layer or address-based lookup for sub-district determination
- [ ] Mapping rules: which parcels fall into Core vs. Edge vs. Default?

### Bergamot District Height

**Needed Citations**:
- [ ] SMMC § [TBD] - Bergamot default height limit (current: 65 ft)
- [ ] SMMC § [TBD] - Bergamot Core district height (current: 75 ft)
- [ ] SMMC § [TBD] - Bergamot Edge district height (current: 55 ft)

**Current Placeholder Values**:
```python
BERGAMOT_HEIGHT = {
    'default': 65.0,    # Default district (PLACEHOLDER)
    'core': 75.0,       # Core district (PLACEHOLDER)
    'edge': 55.0,       # Edge district (PLACEHOLDER)
}
```

---

## 3. Affordable Housing Overlay (AHO) Standards

### AHO Bonuses

**File**: `app/rules/tiered_standards.py`
**Constants**: `AHO_FAR_BONUS`, `AHO_HEIGHT_BONUS`

**Needed Citations**:
- [ ] SMMC § [TBD] - Affordable Housing Overlay Standards
- [ ] Resolution/Ordinance establishing AHO [TBD]
- [ ] SMMC § [TBD] - AHO FAR bonus (current: +0.5)
- [ ] SMMC § [TBD] - AHO height bonus (current: +15 ft)
- [ ] SMMC § [TBD] - AHO eligibility requirements (income levels, affordability %)
- [ ] SMMC § [TBD] - AHO bonus application rules (additive vs. multiplicative)

**Current Placeholder Values**:
```python
AHO_FAR_BONUS = 0.5       # +0.5 FAR for AHO projects (PLACEHOLDER)
AHO_HEIGHT_BONUS = 15.0   # +15 ft for AHO projects (PLACEHOLDER)
```

**Additional Requirements**:
- [ ] Income level thresholds for AHO qualification
- [ ] Minimum affordability percentage requirements
- [ ] Affordability covenant duration requirements
- [ ] Verification that bonuses are additive (current implementation)

---

## 4. Base Zone FAR Standards

### Residential Zones

**File**: `app/rules/tiered_standards.py`
**Constants**: `BASE_ZONE_FAR`

**Needed Citations**:
- [ ] SMMC Article 9 - Zoning Districts and Allowed Land Uses
- [ ] SMMC § 9.04 - Residential Zones (R1, R2, R3, R4)
- [ ] SMMC § 9.28 - Development Standards

**Current Placeholder Values**:
- R1: 0.5 - CITE: SMMC § [TBD]
- R2: 0.75 - CITE: SMMC § [TBD]
- R3: 1.5 - CITE: SMMC § [TBD]
- R4: 2.5 - CITE: SMMC § [TBD]

### Mixed-Use Zones

**Needed Citations**:
- [ ] SMMC § 9.12 - Mixed-Use Zones (MUBL, MUBM, MUBH, MUB, MUCR, NV, WT)

**Current Placeholder Values**:
- NV (Neighborhood Village): 1.0 - CITE: SMMC § [TBD]
- WT (Wilshire Transition): 1.75 - CITE: SMMC § [TBD]
- MUBL (Mixed-Use Boulevard Low): 1.5 - CITE: SMMC § [TBD]
- MUBM (Mixed-Use Boulevard Medium): 2.0 - CITE: SMMC § [TBD]
- MUBH (Mixed-Use Boulevard High): 3.0 - CITE: SMMC § [TBD]
- MUB (Mixed-Use Boulevard): 2.0 - CITE: SMMC § [TBD]
- MUCR (Mixed-Use Creative): 2.0 - CITE: SMMC § [TBD]

### Commercial and Industrial Zones

**Needed Citations**:
- [ ] SMMC § 9.14 - Commercial Zones (C1, C2, C3, OC, OP)
- [ ] SMMC § 9.16 - Industrial Zones (I)

**Current Placeholder Values**:
- C1: 2.0 - CITE: SMMC § [TBD]
- C2: 2.0 - CITE: SMMC § [TBD]
- C3: 2.0 - CITE: SMMC § [TBD]
- OC (Office Commercial): 2.0 - CITE: SMMC § [TBD]
- OP (Office Professional): 1.5 - CITE: SMMC § [TBD]
- I (Industrial): 1.5 - CITE: SMMC § [TBD]

---

## 5. Base Zone Height Standards

### Residential Zones

**File**: `app/rules/tiered_standards.py`
**Constants**: `BASE_ZONE_HEIGHT`

**Current Placeholder Values**:
- R1: 35 ft - CITE: SMMC § [TBD]
- R2: 40 ft - CITE: SMMC § [TBD]
- R3: 55 ft - CITE: SMMC § [TBD]
- R4: 75 ft - CITE: SMMC § [TBD]

### Mixed-Use Zones

**Current Placeholder Values**:
- NV (Neighborhood Village): 35 ft - CITE: SMMC § [TBD]
- WT (Wilshire Transition): 50 ft - CITE: SMMC § [TBD]
- MUBL (Mixed-Use Boulevard Low): 45 ft - CITE: SMMC § [TBD]
- MUBM (Mixed-Use Boulevard Medium): 55 ft - CITE: SMMC § [TBD]
- MUBH (Mixed-Use Boulevard High): 84 ft - CITE: SMMC § [TBD]
- MUB (Mixed-Use Boulevard): 65 ft - CITE: SMMC § [TBD]
- MUCR (Mixed-Use Creative): 65 ft - CITE: SMMC § [TBD]

### Commercial and Industrial Zones

**Current Placeholder Values**:
- C1: 65 ft - CITE: SMMC § [TBD]
- C2: 65 ft - CITE: SMMC § [TBD]
- C3: 65 ft - CITE: SMMC § [TBD]
- OC (Office Commercial): 65 ft - CITE: SMMC § [TBD]
- OP (Office Professional): 55 ft - CITE: SMMC § [TBD]
- I (Industrial): 45 ft - CITE: SMMC § [TBD]

---

## 6. Additional Verification Needed

### Zone Code Verification

**Action Items**:
- [ ] Verify all zone code abbreviations match current SMMC
- [ ] Check if any zones have been renamed or consolidated
- [ ] Confirm zone code capitalization/formatting
- [ ] Document any zone code variants (e.g., "R2A", "R2-5000")

### Overlay Interaction Rules

**Action Items**:
- [ ] Verify precedence order: DCP tier vs. Bergamot vs. base zoning
- [ ] Confirm AHO bonuses are additive (not multiplicative)
- [ ] Document what happens when multiple overlays apply
- [ ] Verify if DCP and Bergamot can overlap (expected: no)

### Default Values

**Current Defaults**:
- Unknown zone FAR: 1.0
- Unknown zone height: 35 ft

**Action Items**:
- [ ] Verify appropriate default values for unknown zones
- [ ] Document fallback behavior in code comments

---

## 7. Implementation Notes

### Priority Order for Citations (P0 = Highest)

1. **P0 - Base Zone Standards**: R1, R2, R3, R4 (most common residential)
2. **P0 - Mixed-Use Standards**: MUBL, MUBM, MUBH (Santa Monica Boulevard corridor)
3. **P1 - DCP Tier Standards**: All three tiers (downtown development)
4. **P1 - AHO Standards**: Bonuses and eligibility
5. **P2 - Bergamot Standards**: All districts
6. **P2 - Special Zones**: NV, WT, MUCR
7. **P3 - Commercial/Industrial**: C1-C3, OC, OP, I

### Source Documents to Review

- [ ] Santa Monica Municipal Code Article 9 (Zoning)
- [ ] Downtown Community Plan (adopted [year])
- [ ] Bergamot Area Plan/Specific Plan
- [ ] Affordable Housing Overlay ordinance/resolution
- [ ] Santa Monica Zoning Ordinance (most recent amendments)
- [ ] Santa Monica General Plan Land Use Element

### Contact Information

**Santa Monica Planning Division**
Phone: (310) 458-8341
Email: planning@smgov.net
Address: 1685 Main Street, Room 212, Santa Monica, CA 90401

---

## Revision History

| Date | Version | Changes |
|------|---------|---------|
| 2025-01-XX | 1.0 | Initial documentation of needed citations |

---

**Last Updated**: 2025-01-XX
**Next Review**: Upon receipt of SMMC citations
