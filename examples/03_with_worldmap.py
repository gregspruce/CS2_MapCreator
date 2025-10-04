"""
Example 3: Creating Maps with Worldmaps

This example demonstrates how to create a heightmap along with a worldmap.
The worldmap shows terrain extending beyond the playable area, creating
better visual context.
"""

import sys
sys.path.append('../src')

from heightmap_generator import HeightmapGenerator
from noise_generator import NoiseGenerator, create_preset_terrain
from worldmap_generator import WorldmapGenerator, create_worldmap_preset
from cs2_exporter import CS2Exporter


def main():
    print("=== Heightmap + Worldmap Generation ===\n")

    # Step 1: Generate playable heightmap
    print("Step 1: Generating playable heightmap (mountains)...")
    terrain_data = create_preset_terrain('mountains', resolution=4096, seed=999)

    heightmap = HeightmapGenerator(resolution=4096, height_scale=4096)
    heightmap.set_height_data(terrain_data)

    # Export playable heightmap
    heightmap_path = "../output/mountain_valley.png"
    heightmap.export_png(heightmap_path)

    # Step 2: Create worldmap with ocean surrounding
    print("\nStep 2: Creating worldmap (ocean surrounding)...")
    noise_gen = NoiseGenerator(seed=999)

    worldmap = create_worldmap_preset(
        preset='ocean',
        playable_heightmap=heightmap.get_height_data(),
        noise_generator=noise_gen,
        world_resolution=4096
    )

    # Export worldmap
    worldmap_path = "../output/mountain_valley_worldmap.png"
    worldmap.export_png(worldmap_path)

    # Step 3: Export both to CS2
    print("\nStep 3: Exporting to Cities Skylines 2...")
    try:
        exporter = CS2Exporter()
        exporter.export_to_cs2(
            heightmap_path=heightmap_path,
            map_name="Mountain Valley Island",
            worldmap_path=worldmap_path,
            overwrite=True
        )
    except Exception as e:
        print(f"Note: {e}")
        print(f"Your files are saved locally in the 'output' folder.")

    print("\n✓ Done! Your heightmap and worldmap are ready.")


def create_seamless_worldmap():
    """
    Alternative example: Create a worldmap that seamlessly extends the playable area.
    """
    print("\n=== Creating Seamless Worldmap ===")

    # Generate highlands terrain
    terrain_data = create_preset_terrain('highlands', resolution=4096, seed=777)

    heightmap = HeightmapGenerator(resolution=4096, height_scale=4096)
    heightmap.set_height_data(terrain_data)

    heightmap_path = "../output/highlands_seamless.png"
    heightmap.export_png(heightmap_path)

    # Create seamless worldmap (terrain continues naturally)
    noise_gen = NoiseGenerator(seed=777)

    worldmap = create_worldmap_preset(
        preset='seamless',
        playable_heightmap=heightmap.get_height_data(),
        noise_generator=noise_gen,
        world_resolution=4096
    )

    worldmap_path = "../output/highlands_seamless_worldmap.png"
    worldmap.export_png(worldmap_path)

    print("✓ Seamless worldmap created!")


if __name__ == "__main__":
    # Run main example
    main()

    # Uncomment to try seamless worldmap
    # create_seamless_worldmap()
