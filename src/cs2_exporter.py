"""
CS2 Exporter - Automatic installation to Cities Skylines 2

This module handles exporting heightmaps directly to the correct CS2 directory.
It automatically detects the CS2 installation path and creates the necessary
folder structure.

CS2 Heightmap Location (from wiki):
C://Users/[username]/AppData/LocalLow/Colossal Order/Cities Skylines II/Heightmaps/
"""

import os
import platform
import shutil
from pathlib import Path
from typing import Optional, Tuple


class CS2Exporter:
    """
    Handles exporting heightmaps to Cities Skylines 2.

    This class automatically finds the CS2 user data directory and provides
    methods to export heightmaps and worldmaps with proper naming and organization.
    """

    def __init__(self):
        """
        Initialize exporter and detect CS2 installation.

        Automatically locates the CS2 heightmaps directory based on the
        operating system and user profile.
        """
        self.cs2_heightmaps_dir = self._find_cs2_directory()
        self.system = platform.system()

    def _find_cs2_directory(self) -> Optional[Path]:
        """
        Automatically detect Cities Skylines 2 heightmaps directory.

        Returns:
            Path to CS2 Heightmaps folder, or None if not found

        The directory location varies by OS:
        - Windows: %USERPROFILE%/AppData/LocalLow/Colossal Order/Cities Skylines II/Heightmaps/
        - macOS: ~/Library/Application Support/Colossal Order/Cities Skylines II/Heightmaps/
        - Linux: ~/.local/share/Colossal Order/Cities Skylines II/Heightmaps/
        """
        system = platform.system()
        username = os.getenv('USERNAME') or os.getenv('USER')

        if system == 'Windows':
            # Windows path: AppData/LocalLow
            base_path = Path(os.getenv('USERPROFILE')) / 'AppData' / 'LocalLow'
        elif system == 'Darwin':  # macOS
            base_path = Path.home() / 'Library' / 'Application Support'
        elif system == 'Linux':
            base_path = Path.home() / '.local' / 'share'
        else:
            return None

        cs2_path = base_path / 'Colossal Order' / 'Cities Skylines II' / 'Heightmaps'

        return cs2_path if cs2_path.exists() else None

    def get_cs2_directory(self) -> Optional[Path]:
        """
        Get the detected CS2 heightmaps directory.

        Returns:
            Path to CS2 Heightmaps folder, or None if not found
        """
        return self.cs2_heightmaps_dir

    def create_cs2_directory(self) -> Path:
        """
        Create the CS2 heightmaps directory if it doesn't exist.

        Returns:
            Path to CS2 Heightmaps folder

        This is useful for testing or if CS2 hasn't been run yet.
        The game will recognize this directory when it starts.
        """
        system = platform.system()

        if system == 'Windows':
            base_path = Path(os.getenv('USERPROFILE')) / 'AppData' / 'LocalLow'
        elif system == 'Darwin':
            base_path = Path.home() / 'Library' / 'Application Support'
        elif system == 'Linux':
            base_path = Path.home() / '.local' / 'share'
        else:
            raise RuntimeError(f"Unsupported operating system: {system}")

        cs2_path = base_path / 'Colossal Order' / 'Cities Skylines II' / 'Heightmaps'
        cs2_path.mkdir(parents=True, exist_ok=True)

        self.cs2_heightmaps_dir = cs2_path
        return cs2_path

    def export_to_cs2(self,
                     heightmap_path: str,
                     map_name: str,
                     worldmap_path: Optional[str] = None,
                     overwrite: bool = False) -> Tuple[Path, Optional[Path]]:
        """
        Export heightmap (and optional worldmap) directly to CS2.

        Args:
            heightmap_path: Path to heightmap PNG file
            map_name: Name for the map (will be shown in CS2)
            worldmap_path: Optional path to worldmap PNG file
            overwrite: Whether to overwrite existing files

        Returns:
            Tuple of (heightmap_dest_path, worldmap_dest_path or None)

        The exported files will appear in CS2's heightmap import menu.
        Map names should be descriptive but concise.
        """
        # Ensure CS2 directory exists
        if self.cs2_heightmaps_dir is None:
            print("CS2 Heightmaps directory not found. Creating it...")
            self.create_cs2_directory()

        # Sanitize map name for filename
        safe_name = self._sanitize_filename(map_name)

        # Destination paths
        heightmap_dest = self.cs2_heightmaps_dir / f"{safe_name}.png"
        worldmap_dest = self.cs2_heightmaps_dir / f"{safe_name}_worldmap.png"

        # Check if files exist
        if heightmap_dest.exists() and not overwrite:
            raise FileExistsError(
                f"Heightmap already exists: {heightmap_dest}\n"
                f"Use overwrite=True to replace it."
            )

        # Copy heightmap
        shutil.copy2(heightmap_path, heightmap_dest)
        print(f"✓ Exported heightmap to: {heightmap_dest}")

        # Copy worldmap if provided
        worldmap_dest_final = None
        if worldmap_path:
            if worldmap_dest.exists() and not overwrite:
                print(f"⚠ Worldmap already exists: {worldmap_dest} (skipping)")
            else:
                shutil.copy2(worldmap_path, worldmap_dest)
                worldmap_dest_final = worldmap_dest
                print(f"✓ Exported worldmap to: {worldmap_dest}")

        print(f"\n✓ Map '{map_name}' ready to import in Cities Skylines 2!")
        print(f"  Open CS2 → Map Editor → Heightmaps → Import Heightmap")
        print(f"  Look for: {safe_name}")

        return heightmap_dest, worldmap_dest_final

    def _sanitize_filename(self, name: str) -> str:
        """
        Sanitize a map name for use as a filename.

        Args:
            name: Raw map name

        Returns:
            Safe filename string

        Removes or replaces characters that aren't safe for filenames
        across different operating systems.
        """
        # Replace spaces with underscores
        safe = name.replace(' ', '_')

        # Remove unsafe characters
        unsafe_chars = '<>:"/\\|?*'
        for char in unsafe_chars:
            safe = safe.replace(char, '')

        # Remove leading/trailing dots and spaces
        safe = safe.strip('. ')

        # Limit length
        if len(safe) > 100:
            safe = safe[:100]

        return safe

    def list_installed_maps(self) -> list:
        """
        List all heightmaps currently installed in CS2.

        Returns:
            List of tuples (map_name, heightmap_path, worldmap_path or None)

        Useful for seeing what's already installed and avoiding conflicts.
        """
        if self.cs2_heightmaps_dir is None or not self.cs2_heightmaps_dir.exists():
            return []

        maps = []
        png_files = list(self.cs2_heightmaps_dir.glob('*.png'))

        # Group files by base name
        heightmaps = [f for f in png_files if not f.stem.endswith('_worldmap')]

        for heightmap in heightmaps:
            map_name = heightmap.stem
            worldmap = self.cs2_heightmaps_dir / f"{map_name}_worldmap.png"

            maps.append((
                map_name,
                heightmap,
                worldmap if worldmap.exists() else None
            ))

        return maps

    def delete_map(self, map_name: str) -> bool:
        """
        Delete a heightmap from CS2.

        Args:
            map_name: Name of the map to delete

        Returns:
            True if deleted, False if not found

        Removes both the heightmap and worldmap (if present).
        """
        if self.cs2_heightmaps_dir is None:
            return False

        safe_name = self._sanitize_filename(map_name)
        heightmap = self.cs2_heightmaps_dir / f"{safe_name}.png"
        worldmap = self.cs2_heightmaps_dir / f"{safe_name}_worldmap.png"

        deleted = False

        if heightmap.exists():
            heightmap.unlink()
            print(f"✓ Deleted heightmap: {safe_name}")
            deleted = True

        if worldmap.exists():
            worldmap.unlink()
            print(f"✓ Deleted worldmap: {safe_name}_worldmap")

        return deleted

    def get_info(self) -> dict:
        """
        Get information about the CS2 installation and exporter status.

        Returns:
            Dictionary with system info and paths

        Useful for diagnostics and troubleshooting.
        """
        installed_maps = self.list_installed_maps()

        return {
            'operating_system': self.system,
            'cs2_directory_found': self.cs2_heightmaps_dir is not None,
            'cs2_heightmaps_path': str(self.cs2_heightmaps_dir) if self.cs2_heightmaps_dir else None,
            'installed_maps_count': len(installed_maps),
            'installed_maps': [name for name, _, _ in installed_maps],
        }


