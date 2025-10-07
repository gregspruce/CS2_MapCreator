"""
Buildability Parameter Sweep Test

This test systematically explores the parameter space to find optimal settings
for achieving CS2 buildable terrain (45-55% at 0-5% slopes).

ROOT CAUSES IDENTIFIED:
1. Scale too small (100 vs needed 3000-5000)
2. Domain warping too aggressive (60 vs needed 0-20)
3. Coherent terrain pipeline adds detail back to smooth zones
4. Terrain realism sharpening applied uniformly

This test will validate these hypotheses and find optimal parameters.
"""

import numpy as np
import sys
import os
from typing import Dict, List, Tuple

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.noise_generator import NoiseGenerator
from src.coherent_terrain_generator_optimized import CoherentTerrainGenerator


def calculate_slope_percentage(heightmap: np.ndarray) -> np.ndarray:
    """Calculate slope percentage for terrain."""
    resolution = heightmap.shape[0]
    map_size_meters = 14336.0
    pixel_size_meters = map_size_meters / resolution

    heightmap_meters = heightmap * 1024.0
    dy, dx = np.gradient(heightmap_meters)
    slope_ratio = np.sqrt(dx**2 + dy**2) / pixel_size_meters
    slope_percent = slope_ratio * 100.0

    return slope_percent


def analyze_buildability(heightmap: np.ndarray) -> Dict[str, float]:
    """Analyze terrain and return buildability metrics."""
    slopes = calculate_slope_percentage(heightmap)

    buildable = np.sum(slopes <= 5.0)
    limited = np.sum((slopes > 5.0) & (slopes <= 10.0))
    scenic = np.sum(slopes > 10.0)
    total = slopes.size

    return {
        'buildable_pct': (buildable / total) * 100,
        'limited_pct': (limited / total) * 100,
        'scenic_pct': (scenic / total) * 100,
        'min_slope': slopes.min(),
        'max_slope': slopes.max(),
        'mean_slope': slopes.mean(),
        'std_slope': slopes.std(),
        'p50_slope': np.percentile(slopes, 50),
        'p90_slope': np.percentile(slopes, 90),
        'p99_slope': np.percentile(slopes, 99)
    }


def test_parameter_combination(
    scale: float,
    octaves: int,
    persistence: float,
    domain_warp: float,
    apply_coherent: bool,
    resolution: int = 512,
    seed: int = 42
) -> Dict[str, float]:
    """Test a specific parameter combination."""
    gen = NoiseGenerator(seed=seed)

    # Generate terrain
    heightmap = gen.generate_perlin(
        resolution=resolution,
        scale=scale,
        octaves=octaves,
        persistence=persistence,
        lacunarity=2.0,
        show_progress=False,
        domain_warp_amp=domain_warp,
        domain_warp_type=0,
        recursive_warp=(domain_warp > 0),
        recursive_warp_strength=4.0
    )

    # Optionally apply coherent terrain processing
    if apply_coherent:
        heightmap = CoherentTerrainGenerator.make_coherent(
            heightmap,
            terrain_type='mountains',
            apply_erosion=False
        )

    # Analyze
    metrics = analyze_buildability(heightmap)

    return metrics


