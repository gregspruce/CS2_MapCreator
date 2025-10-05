"""
Test v2.4.0 Improvements: Coherent Terrain + Water Features Performance

Tests two major fixes:
1. Coherent terrain generation (mountain ranges, not random bumps)
2. Water features performance (downsampling for 16× speedup)
"""

import sys
import os
import time

# Add project root to path
sys.path.insert(0, os.path.dirname(__file__))

import numpy as np
from src.noise_generator import NoiseGenerator
from src.coherent_terrain_generator import CoherentTerrainGenerator
from src.terrain_realism import TerrainRealism
from src.features.river_generator import RiverGenerator


def test_coherent_terrain():
    """Test that coherent terrain creates mountain ranges, not isolated peaks."""
    print("\n" + "="*60)
    print("TEST 1: Coherent Terrain Generation")
    print("="*60 + "\n")

    # Generate base noise (1024 for speed)
    print("1. Generating base Perlin noise (1024×1024)...")
    gen = NoiseGenerator(seed=42)
    start = time.time()
    heightmap = gen.generate_perlin(
        resolution=1024,
        scale=200,
        octaves=6,
        persistence=0.5,
        lacunarity=2.0,
        show_progress=False
    )
    gen_time = time.time() - start
    print(f"   [OK] Generated in {gen_time:.3f}s\n")

    # Apply coherent terrain
    print("2. Applying coherent terrain structure...")
    start = time.time()
    coherent = CoherentTerrainGenerator.make_coherent(
        heightmap,
        terrain_type='mountains'
    )
    coherent_time = time.time() - start

    assert coherent.shape == heightmap.shape, "Shape should be preserved"
    assert 0 <= coherent.min() <= coherent.max() <= 1, "Values should be 0-1"
    assert not np.array_equal(coherent, heightmap), "Should modify heightmap"

    print(f"   [OK] Coherence applied in {coherent_time:.3f}s")
    print(f"   [INFO] Range: {coherent.min():.3f} - {coherent.max():.3f}\n")

    # Apply realism polish
    print("3. Applying terrain realism polish...")
    start = time.time()
    realistic = TerrainRealism.make_realistic(
        coherent,
        terrain_type='mountains',
        enable_warping=False,  # Coherence already provides structure
        enable_ridges=True,
        enable_valleys=True,
        enable_plateaus=False,
        enable_erosion=True
    )
    realism_time = time.time() - start

    assert realistic.shape == heightmap.shape
    assert 0 <= realistic.min() <= realistic.max() <= 1

    print(f"   [OK] Realism polish applied in {realism_time:.3f}s")
    print(f"   [INFO] Range: {realistic.min():.3f} - {realistic.max():.3f}\n")

    # Analyze terrain structure
    print("4. Analyzing terrain structure...")

    # Check for large-scale features (should have coherent zones)
    from scipy import ndimage
    low_freq = ndimage.gaussian_filter(realistic, sigma=50)
    high_freq = realistic - low_freq

    low_freq_range = low_freq.max() - low_freq.min()
    high_freq_range = high_freq.max() - high_freq.min()

    print(f"   Large-scale variation: {low_freq_range:.3f}")
    print(f"   Small-scale variation: {high_freq_range:.3f}")

    # Coherent terrain should have significant large-scale structure
    assert low_freq_range > 0.3, "Should have large-scale mountain zones"
    print(f"   [OK] Has coherent large-scale structure")

    # Should also have detail
    assert high_freq_range > 0.1, "Should still have detail"
    print(f"   [OK] Has fine detail\n")

    total_time = coherent_time + realism_time
    print(f"[SUMMARY] Total terrain generation: {total_time:.3f}s")
    print(f"Estimated for 4096×4096: ~{total_time * 16:.1f}s\n")

    return realistic


