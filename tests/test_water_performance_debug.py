"""
Test water features performance with debug logging.

This script tests all three water features (rivers, lakes, coastal) to:
1. Verify downsampling is activated
2. Measure actual performance
3. Confirm <1 minute generation time at 4096x4096
"""

import numpy as np
import time
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.features.river_generator import RiverGenerator
from src.features.water_body_generator import WaterBodyGenerator
from src.features.coastal_generator import CoastalGenerator


def create_test_heightmap(size: int) -> np.ndarray:
    """Create a simple test heightmap for performance testing."""
    print(f"\n[TEST] Creating {size}x{size} test heightmap...")

    # Create a simple gradient with some noise
    x = np.linspace(0, 1, size)
    y = np.linspace(0, 1, size)
    X, Y = np.meshgrid(x, y)

    # Base terrain: gradient from low (left) to high (right)
    heightmap = X * 0.5 + Y * 0.3

    # Add some random variation
    np.random.seed(42)
    heightmap += np.random.random((size, size)) * 0.2

    # Normalize to 0-1
    heightmap = np.clip(heightmap, 0, 1)

    print(f"[TEST] Test heightmap created: min={heightmap.min():.3f}, max={heightmap.max():.3f}")
    return heightmap


def test_rivers(heightmap: np.ndarray):
    """Test river generation with debug output."""
    print("\n" + "="*70)
    print("TESTING RIVER GENERATION")
    print("="*70)

    start = time.time()

    # Test with downsampling (default)
    print("\n[TEST] Creating RiverGenerator with downsampling=True...")
    river_gen = RiverGenerator(heightmap, downsample=True, target_size=1024)

    print("\n[TEST] Generating river network...")
    result = river_gen.generate_river_network(num_rivers=3, threshold=100, show_progress=False)

    elapsed = time.time() - start
    print(f"\n[TEST] [OK] River generation completed in {elapsed:.2f}s")
    print(f"[TEST] Result shape: {result.shape}")

    # Verify result
    if result.shape != heightmap.shape:
        print(f"[TEST] [ERROR] Result shape mismatch! Expected {heightmap.shape}, got {result.shape}")
    else:
        print(f"[TEST] [OK] Result shape matches input")

    return elapsed


def test_lakes(heightmap: np.ndarray):
    """Test lake generation with debug output."""
    print("\n" + "="*70)
    print("TESTING LAKE GENERATION")
    print("="*70)

    start = time.time()

    # Test with downsampling (default)
    print("\n[TEST] Creating WaterBodyGenerator with downsampling=True...")
    lake_gen = WaterBodyGenerator(heightmap, downsample=True, target_size=1024)

    print("\n[TEST] Generating lakes...")
    result = lake_gen.generate_lakes(num_lakes=3, min_depth=0.02, show_progress=False)

    elapsed = time.time() - start
    print(f"\n[TEST] [OK] Lake generation completed in {elapsed:.2f}s")
    print(f"[TEST] Result shape: {result.shape}")

    # Verify result
    if result.shape != heightmap.shape:
        print(f"[TEST] [ERROR] Result shape mismatch! Expected {heightmap.shape}, got {result.shape}")
    else:
        print(f"[TEST] [OK] Result shape matches input")

    return elapsed


def test_coastal(heightmap: np.ndarray):
    """Test coastal generation with debug output."""
    print("\n" + "="*70)
    print("TESTING COASTAL GENERATION")
    print("="*70)

    start = time.time()

    # Test with downsampling (default)
    print("\n[TEST] Creating CoastalGenerator with downsampling=True...")
    coastal_gen = CoastalGenerator(heightmap, water_level=0.3, downsample=True, target_size=1024)

    print("\n[TEST] Generating coastal features...")
    result = coastal_gen.generate_coastal_features(
        add_beaches=True,
        add_cliffs=True,
        show_progress=False
    )

    elapsed = time.time() - start
    print(f"\n[TEST] [OK] Coastal generation completed in {elapsed:.2f}s")
    print(f"[TEST] Result shape: {result.shape}")

    # Verify result
    if result.shape != heightmap.shape:
        print(f"[TEST] [ERROR] Result shape mismatch! Expected {heightmap.shape}, got {result.shape}")
    else:
        print(f"[TEST] [OK] Result shape matches input")

    return elapsed


def main():
    """Run all water feature performance tests."""
    print("="*70)
    print("WATER FEATURES PERFORMANCE DEBUG TEST")
    print("="*70)
    print("Testing downsampling activation and performance at 4096x4096")
    print()

    # Test at multiple resolutions
    test_sizes = [1024, 2048, 4096]

    results = {}

    for size in test_sizes:
        print("\n" + "#"*70)
        print(f"# TESTING AT RESOLUTION: {size}x{size}")
        print("#"*70)

        heightmap = create_test_heightmap(size)

        results[size] = {
            'rivers': test_rivers(heightmap),
            'lakes': test_lakes(heightmap),
            'coastal': test_coastal(heightmap)
        }

    # Summary
    print("\n" + "="*70)
    print("PERFORMANCE SUMMARY")
    print("="*70)

    for size in test_sizes:
        print(f"\n{size}x{size} Resolution:")
        print(f"  Rivers:  {results[size]['rivers']:6.2f}s")
        print(f"  Lakes:   {results[size]['lakes']:6.2f}s")
        print(f"  Coastal: {results[size]['coastal']:6.2f}s")
        print(f"  TOTAL:   {sum(results[size].values()):6.2f}s")

        # Check if under 1 minute
        total = sum(results[size].values())
        if total < 60:
            print(f"  [OK] PASS: Under 1 minute!")
        else:
            print(f"  [FAIL] Over 1 minute ({total/60:.1f} minutes)")

    # Check 4096 specifically
    print("\n" + "="*70)
    print("4096x4096 PERFORMANCE CHECK")
    print("="*70)

    total_4096 = sum(results[4096].values())
    print(f"Total time: {total_4096:.2f}s ({total_4096/60:.1f} minutes)")

    if total_4096 < 60:
        print("[OK] SUCCESS: All water features complete in under 1 minute!")
    else:
        print(f"[FAIL] Taking {total_4096/60:.1f} minutes (target: <1 minute)")
        print("\nDEBUG: Check the debug output above to see if downsampling was activated")


if __name__ == "__main__":
    main()
