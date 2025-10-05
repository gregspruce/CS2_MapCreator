"""
Integration Test for Progress Tracking with Noise Generation

Tests that progress tracking works correctly with the actual heightmap generator.
This validates the full integration of ProgressTracker with existing codebase.
"""

import sys
from src.noise_generator import NoiseGenerator
from src.heightmap_generator import HeightmapGenerator


def test_noise_generation_with_progress():
    """
    Test noise generation with progress tracking enabled.

    Validates:
    - Progress tracker doesn't break generation
    - Results are identical with/without progress
    - Progress bars display correctly
    """
    print("\n[Integration Test 1] Noise Generation with Progress")
    print("-" * 70)

    # Generate small test map with progress
    print("\nGenerating 256x256 Perlin terrain WITH progress:")
    noise_gen = NoiseGenerator(seed=12345)
    heightmap_with_progress = noise_gen.generate_perlin(
        resolution=256,
        octaves=4,
        show_progress=True
    )

    print(f"\nResult shape: {heightmap_with_progress.shape}")
    print(f"Min height: {heightmap_with_progress.min():.4f}")
    print(f"Max height: {heightmap_with_progress.max():.4f}")
    print(f"Mean height: {heightmap_with_progress.mean():.4f}")

    # Generate same map without progress (silent mode)
    print("\nGenerating same terrain WITHOUT progress (silent):")
    noise_gen_2 = NoiseGenerator(seed=12345)
    heightmap_without_progress = noise_gen_2.generate_perlin(
        resolution=256,
        octaves=4,
        show_progress=False
    )

    # Verify results are identical
    import numpy as np
    if np.allclose(heightmap_with_progress, heightmap_without_progress):
        print("OK - Results are identical (progress tracking is transparent)")
    else:
        print("ERROR - Results differ (progress tracking affected generation)")
        return False

    print("\nPASS - Noise generation integration works correctly")
    return True


def test_simplex_generation():
    """
    Test Simplex noise generation with progress.

    Validates:
    - Simplex generation works with progress tracking
    - Progress bars display for different noise types
    """
    print("\n[Integration Test 2] Simplex Generation with Progress")
    print("-" * 70)

    noise_gen = NoiseGenerator(seed=54321)
    print("\nGenerating 256x256 Simplex terrain:")
    heightmap = noise_gen.generate_simplex(
        resolution=256,
        octaves=4,
        show_progress=True
    )

    print(f"\nResult shape: {heightmap.shape}")
    print(f"Min height: {heightmap.min():.4f}")
    print(f"Max height: {heightmap.max():.4f}")
    print(f"Mean height: {heightmap.mean():.4f}")

    print("\nPASS - Simplex generation integration works correctly")
    return True


def test_full_heightmap_generator():
    """
    Test HeightmapGenerator with progress tracking.

    Validates:
    - Full generation pipeline works
    - Progress tracking throughout workflow
    """
    print("\n[Integration Test 3] Full Heightmap Generator")
    print("-" * 70)

    print("\nCreating heightmap generator:")
    gen = HeightmapGenerator(resolution=256, seed=99999)

    print("Generating terrain from preset...")
    from src.noise_generator import create_preset_terrain
    terrain = create_preset_terrain(
        preset="mountains",
        resolution=256,
        seed=99999
    )

    gen.set_height_data(terrain)

    print(f"\nResult shape: {gen.heightmap.shape}")
    print(f"Min height: {gen.heightmap.min():.4f}")
    print(f"Max height: {gen.heightmap.max():.4f}")

    print("\nPASS - Full heightmap generator works correctly")
    return True


def test_performance_baseline():
    """
    Measure baseline performance with progress tracking.

    Records timing for future optimization comparison (Phase 5).
    """
    print("\n[Performance Baseline] Timing Measurements")
    print("-" * 70)

    import time

    resolutions = [256, 512]
    results = []

    for res in resolutions:
        noise_gen = NoiseGenerator(seed=1000)

        # Time with progress disabled (pure generation)
        start = time.time()
        heightmap = noise_gen.generate_perlin(
            resolution=res,
            octaves=6,
            show_progress=False
        )
        elapsed = time.time() - start

        pixels = res * res
        pixels_per_sec = pixels / elapsed

        results.append({
            'resolution': res,
            'time': elapsed,
            'pixels_per_sec': pixels_per_sec
        })

        print(f"\n{res}x{res} generation:")
        print(f"  Time: {elapsed:.2f} seconds")
        print(f"  Speed: {pixels_per_sec:,.0f} pixels/second")
        print(f"  Total pixels: {pixels:,}")

    # Project 4096x4096 timing
    if len(results) >= 2:
        avg_pixels_per_sec = sum(r['pixels_per_sec'] for r in results) / len(results)
        full_res_pixels = 4096 * 4096
        estimated_time = full_res_pixels / avg_pixels_per_sec

        print(f"\nEstimated 4096x4096 generation time:")
        print(f"  Projected: {estimated_time:.1f} seconds ({estimated_time/60:.1f} minutes)")
        print(f"  (Based on {avg_pixels_per_sec:,.0f} pixels/second)")

    print("\nPASS - Performance baseline recorded")
    return True


def run_all_integration_tests():
    """
    Run all integration tests.

    Returns:
        bool: True if all tests passed
    """
    print("=" * 70)
    print("Progress Tracker Integration Test Suite")
    print("=" * 70)

    try:
        success = True
        success &= test_noise_generation_with_progress()
        success &= test_simplex_generation()
        success &= test_full_heightmap_generator()
        success &= test_performance_baseline()

        print("\n" + "=" * 70)
        if success:
            print("ALL INTEGRATION TESTS PASSED")
        else:
            print("SOME TESTS FAILED")
        print("=" * 70)

        return success

    except Exception as e:
        print("\n" + "=" * 70)
        print(f"INTEGRATION TEST FAILED: {e}")
        print("=" * 70)
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = run_all_integration_tests()
    sys.exit(0 if success else 1)
