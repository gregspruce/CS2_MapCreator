"""
Hybrid Zoned Terrain Generation System

This package implements the hybrid zoned generation + hydraulic erosion
system designed to achieve 55-65% buildable terrain.

Modules:
- zone_generator: Buildability zone generation (Session 2) ✅
- weighted_terrain: Zone-weighted terrain generation (Session 3) ✅
- hydraulic_erosion: Particle-based erosion (Session 4) ✅
- ridge_enhancement: Ridge noise for mountains (Session 5) ✅
- pipeline: Full generation pipeline (Session 6) ✅
- river_analysis: Flow analysis and river placement (Session 7) ✅
- detail_generator: Conditional detail addition for steep areas (Session 8) ✅
- constraint_verifier: Buildability verification and adjustment (Session 8) ✅

Created: 2025-10-09
Updated: 2025-10-10 (Session 8 complete - DETAIL & VERIFICATION INTEGRATED)
Part of: CS2 Final Implementation Plan
"""

from .zone_generator import BuildabilityZoneGenerator, generate_buildability_zones
from .weighted_terrain import ZoneWeightedTerrainGenerator
from .hydraulic_erosion import HydraulicErosionSimulator, apply_hydraulic_erosion
from .ridge_enhancement import RidgeEnhancer
from .river_analysis import RiverAnalyzer, analyze_rivers
from .detail_generator import DetailGenerator, add_detail_to_terrain
from .constraint_verifier import ConstraintVerifier, verify_terrain_buildability
from .pipeline import TerrainGenerationPipeline, generate_terrain, generate_preset

__all__ = [
    # Individual components
    'BuildabilityZoneGenerator',
    'generate_buildability_zones',
    'ZoneWeightedTerrainGenerator',
    'HydraulicErosionSimulator',
    'apply_hydraulic_erosion',
    'RidgeEnhancer',
    'RiverAnalyzer',
    'analyze_rivers',
    'DetailGenerator',
    'add_detail_to_terrain',
    'ConstraintVerifier',
    'verify_terrain_buildability',
    # Integrated pipeline (Sessions 6-8)
    'TerrainGenerationPipeline',
    'generate_terrain',
    'generate_preset',
]
