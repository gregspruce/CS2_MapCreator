"""
Buildability Zone Generator for Hybrid Terrain System

Generates continuous buildability potential maps using low-frequency
Perlin noise. This replaces the deprecated binary mask approach.

WHY continuous zones:
- Smooth amplitude modulation (Session 3)
- No frequency discontinuities
- Gradual transitions between buildable and scenic areas

Created: 2025-10-09 (Session 2)
Part of: CS2 Final Implementation Plan - Hybrid Zoned Generation + Hydraulic Erosion
"""

import numpy as np
from typing import Tuple, Dict, Optional
from ..noise_generator import NoiseGenerator


class BuildabilityZoneGenerator:
    """
    Generates continuous buildability potential maps.

    NOT binary masks - continuous weight fields ranging [0, 1].

    Attributes:
        resolution (int): Heightmap resolution in pixels (4096 for CS2)
        map_size_meters (float): Physical map size in meters (14336 for CS2)
        seed (int): Random seed for reproducibility
    """

    def __init__(self,
                 resolution: int = 4096,
                 map_size_meters: float = 14336.0,
                 seed: Optional[int] = None):
        """
        Initialize zone generator.

        Args:
            resolution: Heightmap resolution (pixels)
            map_size_meters: Physical map size (meters)
            seed: Random seed for reproducible zones
        """
        self.resolution = resolution
        self.map_size_meters = map_size_meters
        self.seed = seed if seed is not None else np.random.randint(0, 100000)

        # Initialize noise generator
        self.noise_gen = NoiseGenerator(seed=self.seed)

    def generate_potential_map(self,
                               target_coverage: float = 0.70,
                               zone_wavelength: float = 6500.0,
                               zone_octaves: int = 2,
                               verbose: bool = True) -> Tuple[np.ndarray, Dict]:
        """
        Generate continuous buildability potential map.

        Args:
            target_coverage: Target percentage of map that should be buildable (0.60-0.80)
            zone_wavelength: Feature size in meters (5000-8000m, default 6500m)
            zone_octaves: Number of octaves (2-3, default 2)
            verbose: Print progress messages

        Returns:
            Tuple of (potential_map, stats_dict)
            - potential_map: np.ndarray, shape (resolution, resolution), dtype float32
              Range [0.0, 1.0] where 1.0 = high buildability, 0.0 = scenic
            - stats_dict: Statistics about generated zones

        Raises:
            ValueError: If parameters out of valid ranges
        """
        # Validate parameters
        if not 0.6 <= target_coverage <= 0.8:
            raise ValueError(f"target_coverage must be 0.6-0.8, got {target_coverage}")
        if not 5000 <= zone_wavelength <= 8000:
            raise ValueError(f"zone_wavelength must be 5000-8000m, got {zone_wavelength}")
        if zone_octaves not in [2, 3]:
            raise ValueError(f"zone_octaves must be 2 or 3, got {zone_octaves}")

        if verbose:
            print(f"\n[ZONE GENERATION - Session 2]")
            print(f"  Resolution: {self.resolution}×{self.resolution}")
            print(f"  Map size: {self.map_size_meters}m")
            print(f"  Target coverage: {target_coverage*100:.1f}%")
            print(f"  Zone wavelength: {zone_wavelength}m")
            print(f"  Zone octaves: {zone_octaves}")

        # Generate low-frequency Perlin noise
        if verbose:
            print(f"  Generating low-frequency Perlin noise...")

        potential = self.noise_gen.generate_perlin(
            resolution=self.resolution,
            scale=zone_wavelength,
            octaves=zone_octaves,
            persistence=0.5,
            lacunarity=2.0,
            show_progress=verbose
        )

        # Calculate coverage statistics
        coverage = 100 * np.sum(potential > 0.5) / potential.size
        mean_potential = potential.mean()
        std_potential = potential.std()

        if verbose:
            print(f"  Coverage (potential > 0.5): {coverage:.1f}%")
            print(f"  Mean potential: {mean_potential:.3f}")
            print(f"  Std deviation: {std_potential:.3f}")

        # Compile statistics
        stats = {
            'coverage_percent': coverage,
            'target_coverage_percent': target_coverage * 100,
            'coverage_error': abs(coverage - target_coverage * 100),
            'mean_potential': float(mean_potential),
            'std_potential': float(std_potential),
            'min_potential': float(potential.min()),
            'max_potential': float(potential.max()),
            'zone_wavelength': zone_wavelength,
            'zone_octaves': zone_octaves,
            'success': abs(coverage - target_coverage * 100) < 10.0  # ±10% tolerance
        }

        if verbose:
            print(f"  Status: {'SUCCESS' if stats['success'] else 'NEEDS ADJUSTMENT'}")
            print(f"[ZONE GENERATION COMPLETE]")

        return potential.astype(np.float32), stats

    def visualize_zones(self, potential_map: np.ndarray, output_path: str = None):
        """
        Create visualization of buildability zones.

        Args:
            potential_map: Potential map from generate_potential_map()
            output_path: Optional path to save visualization

        Note: Visualization implementation deferred to later session
        """
        # TODO: Implement visualization (matplotlib/PIL)
        # For Session 2, just validate the map exists
        print(f"[VISUALIZATION] Potential map shape: {potential_map.shape}")
        print(f"[VISUALIZATION] Range: [{potential_map.min():.3f}, {potential_map.max():.3f}]")


# Module-level convenience function
def generate_buildability_zones(resolution: int = 4096,
                                 map_size_meters: float = 14336.0,
                                 target_coverage: float = 0.70,
                                 zone_wavelength: float = 6500.0,
                                 zone_octaves: int = 2,
                                 seed: Optional[int] = None) -> Tuple[np.ndarray, Dict]:
    """
    Convenience function for zone generation.

    Args:
        resolution: Heightmap resolution (pixels)
        map_size_meters: Physical map size (meters)
        target_coverage: Target buildable percentage (0.60-0.80)
        zone_wavelength: Feature size in meters (5000-8000m)
        zone_octaves: Number of octaves (2-3)
        seed: Random seed for reproducibility

    Returns:
        Tuple of (potential_map, stats_dict)
    """
    generator = BuildabilityZoneGenerator(
        resolution=resolution,
        map_size_meters=map_size_meters,
        seed=seed
    )

    return generator.generate_potential_map(
        target_coverage=target_coverage,
        zone_wavelength=zone_wavelength,
        zone_octaves=zone_octaves
    )
