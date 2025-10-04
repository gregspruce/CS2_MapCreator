#!/usr/bin/env python3
"""
Quick Map Generator for Cities Skylines 2

This is a simple command-line tool for generating heightmaps quickly.
Run without arguments for interactive mode, or provide arguments for batch generation.

Usage:
    python generate_map.py                          # Interactive mode
    python generate_map.py mountains "Alpine City"  # Quick generation
    python generate_map.py --list                   # List available presets
"""

import sys
import argparse
from pathlib import Path

# Add src to path
sys.path.append(str(Path(__file__).parent / 'src'))

from heightmap_generator import HeightmapGenerator
from noise_generator import NoiseGenerator, create_preset_terrain
from worldmap_generator import create_worldmap_preset
from cs2_exporter import CS2Exporter, print_system_info


PRESETS = {
    'flat': 'Completely flat terrain',
    'rolling_hills': 'Gentle rolling hills',
    'mountains': 'Dramatic mountain ranges',
    'islands': 'Island archipelago with coastline',
    'canyon': 'Deep canyons and valleys',
    'highlands': 'High plateau terrain',
    'mesas': 'Flat-topped mesa formations',
}


def list_presets():
    """Print available terrain presets."""
    print("\n=== Available Terrain Presets ===\n")
    for name, description in PRESETS.items():
        print(f"  {name:15s} - {description}")
    print()


def interactive_mode():
    """Interactive map generation."""
    print("=" * 60)
    print("    Cities Skylines 2 - Heightmap Generator")
    print("=" * 60)
    print()

    # Show presets
    list_presets()

    # Get preset
    while True:
        preset = input("Select terrain preset: ").strip().lower()
        if preset in PRESETS:
            break
        print(f"Invalid preset. Choose from: {', '.join(PRESETS.keys())}")

    # Get map name
    map_name = input("Enter map name: ").strip()
    if not map_name:
        map_name = f"Generated {preset.title()}"

    # Get seed
    seed_input = input("Enter seed (or press Enter for random): ").strip()
    seed = int(seed_input) if seed_input.isdigit() else None

    # Ask about worldmap
    add_worldmap = input("Generate worldmap? (y/n): ").strip().lower() == 'y'

    if add_worldmap:
        print("\nWorldmap presets:")
        print("  1. ocean      - Surround with ocean (island)")
        print("  2. seamless   - Extend terrain naturally")
        print("  3. mountains  - Mountainous surroundings")
        print("  4. minimal    - Simple background")

        worldmap_preset = input("Select worldmap preset (or press Enter for 'ocean'): ").strip()
        if not worldmap_preset:
            worldmap_preset = 'ocean'

    print("\n" + "=" * 60)
    print("Generating your heightmap...")
    print("=" * 60)

    # Generate
    generate_map(
        preset=preset,
        map_name=map_name,
        seed=seed,
        add_worldmap=add_worldmap,
        worldmap_preset=worldmap_preset if add_worldmap else None
    )


