"""
Benchmark comparison: Original vs Optimized Coherent Terrain Generator

Tests both implementations to validate performance improvements.
"""

import numpy as np
import time
from src.coherent_terrain_generator import CoherentTerrainGenerator as OriginalCTG
from src.coherent_terrain_generator_optimized import CoherentTerrainGenerator as OptimizedCTG


def benchmark_implementation(impl_class, name, resolution=4096):
    """Benchmark a single implementation."""
    print(f"\n{'='*70}")
    print(f"{name} - Resolution: {resolution}x{resolution}")
    print(f"{'='*70}")

    # Generate input
    np.random.seed(42)
    heightmap = np.random.rand(resolution, resolution)

    # Full pipeline
    start = time.time()
    result = impl_class.make_coherent(heightmap, terrain_type='mountains')
    total_time = time.time() - start

    print(f"\nTotal time: {total_time:.2f}s")

    return total_time, result


def verify_visual_similarity(original, optimized, tolerance=0.05):
    """Verify that optimized version produces visually similar results."""
    print("\n" + "="*70)
    print("VISUAL SIMILARITY VERIFICATION")
    print("="*70)

    # Normalize both for comparison
    orig_norm = (original - original.min()) / (original.max() - original.min())
    opt_norm = (optimized - optimized.min()) / (optimized.max() - optimized.min())

    # Compute difference metrics
    mae = np.mean(np.abs(orig_norm - opt_norm))
    rmse = np.sqrt(np.mean((orig_norm - opt_norm)**2))
    max_diff = np.max(np.abs(orig_norm - opt_norm))

    print(f"  Mean Absolute Error: {mae:.6f}")
    print(f"  Root Mean Square Error: {rmse:.6f}")
    print(f"  Max Difference: {max_diff:.6f}")

    if mae < tolerance:
        print(f"  [PASS] Visual similarity within tolerance ({tolerance})")
        return True
    else:
        print(f"  [FAIL] Visual difference exceeds tolerance ({tolerance})")
        return False


def detailed_component_comparison(resolution=4096):
    """Compare individual components."""
    print("\n" + "="*70)
    print("DETAILED COMPONENT COMPARISON")
    print("="*70)

    np.random.seed(42)
    heightmap = np.random.rand(resolution, resolution)

    results = {
        'original': {},
        'optimized': {}
    }

    # Test Original
    print("\nOriginal Implementation:")
    start = time.time()
    base_h_orig, mask_orig = OriginalCTG.generate_base_geography(heightmap, 'mountains')
    results['original']['base_geography'] = time.time() - start
    print(f"  Base geography: {results['original']['base_geography']:.2f}s")

    start = time.time()
    ranges_orig = OriginalCTG.generate_mountain_ranges(resolution, 'mountains')
    results['original']['mountain_ranges'] = time.time() - start
    print(f"  Mountain ranges: {results['original']['mountain_ranges']:.2f}s")

    start = time.time()
    composed_orig = OriginalCTG.compose_terrain(
        heightmap, base_h_orig, mask_orig, ranges_orig, 'mountains'
    )
    results['original']['composition'] = time.time() - start
    print(f"  Composition: {results['original']['composition']:.2f}s")

    # Test Optimized
    print("\nOptimized Implementation:")
    start = time.time()
    base_h_opt, mask_opt = OptimizedCTG.generate_base_geography(heightmap, 'mountains')
    results['optimized']['base_geography'] = time.time() - start
    print(f"  Base geography: {results['optimized']['base_geography']:.2f}s")

    start = time.time()
    ranges_opt = OptimizedCTG.generate_mountain_ranges(resolution, 'mountains')
    results['optimized']['mountain_ranges'] = time.time() - start
    print(f"  Mountain ranges: {results['optimized']['mountain_ranges']:.2f}s")

    start = time.time()
    composed_opt = OptimizedCTG.compose_terrain(
        heightmap, base_h_opt, mask_opt, ranges_opt, 'mountains'
    )
    results['optimized']['composition'] = time.time() - start
    print(f"  Composition: {results['optimized']['composition']:.2f}s")

    # Calculate speedups
    print("\n" + "="*70)
    print("SPEEDUP ANALYSIS")
    print("="*70)

    for component in ['base_geography', 'mountain_ranges', 'composition']:
        orig_time = results['original'][component]
        opt_time = results['optimized'][component]
        speedup = orig_time / opt_time if opt_time > 0 else float('inf')
        print(f"  {component:20s}: {speedup:6.2f}x speedup ({orig_time:6.2f}s → {opt_time:6.2f}s)")

    total_orig = sum(results['original'].values())
    total_opt = sum(results['optimized'].values())
    total_speedup = total_orig / total_opt if total_opt > 0 else float('inf')
    print(f"  {'TOTAL':20s}: {total_speedup:6.2f}x speedup ({total_orig:6.2f}s → {total_opt:6.2f}s)")

    return composed_orig, composed_opt


