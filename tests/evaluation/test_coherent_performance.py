"""
Performance profiling for coherent terrain generator.

Tests the actual performance bottlenecks at various resolutions.
"""

import numpy as np
import time
from scipy import ndimage
from src.coherent_terrain_generator import CoherentTerrainGenerator


def profile_gaussian_filters(resolution=4096):
    """Profile gaussian filter operations at different sigma values."""
    print(f"\n=== Profiling Gaussian Filters (resolution={resolution}) ===")

    # Generate test data
    data = np.random.rand(resolution, resolution)

    # Test different sigma values used in the code
    test_cases = [
        ("base_scale (0.4 * res)", resolution * 0.4),
        ("mountain_mask (0.05 * res)", resolution * 0.05),
        ("range anisotropic X", (resolution * 0.02, resolution * 0.08)),
        ("range anisotropic Y", (resolution * 0.08, resolution * 0.02)),
        ("range isotropic (0.06 * res)", resolution * 0.06),
    ]

    results = []
    for name, sigma in test_cases:
        start = time.time()
        _ = ndimage.gaussian_filter(data, sigma=sigma)
        elapsed = time.time() - start
        results.append((name, sigma, elapsed))
        print(f"  {name}: {elapsed:.3f}s")

    return results


def profile_full_coherent_pipeline(resolution=4096):
    """Profile the entire make_coherent function."""
    print(f"\n=== Profiling Full Pipeline (resolution={resolution}) ===")

    # Generate input
    heightmap = np.random.rand(resolution, resolution)

    # Profile each major step
    times = {}

    # Step 1: Base geography
    start = time.time()
    base_heights, mountain_mask = CoherentTerrainGenerator.generate_base_geography(
        heightmap, 'mountains'
    )
    times['base_geography'] = time.time() - start
    print(f"  Base geography: {times['base_geography']:.3f}s")

    # Step 2: Mountain ranges
    start = time.time()
    ranges = CoherentTerrainGenerator.generate_mountain_ranges(
        resolution, 'mountains'
    )
    times['mountain_ranges'] = time.time() - start
    print(f"  Mountain ranges: {times['mountain_ranges']:.3f}s")

    # Step 3: Composition
    start = time.time()
    coherent = CoherentTerrainGenerator.compose_terrain(
        heightmap, base_heights, mountain_mask, ranges, 'mountains'
    )
    times['composition'] = time.time() - start
    print(f"  Composition: {times['composition']:.3f}s")

    # Total
    times['total'] = sum(times.values())
    print(f"  TOTAL: {times['total']:.3f}s")

    return times


def profile_array_operations(resolution=4096):
    """Profile array normalization and mathematical operations."""
    print(f"\n=== Profiling Array Operations (resolution={resolution}) ===")

    data = np.random.rand(resolution, resolution)

    # Normalization (used 5+ times in the code)
    start = time.time()
    for _ in range(5):
        normalized = (data - data.min()) / (data.max() - data.min())
    elapsed = time.time() - start
    print(f"  5x normalization: {elapsed:.3f}s ({elapsed/5:.3f}s each)")

    # Power operations (mountain_mask ** 2)
    start = time.time()
    _ = data ** 2
    elapsed = time.time() - start
    print(f"  Power operation (**2): {elapsed:.3f}s")

    # Multiplication and addition
    data2 = np.random.rand(resolution, resolution)
    start = time.time()
    result = data * 0.3 + data2 * 0.4 + (data * data2) * 0.6
    elapsed = time.time() - start
    print(f"  Complex composition: {elapsed:.3f}s")


def test_optimizations(resolution=4096):
    """Test potential optimizations."""
    print(f"\n=== Testing Optimizations (resolution={resolution}) ===")

    data = np.random.rand(resolution, resolution)

    # Current approach: Multiple normalizations
    start = time.time()
    norm1 = (data - data.min()) / (data.max() - data.min())
    norm2 = (data - data.min()) / (data.max() - data.min())
    norm3 = (data - data.min()) / (data.max() - data.min())
    elapsed_current = time.time() - start
    print(f"  Current (3x separate): {elapsed_current:.3f}s")

    # Optimized: Cache min/max
    start = time.time()
    data_min = data.min()
    data_max = data.max()
    data_range = data_max - data_min
    norm1 = (data - data_min) / data_range
    norm2 = (data - data_min) / data_range
    norm3 = (data - data_min) / data_range
    elapsed_cached = time.time() - start
    print(f"  Cached min/max: {elapsed_cached:.3f}s")
    speedup = elapsed_current / elapsed_cached
    print(f"  Speedup: {speedup:.2f}x")

    # Test out parameter for gaussian filter
    result = np.empty_like(data)
    start = time.time()
    ndimage.gaussian_filter(data, sigma=resolution * 0.05, output=result)
    elapsed_inplace = time.time() - start
    print(f"  Gaussian with output param: {elapsed_inplace:.3f}s")

    start = time.time()
    result = ndimage.gaussian_filter(data, sigma=resolution * 0.05)
    elapsed_normal = time.time() - start
    print(f"  Gaussian without output param: {elapsed_normal:.3f}s")


def main():
    """Run all performance tests."""
    print("=" * 70)
    print("COHERENT TERRAIN GENERATOR - PERFORMANCE ANALYSIS")
    print("=" * 70)

    # Test at multiple resolutions
    resolutions = [1024, 2048, 4096]

    for res in resolutions:
        print(f"\n{'='*70}")
        print(f"Resolution: {res}x{res}")
        print(f"{'='*70}")

        profile_gaussian_filters(res)
        profile_array_operations(res)
        profile_full_coherent_pipeline(res)

        if res == 4096:
            test_optimizations(res)

    print("\n" + "=" * 70)
    print("ANALYSIS COMPLETE")
    print("=" * 70)


if __name__ == '__main__':
    main()
