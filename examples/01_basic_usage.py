"""
Example 1: Basic Heightmap Generation

This example demonstrates the simplest way to create a heightmap for CS2.
We'll generate a basic terrain using Perlin noise and export it.
"""

import sys
sys.path.append('../src')

from heightmap_generator import HeightmapGenerator
from noise_generator import NoiseGenerator, create_preset_terrain
from cs2_exporter import CS2Exporter


def main():
    print("=== Basic Heightmap Generation Example ===\n")

    # Step 1: Create a noise generator with a seed for reproducibility
    print("Step 1: Initializing noise generator...")
    noise_gen = NoiseGenerator(seed=12345)

    # Step 2: Generate terrain using Perlin noise
    print("Step 2: Generating terrain with Perlin noise...")
    print("  (This may take a few minutes for 4096x4096 resolution)")

    terrain_data = noise_gen.generate_perlin(
        resolution=4096,      # CS2 standard resolution
        scale=200.0,          # Controls terrain smoothness (larger = smoother)
        octaves=6,            # Number of detail layers
        persistence=0.5,      # How much detail decreases per octave
        lacunarity=2.0        # How much frequency increases per octave
    )

    # Step 3: Create heightmap generator and load terrain data
    print("Step 3: Creating heightmap...")
    heightmap = HeightmapGenerator(
        resolution=4096,
        height_scale=4096,    # Maximum elevation in meters
        seed=12345
    )

    heightmap.set_height_data(terrain_data)

    # Step 4: (Optional) Apply smoothing for more natural terrain
    print("Step 4: Smoothing terrain...")
    heightmap.smooth(iterations=1, kernel_size=3)

    # Step 5: Export to local directory first
    print("Step 5: Exporting heightmap...")
    output_path = "../output/my_first_map.png"
    heightmap.export_png(output_path)

    # Print statistics
    stats = heightmap.get_statistics()
    print("\nTerrain Statistics:")
    print(f"  Mean elevation: {stats['mean_elevation_m']:.1f}m")
    print(f"  Std deviation: {stats['std_elevation_m']:.1f}m")

    # Step 6: (Optional) Export directly to CS2
    print("\nStep 6: Exporting to Cities Skylines 2...")
    try:
        exporter = CS2Exporter()
        exporter.export_to_cs2(
            heightmap_path=output_path,
            map_name="My First Map",
            overwrite=True
        )
    except Exception as e:
        print(f"Note: Could not export to CS2 ({e})")
        print(f"Your heightmap is saved at: {output_path}")

    print("\n✓ Done! Your heightmap is ready to use.")


if __name__ == "__main__":
    main()
