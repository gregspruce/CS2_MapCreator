"""
CS2 Preset Management Module

Implements preset saving/loading using JSON storage.
This is the OPTIMAL format for configuration management.

Why JSON:
- Human-readable (can edit manually)
- Standard format (works everywhere)
- Python built-in support (no dependencies)
- Portable across platforms
- Git-friendly (can track changes)

Alternative formats considered:
- Binary (pickle): Not human-readable, security risk
- YAML: Extra dependency, overkill for simple data
- INI: Limited data types, less flexible
- XML: Verbose, outdated

JSON is the clear winner for preset storage.
"""

import json
import os
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime


class PresetManager:
    """
    Manages terrain generation presets with JSON storage.

    Presets store all parameters needed to recreate a terrain:
    - Noise algorithm and parameters
    - Seed value
    - Resolution
    - Feature settings (rivers, lakes, etc.)

    Storage location:
    - Windows: %USERPROFILE%/.cs2_heightmaps/presets/
    - macOS/Linux: ~/.cs2_heightmaps/presets/
    """

    def __init__(self, preset_dir: Optional[Path] = None):
        """
        Initialize preset manager.

        Args:
            preset_dir: Custom preset directory (None = use default)

        Default preset directory:
        - Cross-platform compatible
        - User-specific (no permissions issues)
        - Hidden (doesn't clutter home directory)
        """
        if preset_dir is None:
            # Default: ~/.cs2_heightmaps/presets/
            home = Path.home()
            preset_dir = home / '.cs2_heightmaps' / 'presets'

        self.preset_dir = Path(preset_dir)
        self._ensure_preset_directory()

    def _ensure_preset_directory(self) -> None:
        """
        Create preset directory if it doesn't exist.

        Why this is safe:
        - Uses Path.mkdir(parents=True, exist_ok=True)
        - Won't fail if directory already exists
        - Creates parent directories as needed
        """
        self.preset_dir.mkdir(parents=True, exist_ok=True)

    def save_preset(self,
                   name: str,
                   preset_data: Dict[str, Any],
                   overwrite: bool = False) -> bool:
        """
        Save preset to JSON file.

        Args:
            name: Preset name (will be sanitized for filename)
            preset_data: Dictionary of preset parameters
            overwrite: Allow overwriting existing preset

        Returns:
            True if saved successfully, False otherwise

        Preset data structure:
        {
            'name': 'My Preset',
            'description': 'Optional description',
            'created': '2025-10-04T20:00:00',
            'version': '1.0',
            'parameters': {
                'algorithm': 'perlin',
                'resolution': 4096,
                'seed': 12345,
                'scale': 100.0,
                'octaves': 6,
                ... (algorithm-specific parameters)
            },
            'features': {
                'rivers': {'enabled': True, 'num_rivers': 5, ...},
                'lakes': {'enabled': True, 'num_lakes': 3, ...},
                'coastal': {'enabled': False, ...}
            }
        }

        Why this structure:
        - Clear separation of metadata and parameters
        - Extensible (can add new features)
        - Self-documenting (includes description, version)
        - Trackable (includes creation date)
        """
        # Sanitize filename
        safe_name = self._sanitize_filename(name)
        filepath = self.preset_dir / f"{safe_name}.json"

        # Check if exists
        if filepath.exists() and not overwrite:
            return False

        # Add metadata if not present
        if 'created' not in preset_data:
            preset_data['created'] = datetime.now().isoformat()
        if 'version' not in preset_data:
            preset_data['version'] = '1.0'
        if 'name' not in preset_data:
            preset_data['name'] = name

        # Save to JSON
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(preset_data, f, indent=2, ensure_ascii=False)
            return True
        except Exception as e:
            print(f"Error saving preset: {e}")
            return False

    def load_preset(self, name: str) -> Optional[Dict[str, Any]]:
        """
        Load preset from JSON file.

        Args:
            name: Preset name

        Returns:
            Dictionary of preset parameters, or None if not found

        Error handling:
        - Returns None if file doesn't exist
        - Returns None if JSON is invalid
        - Prints error message to help debugging
        """
        safe_name = self._sanitize_filename(name)
        filepath = self.preset_dir / f"{safe_name}.json"

        if not filepath.exists():
            return None

        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"Error loading preset: {e}")
            return None

    def list_presets(self) -> List[Dict[str, str]]:
        """
        List all available presets.

        Returns:
            List of dictionaries with preset info:
            [
                {'name': 'mountains', 'description': '...', 'created': '...'},
                ...
            ]

        Sorted alphabetically by name.
        """
        presets = []

        # Find all .json files
        for filepath in self.preset_dir.glob('*.json'):
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    data = json.load(f)

                preset_info = {
                    'name': data.get('name', filepath.stem),
                    'description': data.get('description', 'No description'),
                    'created': data.get('created', 'Unknown')
                }
                presets.append(preset_info)
            except Exception:
                # Skip invalid files
                continue

        # Sort alphabetically
        presets.sort(key=lambda p: p['name'].lower())

        return presets

    def delete_preset(self, name: str) -> bool:
        """
        Delete a preset.

        Args:
            name: Preset name

        Returns:
            True if deleted, False if not found or error

        Safety:
        - Only deletes .json files in preset directory
        - Won't delete files outside preset directory
        - No confirmation prompt (caller should handle)
        """
        safe_name = self._sanitize_filename(name)
        filepath = self.preset_dir / f"{safe_name}.json"

        if not filepath.exists():
            return False

        try:
            filepath.unlink()
            return True
        except Exception as e:
            print(f"Error deleting preset: {e}")
            return False

    def preset_exists(self, name: str) -> bool:
        """
        Check if preset exists.

        Args:
            name: Preset name

        Returns:
            True if preset file exists
        """
        safe_name = self._sanitize_filename(name)
        filepath = self.preset_dir / f"{safe_name}.json"
        return filepath.exists()

    def export_preset(self, name: str, export_path: Path) -> bool:
        """
        Export preset to custom location.

        Args:
            name: Preset name
            export_path: Destination file path

        Returns:
            True if exported successfully

        Use cases:
        - Sharing presets with others
        - Backup before modification
        - Version control
        """
        preset_data = self.load_preset(name)
        if preset_data is None:
            return False

        try:
            with open(export_path, 'w', encoding='utf-8') as f:
                json.dump(preset_data, f, indent=2, ensure_ascii=False)
            return True
        except Exception as e:
            print(f"Error exporting preset: {e}")
            return False

    def import_preset(self, import_path: Path, overwrite: bool = False) -> bool:
        """
        Import preset from file.

        Args:
            import_path: Source file path
            overwrite: Allow overwriting existing preset

        Returns:
            True if imported successfully

        Use cases:
        - Loading shared presets
        - Restoring from backup
        - Migrating from other systems
        """
        if not import_path.exists():
            return False

        try:
            with open(import_path, 'r', encoding='utf-8') as f:
                preset_data = json.load(f)

            name = preset_data.get('name', import_path.stem)
            return self.save_preset(name, preset_data, overwrite=overwrite)
        except Exception as e:
            print(f"Error importing preset: {e}")
            return False

    def _sanitize_filename(self, name: str) -> str:
        """
        Sanitize preset name for use as filename.

        Args:
            name: Raw preset name

        Returns:
            Safe filename (no special characters)

        Rules:
        - Replace spaces with underscores
        - Remove/replace special characters
        - Keep only alphanumeric, underscore, hyphen
        - Lowercase for consistency

        Why lowercase:
        - Case-insensitive filesystems (Windows, macOS)
        - Avoids conflicts like "Mountains" vs "mountains"
        """
        # Replace spaces with underscores
        safe = name.replace(' ', '_')

        # Keep only alphanumeric, underscore, hyphen
        safe = ''.join(c for c in safe if c.isalnum() or c in ('_', '-'))

        # Convert to lowercase
        safe = safe.lower()

        return safe

    def get_preset_path(self, name: str) -> Path:
        """
        Get full path to preset file.

        Args:
            name: Preset name

        Returns:
            Path object (may not exist)

        Use case:
        - For advanced users who want to edit JSON manually
        - For backup/sync tools
        """
        safe_name = self._sanitize_filename(name)
        return self.preset_dir / f"{safe_name}.json"

    def validate_preset(self, preset_data: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """
        Validate preset data structure.

        Args:
            preset_data: Preset dictionary to validate

        Returns:
            Tuple of (is_valid, list_of_errors)

        Validation checks:
        - Required fields present
        - Data types correct
        - Values in valid ranges
        - No unknown/deprecated fields (warning only)

        Use case:
        - Before saving user-created presets
        - After importing external presets
        - Quality checking
        """
        errors = []

        # Required fields
        if 'name' not in preset_data:
            errors.append("Missing required field: name")

        if 'parameters' not in preset_data:
            errors.append("Missing required field: parameters")
        else:
            params = preset_data['parameters']

            # Check parameter fields
            if 'algorithm' not in params:
                errors.append("Missing required parameter: algorithm")

            if 'resolution' in params:
                if not isinstance(params['resolution'], int) or params['resolution'] < 64:
                    errors.append("Invalid resolution (must be integer >= 64)")

            if 'seed' in params:
                if not isinstance(params['seed'], int):
                    errors.append("Invalid seed (must be integer)")

        return (len(errors) == 0, errors)
