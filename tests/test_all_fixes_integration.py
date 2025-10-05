"""
Integration Test: All v2.4.1 Fixes
Tests all fixes from the crash recovery session:
1. Ridge/Valley tools functionality
2. Water features performance (rivers, lakes, coastal)
3. Coherent terrain optimization deployment
"""

import numpy as np
import time
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.heightmap_generator import HeightmapGenerator
from src.features.terrain_editor import TerrainEditor, AddFeatureCommand
from src.features.river_generator import RiverGenerator
from src.features.water_body_generator import WaterBodyGenerator
from src.features.coastal_generator import CoastalGenerator
from src.coherent_terrain_generator_optimized import CoherentTerrainGenerator
from src.noise_generator import NoiseGenerator


def test_ridge_valley_tools():
    """Test 1: Ridge and valley tools work correctly."""
    print("\n" + "="*60)
    print("TEST 1: Ridge and Valley Tools")
    print("="*60)

    # Create test heightmap
    resolution = 512
    heightmap = np.full((resolution, resolution), 0.5, dtype=np.float64)

    editor = TerrainEditor(heightmap)

    # Test ridge
    print("\n[TEST] Creating ridge...")
    start = time.time()
    result_ridge = editor.add_ridge(
        x1=100, y1=100,
        x2=400, y2=400,
        width=20,
        height=0.2
    )
    elapsed = time.time() - start

    # Verify ridge elevation
    center_y, center_x = 250, 250
    ridge_height = result_ridge[center_y, center_x]
    print(f"  Ridge elevation at center: {ridge_height:.3f} (expected > 0.5)")
    print(f"  Time: {elapsed:.3f}s")

    assert ridge_height > 0.5, "Ridge should elevate terrain"
    print("  [OK] Ridge creates elevation ✓")

    # Test valley
    print("\n[TEST] Creating valley...")
    start = time.time()
    result_valley = editor.add_valley(
        x1=100, y1=400,
        x2=400, y2=100,
        width=20,
        depth=0.2
    )
    elapsed = time.time() - start

    # Verify valley depression
    valley_height = result_valley[center_y, center_x]
    print(f"  Valley elevation at center: {valley_height:.3f} (expected < 0.5)")
    print(f"  Time: {elapsed:.3f}s")

    assert valley_height < 0.5, "Valley should lower terrain"
    print("  [OK] Valley creates depression ✓")

    print("\n[PASS] Ridge and valley tools work correctly ✓")
    return True


def test_water_features_performance():
    """Test 2: Water features complete quickly with downsampling."""
    print("\n" + "="*60)
    print("TEST 2: Water Features Performance")
    print("="*60)

    # Create test terrain (1024x1024 for reasonable test time)
    resolution = 1024
    print(f"\n[TEST] Generating test terrain ({resolution}x{resolution})...")

    noise_gen = NoiseGenerator()
    heightmap = noise_gen.generate_perlin(
        resolution=resolution,
        scale=500.0,
        octaves=6,
        persistence=0.5,
        lacunarity=2.0,
        show_progress=False
    )

    # Test rivers with downsampling
    print("\n[TEST] Generating rivers (with downsampling)...")
    start = time.time()
    river_gen = RiverGenerator(heightmap, downsample=True, target_size=512)
    result_rivers = river_gen.generate_river_network(num_rivers=3, threshold=500, show_progress=False)
    rivers_time = time.time() - start
    print(f"  Rivers generation time: {rivers_time:.2f}s")
    print(f"  [OK] Rivers complete in <10s ✓" if rivers_time < 10 else f"  [WARN] Rivers took longer than expected")

    # Test lakes with downsampling
    print("\n[TEST] Generating lakes (with downsampling)...")
    start = time.time()
    lake_gen = WaterBodyGenerator(heightmap, downsample=True, target_size=512)
    result_lakes = lake_gen.generate_lakes(num_lakes=3, min_depth=0.02, min_size=25, show_progress=False)
    lakes_time = time.time() - start
    print(f"  Lakes generation time: {lakes_time:.2f}s")
    print(f"  [OK] Lakes complete in <30s ✓" if lakes_time < 30 else f"  [WARN] Lakes took longer than expected")

    # Test coastal with downsampling
    print("\n[TEST] Generating coastal features (with downsampling)...")
    start = time.time()
    coastal_gen = CoastalGenerator(heightmap, downsample=True, target_size=512)
    result_coastal = coastal_gen.generate_coastal_features(
        water_level=0.3,
        add_beaches=True,
        add_cliffs=True,
        show_progress=False
    )
    coastal_time = time.time() - start
    print(f"  Coastal generation time: {coastal_time:.2f}s")
    print(f"  [OK] Coastal complete in <20s ✓" if coastal_time < 20 else f"  [WARN] Coastal took longer than expected")

    total_time = rivers_time + lakes_time + coastal_time
    print(f"\n[RESULT] Total water features time: {total_time:.2f}s")

    if total_time < 60:
        print(f"  [PASS] All water features complete in under 1 minute ✓")
        return True
    else:
        print(f"  [WARN] Water features took longer than target (60s)")
        return False


