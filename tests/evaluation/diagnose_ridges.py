"""
Diagnose Ridge Suppression - Test Each Processing Stage

This script generates terrain step-by-step and shows how ridge coverage
changes at each stage to identify where ridges are being suppressed.
"""

import numpy as np
from src.noise_generator import NoiseGenerator
from src.coherent_terrain_generator_optimized import CoherentTerrainGenerator
from src.terrain_realism import TerrainRealism


def measure_ridges(heightmap: np.ndarray) -> dict:
    """Measure ridge coverage and sharpness."""
    gy, gx = np.gradient(heightmap)
    slope = np.sqrt(gx**2 + gy**2)

    # Ridge detection: high elevation + high slope
    ridge_mask = (heightmap > np.percentile(heightmap, 70)) & (slope > 0.08)
    ridge_pct = np.sum(ridge_mask) / ridge_mask.size * 100

    # Sharp ridges: very high slope
    sharp_ridge_mask = slope > 0.12
    sharp_ridge_pct = np.sum(sharp_ridge_mask) / sharp_ridge_mask.size * 100

    return {
        'ridge_pct': ridge_pct,
        'sharp_ridge_pct': sharp_ridge_pct,
        'max_slope': slope.max(),
        'mean_slope': slope.mean(),
        'std_elevation': heightmap.std()
    }


def print_stage_analysis(stage_name: str, heightmap: np.ndarray):
    """Print analysis for a processing stage."""
    metrics = measure_ridges(heightmap)

    print(f"\n{stage_name}")
    print(f"  Ridge Coverage: {metrics['ridge_pct']:.2f}%")
    print(f"  Sharp Ridges: {metrics['sharp_ridge_pct']:.2f}%")
    print(f"  Max Slope: {metrics['max_slope']:.4f}")
    print(f"  Mean Slope: {metrics['mean_slope']:.4f}")
    print(f"  Elevation StdDev: {metrics['std_elevation']:.4f}")

    return metrics


def main():
    print("="*60)
    print("RIDGE SUPPRESSION DIAGNOSTIC")
    print("="*60)
    print("\nGenerating 512x512 terrain step-by-step...\n")

    resolution = 512

    # Stage 1: Base Noise
    print("[Stage 1] Base Perlin Noise")
    noise_gen = NoiseGenerator(resolution)
    base_noise = noise_gen.generate_perlin(octaves=6, persistence=0.5, lacunarity=2.0)
    stage1_metrics = print_stage_analysis("  After base noise generation:", base_noise)

    # Stage 2: Coherent Terrain
    print("\n[Stage 2] Coherent Terrain Processing")
    coherent = CoherentTerrainGenerator.make_coherent(base_noise, terrain_type='mountains')
    stage2_metrics = print_stage_analysis("  After coherent processing:", coherent)

    # Stage 3: Individual Realism Components
    print("\n[Stage 3] Geological Realism Components")

    # 3a: Domain Warping
    warped = TerrainRealism.apply_domain_warping(coherent, strength=0.4)
    stage3a_metrics = print_stage_analysis("  After domain warping:", warped)

    # 3b: Ridge Enhancement
    ridges_enhanced = TerrainRealism.enhance_ridges(warped, strength=0.6)
    stage3b_metrics = print_stage_analysis("  After ridge enhancement:", ridges_enhanced)

    # 3c: Valley Carving
    valleys_carved = TerrainRealism.carve_valleys(ridges_enhanced, strength=0.4)
    stage3c_metrics = print_stage_analysis("  After valley carving:", valleys_carved)

    # 3d: Erosion
    eroded = TerrainRealism.fast_erosion(valleys_carved, iterations=2)
    stage3d_metrics = print_stage_analysis("  After erosion (2 iterations):", eroded)

    # Stage 4: Full Pipeline
    print("\n[Stage 4] Full Realism Pipeline")
    full_pipeline = TerrainRealism.make_realistic(
        coherent,
        terrain_type='mountains',
        enable_warping=True,
        enable_ridges=True,
        enable_valleys=True,
        enable_plateaus=False,
        enable_erosion=True
    )
    stage4_metrics = print_stage_analysis("  After full pipeline:", full_pipeline)

    # Analysis
    print("\n" + "="*60)
    print("DIAGNOSTIC RESULTS")
    print("="*60)

    # Check where ridges are lost
    stages = [
        ("Base Noise", stage1_metrics),
        ("Coherent", stage2_metrics),
        ("Warped", stage3a_metrics),
        ("Ridge Enhanced", stage3b_metrics),
        ("Valley Carved", stage3c_metrics),
        ("Eroded", stage3d_metrics),
        ("Full Pipeline", stage4_metrics)
    ]

    print("\nRidge Coverage by Stage:")
    for stage_name, metrics in stages:
        status = "[OK]" if metrics['ridge_pct'] >= 3.0 else "[X]"
        print(f"  {status} {stage_name:20s}: {metrics['ridge_pct']:6.2f}%")

    print("\nSharp Ridge Coverage by Stage:")
    for stage_name, metrics in stages:
        status = "[OK]" if metrics['sharp_ridge_pct'] >= 1.0 else "[X]"
        print(f"  {status} {stage_name:20s}: {metrics['sharp_ridge_pct']:6.2f}%")

    print("\nMax Slope by Stage:")
    for stage_name, metrics in stages:
        status = "[OK]" if metrics['max_slope'] >= 0.10 else "[X]"
        print(f"  {status} {stage_name:20s}: {metrics['max_slope']:6.4f}")

    # Identify problem stages
    print("\n" + "="*60)
    print("PROBLEM IDENTIFICATION")
    print("="*60)

    coherent_loss = stage1_metrics['ridge_pct'] - stage2_metrics['ridge_pct']
    if coherent_loss > 5:
        print(f"\n[!] COHERENT PROCESSING removes {coherent_loss:.1f}% ridges!")
        print("    Issue: Base geography smoothing too aggressive")

    erosion_loss = stage3c_metrics['ridge_pct'] - stage3d_metrics['ridge_pct']
    if erosion_loss > 5:
        print(f"\n[!] EROSION removes {erosion_loss:.1f}% ridges!")
        print("    Issue: Thermal erosion iterations too many or too strong")

    if stage3b_metrics['ridge_pct'] < stage3a_metrics['ridge_pct']:
        print(f"\n[!] RIDGE ENHANCEMENT reduces ridges instead of enhancing!")
        print("    Issue: Ridge enhancement algorithm may be inverted")

    if stage4_metrics['ridge_pct'] < 3:
        print(f"\n[!] FINAL OUTPUT has only {stage4_metrics['ridge_pct']:.1f}% ridges")
        print("    Target: >= 3% for interesting terrain")
        print("\n    RECOMMENDATIONS:")
        print("    1. Reduce erosion iterations (2 -> 1)")
        print("    2. Increase ridge enhancement strength (0.6 -> 0.8)")
        print("    3. Reduce valley carving strength (0.4 -> 0.3)")
        print("    4. Check coherent processing base geography sigma")

    print("\n" + "="*60)


if __name__ == "__main__":
    main()
