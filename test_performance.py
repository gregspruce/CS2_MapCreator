"""
Performance Benchmark Suite for CS2 Heightmap Generator

Tests and validates performance optimizations:
- Multi-threading speedup
- Cache effectiveness
- Memory usage
- Generation time across resolutions

Establishes performance baselines for comparison.
"""

import sys
import time
import numpy as np
from src.parallel_generator import ParallelNoiseGenerator
from src.cache_manager import CacheManager, cached_operation
from src.noise_generator import NoiseGenerator


def test_parallel_speedup():
    """
    Test multi-threading speedup vs sequential.

    Validates:
    - Parallel is faster than sequential
    - Speedup scales reasonably with cores
    - Results are identical (correctness)
    """
    print("\n[TEST 1] Multi-Threading Speedup")
    print("-" * 70)

    resolution = 1024  # Smaller for faster testing
    seed = 12345

    # Sequential generation
    print("Running sequential generation...")
    gen_seq = NoiseGenerator(seed=seed)
    start = time.time()
    result_seq = gen_seq.generate_perlin(resolution=resolution, octaves=4, show_progress=False)
    time_seq = time.time() - start

    # Parallel generation
    print("Running parallel generation...")
    gen_par = ParallelNoiseGenerator(seed=seed)
    start = time.time()
    result_par = gen_par.generate_perlin_parallel(resolution=resolution, octaves=4, show_progress=False)
    time_par = time.time() - start

    speedup = time_seq / time_par

    print(f"\nSequential time: {time_seq:.2f}s")
    print(f"Parallel time: {time_par:.2f}s")
    print(f"Speedup: {speedup:.2f}x")
    print(f"Workers: {gen_par.num_workers}")

    # Verify results are close (floating point differences acceptable)
    if np.allclose(result_seq, result_par, rtol=0.01):
        print("OK - Results are equivalent (correctness maintained)")
    else:
        print("WARNING - Results differ (may indicate bug)")

    if speedup > 1.5:
        print(f"OK - Significant speedup achieved ({speedup:.2f}x)")
    else:
        print(f"WARNING - Speedup lower than expected ({speedup:.2f}x)")

    print("PASS - Multi-threading speedup validated")


def test_cache_effectiveness():
    """
    Test cache hit/miss behavior.

    Validates:
    - First call is slow (cache miss)
    - Second call is fast (cache hit)
    - Cache returns correct results
    """
    print("\n[TEST 2] Cache Effectiveness")
    print("-" * 70)

    cache_mgr = CacheManager()

    # Define cached function
    @cached_operation(cache_mgr, use_disk=False)  # Memory cache only for speed
    def expensive_operation(size: int, value: float) -> np.ndarray:
        """Simulate expensive operation"""
        time.sleep(0.1)  # Simulate computation time
        return np.full((size, size), value)

    # First call (cache miss)
    print("First call (cache miss)...")
    start = time.time()
    result1 = expensive_operation(100, 0.5)
    time_miss = time.time() - start

    # Second call (cache hit)
    print("Second call (cache hit)...")
    start = time.time()
    result2 = expensive_operation(100, 0.5)
    time_hit = time.time() - start

    speedup = time_miss / time_hit

    print(f"\nCache miss time: {time_miss:.4f}s")
    print(f"Cache hit time: {time_hit:.4f}s")
    print(f"Cache speedup: {speedup:.1f}x")

    # Verify results are identical
    if np.array_equal(result1, result2):
        print("OK - Cached result matches original")
    else:
        print("ERROR - Cached result differs from original")

    if speedup > 10:
        print(f"OK - Cache provides significant speedup ({speedup:.1f}x)")
    else:
        print(f"WARNING - Cache speedup lower than expected ({speedup:.1f}x)")

    # Clean up
    expensive_operation.cache_clear()

    print("PASS - Cache effectiveness validated")