def run_scale_sweep():
    """Test different scale values to find optimal for buildable terrain."""
    print("\n" + "="*80)
    print("SCALE PARAMETER SWEEP - Finding Optimal Scale for Buildable Terrain")
    print("="*80)
    print("\nHypothesis: Scale=100 is too small, need scale=3000-5000 for gentle terrain")
    print("Testing: octaves=2, persistence=0.3, domain_warp=0 (pure smooth noise)")
    print("\n")

    scales_to_test = [100, 500, 1000, 2000, 3000, 4000, 5000, 7000]
    results = []

    for scale in scales_to_test:
        print(f"Testing scale={scale}...", end=" ", flush=True)

        metrics = test_parameter_combination(
            scale=scale,
            octaves=2,
            persistence=0.3,
            domain_warp=0.0,
            apply_coherent=False,
            resolution=512
        )

        results.append({
            'scale': scale,
            **metrics
        })

        print(f"Buildable: {metrics['buildable_pct']:.1f}%, Mean slope: {metrics['mean_slope']:.1f}%")

    # Print summary table
    print("\n" + "-"*80)
    print("SCALE SWEEP RESULTS")
    print("-"*80)
    print(f"{'Scale':<8} {'Buildable':<12} {'Mean Slope':<12} {'P50 Slope':<12} {'P90 Slope':<12}")
    print("-"*80)

    for r in results:
        print(f"{r['scale']:<8.0f} {r['buildable_pct']:>10.1f}% {r['mean_slope']:>10.1f}% "
              f"{r['p50_slope']:>10.1f}% {r['p90_slope']:>10.1f}%")

    print("-"*80)

    # Find optimal
    target_buildable = [r for r in results if 45 <= r['buildable_pct'] <= 55]
    if target_buildable:
        optimal = target_buildable[0]
        print(f"\n[SUCCESS] OPTIMAL SCALE FOUND: {optimal['scale']:.0f}")
        print(f"   Buildable: {optimal['buildable_pct']:.1f}%")
        print(f"   Mean slope: {optimal['mean_slope']:.1f}%")
    else:
        print(f"\n[WARNING] No scale achieved target (45-55% buildable)")
        closest = min(results, key=lambda r: abs(r['buildable_pct'] - 50))
        print(f"   Closest: scale={closest['scale']:.0f} with {closest['buildable_pct']:.1f}% buildable")

    return results


def run_domain_warp_sweep():
    """Test impact of domain warping on buildability."""
    print("\n" + "="*80)
    print("DOMAIN WARP SWEEP - Impact on Buildable Terrain")
    print("="*80)
    print("\nHypothesis: Domain warping adds jaggedness, should be minimal for buildable zones")
    print("Testing: scale=3000 (from scale sweep), octaves=2, persistence=0.3")
    print("\n")

    warp_values = [0, 10, 20, 40, 60]
    results = []

    for warp in warp_values:
        print(f"Testing domain_warp={warp}...", end=" ", flush=True)

        metrics = test_parameter_combination(
            scale=3000,
            octaves=2,
            persistence=0.3,
            domain_warp=float(warp),
            apply_coherent=False,
            resolution=512
        )

        results.append({
            'domain_warp': warp,
            **metrics
        })

        print(f"Buildable: {metrics['buildable_pct']:.1f}%, Mean slope: {metrics['mean_slope']:.1f}%")

    # Print summary
    print("\n" + "-"*80)
    print("DOMAIN WARP RESULTS")
    print("-"*80)
    print(f"{'Warp':<8} {'Buildable':<12} {'Mean Slope':<12} {'Std Slope':<12}")
    print("-"*80)

    for r in results:
        print(f"{r['domain_warp']:<8.0f} {r['buildable_pct']:>10.1f}% {r['mean_slope']:>10.1f}% "
              f"{r['std_slope']:>10.1f}%")

    print("-"*80)

    return results


