"""
Quick Terrain Quality Test - Single Terrain Analysis

Generates one mountains terrain and provides detailed evaluation.
"""

import numpy as np
import matplotlib.pyplot as plt
from src.noise_generator import NoiseGenerator
from src.coherent_terrain_generator_optimized import CoherentTerrainGenerator
from src.terrain_realism import TerrainRealism
from pathlib import Path
import time


def analyze_heightmap(heightmap: np.ndarray) -> None:
    """Analyze and print heightmap quality metrics."""

    print("\n" + "="*60)
    print("TERRAIN QUALITY ANALYSIS")
    print("="*60)

    # Calculate slopes
    gy, gx = np.gradient(heightmap)
    slope = np.sqrt(gx**2 + gy**2)

    # Buildable area (slope < 0.05 = ~5% grade)
    buildable_mask = slope < 0.05
    buildable_pct = np.sum(buildable_mask) / buildable_mask.size * 100

    # Very flat area (slope < 0.02 = ~2% grade - ideal for cities)
    very_flat_mask = slope < 0.02
    very_flat_pct = np.sum(very_flat_mask) / very_flat_mask.size * 100

    # Steep areas (unbuildable)
    steep_mask = slope > 0.10
    steep_pct = np.sum(steep_mask) / steep_mask.size * 100

    # Feature detection
    ridge_mask = (heightmap > np.percentile(heightmap, 70)) & (slope > 0.08)
    ridge_pct = np.sum(ridge_mask) / ridge_mask.size * 100

    valley_mask = (heightmap < np.percentile(heightmap, 30)) & (slope < 0.05)
    valley_pct = np.sum(valley_mask) / valley_mask.size * 100

    # Print analysis
    print("\nELEVATION STATISTICS:")
    print(f"  Min: {heightmap.min():.4f}")
    print(f"  Max: {heightmap.max():.4f}")
    print(f"  Range: {heightmap.max() - heightmap.min():.4f}")
    print(f"  Mean: {heightmap.mean():.4f}")
    print(f"  Std Dev: {heightmap.std():.4f}")

    print("\nSLOPE STATISTICS:")
    print(f"  Mean Slope: {slope.mean():.4f}")
    print(f"  Max Slope: {slope.max():.4f}")
    print(f"  Median Slope: {np.median(slope):.4f}")

    print("\nBUILDABLE AREA (City Builder Perspective):")
    print(f"  Very Flat (<2% grade): {very_flat_pct:.1f}% - IDEAL for cities")
    print(f"  Buildable (<5% grade): {buildable_pct:.1f}% - OK for development")
    print(f"  Steep (>10% grade): {steep_pct:.1f}% - Challenging/unbuildable")

    print("\nGEOLOGICAL FEATURES:")
    print(f"  Ridge Coverage: {ridge_pct:.1f}% - Mountain peaks/ridgelines")
    print(f"  Valley Coverage: {valley_pct:.1f}% - Flat valleys (good for cities)")

    print("\n" + "="*60)
    print("EVALUATION FOR CITIES SKYLINES 2")
    print("="*60)

    # Evaluation criteria
    usable = buildable_pct >= 60
    interesting = ridge_pct >= 3 and valley_pct >= 10
    variety = heightmap.std() >= 0.15

    print("\nCriteria:")
    print(f"  [{'OK' if buildable_pct >= 60 else 'X'}] Buildable Area >= 60%: {buildable_pct:.1f}%")
    print(f"  [{'OK' if very_flat_pct >= 20 else 'X'}] Very Flat >= 20%: {very_flat_pct:.1f}%")
    print(f"  [{'OK' if ridge_pct >= 3 else 'X'}] Ridges >= 3%: {ridge_pct:.1f}%")
    print(f"  [{'OK' if valley_pct >= 10 else 'X'}] Valleys >= 10%: {valley_pct:.1f}%")
    print(f"  [{'OK' if variety else 'X'}] Elevation Variety >= 0.15: {heightmap.std():.3f}")

    overall_pass = usable and interesting and variety
    print(f"\nOVERALL: [{'OK' if overall_pass else 'X'}] {'USABLE FOR CITY BUILDER' if overall_pass else 'NEEDS IMPROVEMENT'}")

    if not usable:
        print("\n[!] WARNING: Too mountainous - not enough buildable area")
        print("    Consider: Lower terrain roughness, increase valley carving")

    if not interesting:
        print("\n[!] WARNING: Terrain lacks interesting features")
        print("    Consider: Increase ridge enhancement, enable plateaus")

    if not variety:
        print("\n[!] WARNING: Terrain too uniform")
        print("    Consider: Increase octaves, enable domain warping")

    return {
        'buildable_pct': buildable_pct,
        'very_flat_pct': very_flat_pct,
        'ridge_pct': ridge_pct,
        'valley_pct': valley_pct,
        'std': heightmap.std()
    }


