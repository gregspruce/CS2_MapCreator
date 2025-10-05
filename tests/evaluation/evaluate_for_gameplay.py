"""
Evaluate Terrain for Cities Skylines 2 Gameplay

This focuses on GAMEPLAY metrics, not arbitrary mathematical thresholds:
- Visual interest (elevation variety, features)
- Buildability (enough flat/gentle areas)
- Natural appearance (geological realism)
- Challenge variety (mix of easy/hard areas)
"""

import numpy as np
import matplotlib.pyplot as plt
from src.noise_generator import NoiseGenerator
from src.coherent_terrain_generator_optimized import CoherentTerrainGenerator
from src.terrain_realism import TerrainRealism
from pathlib import Path


def evaluate_for_cs2(heightmap: np.ndarray) -> dict:
    """Evaluate terrain specifically for Cities Skylines 2 gameplay."""

    # Calculate slopes
    gy, gx = np.gradient(heightmap)
    slope = np.sqrt(gx**2 + gy**2)

    # GAMEPLAY METRICS (what matters for city builder)

    # 1. BUILDABLE ZONES (critical for gameplay)
    easy_build = slope < 0.02  # <2% - Easy (residential, commercial)
    medium_build = (slope >= 0.02) & (slope < 0.05)  # 2-5% - Medium (industrial, infrastructure)
    hard_build = (slope >= 0.05) & (slope < 0.10)  # 5-10% - Challenging (special districts)
    very_hard = slope >= 0.10  # >10% - Very challenging / scenery

    easy_pct = np.sum(easy_build) / easy_build.size * 100
    medium_pct = np.sum(medium_build) / medium_build.size * 100
    hard_pct = np.sum(hard_build) / hard_build.size * 100
    very_hard_pct = np.sum(very_hard) / very_hard.size * 100

    # 2. VISUAL INTEREST (elevation variation)
    elev_range = heightmap.max() - heightmap.min()
    elev_std = heightmap.std()

    # Check for varied features (not uniform)
    height_levels = np.histogram(heightmap, bins=10)[0]
    height_variety = np.std(height_levels) / np.mean(height_levels)  # Coefficient of variation

    # 3. GEOGRAPHICAL FEATURES (for CS2 "interesting" factor)
    # High areas (mountains/hills for landmarks)
    high_areas = heightmap > np.percentile(heightmap, 75)
    high_pct = np.sum(high_areas) / high_areas.size * 100

    # Low areas (valleys/plains for main city)
    low_areas = heightmap < np.percentile(heightmap, 25)
    low_pct = np.sum(low_areas) / low_areas.size * 100

    # Moderate slopes (interesting terrain features)
    interesting_slopes = (slope > np.percentile(slope, 60)) & (slope < 0.08)
    interesting_pct = np.sum(interesting_slopes) / interesting_slopes.size * 100

    # 4. LAYOUT SUITABILITY
    # Large contiguous flat areas (good for city centers)
    from scipy import ndimage
    flat_labels, num_flat_regions = ndimage.label(easy_build)
    if num_flat_regions > 0:
        region_sizes = [np.sum(flat_labels == i) for i in range(1, num_flat_regions + 1)]
        largest_flat_region = max(region_sizes) if region_sizes else 0
        largest_flat_pct = (largest_flat_region / easy_build.size * 100)
    else:
        largest_flat_pct = 0

    return {
        'buildability': {
            'easy': easy_pct,
            'medium': medium_pct,
            'hard': hard_pct,
            'very_hard': very_hard_pct,
            'total_usable': easy_pct + medium_pct + hard_pct
        },
        'interest': {
            'elevation_range': elev_range,
            'elevation_std': elev_std,
            'height_variety': height_variety,
            'max_slope': slope.max()
        },
        'features': {
            'high_areas': high_pct,
            'low_areas': low_pct,
            'interesting_slopes': interesting_pct
        },
        'layout': {
            'largest_flat_region_pct': largest_flat_pct
        }
    }


