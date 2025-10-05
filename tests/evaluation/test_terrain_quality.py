"""
Test Terrain Quality - Generate and Analyze Heightmaps

This script generates multiple terrains and evaluates:
1. Geographical realism (ridges, valleys, coherent features)
2. Buildable area percentage (flat enough for cities)
3. Feature variety and interest
4. Statistical distribution
"""

import numpy as np
import matplotlib.pyplot as plt
from src.noise_generator import NoiseGenerator
from src.coherent_terrain_generator_optimized import CoherentTerrainGenerator
from src.terrain_realism import TerrainRealism
from pathlib import Path


def analyze_heightmap(heightmap: np.ndarray, name: str) -> dict:
    """
    Analyze a heightmap for quality metrics.

    Returns dict with:
    - buildable_pct: Percentage of terrain flat enough for building
    - slope_stats: Statistics about terrain slopes
    - elevation_stats: Statistics about elevation distribution
    - feature_detection: Detection of ridges, valleys, etc.
    """
    # Calculate slopes (gradient magnitude)
    gy, gx = np.gradient(heightmap)
    slope = np.sqrt(gx**2 + gy**2)

    # CS2 buildable slopes (approximately < 15% grade = < 0.15 slope)
    buildable_mask = slope < 0.05  # Conservative threshold
    buildable_pct = np.sum(buildable_mask) / buildable_mask.size * 100

    # Slope statistics
    slope_stats = {
        'mean': np.mean(slope),
        'std': np.std(slope),
        'max': np.max(slope),
        'median': np.median(slope)
    }

    # Elevation statistics
    elevation_stats = {
        'mean': np.mean(heightmap),
        'std': np.std(heightmap),
        'min': np.min(heightmap),
        'max': np.max(heightmap),
        'range': np.max(heightmap) - np.min(heightmap)
    }

    # Feature detection
    # Ridges: High elevation + high curvature
    ridge_mask = (heightmap > np.percentile(heightmap, 70)) & (slope > 0.08)
    ridge_pct = np.sum(ridge_mask) / ridge_mask.size * 100

    # Valleys: Low elevation + moderate slope
    valley_mask = (heightmap < np.percentile(heightmap, 30)) & (slope < 0.05)
    valley_pct = np.sum(valley_mask) / valley_mask.size * 100

    # Flat plateaus: High elevation + low slope
    plateau_mask = (heightmap > np.percentile(heightmap, 60)) & (slope < 0.03)
    plateau_pct = np.sum(plateau_mask) / plateau_mask.size * 100

    return {
        'name': name,
        'buildable_pct': buildable_pct,
        'slope_stats': slope_stats,
        'elevation_stats': elevation_stats,
        'features': {
            'ridges_pct': ridge_pct,
            'valleys_pct': valley_pct,
            'plateaus_pct': plateau_pct
        }
    }


def generate_terrain(resolution: int, terrain_type: str, seed: int = None) -> np.ndarray:
    """Generate a complete terrain with all processing steps."""
    print(f"\n{'='*60}")
    print(f"Generating {terrain_type} terrain (resolution: {resolution})")
    print(f"{'='*60}")

    # Step 1: Generate base noise
    print("Step 1: Generating base noise...")
    noise_gen = NoiseGenerator(resolution)
    base_noise = noise_gen.generate_perlin(octaves=6, persistence=0.5, lacunarity=2.0)

    # Step 2: Make coherent (organized mountain ranges)
    print("Step 2: Making terrain coherent...")
    coherent = CoherentTerrainGenerator.make_coherent(base_noise, terrain_type=terrain_type)

    # Step 3: Add geological realism
    print("Step 3: Adding geological realism...")
    realistic = TerrainRealism.make_realistic(
        coherent,
        terrain_type=terrain_type,
        enable_warping=True,
        enable_ridges=True,
        enable_valleys=True,
        enable_plateaus=(terrain_type in ['highlands', 'mesas']),
        enable_erosion=True
    )

    print(f"[OK] Terrain generation complete!")
    print(f"  Range: {realistic.min():.3f} to {realistic.max():.3f}")
    print(f"  Mean: {realistic.mean():.3f}, Std: {realistic.std():.3f}")

    return realistic


