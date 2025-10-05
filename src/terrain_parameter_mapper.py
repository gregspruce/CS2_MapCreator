"""
CS2 Heightmap Generator - Terrain Parameter Mapper

Converts user-friendly terrain parameters to technical noise parameters.

Why This Exists:
Technical noise parameters (scale, octaves, persistence, lacunarity) are
meaningless to most users. This mapper provides intuitive controls:
- Roughness: smooth ↔ jagged
- Feature Size: small ↔ large
- Detail Level: simple ↔ intricate
- Height Variation: flat ↔ extreme

Users control what they care about, system handles the math.
"""

from typing import Dict, Tuple
import numpy as np


class TerrainParameterMapper:
    """
    Maps intuitive terrain parameters to technical noise parameters.

    Intuitive Parameters (0-100%):
    - roughness: 0% = smooth rolling hills, 100% = jagged mountains
    - feature_size: 0% = small tight hills, 100% = large sweeping ranges
    - detail_level: 0% = simple terrain, 100% = intricate details
    - height_variation: 0% = flat, 100% = extreme elevation changes

    Technical Parameters (output):
    - scale: 50-400 (wavelength of noise)
    - octaves: 2-8 (detail layers)
    - persistence: 0.3-0.7 (amplitude falloff per octave)
    - lacunarity: 2.0 (fixed, standard value)
    """

    @staticmethod
    def intuitive_to_technical(
        roughness: float,
        feature_size: float,
        detail_level: float,
        height_variation: float
    ) -> Dict[str, float]:
        """
        Convert intuitive parameters to technical noise parameters.

        Args:
            roughness: 0-100 (smooth to jagged)
            feature_size: 0-100 (small to large)
            detail_level: 0-100 (simple to intricate)
            height_variation: 0-100 (flat to extreme)

        Returns:
            Dictionary with technical parameters:
            - scale: float (50-400)
            - octaves: int (2-8)
            - persistence: float (0.3-0.7)
            - lacunarity: float (2.0)
            - height_multiplier: float (for post-processing)

        Implementation notes:
        - Roughness → persistence (higher = rougher)
        - Feature Size → scale (higher = larger features)
        - Detail Level → octaves (more = more detail)
        - Height Variation → post-processing multiplier
        """
        # Validate inputs
        roughness = np.clip(roughness, 0, 100)
        feature_size = np.clip(feature_size, 0, 100)
        detail_level = np.clip(detail_level, 0, 100)
        height_variation = np.clip(height_variation, 0, 100)

        # Map roughness to persistence (0.3-0.7)
        # Lower persistence = smoother terrain
        # Higher persistence = rougher, more chaotic terrain
        persistence = 0.3 + (roughness / 100.0) * 0.4

        # Map feature_size to scale (50-400)
        # Lower scale = tight, small features
        # Higher scale = large, sweeping features
        scale = 50.0 + (feature_size / 100.0) * 350.0

        # Map detail_level to octaves (2-8)
        # Fewer octaves = simple, fast generation
        # More octaves = detailed, slower generation
        octaves = 2 + int((detail_level / 100.0) * 6)

        # Lacunarity is fixed at 2.0 (standard for natural terrain)
        lacunarity = 2.0

        # Height variation for post-processing
        # 0% = compress toward middle (flat)
        # 100% = full range (extreme variation)
        height_multiplier = height_variation / 100.0

        return {
            'scale': scale,
            'octaves': octaves,
            'persistence': persistence,
            'lacunarity': lacunarity,
            'height_multiplier': height_multiplier
        }

    @staticmethod
    def apply_height_variation(heightmap: np.ndarray, height_multiplier: float) -> np.ndarray:
        """
        Apply height variation to normalized heightmap.

        Args:
            heightmap: Normalized heightmap (0-1)
            height_multiplier: 0-1 (0=flat, 1=full range)

        Returns:
            Heightmap with adjusted variation

        How it works:
        - Power curve compresses toward 0 (flatter)
        - height_multiplier controls compression amount
        - 0.0 = almost completely flat
        - 1.0 = no change (full variation)
        """
        if height_multiplier < 0.01:
            # Nearly flat
            return np.full_like(heightmap, 0.5)

        # Apply power curve to compress/expand range
        # Exponent > 1 = compress (flatter)
        # Exponent < 1 = expand (more extreme)
        exponent = 1.0 / (0.5 + height_multiplier * 1.5)
        adjusted = heightmap ** exponent

        # Re-normalize to 0-1
        return (adjusted - adjusted.min()) / (adjusted.max() - adjusted.min())


# Preset definitions using intuitive parameters
INTUITIVE_PRESETS = {
    'flat': {
        'roughness': 10,
        'feature_size': 80,
        'detail_level': 20,
        'height_variation': 10,
        'description': 'Nearly flat terrain with minimal variation'
    },
    'hills': {
        'roughness': 35,
        'feature_size': 45,
        'detail_level': 50,
        'height_variation': 45,
        'description': 'Gentle rolling hills with moderate elevation'
    },
    'mountains': {
        'roughness': 70,
        'feature_size': 60,
        'detail_level': 75,
        'height_variation': 85,
        'description': 'Dramatic mountain ranges with high peaks'
    },
    'islands': {
        'roughness': 55,
        'feature_size': 35,
        'detail_level': 60,
        'height_variation': 70,
        'description': 'Island archipelago with varied coastlines'
    },
    'canyons': {
        'roughness': 50,
        'feature_size': 30,
        'detail_level': 65,
        'height_variation': 80,
        'description': 'Deep canyons and dramatic valleys'
    },
    'highlands': {
        'roughness': 40,
        'feature_size': 50,
        'detail_level': 55,
        'height_variation': 60,
        'description': 'High plateau terrain with moderate variation'
    },
    'mesas': {
        'roughness': 30,
        'feature_size': 40,
        'detail_level': 45,
        'height_variation': 55,
        'description': 'Flat-topped mesas with sharp cliffs'
    }
}


def get_preset_parameters(preset_name: str) -> Dict[str, float]:
    """
    Get intuitive parameters for a preset.

    Args:
        preset_name: Name of preset ('mountains', 'hills', etc.)

    Returns:
        Dictionary with intuitive parameters

    Raises:
        KeyError: If preset doesn't exist
    """
    if preset_name not in INTUITIVE_PRESETS:
        raise KeyError(f"Unknown preset: {preset_name}")

    return INTUITIVE_PRESETS[preset_name].copy()


def get_preset_description(preset_name: str) -> str:
    """Get description for a preset."""
    if preset_name not in INTUITIVE_PRESETS:
        return "Unknown preset"
    return INTUITIVE_PRESETS[preset_name]['description']


def list_presets() -> list:
    """Get list of available preset names."""
    return list(INTUITIVE_PRESETS.keys())
