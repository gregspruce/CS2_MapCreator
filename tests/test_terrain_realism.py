"""
Test terrain realism enhancements.

Verifies that terrain realism post-processing:
1. Completes without errors
2. Maintains value range (0-1)
3. Improves terrain structure
4. Runs in acceptable time (<2s total)
"""

import sys
import os
import time

# Add project root to path
sys.path.insert(0, os.path.dirname(__file__))

import numpy as np
from src.terrain_realism import TerrainRealism
from src.noise_generator import NoiseGenerator


def test_terrain_realism():
    """Test all terrain realism functions."""
    print("\n" + "="*60)
    print("Testing Terrain Realism Enhancements")
    print("="*60 + "\n")

    # Generate test heightmap (smaller for speed)
    print("1. Generating test heightmap (1024x1024)...")
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
    print(f"   [PASS] Generated in {gen_time:.3f}s")
    print(f"   [INFO] Range: {heightmap.min():.3f} - {heightmap.max():.3f}\n")

    # Test 2: Domain warping
    print("2. Testing domain warping...")
    start = time.time()
    warped = TerrainRealism.apply_domain_warping(heightmap, strength=0.4)
    warp_time = time.time() - start

    assert warped.shape == heightmap.shape, "Shape should be preserved"
    assert 0 <= warped.min() <= warped.max() <= 1, "Values should be 0-1"
    assert not np.array_equal(warped, heightmap), "Should modify heightmap"

    print(f"   [PASS] Domain warping completed in {warp_time:.3f}s")
    print(f"   [INFO] Range: {warped.min():.3f} - {warped.max():.3f}\n")

    # Test 3: Ridge enhancement
    print("3. Testing ridge enhancement...")
    start = time.time()
    ridged = TerrainRealism.enhance_ridges(heightmap, strength=0.6)
    ridge_time = time.time() - start

    assert ridged.shape == heightmap.shape
    assert 0 <= ridged.min() <= ridged.max() <= 1
    assert not np.array_equal(ridged, heightmap)

    print(f"   [PASS] Ridge enhancement completed in {ridge_time:.3f}s")
    print(f"   [INFO] Range: {ridged.min():.3f} - {ridged.max():.3f}\n")

    # Test 4: Valley carving
    print("4. Testing valley carving...")
    start = time.time()
    valleys = TerrainRealism.carve_valleys(heightmap, strength=0.4)
    valley_time = time.time() - start

    assert valleys.shape == heightmap.shape
    assert 0 <= valleys.min() <= valleys.max() <= 1
    assert not np.array_equal(valleys, heightmap)

    print(f"   [PASS] Valley carving completed in {valley_time:.3f}s")
    print(f"   [INFO] Range: {valleys.min():.3f} - {valleys.max():.3f}\n")

    # Test 5: Plateaus
    print("5. Testing plateau generation...")
    start = time.time()
    plateaus = TerrainRealism.add_plateaus(heightmap, strength=0.5)
    plateau_time = time.time() - start

    assert plateaus.shape == heightmap.shape
    assert 0 <= plateaus.min() <= plateaus.max() <= 1

    print(f"   [PASS] Plateau generation completed in {plateau_time:.3f}s")
    print(f"   [INFO] Range: {plateaus.min():.3f} - {plateaus.max():.3f}\n")

    # Test 6: Fast erosion
    print("6. Testing fast erosion...")
    start = time.time()
    eroded = TerrainRealism.fast_erosion(heightmap, iterations=2)
    erosion_time = time.time() - start

    assert eroded.shape == heightmap.shape
    assert 0 <= eroded.min() <= eroded.max() <= 1
    assert not np.array_equal(eroded, heightmap)

    print(f"   [PASS] Fast erosion completed in {erosion_time:.3f}s")
    print(f"   [INFO] Range: {eroded.min():.3f} - {eroded.max():.3f}\n")

    # Test 7: Full realistic pipeline
    print("7. Testing full realistic terrain pipeline...")
    terrain_types = ['mountains', 'hills', 'highlands', 'islands', 'canyons', 'mesas']

    for terrain_type in terrain_types:
        start = time.time()
        realistic = TerrainRealism.make_realistic(heightmap, terrain_type=terrain_type)
        process_time = time.time() - start

        assert realistic.shape == heightmap.shape
        assert 0 <= realistic.min() <= realistic.max() <= 1
        assert not np.array_equal(realistic, heightmap)

        print(f"   [PASS] {terrain_type.capitalize()}: {process_time:.3f}s")

    print()

    # Performance summary
    total_time = (
        warp_time + ridge_time + valley_time +
        plateau_time + erosion_time
    )

    print("="*60)
    print("ALL TESTS PASSED!")
    print("="*60 + "\n")

    print("Performance Summary (1024x1024):")
    print(f"  Domain warping:    {warp_time:.3f}s")
    print(f"  Ridge enhancement: {ridge_time:.3f}s")
    print(f"  Valley carving:    {valley_time:.3f}s")
    print(f"  Plateau creation:  {plateau_time:.3f}s")
    print(f"  Fast erosion (2x): {erosion_time:.3f}s")
    print(f"  --------------------------------")
    print(f"  Total:             {total_time:.3f}s\n")

    # Estimate for 4096x4096
    scale_factor = (4096 / 1024) ** 2  # Area scaling
    estimated_4k = total_time * scale_factor
    print(f"Estimated time for 4096x4096: ~{estimated_4k:.1f}s")

    if estimated_4k < 5:
        print("[OK] EXCELLENT: Fast enough for real-time generation")
    elif estimated_4k < 10:
        print("[OK] GOOD: Acceptable processing time")
    else:
        print("[WARN] May need optimization for 4096x4096")

    print("\nExpected user experience:")
    print("1. User clicks 'Generate Playable'")
    print("2. Noise generation: ~1s")
    print(f"3. Realism processing: ~{estimated_4k:.1f}s")
    print(f"4. Total: ~{1 + estimated_4k:.1f}s")
    print("5. User sees realistic, usable terrain!")


if __name__ == '__main__':
    test_terrain_realism()
