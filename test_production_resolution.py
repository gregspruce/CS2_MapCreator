"""
Test at PRODUCTION resolution (4096x4096) - Exact GUI configuration
This reproduces what the user experiences.
"""

import numpy as np
import sys
from pathlib import Path

project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.generation.pipeline import TerrainGenerationPipeline
from src.buildability_enforcer import BuildabilityEnforcer


def test_production_resolution():
    """Test at 4096x4096 with exact GUI defaults."""

    print("="*80)
    print("PRODUCTION RESOLUTION TEST (4096x4096)")
    print("="*80)
    print("Testing with EXACT GUI defaults at production resolution")
    print("This should match what the user experiences.\n")

    # Create pipeline at PRODUCTION resolution
    pipeline = TerrainGenerationPipeline(
        resolution=4096,  # PRODUCTION
        map_size_meters=14336.0,
        seed=42  # Use same seed for consistency
    )

    # EXACT GUI defaults from parameter_panel.py
    params = {
        # Zone Generation (Session 2)
        'target_coverage': 0.72,
        'zone_wavelength': 6500.0,
        'zone_octaves': 2,

        # Terrain Generation (Session 3)
        'base_amplitude': 0.063,  # Tuned for 55-65% buildability at 5% slope threshold
        'min_amplitude_mult': 0.3,
        'max_amplitude_mult': 1.0,
        'terrain_wavelength': 1000.0,
        'terrain_octaves': 6,

        # Ridge Enhancement (Session 5)
        'ridge_strength': 0.2,
        'ridge_octaves': 5,
        'ridge_wavelength': 1500.0,
        'apply_ridges': True,  # ENABLED

        # Hydraulic Erosion (Session 4)
        'num_particles': 100000,
        'erosion_rate': 0.2,
        'deposition_rate': 0.6,
        'apply_erosion': True,  # ENABLED

        # River Analysis (Session 7)
        'river_threshold_percentile': 99.0,
        'min_river_length': 10,
        'apply_rivers': True,

        # Detail Addition (Session 8)
        'detail_amplitude': 0.02,
        'detail_wavelength': 75.0,
        'apply_detail': True,  # ENABLED per user request

        # Constraint Verification (Session 8)
        'target_buildable_min': 55.0,
        'target_buildable_max': 65.0,
        'apply_constraint_adjustment': True,

        # Control
        'verbose': True
    }

    print(f"Generating terrain at 4096x4096 (this may take a few minutes)...\n")

    # Generate terrain
    terrain, stats = pipeline.generate(**params)

    # Report results
    print("\n" + "="*80)
    print("PRODUCTION TEST RESULTS")
    print("="*80)
    print(f"Resolution: 4096x4096")
    print(f"Final Buildability: {stats['final_buildable_pct']:.1f}%")
    print(f"Target Range: 55-65%")
    print(f"Status: {'SUCCESS' if stats['target_achieved'] else 'FAILED'}")
    print(f"\nTerrain Stats:")
    print(f"  After terrain: {stats['terrain_stats']['buildable_percent']:.1f}%")
    if not stats['ridge_stats'].get('skipped'):
        ridge_pct = stats['ridge_stats'].get('final_buildable_pct')
        if ridge_pct is not None and isinstance(ridge_pct, (int, float)):
            print(f"  After ridges: {ridge_pct:.1f}%")
        else:
            print(f"  After ridges: N/A")
    if not stats['erosion_stats'].get('skipped'):
        erosion_pct = stats['erosion_stats'].get('final_buildable_pct')
        if erosion_pct is not None and isinstance(erosion_pct, (int, float)):
            print(f"  After erosion: {erosion_pct:.1f}%")
        else:
            print(f"  After erosion: N/A")
    print(f"  Final: {stats['final_buildable_pct']:.1f}%")
    print(f"\nSlopes:")
    print(f"  Mean: {stats['final_mean_slope']:.2f}%")
    print(f"  P90: {stats['final_p90_slope']:.2f}%")
    print(f"\nGeneration Time: {stats['total_pipeline_time']:.1f}s")
    print("="*80)

    # Check zone coverage
    zone_coverage = stats['zone_stats']['coverage_percent']
    print(f"\n[DIAGNOSTIC] Zone Coverage: {zone_coverage:.1f}% (target: {params['target_coverage']*100:.0f}%)")

    return terrain, stats


if __name__ == "__main__":
    terrain, stats = test_production_resolution()

    # Exit with error if failed
    if not stats['target_achieved']:
        print("\n[FAILURE] Buildability target NOT achieved!")
        sys.exit(1)
    else:
        print("\n[SUCCESS] Buildability target achieved!")
        sys.exit(0)