def run_pipeline_impact_test():
    """Test impact of coherent terrain pipeline on buildability."""
    print("\n" + "="*80)
    print("COHERENT PIPELINE IMPACT TEST")
    print("="*80)
    print("\nHypothesis: Coherent terrain generator adds detail back to smooth zones")
    print("Testing: scale=3000, octaves=2, persistence=0.3, domain_warp=0")
    print("\n")

    # Test without coherent
    print("Testing WITHOUT coherent terrain...", end=" ", flush=True)
    metrics_no_coherent = test_parameter_combination(
        scale=3000,
        octaves=2,
        persistence=0.3,
        domain_warp=0.0,
        apply_coherent=False,
        resolution=512
    )
    print(f"Buildable: {metrics_no_coherent['buildable_pct']:.1f}%")

    # Test with coherent
    print("Testing WITH coherent terrain...", end=" ", flush=True)
    metrics_with_coherent = test_parameter_combination(
        scale=3000,
        octaves=2,
        persistence=0.3,
        domain_warp=0.0,
        apply_coherent=True,
        resolution=512
    )
    print(f"Buildable: {metrics_with_coherent['buildable_pct']:.1f}%")

    # Compare
    print("\n" + "-"*80)
    print("PIPELINE IMPACT COMPARISON")
    print("-"*80)
    print(f"{'Configuration':<25} {'Buildable':<12} {'Mean Slope':<12} {'P90 Slope':<12}")
    print("-"*80)
    print(f"{'Without coherent':<25} {metrics_no_coherent['buildable_pct']:>10.1f}% "
          f"{metrics_no_coherent['mean_slope']:>10.1f}% {metrics_no_coherent['p90_slope']:>10.1f}%")
    print(f"{'With coherent':<25} {metrics_with_coherent['buildable_pct']:>10.1f}% "
          f"{metrics_with_coherent['mean_slope']:>10.1f}% {metrics_with_coherent['p90_slope']:>10.1f}%")
    print("-"*80)

    buildable_change = metrics_with_coherent['buildable_pct'] - metrics_no_coherent['buildable_pct']
    print(f"\nBuildability change: {buildable_change:+.1f}%")

    if buildable_change < -5:
        print("[WARNING] Coherent terrain REDUCES buildability significantly")
        print("   Solution: Apply coherent ONLY to scenic zones, not buildable zones")
    else:
        print("[SUCCESS] Coherent terrain impact is acceptable")

    return metrics_no_coherent, metrics_with_coherent


def main():
    """Run comprehensive parameter sweep."""
    print("\n" + "="*80)
    print("BUILDABILITY PARAMETER SWEEP - COMPREHENSIVE ANALYSIS")
    print("="*80)
    print("\nObjective: Find optimal parameters for CS2 buildable terrain (45-55% at 0-5% slopes)")
    print("\nIdentified issues:")
    print("  1. Scale too small (100 vs needed 3000-5000)")
    print("  2. Domain warping too aggressive (60 vs needed 0-20)")
    print("  3. Coherent terrain adds detail back")
    print("  4. Pipeline not control-map aware")
    print("\nRunning systematic tests to validate and find optimal parameters...")

    try:
        # Test 1: Scale sweep
        scale_results = run_scale_sweep()

        # Test 2: Domain warp sweep
        warp_results = run_domain_warp_sweep()

        # Test 3: Pipeline impact
        no_coherent, with_coherent = run_pipeline_impact_test()

        # Final recommendations
        print("\n" + "="*80)
        print("FINAL RECOMMENDATIONS")
        print("="*80)

        # Find best scale
        best_scale = None
        for r in scale_results:
            if 45 <= r['buildable_pct'] <= 55:
                best_scale = r['scale']
                break

        if not best_scale:
            # Find closest
            best_scale = min(scale_results, key=lambda r: abs(r['buildable_pct'] - 50))['scale']

        # Find best warp
        best_warp = min(warp_results, key=lambda r: abs(r['buildable_pct'] - 50))['domain_warp']

        print(f"\nFor BUILDABLE zones:")
        print(f"  • scale = {best_scale:.0f}")
        print(f"  • octaves = 2")
        print(f"  • persistence = 0.3")
        print(f"  • domain_warp_amp = {best_warp:.0f}")
        print(f"  • Apply coherent terrain: NO (or make control-map aware)")

        print(f"\nFor SCENIC zones:")
        print(f"  • scale = user-defined (100-200)")
        print(f"  • octaves = 8")
        print(f"  • persistence = 0.5")
        print(f"  • domain_warp_amp = 60")
        print(f"  • Apply coherent terrain: YES")

        print(f"\nArchitectural fix required:")
        print(f"  • Generate buildable and scenic terrains separately")
        print(f"  • Apply coherent/realism ONLY to scenic terrain")
        print(f"  • Blend AFTER all processing (not before)")

        print("\n" + "="*80)
        print("PARAMETER SWEEP COMPLETE")
        print("="*80)

    except Exception as e:
        print(f"\n[ERROR] Test failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
