"""
California State Law Development Programs

This module contains implementations of California state housing laws
that apply uniformly across all cities in the state:

- SB 9 (2021): Single-family lot splits and duplexes
- SB 35 (2017): Streamlined ministerial approval for affordable housing
- AB 2011 (2022): Office-to-residential conversions
- AB 2097 (2022): Parking requirement reductions near transit
- State Density Bonus Law (Gov Code § 65915): Density/FAR/height bonuses for affordable housing

These programs may interact with or preempt local regulations in some cases.
"""

__all__ = [
    "analyze_sb9",
    "analyze_sb35",
    "analyze_ab2011",
    "apply_ab2097_parking_reduction",
    "apply_density_bonus",
]
