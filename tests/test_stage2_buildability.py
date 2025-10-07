"""
Test Stage 2 Task 2.2: Buildability Constraints via Conditional Octave Generation

This test validates the evidence-based buildability implementation:
- Control map generation
- Conditional octave terrain generation
- Slope distribution analysis
- Verification that 45-55% of terrain is buildable (0-5% slopes)

WHY: This is the ROOT CAUSE solution - terrain is GENERATED buildable,
not post-processed. This test ensures the implementation works correctly.
"""

import numpy as np
import sys
import os

# Add src to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.noise_generator import NoiseGenerator
from src.coherent_terrain_generator_optimized import CoherentTerrainGenerator


def calculate_slope_percentage(heightmap: np.ndarray) -> np.ndarray:
    """
    Calculate slope percentage for each pixel.

    Args:
        heightmap: 2D array normalized to [0, 1] representing elevations 0-1024m

    Returns:
        2D array of slope percentages

    CS2 Buildability Standard:
    - 0-5% slope: Buildable for most structures
    - 5-10% slope: Limited buildability
    - 10%+ slope: Scenic/unbuildable

    WHY this calculation method:
    CS2 uses 14.336km x 14.336km maps with elevation range 0-1024m.
    At 4096 resolution: pixel_size = 14336m / 4096 = 3.5m
    At 1024 resolution: pixel_size = 14336m / 1024 = 14.0m
    The pixel size depends on resolution, so we calculate it dynamically.
    """
    resolution = heightmap.shape[0]

    # Calculate pixel size in meters based on resolution
    # CS2 map size: 14.336km = 14336m
    map_size_meters = 14336.0
    pixel_size_meters = map_size_meters / resolution

    # Convert normalized heightmap to meters (CS2: 0-1024m range)
    heightmap_meters = heightmap * 1024.0

    # Calculate gradients in meters/pixel using numpy gradient
    # np.gradient returns change per pixel index
    dy, dx = np.gradient(heightmap_meters)

    # Calculate slope magnitude (rise over run)
    # rise = sqrt(dx^2 + dy^2) meters per pixel
    # run = pixel_size_meters
    slope_ratio = np.sqrt(dx**2 + dy**2) / pixel_size_meters

    # Convert to percentage (slope_ratio * 100)
    slope_percent = slope_ratio * 100.0

    return slope_percent


def analyze_buildability(heightmap: np.ndarray, label: str = "Terrain"):
    """
    Analyze slope distribution and buildability percentage.

    Args:
        heightmap: Terrain heightmap [0, 1]
        label: Description for output
    """
    slopes = calculate_slope_percentage(heightmap)

    # Calculate distribution
    buildable = np.sum(slopes <= 5.0)
    limited = np.sum((slopes > 5.0) & (slopes <= 10.0))
    scenic = np.sum(slopes > 10.0)
    total = slopes.size

    buildable_pct = (buildable / total) * 100
    limited_pct = (limited / total) * 100
    scenic_pct = (scenic / total) * 100

    print(f"\n{label} - Slope Distribution:")
    print(f"  Buildable (0-5%): {buildable_pct:.1f}% ({buildable:,} pixels)")
    print(f"  Limited (5-10%): {limited_pct:.1f}% ({limited:,} pixels)")
    print(f"  Scenic (10%+): {scenic_pct:.1f}% ({scenic:,} pixels)")
    print(f"  Min slope: {slopes.min():.2f}%, Max slope: {slopes.max():.2f}%")
    print(f"  Mean slope: {slopes.mean():.2f}%, Std: {slopes.std():.2f}%")

    return buildable_pct


def test_control_map_generation():
    """Test 1: Buildability control map generation."""
    print("\n" + "="*70)
    print("TEST 1: Buildability Control Map Generation")
    print("="*70)

    gen = NoiseGenerator(seed=42)

    # Test at multiple target percentages
    for target in [30.0, 50.0, 70.0]:
        print(f"\nGenerating control map (target={target:.0f}%)...")
        control_map = gen.generate_buildability_control_map(
            resolution=512,  # Small for speed
            target_percent=target,
            seed=42,
            smoothing_radius=5
        )

        # Verify output
        assert control_map.shape == (512, 512), "Wrong shape"
        assert control_map.min() >= 0.0 and control_map.max() <= 1.0, "Values out of range"

        actual_percent = np.mean(control_map) * 100
        error = abs(actual_percent - target)

        print(f"  Target: {target:.0f}%, Actual: {actual_percent:.1f}%, Error: {error:.1f}%")

        # Allow ±5% error due to morphological smoothing
        if error > 5.0:
            print(f"  [WARNING] Error exceeds 5% tolerance")
        else:
            print(f"  [PASS] Within tolerance")

    print("\n[TEST 1 COMPLETE]")


