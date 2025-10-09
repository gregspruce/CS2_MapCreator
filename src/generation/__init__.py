"""
Hybrid Zoned Terrain Generation System

This package implements the hybrid zoned generation + hydraulic erosion
system designed to achieve 55-65% buildable terrain.

Modules:
- zone_generator: Buildability zone generation (Session 2) ✅
- weighted_terrain: Zone-weighted terrain generation (Session 3) ✅
- hydraulic_erosion: Particle-based erosion (Session 4) - TODO
- ridge_enhancement: Ridge noise for mountains (Session 5) - TODO
- pipeline: Full generation pipeline (Session 6) - TODO

Created: 2025-10-09
Part of: CS2 Final Implementation Plan
"""

from .zone_generator import BuildabilityZoneGenerator, generate_buildability_zones
from .weighted_terrain import ZoneWeightedTerrainGenerator

__all__ = [
    'BuildabilityZoneGenerator',
    'generate_buildability_zones',
    'ZoneWeightedTerrainGenerator',
]