def main():
    print("="*60)
    print("QUICK TERRAIN QUALITY TEST")
    print("="*60)
    print("\nGenerating 512x512 mountains terrain...")

    resolution = 512
    start_time = time.time()

    # Generate base noise
    print("\n[1/3] Generating base noise...")
    noise_gen = NoiseGenerator(resolution)
    base_noise = noise_gen.generate_perlin(octaves=6, persistence=0.5, lacunarity=2.0)

    # Make coherent
    print("[2/3] Making terrain coherent...")
    coherent = CoherentTerrainGenerator.make_coherent(base_noise, terrain_type='mountains')

    # Add realism
    print("[3/3] Adding geological realism...")
    terrain = TerrainRealism.make_realistic(
        coherent,
        terrain_type='mountains',
        enable_warping=True,
        enable_ridges=True,
        enable_valleys=True,
        enable_plateaus=False,
        enable_erosion=True
    )

    elapsed = time.time() - start_time
    print(f"\n[OK] Terrain generated in {elapsed:.1f}s")

    # Analyze
    stats = analyze_heightmap(terrain)

    # Save visualization
    print("\nCreating visualization...")
    output_dir = Path("terrain_analysis")
    output_dir.mkdir(exist_ok=True)

    fig, axes = plt.subplots(2, 2, figsize=(12, 12))
    fig.suptitle('Terrain Quality Analysis - Mountains 512x512', fontsize=14, fontweight='bold')

    # Heightmap
    ax = axes[0, 0]
    im = ax.imshow(terrain, cmap='terrain', interpolation='bilinear')
    ax.set_title('Heightmap (Terrain Colors)')
    ax.axis('off')
    plt.colorbar(im, ax=ax, fraction=0.046)

    # Slope map
    ax = axes[0, 1]
    gy, gx = np.gradient(terrain)
    slope = np.sqrt(gx**2 + gy**2)
    im = ax.imshow(slope, cmap='hot', interpolation='bilinear')
    ax.set_title('Slope Map (Hot = Steep)')
    ax.axis('off')
    plt.colorbar(im, ax=ax, fraction=0.046)

    # Buildable map
    ax = axes[1, 0]
    buildable = slope < 0.05
    im = ax.imshow(buildable, cmap='RdYlGn', interpolation='nearest')
    ax.set_title(f'Buildable Area ({stats["buildable_pct"]:.1f}%)')
    ax.axis('off')
    plt.colorbar(im, ax=ax, fraction=0.046)

    # Statistics
    ax = axes[1, 1]
    ax.axis('off')
    stats_text = f"""
QUALITY METRICS:

Buildable: {stats['buildable_pct']:.1f}%
Very Flat: {stats['very_flat_pct']:.1f}%
Ridges: {stats['ridge_pct']:.1f}%
Valleys: {stats['valley_pct']:.1f}%
Variety: {stats['std']:.3f}

PASS/FAIL:
Buildable >= 60%: {'PASS' if stats['buildable_pct'] >= 60 else 'FAIL'}
Very Flat >= 20%: {'PASS' if stats['very_flat_pct'] >= 20 else 'FAIL'}
Ridges >= 3%: {'PASS' if stats['ridge_pct'] >= 3 else 'FAIL'}
Valleys >= 10%: {'PASS' if stats['valley_pct'] >= 10 else 'FAIL'}
Variety >= 0.15: {'PASS' if stats['std'] >= 0.15 else 'FAIL'}
"""
    ax.text(0.05, 0.5, stats_text, fontsize=11, family='monospace',
            verticalalignment='center', transform=ax.transAxes)

    plt.tight_layout()
    viz_path = output_dir / "quick_terrain_analysis.png"
    plt.savefig(str(viz_path), dpi=150, bbox_inches='tight')
    print(f"[OK] Visualization saved: {viz_path}")

    # Save raw data for further analysis
    np.save(str(output_dir / "terrain_512.npy"), terrain)
    print(f"[OK] Terrain data saved: terrain_512.npy")

    print("\n" + "="*60)


if __name__ == "__main__":
    main()