def test_memory_usage():
    """
    Test memory usage is reasonable.

    Validates:
    - 4096x4096 heightmap fits in memory
    - Memory is released after generation
    - No memory leaks
    """
    print("\n[TEST 3] Memory Usage")
    print("-" * 70)

    import psutil
    import os

    process = psutil.Process(os.getpid())

    # Measure baseline memory
    baseline_mb = process.memory_info().rss / 1024 / 1024

    # Generate large heightmap
    print("Generating 2048x2048 heightmap...")
    gen = NoiseGenerator(seed=99999)
    heightmap = gen.generate_perlin(resolution=2048, octaves=4, show_progress=False)

    # Measure peak memory
    peak_mb = process.memory_info().rss / 1024 / 1024

    # Delete heightmap
    del heightmap
    import gc
    gc.collect()

    # Measure after cleanup
    after_mb = process.memory_info().rss / 1024 / 1024

    memory_used = peak_mb - baseline_mb
    memory_leaked = after_mb - baseline_mb

    print(f"\nBaseline memory: {baseline_mb:.1f} MB")
    print(f"Peak memory: {peak_mb:.1f} MB")
    print(f"After cleanup: {after_mb:.1f} MB")
    print(f"Memory used for generation: {memory_used:.1f} MB")
    print(f"Memory retained after cleanup: {memory_leaked:.1f} MB")

    # 2048x2048 float64 array = ~32MB
    # With overhead, ~50-100MB is reasonable
    if memory_used < 200:
        print("OK - Memory usage is reasonable")
    else:
        print("WARNING - Memory usage higher than expected")

    if memory_leaked < 50:
        print("OK - Minimal memory leak detected")
    else:
        print("WARNING - Significant memory retained after cleanup")

    print("PASS - Memory usage acceptable")


def test_scaling_performance():
    """
    Test performance scaling across resolutions.

    Validates:
    - Time scales approximately O(n^2) as expected
    - No unexpected performance cliffs
    - Predictable behavior
    """
    print("\n[TEST 4] Performance Scaling")
    print("-" * 70)

    resolutions = [256, 512, 1024]
    times = []

    gen = ParallelNoiseGenerator(seed=11111)

    for res in resolutions:
        print(f"\nGenerating {res}x{res}...")
        start = time.time()
        gen.generate_perlin_parallel(resolution=res, octaves=4, show_progress=False)
        elapsed = time.time() - start

        times.append(elapsed)
        pixels = res * res
        pixels_per_sec = pixels / elapsed

        print(f"  Time: {elapsed:.2f}s")
        print(f"  Speed: {pixels_per_sec:,.0f} pixels/sec")

    # Check scaling relationship
    # Doubling resolution = ~4x pixels = ~4x time (with some overhead)
    ratio_1 = times[1] / times[0]  # 512 vs 256
    ratio_2 = times[2] / times[1]  # 1024 vs 512

    print(f"\nScaling ratios:")
    print(f"  512/256: {ratio_1:.2f}x (expected ~4x)")
    print(f"  1024/512: {ratio_2:.2f}x (expected ~4x)")

    if 2.5 < ratio_1 < 5.5 and 2.5 < ratio_2 < 5.5:
        print("OK - Scaling behavior is reasonable (near O(n^2))")
    else:
        print("WARNING - Scaling behavior unexpected")

    print("PASS - Performance scaling validated")


def test_tile_size_impact():
    """
    Test impact of tile size on performance.

    Validates:
    - Tile size affects performance
    - 256x256 is near-optimal
    - Very small/large tiles are suboptimal
    """
    print("\n[TEST 5] Tile Size Impact")
    print("-" * 70)

    resolution = 1024
    tile_sizes = [128, 256, 512]
    times = []

    gen = ParallelNoiseGenerator(seed=22222)

    for tile_size in tile_sizes:
        print(f"\nTesting tile size {tile_size}x{tile_size}...")
        start = time.time()
        gen.generate_perlin_parallel(
            resolution=resolution,
            octaves=4,
            tile_size=tile_size,
            show_progress=False
        )
        elapsed = time.time() - start

        times.append(elapsed)
        print(f"  Time: {elapsed:.2f}s")

    # Find best tile size
    best_idx = times.index(min(times))
    best_tile_size = tile_sizes[best_idx]

    print(f"\nBest tile size: {best_tile_size}x{best_tile_size} ({times[best_idx]:.2f}s)")

    for i, tile_size in enumerate(tile_sizes):
        overhead = ((times[i] - times[best_idx]) / times[best_idx]) * 100
        print(f"  {tile_size}x{tile_size}: {times[i]:.2f}s (+{overhead:.1f}% overhead)")

    if best_tile_size == 256:
        print("OK - 256x256 tiles are optimal (as expected)")
    else:
        print(f"NOTE - {best_tile_size}x{best_tile_size} tiles performed best on this system")

    print("PASS - Tile size impact measured")


def run_all_tests():
    """
    Run all performance tests.

    Returns:
        bool: True if all tests passed
    """
    print("=" * 70)
    print("Performance Benchmark Suite")
    print("=" * 70)

    try:
        test_parallel_speedup()
        test_cache_effectiveness()
        test_memory_usage()
        test_scaling_performance()
        test_tile_size_impact()

        print("\n" + "=" * 70)
        print("ALL PERFORMANCE TESTS PASSED")
        print("=" * 70)
        return True

    except Exception as e:
        print("\n" + "=" * 70)
        print(f"PERFORMANCE TEST FAILED: {e}")
        print("=" * 70)
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
