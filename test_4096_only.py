"""
Quick benchmark at 4096 resolution only - where optimizations matter most.
"""

import numpy as np
import time
from src.coherent_terrain_generator import CoherentTerrainGenerator as OriginalCTG
from src.coherent_terrain_generator_optimized import CoherentTerrainGenerator as OptimizedCTG


def benchmark_4096():
    """Benchmark both implementations at 4096 resolution."""
    resolution = 4096

    print("="*70)
    print(f"COHERENT TERRAIN - 4096x4096 BENCHMARK")
    print("="*70)

    # Generate input
    np.random.seed(42)
    heightmap = np.random.rand(resolution, resolution)

    # Original
    print("\nOriginal Implementation:")
    print("-"*70)
    start = time.time()
    result_orig = OriginalCTG.make_coherent(heightmap, terrain_type='mountains')
    time_orig = time.time() - start
    print(f"Time: {time_orig:.2f}s")

    # Optimized
    print("\nOptimized Implementation:")
    print("-"*70)
    start = time.time()
    result_opt = OptimizedCTG.make_coherent(heightmap, terrain_type='mountains')
    time_opt = time.time() - start
    print(f"Time: {time_opt:.2f}s")

    # Results
    speedup = time_orig / time_opt
    print("\n" + "="*70)
    print("RESULTS")
    print("="*70)
    print(f"Original:  {time_orig:.2f}s")
    print(f"Optimized: {time_opt:.2f}s")
    print(f"Speedup:   {speedup:.2f}x")
    print(f"Saved:     {time_orig - time_opt:.2f}s")

    # Visual similarity
    orig_norm = (result_orig - result_orig.min()) / (result_orig.max() - result_orig.min())
    opt_norm = (result_opt - result_opt.min()) / (result_opt.max() - result_opt.min())
    mae = np.mean(np.abs(orig_norm - opt_norm))
    print(f"\nVisual difference (MAE): {mae:.6f}")

    if mae < 0.05:
        print("[PASS] Results are visually similar")
    else:
        print("[WARNING] Results differ significantly")

    print("="*70)


if __name__ == '__main__':
    benchmark_4096()
