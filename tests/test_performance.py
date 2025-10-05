"""
Performance Benchmark Test for Vectorized Noise Generation

This script tests the performance improvement from the vectorized
FastNoiseLite implementation.

Expected Results:
- Old implementation (nested loops): 60-120s for 4096x4096
- New implementation (vectorized): 1-10s for 4096x4096
- Speedup: 10-100x depending on system
"""

import time
import numpy as np
from src.noise_generator import NoiseGenerator

def benchmark_generation(resolution=4096, test_name="Terrain Generation"):
    """
    Benchmark terrain generation at specified resolution.

    Args:
        resolution: Size of heightmap to generate
        test_name: Name for the test (for display)

    Returns:
        Time taken in seconds
    """
    print(f"\n{'='*60}")
    print(f"Benchmark: {test_name}")
    print(f"Resolution: {resolution}x{resolution} ({resolution**2:,} pixels)")
    print(f"{'='*60}")

    # Create noise generator with fixed seed for consistency
    noise_gen = NoiseGenerator(seed=42)

    # Warm-up run (first run may be slower due to JIT compilation)
    print("Warming up...")
    _ = noise_gen.generate_perlin(
        resolution=256,
        scale=100.0,
        octaves=4,
        show_progress=False
    )

    # Actual benchmark
    print(f"\nGenerating {resolution}x{resolution} terrain...")
    start_time = time.time()

    terrain = noise_gen.generate_perlin(
        resolution=resolution,
        scale=150.0,
        octaves=6,
        persistence=0.5,
        lacunarity=2.0,
        show_progress=True
    )

    elapsed = time.time() - start_time

    # Validate output
    assert terrain.shape == (resolution, resolution), f"Wrong shape: {terrain.shape}"
    assert terrain.min() >= 0.0 and terrain.max() <= 1.0, "Values not normalized"
    assert not np.isnan(terrain).any(), "Contains NaN values"

    print(f"\n[OK] Generation complete!")
    print(f"  Time taken: {elapsed:.2f} seconds")
    print(f"  Pixels/sec: {resolution**2/elapsed:,.0f}")
    print(f"  Min value: {terrain.min():.4f}")
    print(f"  Max value: {terrain.max():.4f}")
    print(f"  Mean value: {terrain.mean():.4f}")

    return elapsed


def benchmark_simplex(resolution=4096):
    """Benchmark Simplex/OpenSimplex2 generation."""
    print(f"\n{'='*60}")
    print(f"Benchmark: Simplex (OpenSimplex2) Generation")
    print(f"Resolution: {resolution}x{resolution}")
    print(f"{'='*60}")

    noise_gen = NoiseGenerator(seed=42)

    print(f"\nGenerating {resolution}x{resolution} Simplex terrain...")
    start_time = time.time()

    terrain = noise_gen.generate_simplex(
        resolution=resolution,
        scale=150.0,
        octaves=6,
        persistence=0.5,
        lacunarity=2.0,
        show_progress=True
    )

    elapsed = time.time() - start_time

    print(f"\n[OK] Simplex generation complete!")
    print(f"  Time taken: {elapsed:.2f} seconds")
    print(f"  Pixels/sec: {resolution**2/elapsed:,.0f}")

    return elapsed


def compare_resolutions():
    """Test performance scaling across different resolutions."""
    print("\n" + "="*60)
    print("RESOLUTION SCALING TEST")
    print("="*60)

    resolutions = [1024, 2048, 4096]
    results = []

    for res in resolutions:
        elapsed = benchmark_generation(res, f"{res}x{res} Perlin")
        pixels = res * res
        results.append({
            'resolution': res,
            'pixels': pixels,
            'time': elapsed,
            'pixels_per_sec': pixels / elapsed
        })

    print("\n" + "="*60)
    print("SCALING RESULTS")
    print("="*60)
    print(f"{'Resolution':<12} {'Pixels':<12} {'Time (s)':<12} {'Pixels/sec':<15}")
    print("-" * 60)

    for r in results:
        print(f"{r['resolution']}x{r['resolution']:<7} "
              f"{r['pixels']:>10,}  "
              f"{r['time']:>10.2f}  "
              f"{r['pixels_per_sec']:>13,.0f}")

    # Calculate scaling efficiency
    if len(results) >= 2:
        print("\n" + "="*60)
        print("SCALING EFFICIENCY")
        print("="*60)
        for i in range(1, len(results)):
            pixel_ratio = results[i]['pixels'] / results[i-1]['pixels']
            time_ratio = results[i]['time'] / results[i-1]['time']
            efficiency = (pixel_ratio / time_ratio) * 100

            print(f"{results[i-1]['resolution']}->{results[i]['resolution']}: "
                  f"{pixel_ratio:.1f}x pixels, {time_ratio:.2f}x time "
                  f"({efficiency:.1f}% efficient)")


def main():
    """Run all benchmarks."""
    print("\n" + "="*60)
    print("CS2 HEIGHTMAP GENERATOR - PERFORMANCE BENCHMARK")
    print("Vectorized FastNoiseLite Implementation")
    print("="*60)

    # Test 1: Standard 4096x4096 generation (CS2 requirement)
    perlin_time = benchmark_generation(4096, "CS2 Standard (4096x4096 Perlin)")

    # Test 2: Simplex comparison
    simplex_time = benchmark_simplex(4096)

    # Test 3: Resolution scaling
    compare_resolutions()

    # Summary
    print("\n" + "="*60)
    print("BENCHMARK SUMMARY")
    print("="*60)
    print(f"4096x4096 Perlin:        {perlin_time:.2f}s")
    print(f"4096x4096 OpenSimplex2:  {simplex_time:.2f}s")
    print(f"Simplex speedup:         {perlin_time/simplex_time:.2f}x faster than Perlin")

    # Performance targets
    print("\n" + "="*60)
    print("PERFORMANCE TARGETS")
    print("="*60)

    if perlin_time < 10:
        print("[EXCELLENT] Sub-10s generation achieved!")
        print("  Ready for real-time terrain editing workflows")
    elif perlin_time < 30:
        print("[GOOD] Sub-30s generation achieved!")
        print("  Suitable for interactive terrain design")
    elif perlin_time < 60:
        print("[ACCEPTABLE] Sub-60s generation")
        print("  Consider GPU acceleration for further improvement")
    else:
        print("[SLOW] >60s generation")
        print("  Check if FastNoiseLite is installed: pip install pyfastnoiselite")

    print("\n" + "="*60)
    print("Benchmark complete!")
    print("="*60 + "\n")


if __name__ == "__main__":
    main()