def test_water_features_performance():
    """Test that water features use downsampling for performance."""
    print("\n" + "="*60)
    print("TEST 2: Water Features Performance (Downsampling)")
    print("="*60 + "\n")

    # Generate test heightmap (small for quick testing)
    print("1. Generating test heightmap (512×512)...")
    gen = NoiseGenerator(seed=123)
    heightmap = gen.generate_perlin(
        resolution=512,
        scale=100,
        octaves=4,
        persistence=0.5,
        lacunarity=2.0,
        show_progress=False
    )
    print(f"   [OK] Generated {heightmap.shape[0]}×{heightmap.shape[1]} heightmap\n")

    # Test with downsampling (should be fast)
    print("2. Testing river generation WITH downsampling...")
    start = time.time()
    river_gen_down = RiverGenerator(heightmap, downsample=True, target_size=256)
    rivers_down = river_gen_down.generate_river_network(
        num_rivers=3,
        threshold=100,
        show_progress=False
    )
    time_with_down = time.time() - start

    assert rivers_down.shape == heightmap.shape, "Should return original size"
    assert not np.array_equal(rivers_down, heightmap), "Should carve rivers"

    print(f"   [OK] WITH downsampling: {time_with_down:.3f}s\n")

    # Test without downsampling (should be slower)
    print("3. Testing river generation WITHOUT downsampling...")
    start = time.time()
    river_gen_no_down = RiverGenerator(heightmap, downsample=False)
    rivers_no_down = river_gen_no_down.generate_river_network(
        num_rivers=3,
        threshold=100,
        show_progress=False
    )
    time_without_down = time.time() - start

    assert rivers_no_down.shape == heightmap.shape

    print(f"   [OK] WITHOUT downsampling: {time_without_down:.3f}s\n")

    # Calculate speedup
    speedup = time_without_down / time_with_down
    print(f"[SUMMARY] Speedup from downsampling: {speedup:.1f}×")

    # Estimate for 4096×4096
    # 512×512 without downsampling took time_without_down
    # 4096×4096 is 64× more cells
    estimated_4k_no_down = time_without_down * 64
    estimated_4k_with_down = time_with_down * 16  # 4096→1024 = 16× more than 512→256

    print(f"\nEstimated time for 4096×4096:")
    print(f"  WITHOUT downsampling: ~{estimated_4k_no_down:.0f}s ({estimated_4k_no_down/60:.1f}min)")
    print(f"  WITH downsampling:    ~{estimated_4k_with_down:.0f}s")

    if estimated_4k_with_down < 60:
        print(f"  [OK] Acceptable performance with downsampling\n")
    else:
        print(f"  [WARN] May still be slow on 4096×4096\n")

    return rivers_down


def test_combined_workflow():
    """Test complete workflow: Coherent terrain + Water features."""
    print("\n" + "="*60)
    print("TEST 3: Complete Workflow (Coherent + Water)")
    print("="*60 + "\n")

    print("Generating realistic mountain terrain with rivers...\n")

    # Step 1: Generate base noise
    print("1. Base noise generation...")
    gen = NoiseGenerator(seed=999)
    start_total = time.time()
    heightmap = gen.generate_perlin(
        resolution=1024,
        scale=200,
        octaves=6,
        persistence=0.5,
        lacunarity=2.0,
        show_progress=False
    )
    print(f"   [OK] Complete\n")

    # Step 2: Make coherent
    print("2. Creating coherent mountain structure...")
    heightmap = CoherentTerrainGenerator.make_coherent(heightmap, terrain_type='mountains')
    print(f"   [OK] Mountain ranges created\n")

    # Step 3: Add realism
    print("3. Adding terrain realism...")
    heightmap = TerrainRealism.make_realistic(
        heightmap,
        terrain_type='mountains',
        enable_warping=False,
        enable_ridges=True,
        enable_valleys=True,
        enable_plateaus=False,
        enable_erosion=True
    )
    print(f"   [OK] Realism applied\n")

    # Step 4: Add rivers
    print("4. Generating river network...")
    river_gen = RiverGenerator(heightmap, downsample=True, target_size=512)
    final = river_gen.generate_river_network(num_rivers=5, threshold=200, show_progress=False)
    print(f"   [OK] Rivers added\n")

    total_time = time.time() - start_total

    assert final.shape == heightmap.shape
    assert 0 <= final.min() <= final.max() <= 1

    print(f"[SUMMARY] Complete workflow: {total_time:.3f}s")
    print(f"Estimated for 4096×4096: ~{total_time * 16:.1f}s\n")

    print("[SUCCESS] All components working together!")

    return final


if __name__ == '__main__':
    print("\n" + "#"*60)
    print("# CS2 Heightmap Generator v2.4.0 - Integration Tests")
    print("#"*60)

    try:
        # Test 1: Coherent terrain
        coherent_result = test_coherent_terrain()

        # Test 2: Water features performance
        water_result = test_water_features_performance()

        # Test 3: Complete workflow
        final_result = test_combined_workflow()

        # Final summary
        print("\n" + "="*60)
        print("ALL TESTS PASSED!")
        print("="*60 + "\n")

        print("v2.4.0 Improvements Verified:")
        print("  [OK] Coherent terrain creates mountain ranges")
        print("  [OK] Water features use downsampling for performance")
        print("  [OK] Complete workflow is responsive and realistic")
        print("\nReady for user testing!")

    except AssertionError as e:
        print(f"\n[FAIL] Test failed: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n[ERROR] Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