def print_cs2_evaluation(metrics: dict):
    """Print gameplay-focused evaluation."""

    print("\n" + "="*60)
    print("CITIES SKYLINES 2 GAMEPLAY EVALUATION")
    print("="*60)

    # Buildability
    print("\n1. BUILDABILITY (Can you build a city here?)")
    print(f"   Easy Building (<2% slope):    {metrics['buildability']['easy']:.1f}%")
    print(f"   Medium Building (2-5% slope):  {metrics['buildability']['medium']:.1f}%")
    print(f"   Hard Building (5-10% slope):   {metrics['buildability']['hard']:.1f}%")
    print(f"   Very Challenging (>10% slope): {metrics['buildability']['very_hard']:.1f}%")
    print(f"   Total Usable:                   {metrics['buildability']['total_usable']:.1f}%")

    usable_ok = metrics['buildability']['total_usable'] >= 70
    easy_ok = metrics['buildability']['easy'] >= 40
    print(f"\n   [{'OK' if usable_ok else 'X'}] Total Usable >= 70%: {'PASS' if usable_ok else 'FAIL'}")
    print(f"   [{'OK' if easy_ok else 'X'}] Easy Building >= 40%: {'PASS' if easy_ok else 'FAIL'}")

    # Visual Interest
    print("\n2. VISUAL INTEREST (Is it interesting to look at?)")
    print(f"   Elevation Range:     {metrics['interest']['elevation_range']:.3f}")
    print(f"   Elevation Std Dev:   {metrics['interest']['elevation_std']:.3f}")
    print(f"   Height Variety:      {metrics['interest']['height_variety']:.3f}")
    print(f"   Max Slope:           {metrics['interest']['max_slope']:.4f} ({metrics['interest']['max_slope']*100:.1f}%)")

    variety_ok = metrics['interest']['elevation_std'] >= 0.12
    range_ok = metrics['interest']['elevation_range'] >= 0.8
    print(f"\n   [{'OK' if variety_ok else 'X'}] Elevation Variety >= 0.12: {'PASS' if variety_ok else 'FAIL'}")
    print(f"   [{'OK' if range_ok else 'X'}] Elevation Range >= 0.80: {'PASS' if range_ok else 'FAIL'}")

    # Geographical Features
    print("\n3. GEOGRAPHICAL FEATURES (Natural-looking terrain?)")
    print(f"   High Areas (landmarks):    {metrics['features']['high_areas']:.1f}%")
    print(f"   Low Areas (city centers):  {metrics['features']['low_areas']:.1f}%")
    print(f"   Interesting Slopes:        {metrics['features']['interesting_slopes']:.1f}%")

    features_ok = metrics['features']['interesting_slopes'] >= 15
    print(f"\n   [{'OK' if features_ok else 'X'}] Interesting Slopes >= 15%: {'PASS' if features_ok else 'FAIL'}")

    # Layout
    print("\n4. CITY LAYOUT (Room for city center?)")
    print(f"   Largest Flat Region: {metrics['layout']['largest_flat_region_pct']:.1f}%")

    layout_ok = metrics['layout']['largest_flat_region_pct'] >= 5
    print(f"\n   [{'OK' if layout_ok else 'X'}] Largest Flat >= 5%: {'PASS' if layout_ok else 'FAIL'}")

    # Overall
    print("\n" + "="*60)
    print("OVERALL VERDICT")
    print("="*60)

    all_ok = usable_ok and easy_ok and variety_ok and range_ok and features_ok and layout_ok

    if all_ok:
        print("\n   [OK] EXCELLENT - Ready for CS2!")
        print("   This map has good buildability, visual interest, and natural features.")
    elif usable_ok and easy_ok:
        print("\n   [OK] GOOD - Usable for CS2")
        print("   Buildability is good. May lack some visual interest or features.")
    else:
        print("\n   [X] NEEDS IMPROVEMENT")
        if not usable_ok:
            print("   - Not enough buildable area for a functioning city")
        if not easy_ok:
            print("   - Not enough easy building areas for residential/commercial")
        if not variety_ok:
            print("   - Terrain too uniform - needs more elevation variation")

    print("\n" + "="*60)