def test_fft_gaussian_accuracy():
    """Test FFT gaussian filter accuracy vs scipy."""
    print("\n" + "="*70)
    print("FFT GAUSSIAN FILTER ACCURACY TEST")
    print("="*70)

    from scipy.ndimage import gaussian_filter

    resolution = 1024
    sigma = 400  # Large sigma

    np.random.seed(42)
    data = np.random.rand(resolution, resolution)

    # Standard scipy
    start = time.time()
    result_scipy = gaussian_filter(data, sigma=sigma)
    time_scipy = time.time() - start

    # FFT method
    start = time.time()
    result_fft = OptimizedCTG._fft_gaussian_filter(data, sigma)
    time_fft = time.time() - start

    # Compare
    diff = np.abs(result_scipy - result_fft)
    mae = np.mean(diff)
    rmse = np.sqrt(np.mean(diff**2))

    print(f"  Sigma: {sigma}")
    print(f"  Resolution: {resolution}x{resolution}")
    print(f"  Scipy time: {time_scipy:.3f}s")
    print(f"  FFT time: {time_fft:.3f}s")
    print(f"  Speedup: {time_scipy/time_fft:.2f}x")
    print(f"  Mean Absolute Error: {mae:.6f}")
    print(f"  RMSE: {rmse:.6f}")

    if mae < 0.001:
        print("  [PASS] FFT method is accurate")
    else:
        print("  [WARNING] FFT method has noticeable error")


def main():
    """Run all benchmarks and comparisons."""
    print("="*70)
    print("COHERENT TERRAIN GENERATOR - OPTIMIZATION BENCHMARK")
    print("="*70)

    # Test FFT accuracy first
    test_fft_gaussian_accuracy()

    # Test at smaller resolution first (faster)
    print("\n" + "="*70)
    print("QUICK TEST - Resolution 1024x1024")
    print("="*70)

    time_orig_1k, result_orig_1k = benchmark_implementation(
        OriginalCTG, "Original", resolution=1024
    )
    time_opt_1k, result_opt_1k = benchmark_implementation(
        OptimizedCTG, "Optimized", resolution=1024
    )

    speedup_1k = time_orig_1k / time_opt_1k
    print(f"\n{'='*70}")
    print(f"1024x1024 Speedup: {speedup_1k:.2f}x ({time_orig_1k:.2f}s -> {time_opt_1k:.2f}s)")
    print(f"{'='*70}")

    verify_visual_similarity(result_orig_1k, result_opt_1k, tolerance=0.05)

    # Full resolution test (4096x4096)
    print("\n" + "="*70)
    print("PRODUCTION TEST - Resolution 4096x4096")
    print("="*70)
    print("WARNING: This will take ~2 minutes for original implementation")
    print("="*70)

    time_orig_4k, result_orig_4k = benchmark_implementation(
        OriginalCTG, "Original", resolution=4096
    )
    time_opt_4k, result_opt_4k = benchmark_implementation(
        OptimizedCTG, "Optimized", resolution=4096
    )

    speedup_4k = time_orig_4k / time_opt_4k
    print(f"\n{'='*70}")
    print(f"4096x4096 Speedup: {speedup_4k:.2f}x ({time_orig_4k:.2f}s -> {time_opt_4k:.2f}s)")
    print(f"{'='*70}")

    verify_visual_similarity(result_orig_4k, result_opt_4k, tolerance=0.05)

    # Detailed component analysis
    composed_orig, composed_opt = detailed_component_comparison(resolution=4096)

    # Final summary
    print("\n" + "="*70)
    print("FINAL SUMMARY")
    print("="*70)
    print(f"Resolution 1024x1024:")
    print(f"  Original: {time_orig_1k:.2f}s")
    print(f"  Optimized: {time_opt_1k:.2f}s")
    print(f"  Speedup: {speedup_1k:.2f}x")
    print(f"\nResolution 4096x4096:")
    print(f"  Original: {time_orig_4k:.2f}s")
    print(f"  Optimized: {time_opt_4k:.2f}s")
    print(f"  Speedup: {speedup_4k:.2f}x")
    print(f"\nUser Experience Impact:")
    print(f"  4096x4096 terrain generation: {time_orig_4k:.0f}s -> {time_opt_4k:.0f}s")
    print("="*70)


if __name__ == '__main__':
    main()