def visualize_terrain(heightmap: np.ndarray, analysis: dict, save_path: str):
    """Create comprehensive visualization of terrain."""
    fig, axes = plt.subplots(2, 3, figsize=(18, 12))
    fig.suptitle(f"Terrain Analysis: {analysis['name']}", fontsize=16, fontweight='bold')

    # 1. Heightmap
    ax = axes[0, 0]
    im = ax.imshow(heightmap, cmap='terrain', interpolation='bilinear')
    ax.set_title('Heightmap (Terrain Colors)')
    ax.axis('off')
    plt.colorbar(im, ax=ax, fraction=0.046)

    # 2. Elevation distribution
    ax = axes[0, 1]
    ax.hist(heightmap.flatten(), bins=50, color='brown', alpha=0.7, edgecolor='black')
    ax.axvline(analysis['elevation_stats']['mean'], color='red', linestyle='--',
               label=f"Mean: {analysis['elevation_stats']['mean']:.3f}")
    ax.set_title('Elevation Distribution')
    ax.set_xlabel('Elevation')
    ax.set_ylabel('Frequency')
    ax.legend()
    ax.grid(True, alpha=0.3)

    # 3. Slope map
    ax = axes[0, 2]
    gy, gx = np.gradient(heightmap)
    slope = np.sqrt(gx**2 + gy**2)
    im = ax.imshow(slope, cmap='hot', interpolation='bilinear')
    ax.set_title('Slope Map (Hot = Steep)')
    ax.axis('off')
    plt.colorbar(im, ax=ax, fraction=0.046)

    # 4. Buildable area map
    ax = axes[1, 0]
    buildable = slope < 0.05
    im = ax.imshow(buildable, cmap='RdYlGn', interpolation='nearest')
    ax.set_title(f'Buildable Area ({analysis["buildable_pct"]:.1f}%)')
    ax.axis('off')
    plt.colorbar(im, ax=ax, fraction=0.046)

    # 5. Feature detection
    ax = axes[1, 1]
    features = np.zeros_like(heightmap)
    # Ridges = 1 (red)
    ridge_mask = (heightmap > np.percentile(heightmap, 70)) & (slope > 0.08)
    features[ridge_mask] = 1
    # Valleys = 0.5 (yellow)
    valley_mask = (heightmap < np.percentile(heightmap, 30)) & (slope < 0.05)
    features[valley_mask] = 0.5
    # Plateaus = 0.75 (light)
    plateau_mask = (heightmap > np.percentile(heightmap, 60)) & (slope < 0.03)
    features[plateau_mask] = 0.75

    im = ax.imshow(features, cmap='RdYlGn', interpolation='nearest')
    ax.set_title('Detected Features\n(Red=Ridges, Yellow=Valleys, Light=Plateaus)')
    ax.axis('off')
    plt.colorbar(im, ax=ax, fraction=0.046)

    # 6. Statistics summary
    ax = axes[1, 2]
    ax.axis('off')
    stats_text = f"""
TERRAIN QUALITY METRICS

Buildable Area: {analysis['buildable_pct']:.1f}%
  (Target: >60% for city builder)

Elevation:
  Range: {analysis['elevation_stats']['range']:.3f}
  Mean: {analysis['elevation_stats']['mean']:.3f}
  Std Dev: {analysis['elevation_stats']['std']:.3f}

Slope:
  Mean: {analysis['slope_stats']['mean']:.4f}
  Max: {analysis['slope_stats']['max']:.4f}

Features:
  Ridges: {analysis['features']['ridges_pct']:.1f}%
  Valleys: {analysis['features']['valleys_pct']:.1f}%
  Plateaus: {analysis['features']['plateaus_pct']:.1f}%

EVALUATION:
  Buildable: {"[OK] GOOD" if analysis['buildable_pct'] > 60 else "[X] POOR"}
  Variety: {"[OK] GOOD" if analysis['elevation_stats']['std'] > 0.15 else "[X] POOR"}
  Features: {"[OK] GOOD" if analysis['features']['ridges_pct'] > 3 else "[X] POOR"}
"""
    ax.text(0.1, 0.5, stats_text, fontsize=11, family='monospace',
            verticalalignment='center', transform=ax.transAxes)

    plt.tight_layout()
    plt.savefig(save_path, dpi=150, bbox_inches='tight')
    print(f"  Visualization saved: {save_path}")
    plt.close()