def main():
    print("="*60)
    print("CS2 GAMEPLAY EVALUATION")
    print("="*60)
    print("\nGenerating 512x512 mountains terrain...\n")

    resolution = 512

    # Generate terrain
    noise_gen = NoiseGenerator(resolution)
    base_noise = noise_gen.generate_perlin(octaves=6, persistence=0.5, lacunarity=2.0)
    coherent = CoherentTerrainGenerator.make_coherent(base_noise, terrain_type='mountains')
    terrain = TerrainRealism.make_realistic(
        coherent,
        terrain_type='mountains',
        enable_warping=True,
        enable_ridges=True,
        enable_valleys=True,
        enable_plateaus=False,
        enable_erosion=True
    )

    # Evaluate
    metrics = evaluate_for_cs2(terrain)
    print_cs2_evaluation(metrics)

    # Visualize
    output_dir = Path("terrain_analysis")
    output_dir.mkdir(exist_ok=True)

    fig, axes = plt.subplots(2, 2, figsize=(12, 12))
    fig.suptitle('CS2 Gameplay Evaluation', fontsize=14, fontweight='bold')

    # Heightmap
    ax = axes[0, 0]
    im = ax.imshow(terrain, cmap='terrain', interpolation='bilinear')
    ax.set_title('Heightmap')
    ax.axis('off')
    plt.colorbar(im, ax=ax, fraction=0.046)

    # Buildability zones
    ax = axes[0, 1]
    gy, gx = np.gradient(terrain)
    slope = np.sqrt(gx**2 + gy**2)
    buildability = np.zeros_like(terrain)
    buildability[slope < 0.02] = 3  # Easy (green)
    buildability[(slope >= 0.02) & (slope < 0.05)] = 2  # Medium (yellow)
    buildability[(slope >= 0.05) & (slope < 0.10)] = 1  # Hard (orange)
    # Very hard = 0 (red)
    im = ax.imshow(buildability, cmap='RdYlGn', interpolation='nearest', vmin=0, vmax=3)
    ax.set_title(f'Buildability Zones\n(Green=Easy, Yellow=Medium, Orange=Hard, Red=Very Hard)')
    ax.axis('off')
    plt.colorbar(im, ax=ax, fraction=0.046)

    # Elevation distribution
    ax = axes[1, 0]
    ax.hist(terrain.flatten(), bins=30, color='brown', alpha=0.7, edgecolor='black')
    ax.set_title('Elevation Distribution')
    ax.set_xlabel('Elevation')
    ax.set_ylabel('Frequency')
    ax.grid(True, alpha=0.3)

    # Summary
    ax = axes[1, 1]
    ax.axis('off')
    summary_text = f"""
CS2 GAMEPLAY METRICS:

BUILD ABILITY:
  Easy: {metrics['buildability']['easy']:.1f}%
  Medium: {metrics['buildability']['medium']:.1f}%
  Hard: {metrics['buildability']['hard']:.1f}%
  Total: {metrics['buildability']['total_usable']:.1f}%

VISUAL INTEREST:
  Elevation Range: {metrics['interest']['elevation_range']:.2f}
  Elevation Std: {metrics['interest']['elevation_std']:.3f}
  Max Slope: {metrics['interest']['max_slope']*100:.1f}%

FEATURES:
  High Areas: {metrics['features']['high_areas']:.1f}%
  Low Areas: {metrics['features']['low_areas']:.1f}%
  Interesting: {metrics['features']['interesting_slopes']:.1f}%

LAYOUT:
  Largest Flat: {metrics['layout']['largest_flat_region_pct']:.1f}%
"""
    ax.text(0.05, 0.5, summary_text, fontsize=10, family='monospace',
            verticalalignment='center', transform=ax.transAxes)

    plt.tight_layout()
    viz_path = output_dir / "cs2_gameplay_evaluation.png"
    plt.savefig(str(viz_path), dpi=150, bbox_inches='tight')
    print(f"\n[OK] Visualization saved: {viz_path}")


if __name__ == "__main__":
    main()
