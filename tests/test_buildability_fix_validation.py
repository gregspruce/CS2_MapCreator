"""
Validate Buildability Fix

Tests the corrected implementation with scale=500-800 for buildable zones.
Expected: 30-50% buildable terrain (vs <3% before fix).
"""

import numpy as np
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.noise_generator import NoiseGenerator
from src.coherent_terrain_generator_optimized import CoherentTerrainGenerator


def calculate_slope_percentage(heightmap: np.ndarray) -> np.ndarray:
    """Calculate slope percentage."""
    resolution = heightmap.shape[0]
    map_size_meters = 14336.0
    pixel_size_meters = map_size_meters / resolution
    heightmap_meters = heightmap * 1024.0
    dy, dx = np.gradient(heightmap_meters)
    slope_ratio = np.sqrt(dx**2 + dy**2) / pixel_size_meters
    return slope_ratio * 100.0


def test_fixed_buildability():
    """Test buildability with corrected parameters."""
    print("\n" + "="*80)
    print("BUILDABILITY FIX VALIDATION")
    print("="*80)
    print("\nTesting corrected implementation:")
    print("  Buildable zones: scale=500, octaves=2, persistence=0.3")
    print("  Scenic zones: scale=100, octaves=8, persistence=0.5")
    print("  WITH coherent terrain applied")
    print("  WITH domain warping (creates needed variation)")
    print("\n")

    resolution = 1024  # Medium resolution for reasonable test time
    gen = NoiseGenerator(seed=42)
    user_scale = 100  # Typical user setting

    # Generate control map
    print("Generating control map (target=50%)...")
    control_map = gen.generate_buildability_control_map(
        resolution=resolution,
        target_percent=50.0,
        seed=42,
        smoothing_radius=max(10, resolution // 100)
    )

    # Generate buildable terrain with CORRECTED scale
    buildable_scale = max(500, user_scale * 5)
    print(f"\nGenerating buildable terrain (scale={buildable_scale})...")
    heightmap_smooth = gen.generate_perlin(
        resolution=resolution,
        scale=buildable_scale,  # CORRECTED: Large scale
        octaves=2,
        persistence=0.3,
        lacunarity=2.0,
        show_progress=True,
        domain_warp_amp=60.0,
        recursive_warp=True
    )

    # Apply coherent terrain to buildable
    print("\nApplying coherent terrain to buildable zones...")
    heightmap_smooth_coherent = CoherentTerrainGenerator.make_coherent(
        heightmap_smooth,
        terrain_type='mountains',
        apply_erosion=False
    )

    # Generate scenic terrain (user scale)
    print(f"\nGenerating scenic terrain (scale={user_scale})...")
    heightmap_detailed = gen.generate_perlin(
        resolution=resolution,
        scale=user_scale,
        octaves=8,
        persistence=0.5,
        lacunarity=2.0,
        show_progress=True,
        domain_warp_amp=60.0,
        recursive_warp=True
    )

    # Apply coherent terrain to scenic
    print("\nApplying coherent terrain to scenic zones...")
    heightmap_detailed_coherent = CoherentTerrainGenerator.make_coherent(
        heightmap_detailed,
        terrain_type='mountains',
        apply_erosion=False
    )

    # Blend
    print("\nBlending terrains based on control map...")
    heightmap_final = (heightmap_smooth_coherent * control_map +
                      heightmap_detailed_coherent * (1.0 - control_map))

    # Analyze each component
    print("\n" + "-"*80)
    print("ANALYSIS")
    print("-"*80)

    for label, hmap in [
        ("Buildable (before coherent)", heightmap_smooth),
        ("Buildable (after coherent)", heightmap_smooth_coherent),
        ("Scenic (before coherent)", heightmap_detailed),
        ("Scenic (after coherent)", heightmap_detailed_coherent),
        ("Final blended terrain", heightmap_final)
    ]:
        slopes = calculate_slope_percentage(hmap)
        buildable = np.sum(slopes <= 5.0)
        total = slopes.size
        buildable_pct = (buildable / total) * 100

        print(f"\n{label}:")
        print(f"  Buildable (0-5%): {buildable_pct:.1f}%")
        print(f"  Mean slope: {slopes.mean():.1f}%")
        print(f"  P50 slope: {np.percentile(slopes, 50):.1f}%")
        print(f"  P90 slope: {np.percentile(slopes, 90):.1f}%")

    # Final verdict
    slopes_final = calculate_slope_percentage(heightmap_final)
    buildable_final = (np.sum(slopes_final <= 5.0) / slopes_final.size) * 100

    print("\n" + "="*80)
    print("VERDICT")
    print("="*80)
    print(f"\nFinal buildability: {buildable_final:.1f}%")

    if buildable_final >= 25:
        print(f"[SUCCESS] Buildability significantly improved!")
        print(f"  Before fix: ~2-3% buildable")
        print(f"  After fix: {buildable_final:.1f}% buildable")
        if 30 <= buildable_final <= 50:
            print(f"  [EXCELLENT] Within optimal range (30-50%)")
        else:
            print(f"  [GOOD] Approaching target, may need further tuning")
    else:
        print(f"[WARNING] Buildability still low")
        print(f"  May need additional parameter adjustments")

    print("\n" + "="*80)
    print("VALIDATION COMPLETE")
    print("="*80)

    return buildable_final


if __name__ == "__main__":
    try:
        buildability = test_fixed_buildability()
        sys.exit(0 if buildability >= 25 else 1)
    except Exception as e:
        print(f"\n[ERROR] Validation failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