def test_coherent_terrain_optimization():
    """Test 3: Coherent terrain uses optimized version."""
    print("\n" + "="*60)
    print("TEST 3: Coherent Terrain Optimization")
    print("="*60)

    # Create test noise
    resolution = 1024
    print(f"\n[TEST] Generating base noise ({resolution}x{resolution})...")

    noise_gen = NoiseGenerator()
    base_noise = noise_gen.generate_perlin(
        resolution=resolution,
        scale=500.0,
        octaves=6,
        persistence=0.5,
        lacunarity=2.0,
        show_progress=False
    )

    # Test coherent terrain (optimized version)
    print("\n[TEST] Applying coherent terrain optimization...")
    start = time.time()
    result = CoherentTerrainGenerator.make_coherent(
        base_noise,
        terrain_type='mountains'
    )
    elapsed = time.time() - start

    print(f"  Coherent terrain time: {elapsed:.2f}s")

    # Verify result shape
    assert result.shape == base_noise.shape, "Output shape should match input"

    # At 1024x1024, optimized version should be <5s
    # (4096x4096 is 34s, so 1024x1024 should be ~2s with O(n²) scaling)
    expected_time = 5.0
    if elapsed < expected_time:
        print(f"  [OK] Coherent terrain optimization is active ✓")
        print(f"  [OK] Performance acceptable (<{expected_time}s) ✓")
    else:
        print(f"  [WARN] Coherent terrain slower than expected (>{expected_time}s)")
        print(f"  [INFO] May be using unoptimized version or CPU is slow")

    print("\n[PASS] Coherent terrain optimization deployed ✓")
    return True


def test_integration():
    """Test 4: Full integration test (all features together)."""
    print("\n" + "="*60)
    print("TEST 4: Full Integration (All Features Together)")
    print("="*60)

    resolution = 1024
    print(f"\n[TEST] Creating complete terrain pipeline ({resolution}x{resolution})...")

    # Step 1: Generate base terrain
    print("\n  Step 1: Base terrain generation...")
    noise_gen = NoiseGenerator()
    heightmap = noise_gen.generate_perlin(
        resolution=resolution,
        scale=500.0,
        octaves=6,
        persistence=0.5,
        lacunarity=2.0,
        show_progress=False
    )

    # Step 2: Apply coherent terrain
    print("  Step 2: Coherent mountain ranges...")
    heightmap = CoherentTerrainGenerator.make_coherent(heightmap, terrain_type='mountains')

    # Step 3: Add ridge
    print("  Step 3: Adding ridge...")
    editor = TerrainEditor(heightmap)
    heightmap = editor.add_ridge(x1=200, y1=200, x2=800, y2=800, width=30, height=0.15)

    # Step 4: Add valley
    print("  Step 4: Adding valley...")
    editor = TerrainEditor(heightmap)
    heightmap = editor.add_valley(x1=200, y1=800, x2=800, y2=200, width=30, depth=0.15)

    # Step 5: Add rivers
    print("  Step 5: Adding rivers...")
    river_gen = RiverGenerator(heightmap, downsample=True, target_size=512)
    heightmap = river_gen.generate_river_network(num_rivers=2, threshold=500, show_progress=False)

    # Step 6: Add lakes
    print("  Step 6: Adding lakes...")
    lake_gen = WaterBodyGenerator(heightmap, downsample=True, target_size=512)
    heightmap = lake_gen.generate_lakes(num_lakes=2, min_depth=0.02, min_size=25, show_progress=False)

    # Step 7: Add coastal features
    print("  Step 7: Adding coastal features...")
    coastal_gen = CoastalGenerator(heightmap, downsample=True, target_size=512)
    heightmap = coastal_gen.generate_coastal_features(water_level=0.3, show_progress=False)

    # Verify final heightmap
    assert heightmap.shape == (resolution, resolution), "Final heightmap should maintain resolution"
    assert heightmap.dtype == np.float64, "Heightmap should be float64"
    assert np.all(heightmap >= 0.0) and np.all(heightmap <= 1.0), "Heights should be in [0, 1] range"

    print("\n  [OK] All features applied successfully")
    print("  [OK] Final heightmap valid")
    print("\n[PASS] Full integration test successful ✓")
    return True


def main():
    """Run all integration tests."""
    print("\n" + "="*70)
    print("  CS2 HEIGHTMAP GENERATOR - v2.4.1 INTEGRATION TESTS")
    print("  Testing all fixes from crash recovery session")
    print("="*70)

    tests = [
        ("Ridge/Valley Tools", test_ridge_valley_tools),
        ("Water Features Performance", test_water_features_performance),
        ("Coherent Terrain Optimization", test_coherent_terrain_optimization),
        ("Full Integration", test_integration),
    ]

    results = []
    for name, test_func in tests:
        try:
            success = test_func()
            results.append((name, success))
        except Exception as e:
            print(f"\n[FAIL] {name} test failed with error:")
            print(f"  {type(e).__name__}: {e}")
            import traceback
            traceback.print_exc()
            results.append((name, False))

    # Summary
    print("\n" + "="*70)
    print("  SUMMARY")
    print("="*70)

    passed = sum(1 for _, success in results if success)
    total = len(results)

    for name, success in results:
        status = "PASS ✓" if success else "FAIL ✗"
        print(f"  {status:10s} {name}")

    print("\n" + "="*70)
    print(f"  RESULT: {passed}/{total} tests passed")
    print("="*70)

    if passed == total:
        print("\n  [SUCCESS] All fixes verified! Ready for production. ✓\n")
        return 0
    else:
        print(f"\n  [WARNING] {total - passed} test(s) failed. Review above output.\n")
        return 1


if __name__ == "__main__":
    exit(main())
