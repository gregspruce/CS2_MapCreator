"""
Final Buildability Fix Validation

Tests the CORRECT pipeline implementation:
- Buildable zones: Pure smooth terrain (NO coherent/realism processing)
- Scenic zones: Full pipeline (coherent + realism)
- Blend AFTER processing scenic

This should finally achieve buildable terrain!
"""

import numpy as np
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.noise_generator import NoiseGenerator
from src.coherent_terrain_generator_optimized import CoherentTerrainGenerator
from src.terrain_realism import TerrainRealism


def calculate_slope_percentage(heightmap: np.ndarray) -> np.ndarray:
    """Calculate slope percentage."""
    resolution = heightmap.shape[0]
    map_size_meters = 14336.0
    pixel_size_meters = map_size_meters / resolution
    heightmap_meters = heightmap * 1024.0
    dy, dx = np.gradient(heightmap_meters)
    slope_ratio = np.sqrt(dx**2 + dy**2) / pixel_size_meters
    return slope_ratio * 100.0


def analyze(heightmap: np.ndarray, label: str):
    """Analyze and print buildability metrics."""
    slopes = calculate_slope_percentage(heightmap)
    buildable_pct = (np.sum(slopes <= 5.0) / slopes.size) * 100
    mean_slope = slopes.mean()
    p50_slope = np.percentile(slopes, 50)
    p90_slope = np.percentile(slopes, 90)

    print(f"\n{label}:")
    print(f"  Buildable (0-5%): {buildable_pct:.1f}%")
    print(f"  Mean slope: {mean_slope:.1f}%")
    print(f"  P50 slope: {p50_slope:.1f}%")
    print(f"  P90 slope: {p90_slope:.1f}%")

    return buildable_pct


def main():
    """Test the corrected pipeline implementation."""
    print("\n" + "="*80)
    print("FINAL BUILDABILITY FIX VALIDATION")
    print("="*80)
    print("\nTesting CORRECTED pipeline:")
    print("  1. Generate buildable (scale=4000, octaves=2) - KEEP PURE")
    print("  2. Generate scenic (scale=100, octaves=8)")
    print("  3. Apply full pipeline to SCENIC ONLY (coherent + realism)")
    print("  4. Blend processed scenic with pure buildable")
    print("\nKey fix: Buildable zones NEVER go through coherent/realism pipeline!")
    print("="*80)

    resolution = 1024  # Test at reasonable resolution
    gen = NoiseGenerator(seed=42)

    # Step 1: Generate control map
    print("\n[1/5] Generating control map...")
    control_map = gen.generate_buildability_control_map(
        resolution=resolution,
        target_percent=50.0,
        seed=42,
        smoothing_radius=max(10, resolution // 100)
    )

    # Step 2: Generate buildable terrain (KEEP PURE!)
    buildable_scale = 500 * (resolution / 512)  # Resolution-scaled
    print(f"\n[2/5] Generating buildable terrain (scale={buildable_scale:.0f})...")
    heightmap_buildable = gen.generate_perlin(
        resolution=resolution,
        scale=buildable_scale,
        octaves=2,
        persistence=0.3,
        lacunarity=2.0,
        show_progress=False,
        domain_warp_amp=0.0,  # CRITICAL FIX: NO domain warp for buildable!
        recursive_warp=False  # NO recursive warping - keep smooth
    )
    buildable_pct_pure = analyze(heightmap_buildable, "Buildable terrain (PURE, no pipeline)")

    # Step 3: Generate scenic terrain
    print(f"\n[3/5] Generating scenic terrain (scale=100)...")
    heightmap_scenic = gen.generate_perlin(
        resolution=resolution,
        scale=100,
        octaves=8,
        persistence=0.5,
        lacunarity=2.0,
        show_progress=False,
        domain_warp_amp=60.0,
        recursive_warp=True
    )

    # Step 4: Apply full pipeline to SCENIC ONLY
    print(f"\n[4/5] Applying pipeline to SCENIC terrain only...")
    print("  - Applying coherent terrain...")
    heightmap_scenic_processed = CoherentTerrainGenerator.make_coherent(
        heightmap_scenic,
        terrain_type='mountains',
        apply_erosion=False
    )
    print("  - Applying terrain realism...")
    heightmap_scenic_processed = TerrainRealism.make_realistic(
        heightmap_scenic_processed,
        terrain_type='mountains',
        enable_warping=True,
        enable_ridges=True,
        enable_valleys=True,
        enable_plateaus=False,
        enable_erosion=True
    )
    scenic_pct_processed = analyze(heightmap_scenic_processed, "Scenic terrain (AFTER pipeline)")

    # Step 5: Blend (pure buildable + processed scenic)
    # CRITICAL: Binarize control map to prevent blending contamination
    control_map_binary = (control_map >= 0.5).astype(np.float64)
    print(f"\n[5/5] Blending with BINARY control map (pure buildable + processed scenic)...")
    heightmap_final = (heightmap_buildable * control_map_binary +
                      heightmap_scenic_processed * (1.0 - control_map_binary))
    final_pct = analyze(heightmap_final, "FINAL blended terrain")

    # Verdict
    print("\n" + "="*80)
    print("VERDICT")
    print("="*80)
    print(f"\nPure buildable terrain: {buildable_pct_pure:.1f}% buildable")
    print(f"Final blended terrain: {final_pct:.1f}% buildable")
    print(f"Control map target: 50.0% buildable zones\n")

    if final_pct >= 20:
        print(f"[SUCCESS] Buildability SIGNIFICANTLY improved!")
        print(f"  Before fix: ~0-2% buildable")
        print(f"  After fix: {final_pct:.1f}% buildable")
        if 25 <= final_pct <= 55:
            print(f"  [EXCELLENT] Within acceptable range for CS2")
        else:
            print(f"  [GOOD] Approaching target, may benefit from parameter tuning")
    else:
        print(f"[PARTIAL] Some improvement but still needs work")
        print(f"  Current: {final_pct:.1f}%")
        print(f"  Target: 25-55% for CS2 gameplay")

    print("\n" + "="*80)
    print("ANALYSIS COMPLETE")
    print("="*80)

    return final_pct


if __name__ == "__main__":
    try:
        buildability = main()
        sys.exit(0 if buildability >= 20 else 1)
    except Exception as e:
        print(f"\n[ERROR] Test failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
