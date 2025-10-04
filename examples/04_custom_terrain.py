"""
Example 4: Custom Terrain Design

This example shows how to build custom terrain by combining
different generation techniques and manual modifications.
"""

import sys
sys.path.append('../src')

from heightmap_generator import HeightmapGenerator
from noise_generator import NoiseGenerator
import numpy as np


def main():
    print("=== Custom Terrain Design Example ===\n")

    # Initialize
    heightmap = HeightmapGenerator(resolution=4096, height_scale=5000)

    # Step 1: Start with a gentle gradient (valley floor to hills)
    print("Step 1: Creating base gradient...")
    heightmap.create_gradient(start_height=0.3, end_height=0.6, direction='vertical')

    # Step 2: Add a major mountain in the center
    print("Step 2: Adding central mountain...")
    heightmap.add_circle(
        center_x=0.5,
        center_y=0.5,
        radius=0.15,
        height=0.35,
        blend=True
    )

    # Step 3: Add some smaller hills around
    print("Step 3: Adding surrounding hills...")
    hills = [
        (0.3, 0.3, 0.08, 0.15),
        (0.7, 0.3, 0.08, 0.15),
        (0.3, 0.7, 0.08, 0.15),
        (0.7, 0.7, 0.08, 0.15),
    ]

    for x, y, r, h in hills:
        heightmap.add_circle(x, y, r, h, blend=True)

    # Step 4: Add noise for natural texture
    print("Step 4: Adding detail with noise...")
    noise_gen = NoiseGenerator(seed=123)

    detail_noise = noise_gen.generate_perlin(
        resolution=4096,
        scale=50.0,      # Small scale for fine detail
        octaves=3,       # Just a few octaves
        persistence=0.3,
        lacunarity=2.0
    )

    # Blend noise with existing terrain (add subtle variation)
    current_data = heightmap.get_height_data()
    combined = current_data * 0.85 + detail_noise * 0.15
    heightmap.set_height_data(combined)

    # Step 5: Smooth to remove any harsh transitions
    print("Step 5: Smoothing terrain...")
    heightmap.smooth(iterations=2, kernel_size=5)

    # Step 6: Normalize to use full height range
    heightmap.normalize_range(min_height=0.0, max_height=1.0)

    # Export
    output_path = "../output/custom_terrain.png"
    heightmap.export_png(output_path)

    stats = heightmap.get_statistics()
    print(f"\nTerrain Statistics:")
    print(f"  Height scale: {heightmap.height_scale}m")
    print(f"  Mean elevation: {stats['mean_elevation_m']:.1f}m")
    print(f"  Max elevation: {stats['max_elevation_m']:.1f}m")
    print(f"\n✓ Custom terrain saved to: {output_path}")


def create_river_valley():
    """
    Advanced example: Create a terrain with a river valley.
    """
    print("\n=== Creating River Valley ===")

    heightmap = HeightmapGenerator(resolution=4096, height_scale=3000)

    # Start with rolling hills
    noise_gen = NoiseGenerator(seed=456)
    base_terrain = noise_gen.generate_perlin(
        resolution=4096,
        scale=200.0,
        octaves=5,
        persistence=0.5,
        lacunarity=2.0
    )

    heightmap.set_height_data(base_terrain)

    # Carve a valley through the middle
    # Create a depression that runs horizontally
    data = heightmap.get_height_data()
    resolution = 4096

    for y in range(resolution):
        # Valley is strongest in the middle, fades toward edges
        valley_strength = 1.0 - abs(y - resolution/2) / (resolution/2)
        valley_strength = valley_strength ** 3  # Sharp valley

        for x in range(resolution):
            # Create meandering by offsetting valley center
            meander = int(resolution * 0.1 * np.sin(x / 500.0))
            y_offset = y + meander

            if 0 <= y_offset < resolution:
                if valley_strength > 0.1:
                    # Lower the terrain to create valley
                    data[y, x] -= valley_strength * 0.3

    heightmap.set_height_data(data)

    # Smooth the valley edges
    heightmap.smooth(iterations=3, kernel_size=7)

    # Export
    output_path = "../output/river_valley.png"
    heightmap.export_png(output_path)
    print(f"✓ River valley saved to: {output_path}")


if __name__ == "__main__":
    # Run main custom terrain
    main()

    # Uncomment to create river valley
    # create_river_valley()