def generate_map(preset: str,
                map_name: str,
                seed: int = None,
                add_worldmap: bool = False,
                worldmap_preset: str = 'ocean',
                export_to_cs2: bool = True):
    """
    Generate a heightmap with specified parameters.

    Args:
        preset: Terrain preset name
        map_name: Name for the map
        seed: Random seed (None for random)
        add_worldmap: Whether to generate worldmap
        worldmap_preset: Worldmap preset ('ocean', 'seamless', etc.)
        export_to_cs2: Whether to export to CS2 directory
    """
    print(f"\n1. Generating '{preset}' terrain...")
    if seed:
        print(f"   Using seed: {seed}")

    # Generate terrain
    terrain_data = create_preset_terrain(
        preset=preset,
        resolution=4096,
        seed=seed
    )

    # Create heightmap
    heightmap = HeightmapGenerator(resolution=4096, height_scale=4096, seed=seed)
    heightmap.set_height_data(terrain_data)

    # Apply smoothing for better appearance
    print("2. Smoothing terrain...")
    heightmap.smooth(iterations=1, kernel_size=3)

    # Export locally
    output_dir = Path(__file__).parent / 'output'
    output_dir.mkdir(exist_ok=True)

    safe_name = map_name.replace(' ', '_').replace('/', '_')
    heightmap_path = output_dir / f"{safe_name}.png"

    print(f"3. Exporting heightmap...")
    heightmap.export_png(str(heightmap_path))

    # Print statistics
    stats = heightmap.get_statistics()
    print(f"\n   Terrain Statistics:")
    print(f"   - Mean elevation: {stats['mean_elevation_m']:.1f}m")
    print(f"   - Std deviation: {stats['std_elevation_m']:.1f}m")

    # Generate worldmap if requested
    worldmap_path = None
    if add_worldmap:
        print(f"\n4. Generating worldmap (preset: {worldmap_preset})...")
        noise_gen = NoiseGenerator(seed=seed)

        worldmap = create_worldmap_preset(
            preset=worldmap_preset,
            playable_heightmap=heightmap.get_height_data(),
            noise_generator=noise_gen,
            world_resolution=4096
        )

        worldmap_path = output_dir / f"{safe_name}_worldmap.png"
        worldmap.export_png(str(worldmap_path))

    # Export to CS2
    if export_to_cs2:
        print(f"\n{'5' if add_worldmap else '4'}. Exporting to Cities Skylines 2...")
        try:
            exporter = CS2Exporter()
            exporter.export_to_cs2(
                heightmap_path=str(heightmap_path),
                map_name=map_name,
                worldmap_path=str(worldmap_path) if worldmap_path else None,
                overwrite=True
            )
        except Exception as e:
            print(f"\n   Note: Could not export to CS2: {e}")
            print(f"   Your heightmap is saved at: {heightmap_path}")

    print("\n" + "=" * 60)
    print("✓ Generation complete!")
    print("=" * 60)
    print(f"\nLocal files:")
    print(f"  Heightmap: {heightmap_path}")
    if worldmap_path:
        print(f"  Worldmap:  {worldmap_path}")

    if seed:
        print(f"\nSeed: {seed} (save this to recreate exact terrain)")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description='Generate heightmaps for Cities Skylines 2',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python generate_map.py                              # Interactive mode
  python generate_map.py mountains "Alpine Valley"     # Quick generation
  python generate_map.py islands "Tropical Paradise" --seed 42
  python generate_map.py highlands "Scottish Highlands" --worldmap seamless
  python generate_map.py --list                       # List presets
  python generate_map.py --info                       # System info
        """
    )

    parser.add_argument('preset', nargs='?', help='Terrain preset name')
    parser.add_argument('name', nargs='?', help='Map name')
    parser.add_argument('--seed', type=int, help='Random seed for reproducibility')
    parser.add_argument('--worldmap', choices=['ocean', 'seamless', 'mountains', 'minimal'],
                       help='Generate worldmap with specified preset')
    parser.add_argument('--list', action='store_true', help='List available presets')
    parser.add_argument('--info', action='store_true', help='Show system information')
    parser.add_argument('--no-export', action='store_true', help='Skip CS2 export')

    args = parser.parse_args()

    # Handle special commands
    if args.list:
        list_presets()
        return

    if args.info:
        print_system_info()
        return

    # Interactive mode if no preset provided
    if not args.preset:
        interactive_mode()
        return

    # Validate preset
    if args.preset not in PRESETS:
        print(f"Error: Unknown preset '{args.preset}'")
        list_presets()
        sys.exit(1)

    # Use provided name or generate one
    map_name = args.name if args.name else f"Generated {args.preset.title()}"

    # Generate map
    generate_map(
        preset=args.preset,
        map_name=map_name,
        seed=args.seed,
        add_worldmap=args.worldmap is not None,
        worldmap_preset=args.worldmap or 'ocean',
        export_to_cs2=not args.no_export
    )


if __name__ == "__main__":
    main()
