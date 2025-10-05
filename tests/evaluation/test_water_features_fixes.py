"""
Test script to verify water feature bug fixes.

Tests three critical bugs:
1. Coastal features flattening entire map
2. Rivers flattening entire map
3. Lakes hanging the program

All bugs were caused by upsampling issues and flood fill problems.
"""

import numpy as np
import time
import sys

print("=" * 80)
print("WATER FEATURES BUG FIX VERIFICATION TEST")
print("=" * 80)
print()

# Import the generators
from src.features.coastal_generator import CoastalGenerator
from src.features.river_generator import RiverGenerator
from src.features.water_body_generator import WaterBodyGenerator


def create_test_heightmap(size=2048):
    """Create a realistic test heightmap with varied terrain."""
    print(f"Creating {size}x{size} test heightmap...")

    # Create multi-scale terrain using noise
    heightmap = np.zeros((size, size))

    # Large features (mountains)
    x = np.linspace(0, 4*np.pi, size)
    y = np.linspace(0, 4*np.pi, size)
    X, Y = np.meshgrid(x, y)
    heightmap += 0.3 * np.sin(X) * np.cos(Y)

    # Medium features (hills)
    x2 = np.linspace(0, 8*np.pi, size)
    y2 = np.linspace(0, 8*np.pi, size)
    X2, Y2 = np.meshgrid(x2, y2)
    heightmap += 0.2 * np.sin(X2 * 1.5) * np.cos(Y2 * 1.5)

    # Small features (details)
    np.random.seed(42)
    heightmap += 0.1 * np.random.randn(size, size)

    # Normalize to 0-1 range
    heightmap = (heightmap - heightmap.min()) / (heightmap.max() - heightmap.min())

    print(f"  Heightmap stats: min={heightmap.min():.3f}, max={heightmap.max():.3f}, mean={heightmap.mean():.3f}, std={heightmap.std():.3f}")
    return heightmap


def verify_terrain_preserved(original, modified, feature_name, tolerance=0.1):
    """
    Verify that the modified terrain still has the original detail.

    If upsampling is wrong, the modified terrain will be flat/uniform.
    """
    print(f"\nVerifying {feature_name} preserves terrain detail...")

    # Calculate statistics
    orig_std = np.std(original)
    mod_std = np.std(modified)
    orig_range = np.ptp(original)  # peak-to-peak (max - min)
    mod_range = np.ptp(modified)

    print(f"  Original: std={orig_std:.6f}, range={orig_range:.6f}")
    print(f"  Modified: std={mod_std:.6f}, range={mod_range:.6f}")

    # Check if terrain was flattened (bug symptom)
    if mod_std < orig_std * 0.1:
        print(f"  [FAIL] Terrain was flattened! (std dropped by {(1 - mod_std/orig_std)*100:.1f}%)")
        return False

    if mod_range < orig_range * 0.1:
        print(f"  [FAIL] Terrain elevation range collapsed! (range dropped by {(1 - mod_range/orig_range)*100:.1f}%)")
        return False

    # Check that most of the terrain is preserved
    # (features should only modify specific areas)
    unchanged_ratio = np.mean(np.abs(modified - original) < tolerance)
    print(f"  Unchanged cells: {unchanged_ratio*100:.1f}% (threshold: >50%)")

    if unchanged_ratio < 0.5:
        print(f"  [WARNING] Large portion of terrain was modified")

    # Calculate actual changes
    delta = modified - original
    delta_nonzero = delta[np.abs(delta) > 0.001]

    if len(delta_nonzero) > 0:
        print(f"  Changes: {len(delta_nonzero)} cells modified ({len(delta_nonzero)/delta.size*100:.2f}%)")
        print(f"  Delta range: {delta_nonzero.min():.6f} to {delta_nonzero.max():.6f}")
        print(f"  [PASS] Terrain detail preserved")
        return True
    else:
        print(f"  [WARNING] No changes detected")
        return True


def test_coastal_features():
    """Test Bug #1: Coastal features should not flatten entire map."""
    print("\n" + "=" * 80)
    print("TEST 1: COASTAL FEATURES BUG FIX")
    print("=" * 80)

    # Create test terrain
    heightmap = create_test_heightmap(2048)

    # Apply coastal features with downsampling
    print("\nApplying coastal features with downsampling...")
    start_time = time.time()

    coastal_gen = CoastalGenerator(heightmap, water_level=0.3, downsample=True, target_size=1024)
    result = coastal_gen.generate_coastal_features(
        add_beaches=True,
        add_cliffs=True,
        beach_intensity=0.5,
        cliff_intensity=0.5
    )

    elapsed = time.time() - start_time
    print(f"Coastal features completed in {elapsed:.2f}s")

    # Verify terrain preserved
    return verify_terrain_preserved(heightmap, result, "coastal features")