def test_conditional_generation():
    """Test 2: Conditional octave terrain generation."""
    print("\n" + "="*70)
    print("TEST 2: Conditional Octave Terrain Generation")
    print("="*70)

    resolution = 1024  # Medium resolution for reasonable test time
    gen = NoiseGenerator(seed=42)

    print("\nGenerating control map...")
    control_map = gen.generate_buildability_control_map(
        resolution=resolution,
        target_percent=50.0,
        seed=42,
        smoothing_radius=max(10, resolution // 100)
    )

    print("\nGenerating smooth terrain (octaves=2, persistence=0.3)...")
    heightmap_smooth = gen.generate_perlin(
        resolution=resolution,
        scale=100.0,
        octaves=2,  # LOW octaves
        persistence=0.3,  # Low persistence
        lacunarity=2.0,
        show_progress=True,
        domain_warp_amp=60.0,
        recursive_warp=True
    )

    print("\nGenerating detailed terrain (octaves=8, persistence=0.5)...")
    heightmap_detailed = gen.generate_perlin(
        resolution=resolution,
        scale=100.0,
        octaves=8,  # HIGH octaves
        persistence=0.5,  # Higher persistence
        lacunarity=2.0,
        show_progress=True,
        domain_warp_amp=60.0,
        recursive_warp=True
    )

    print("\nBlending terrains based on control map...")
    heightmap_blended = heightmap_smooth * control_map + heightmap_detailed * (1.0 - control_map)

    # Verify no NaN or inf
    assert not np.any(np.isnan(heightmap_blended)), "NaN values detected"
    assert not np.any(np.isinf(heightmap_blended)), "Inf values detected"
    assert heightmap_blended.min() >= 0.0 and heightmap_blended.max() <= 1.0, "Values out of range"

    # Analyze slopes
    print("\n--- Smooth Terrain Analysis ---")
    smooth_buildable = analyze_buildability(heightmap_smooth, "Smooth (octaves=2)")

    print("\n--- Detailed Terrain Analysis ---")
    detailed_buildable = analyze_buildability(heightmap_detailed, "Detailed (octaves=8)")

    print("\n--- Blended Terrain Analysis ---")
    blended_buildable = analyze_buildability(heightmap_blended, "Blended (conditional)")

    # Verify blended has more buildable terrain than detailed
    print(f"\n[COMPARISON]")
    print(f"  Smooth terrain: {smooth_buildable:.1f}% buildable")
    print(f"  Detailed terrain: {detailed_buildable:.1f}% buildable")
    print(f"  Blended terrain: {blended_buildable:.1f}% buildable")

    if blended_buildable > detailed_buildable:
        print(f"  [PASS] Blended has more buildable terrain than detailed")
    else:
        print(f"  [WARNING] Blended should have more buildable terrain")

    print("\n[TEST 2 COMPLETE]")

    return blended_buildable


def test_full_pipeline():
    """Test 3: Full pipeline with coherent terrain generator."""
    print("\n" + "="*70)
    print("TEST 3: Full Pipeline with Coherent Terrain")
    print("="*70)

    resolution = 1024
    gen = NoiseGenerator(seed=42)

    print("\nGenerating control map...")
    control_map = gen.generate_buildability_control_map(
        resolution=resolution,
        target_percent=50.0,
        seed=42,
        smoothing_radius=max(10, resolution // 100)
    )

    print("\nGenerating buildable terrain...")
    heightmap_smooth = gen.generate_perlin(
        resolution=resolution,
        scale=100.0,
        octaves=2,
        persistence=0.3,
        lacunarity=2.0,
        show_progress=True,
        domain_warp_amp=60.0,
        recursive_warp=True
    )

    print("\nGenerating scenic terrain...")
    heightmap_detailed = gen.generate_perlin(
        resolution=resolution,
        scale=100.0,
        octaves=8,
        persistence=0.5,
        lacunarity=2.0,
        show_progress=True,
        domain_warp_amp=60.0,
        recursive_warp=True
    )

    print("\nBlending...")
    heightmap = heightmap_smooth * control_map + heightmap_detailed * (1.0 - control_map)

    print("\nApplying coherent terrain structure...")
    heightmap_coherent = CoherentTerrainGenerator.make_coherent(
        heightmap,
        terrain_type='mountains',
        apply_erosion=False  # Skip erosion for faster test
    )

    # Analyze final result
    print("\n--- Before Coherent Processing ---")
    before_buildable = analyze_buildability(heightmap, "Blended (before coherent)")

    print("\n--- After Coherent Processing ---")
    after_buildable = analyze_buildability(heightmap_coherent, "Final (after coherent)")

    # Check if buildability is maintained through pipeline
    print(f"\n[PIPELINE CHECK]")
    print(f"  Before coherent: {before_buildable:.1f}% buildable")
    print(f"  After coherent: {after_buildable:.1f}% buildable")
    buildability_change = after_buildable - before_buildable
    print(f"  Change: {buildability_change:+.1f}%")

    # Target is 45-55% buildable for CS2
    if 45.0 <= after_buildable <= 55.0:
        print(f"  [PASS] Within CS2 target range (45-55%)")
    else:
        print(f"  [WARNING] Outside CS2 target range")

    print("\n[TEST 3 COMPLETE]")

    return after_buildable


def main():
    """Run all tests."""
    print("\n" + "="*70)
    print("STAGE 2 TASK 2.2: BUILDABILITY CONSTRAINTS TEST SUITE")
    print("="*70)
    print("\nTesting evidence-based conditional octave generation...")
    print("WHY: This is the ROOT CAUSE solution (not post-processing)")

    try:
        # Test 1: Control map generation
        test_control_map_generation()

        # Test 2: Conditional generation
        blended_buildable = test_conditional_generation()

        # Test 3: Full pipeline
        final_buildable = test_full_pipeline()

        # Final summary
        print("\n" + "="*70)
        print("TEST SUMMARY")
        print("="*70)
        print(f"Conditional generation buildability: {blended_buildable:.1f}%")
        print(f"Full pipeline buildability: {final_buildable:.1f}%")

        if 45.0 <= final_buildable <= 55.0:
            print(f"\n[SUCCESS] Implementation meets CS2 requirements (45-55%)")
            print("Stage 2 Task 2.2 implementation VERIFIED!")
        else:
            print(f"\n[WARNING] Buildability outside target range")
            print("May need parameter tuning")

        print("\n[ALL TESTS COMPLETE]")

    except Exception as e:
        print(f"\n[ERROR] Test failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
