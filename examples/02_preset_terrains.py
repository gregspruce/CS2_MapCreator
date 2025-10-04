"""
Example 2: Using Terrain Presets

This example shows how to quickly create different types of terrain
using the built-in presets. Presets have pre-tuned parameters for
realistic results.
"""

import sys
sys.path.append('../src')

from heightmap_generator import HeightmapGenerator
from noise_generator import create_preset_terrain


def generate_preset_map(preset_name: str, seed: int = None):
    """
    Generate a heightmap using a preset.

    Available presets:
    - 'flat': Completely flat terrain
    - 'rolling_hills': Gentle rolling hills
    - 'mountains': Dramatic mountain ranges
    - 'islands': Island archipelago
    - 'canyon': Deep canyons and valleys
    - 'highlands': High plateau terrain
    - 'mesas': Flat-topped mesas with cliffs
    """
    print(f"\n=== Generating '{preset_name}' terrain ===")

    # Generate terrain using preset
    print("Generating terrain data...")
    terrain_data = create_preset_terrain(
        preset=preset_name,
        resolution=4096,
        seed=seed
    )

    # Create heightmap
    heightmap = HeightmapGenerator(resolution=4096, height_scale=4096)
    heightmap.set_height_data(terrain_data)

    # Export
    output_path = f"../output/{preset_name}_map.png"
    heightmap.export_png(output_path)

    # Print stats
    stats = heightmap.get_statistics()
    print(f"Mean elevation: {stats['mean_elevation_m']:.1f}m")
    print(f"✓ Saved to: {output_path}")


def main():
    print("=== Terrain Preset Examples ===")
    print("This will generate multiple terrain types using presets.\n")

    # Use the same seed for all to ensure reproducibility
    seed = 42

    # Generate different preset types
    presets = [
        'rolling_hills',
        'mountains',
        'islands',
        'highlands'
    ]

    for preset in presets:
        generate_preset_map(preset, seed=seed)

    print("\n✓ All presets generated!")
    print("Check the 'output' folder to see your heightmaps.")


if __name__ == "__main__":
    main()