def main():
    """Generate and analyze multiple terrains."""
    print("="*60)
    print("TERRAIN QUALITY EVALUATION")
    print("="*60)

    # Create output directory
    output_dir = Path("terrain_analysis")
    output_dir.mkdir(exist_ok=True)

    # Test configurations
    test_cases = [
        {'type': 'mountains', 'resolution': 1024, 'name': 'Mountains_1024'},
        {'type': 'hills', 'resolution': 1024, 'name': 'Hills_1024'},
        {'type': 'highlands', 'resolution': 1024, 'name': 'Highlands_1024'},
        {'type': 'islands', 'resolution': 1024, 'name': 'Islands_1024'},
    ]

    results = []

    for i, config in enumerate(test_cases, 1):
        print(f"\n\nTEST {i}/{len(test_cases)}: {config['name']}")
        print("-" * 60)

        # Generate terrain
        terrain = generate_terrain(config['resolution'], config['type'])

        # Analyze
        analysis = analyze_heightmap(terrain, config['name'])
        results.append(analysis)

        # Visualize
        viz_path = output_dir / f"{config['name']}_analysis.png"
        visualize_terrain(terrain, analysis, str(viz_path))

        # Print summary
        print(f"\n[ANALYSIS SUMMARY]:")
        print(f"  Buildable Area: {analysis['buildable_pct']:.1f}%")
        print(f"  Elevation Variety: {analysis['elevation_stats']['std']:.3f}")
        print(f"  Ridges: {analysis['features']['ridges_pct']:.1f}%")
        print(f"  Valleys: {analysis['features']['valleys_pct']:.1f}%")
        print(f"  Plateaus: {analysis['features']['plateaus_pct']:.1f}%")

    # Generate comparison report
    print("\n\n" + "="*60)
    print("FINAL EVALUATION - TERRAIN QUALITY FOR CITY BUILDER")
    print("="*60)

    report_path = output_dir / "quality_report.txt"
    with open(report_path, 'w') as f:
        f.write("TERRAIN QUALITY EVALUATION REPORT\n")
        f.write("="*60 + "\n\n")

        for analysis in results:
            f.write(f"{analysis['name']}\n")
            f.write("-" * 40 + "\n")
            f.write(f"  Buildable Area: {analysis['buildable_pct']:.1f}%\n")
            f.write(f"  Elevation Range: {analysis['elevation_stats']['range']:.3f}\n")
            f.write(f"  Elevation Std: {analysis['elevation_stats']['std']:.3f}\n")
            f.write(f"  Mean Slope: {analysis['slope_stats']['mean']:.4f}\n")
            f.write(f"  Ridges: {analysis['features']['ridges_pct']:.1f}%\n")
            f.write(f"  Valleys: {analysis['features']['valleys_pct']:.1f}%\n")
            f.write(f"  Plateaus: {analysis['features']['plateaus_pct']:.1f}%\n")

            # Evaluation
            f.write("\n  EVALUATION:\n")
            buildable_ok = analysis['buildable_pct'] > 60
            variety_ok = analysis['elevation_stats']['std'] > 0.15
            features_ok = analysis['features']['ridges_pct'] > 3

            f.write(f"    Buildable: {'[OK] PASS' if buildable_ok else '[X] FAIL'}\n")
            f.write(f"    Variety: {'[OK] PASS' if variety_ok else '[X] FAIL'}\n")
            f.write(f"    Features: {'[OK] PASS' if features_ok else '[X] FAIL'}\n")
            f.write(f"    Overall: {'[OK] USABLE' if all([buildable_ok, variety_ok, features_ok]) else '[X] NEEDS WORK'}\n")
            f.write("\n\n")

        # Overall summary
        f.write("SUMMARY\n")
        f.write("="*60 + "\n")
        avg_buildable = np.mean([r['buildable_pct'] for r in results])
        avg_variety = np.mean([r['elevation_stats']['std'] for r in results])
        avg_ridges = np.mean([r['features']['ridges_pct'] for r in results])

        f.write(f"Average Buildable Area: {avg_buildable:.1f}%\n")
        f.write(f"Average Elevation Variety: {avg_variety:.3f}\n")
        f.write(f"Average Ridge Coverage: {avg_ridges:.1f}%\n")
        f.write("\n")
        f.write(f"Overall Quality: {'[OK] GOOD FOR CITY BUILDER' if avg_buildable > 60 else '[X] TOO MOUNTAINOUS'}\n")

    print(f"\n[OK] All results saved to: {output_dir}/")
    print(f"  - Individual visualizations: *_analysis.png")
    print(f"  - Quality report: quality_report.txt")
    print("\n" + "="*60)


if __name__ == "__main__":
    main()