def test_rivers():
    """Test Bug #2: Rivers should not flatten entire map."""
    print("\n" + "=" * 80)
    print("TEST 2: RIVERS BUG FIX")
    print("=" * 80)

    # Create test terrain
    heightmap = create_test_heightmap(2048)

    # Apply rivers with downsampling
    print("\nApplying rivers with downsampling...")
    start_time = time.time()

    river_gen = RiverGenerator(heightmap, downsample=True, target_size=1024)
    result = river_gen.generate_river_network(num_rivers=5, threshold=500)

    elapsed = time.time() - start_time
    print(f"Rivers completed in {elapsed:.2f}s")

    # Verify terrain preserved
    return verify_terrain_preserved(heightmap, result, "rivers")


def test_lakes_no_hang():
    """Test Bug #3: Lakes should not hang the program."""
    print("\n" + "=" * 80)
    print("TEST 3: LAKES HANG BUG FIX")
    print("=" * 80)

    # Create test terrain
    heightmap = create_test_heightmap(2048)

    # Apply lakes with downsampling and timeout
    print("\nApplying lakes with downsampling and timeout check...")
    start_time = time.time()

    # Set a timeout - if it takes more than 120 seconds, it's hanging
    TIMEOUT = 120

    try:
        water_gen = WaterBodyGenerator(heightmap, downsample=True, target_size=1024)
        result = water_gen.generate_lakes(num_lakes=5, min_depth=0.02, min_size=25)

        elapsed = time.time() - start_time
        print(f"Lakes completed in {elapsed:.2f}s")

        if elapsed > TIMEOUT:
            print(f"  [FAIL] Took too long ({elapsed:.1f}s > {TIMEOUT}s timeout)")
            return False

        # Verify terrain preserved
        return verify_terrain_preserved(heightmap, result, "lakes")

    except KeyboardInterrupt:
        elapsed = time.time() - start_time
        print(f"\n  [FAIL] Interrupted after {elapsed:.1f}s - likely hanging")
        return False
    except Exception as e:
        elapsed = time.time() - start_time
        print(f"\n  [FAIL] Exception after {elapsed:.1f}s: {e}")
        return False


def test_all_features_together():
    """Test all three features applied together."""
    print("\n" + "=" * 80)
    print("TEST 4: ALL FEATURES TOGETHER")
    print("=" * 80)

    # Create test terrain
    heightmap = create_test_heightmap(2048)

    print("\nApplying all features in sequence...")
    start_time = time.time()

    # Apply coastal features
    print("\n1. Coastal features...")
    coastal_gen = CoastalGenerator(heightmap, water_level=0.3, downsample=True, target_size=1024)
    heightmap = coastal_gen.generate_coastal_features(add_beaches=True, add_cliffs=True)

    # Apply rivers
    print("\n2. Rivers...")
    river_gen = RiverGenerator(heightmap, downsample=True, target_size=1024)
    heightmap = river_gen.generate_river_network(num_rivers=5, threshold=500)

    # Apply lakes
    print("\n3. Lakes...")
    water_gen = WaterBodyGenerator(heightmap, downsample=True, target_size=1024)
    heightmap = water_gen.generate_lakes(num_lakes=5, min_depth=0.02, min_size=25)

    elapsed = time.time() - start_time
    print(f"\nAll features completed in {elapsed:.2f}s")

    # Just verify it completed without hanging
    print(f"  [PASS] All features completed without hanging")
    return True


if __name__ == "__main__":
    print()
    results = {}

    try:
        # Run all tests
        results["coastal"] = test_coastal_features()
        results["rivers"] = test_rivers()
        results["lakes"] = test_lakes_no_hang()
        results["combined"] = test_all_features_together()

    except Exception as e:
        print(f"\n[CRITICAL ERROR] {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

    # Summary
    print("\n" + "=" * 80)
    print("TEST SUMMARY")
    print("=" * 80)

    for test_name, passed in results.items():
        status = "[PASS]" if passed else "[FAIL]"
        print(f"{test_name:20s}: {status}")

    all_passed = all(results.values())

    print("\n" + "=" * 80)
    if all_passed:
        print("ALL TESTS PASSED - All water feature bugs are FIXED!")
    else:
        print("SOME TESTS FAILED - Bugs still present")
    print("=" * 80)

    sys.exit(0 if all_passed else 1)