def quick_export(heightmap_path: str,
                map_name: str,
                worldmap_path: Optional[str] = None,
                overwrite: bool = False) -> None:
    """
    Convenience function for quick export to CS2.

    Args:
        heightmap_path: Path to heightmap PNG
        map_name: Name for the map
        worldmap_path: Optional worldmap PNG path
        overwrite: Whether to overwrite existing files

    This is a simple wrapper for common use cases.
    """
    exporter = CS2Exporter()

    if exporter.get_cs2_directory() is None:
        print("⚠ CS2 Heightmaps directory not found!")
        print("Creating directory structure...")
        exporter.create_cs2_directory()

    exporter.export_to_cs2(
        heightmap_path=heightmap_path,
        map_name=map_name,
        worldmap_path=worldmap_path,
        overwrite=overwrite
    )


def print_system_info() -> None:
    """
    Print information about CS2 installation and system.

    Useful for troubleshooting and confirming correct setup.
    """
    exporter = CS2Exporter()
    info = exporter.get_info()

    print("=== CS2 Exporter System Information ===")
    print(f"Operating System: {info['operating_system']}")
    print(f"CS2 Directory Found: {'✓ Yes' if info['cs2_directory_found'] else '✗ No'}")

    if info['cs2_heightmaps_path']:
        print(f"CS2 Heightmaps Path: {info['cs2_heightmaps_path']}")
        print(f"Installed Maps: {info['installed_maps_count']}")

        if info['installed_maps']:
            print("\nInstalled Heightmaps:")
            for map_name in info['installed_maps']:
                print(f"  - {map_name}")
    else:
        print("\n⚠ CS2 not detected. Directory will be created on first export.")

    print("\n" + "="*50)
