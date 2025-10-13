"""
Detail Generator for Terrain Enhancement (Session 8)

Adds conditional micro-scale detail to steep areas while preserving buildable zones.
Detail is applied proportionally based on local slope, ensuring flat areas remain flat.

Author: Claude Code (Session 8 Implementation)
Date: 2025-10-10
"""

import numpy as np
import time
from typing import Tuple, Dict, Optional

from src.noise_generator import NoiseGenerator
from src.buildability_enforcer import BuildabilityEnforcer


class DetailGenerator:
    """
    Adds conditional high-frequency detail to steep terrain areas.

    Key Features:
    - Detail ONLY applied to steep areas (slope > 5%)
    - Amplitude scales proportionally with slope (0% at 5%, 100% at 15%+)
    - Preserves flat buildable zones (no modification where slope < 5%)
    - High-frequency noise for natural micro-scale variation
    - Performance optimized with vectorized operations

    Algorithm:
    1. Calculate local slopes across terrain
    2. Generate high-frequency detail noise (wavelength ~50-100m)
    3. Calculate scaling factor per pixel: max(0, (slope - 0.05) / 0.10)
    4. Apply scaled detail: new_height = height + (detail * scaling * amplitude)

    Usage:
        generator = DetailGenerator(resolution=4096, map_size_meters=14336, seed=42)
        detailed_terrain, stats = generator.add_detail(
            terrain,
            detail_amplitude=0.02,
            detail_wavelength=75.0
        )
    """

    def __init__(
        self,
        resolution: int,
        map_size_meters: float = 14336.0,
        seed: int = 42
    ):
        """
        Initialize detail generator.

        Args:
            resolution: Heightmap resolution (e.g., 4096 for 4096x4096)
            map_size_meters: Physical map size in meters (default: 14336m = 14.3km)
            seed: Random seed for reproducibility

        Raises:
            ValueError: If parameters are invalid
        """
        # Validation
        if resolution < 256 or resolution > 8192:
            raise ValueError(f"Resolution must be 256-8192, got {resolution}")
        if map_size_meters < 1000.0 or map_size_meters > 100000.0:
            raise ValueError(f"Map size must be 1000-100000m, got {map_size_meters}")

        self.resolution = resolution
        self.map_size_meters = map_size_meters
        self.seed = seed

        # Initialize noise generator for high-frequency detail
        self.noise_gen = NoiseGenerator(seed=seed)

        # Calculate pixel size for slope calculations
        self.pixel_size_meters = map_size_meters / resolution

        print(f"[DetailGenerator] Initialized (resolution={resolution}, seed={seed})")

    def add_detail(
        self,
        terrain: np.ndarray,
        detail_amplitude: float = 0.02,
        detail_wavelength: float = 75.0,
        min_slope_threshold: float = 0.05,
        max_slope_threshold: float = 0.15,
        octaves: int = 2,
        persistence: float = 0.5,
        lacunarity: float = 2.0,
        verbose: bool = True
    ) -> Tuple[np.ndarray, Dict]:
        """
        Add conditional detail to steep terrain areas.

        Args:
            terrain: Input terrain heightmap [0, 1], shape (N, N)
            detail_amplitude: Maximum detail height (default: 0.02 = 2% of range)
            detail_wavelength: Detail feature size in meters (default: 75m)
            min_slope_threshold: No detail below this slope (default: 0.05 = 5%)
            max_slope_threshold: Full detail above this slope (default: 0.15 = 15%)
            octaves: Number of noise octaves (default: 2)
            persistence: Amplitude decay per octave (default: 0.5)
            lacunarity: Frequency multiplier per octave (default: 2.0)
            verbose: Print progress information (default: True)

        Returns:
            Tuple of (detailed_terrain, statistics_dict)

        Raises:
            ValueError: If parameters are invalid
        """
        start_time = time.time()

        # Validation
        if terrain.shape != (self.resolution, self.resolution):
            raise ValueError(
                f"Terrain shape must be ({self.resolution}, {self.resolution}), "
                f"got {terrain.shape}"
            )
        if terrain.dtype != np.float32:
            raise ValueError(f"Terrain must be float32, got {terrain.dtype}")
        if detail_amplitude < 0.0 or detail_amplitude > 0.1:
            raise ValueError(f"Detail amplitude must be 0-0.1, got {detail_amplitude}")
        if detail_wavelength < 10.0 or detail_wavelength > 500.0:
            raise ValueError(f"Detail wavelength must be 10-500m, got {detail_wavelength}")
        if min_slope_threshold < 0.0 or min_slope_threshold > 0.2:
            raise ValueError(f"Min slope must be 0-0.2, got {min_slope_threshold}")
        if max_slope_threshold <= min_slope_threshold or max_slope_threshold > 0.5:
            raise ValueError(f"Max slope must be >{min_slope_threshold} and <=0.5, got {max_slope_threshold}")
        if octaves < 1 or octaves > 4:
            raise ValueError(f"Octaves must be 1-4, got {octaves}")

        # CRITICAL FIX: Scale detail_amplitude relative to terrain amplitude
        # This prevents detail from being too large for gentle terrain
        terrain_amplitude = float(terrain.max() - terrain.min())
        if terrain_amplitude < 0.001:
            # Terrain too flat, skip detail
            if verbose:
                print(f"\n[DetailGenerator] Terrain too flat (amplitude={terrain_amplitude:.6f}), skipping detail")
            return terrain.copy(), {'skipped': True, 'reason': 'terrain_too_flat'}

        # Scale detail to be proportional to terrain amplitude
        # Conservative scaling to prevent high-frequency detail from creating excessive slopes
        # For terrain amplitude 0.1, detail_amplitude 0.02 becomes 0.0002 (0.1% of range)
        # For terrain amplitude 1.0, detail_amplitude 0.02 becomes 0.002 (0.1% of range)
        # Using 0.01x multiplier because detail is high-frequency and affects slopes significantly
        scaled_detail_amplitude = detail_amplitude * terrain_amplitude * 0.01

        if verbose:
            print(f"\n[DetailGenerator] Adding conditional detail...")
            print(f"  Terrain amplitude: {terrain_amplitude:.4f}")
            print(f"  Detail amplitude (original): {detail_amplitude:.3f}")
            print(f"  Detail amplitude (scaled): {scaled_detail_amplitude:.4f}")
            print(f"  Scaling factor: {terrain_amplitude:.2f}x")
            print(f"  Detail wavelength: {detail_wavelength:.1f}m")
            print(f"  Slope range: {min_slope_threshold:.1%} - {max_slope_threshold:.1%}")

        # Step 1: Calculate slopes
        if verbose:
            print(f"  [1/4] Calculating slopes...")
        slopes = BuildabilityEnforcer.calculate_slopes(
            terrain,
            self.map_size_meters
        )

        # Step 2: Generate high-frequency detail noise
        if verbose:
            print(f"  [2/4] Generating detail noise ({octaves} octaves)...")
        detail_noise = self._generate_detail_noise(
            detail_wavelength,
            octaves,
            persistence,
            lacunarity
        )

        # Step 3: Calculate proportional scaling factors
        if verbose:
            print(f"  [3/4] Computing scaling factors...")
        scaling_factors = self._calculate_scaling_factors(
            slopes,
            min_slope_threshold,
            max_slope_threshold
        )

        # Step 4: Apply scaled detail
        if verbose:
            print(f"  [4/4] Applying detail...")
        detailed_terrain = terrain.copy()
        detail_contribution = detail_noise * scaling_factors * scaled_detail_amplitude  # Use scaled amplitude!
        detailed_terrain += detail_contribution

        # Clip to valid range [0, 1]
        detailed_terrain = np.clip(detailed_terrain, 0.0, 1.0)

        # Calculate statistics
        elapsed = time.time() - start_time
        stats = self._calculate_statistics(
            terrain,
            detailed_terrain,
            scaling_factors,
            detail_contribution,
            slopes,
            min_slope_threshold,
            elapsed
        )

        if verbose:
            print(f"  [SUCCESS] Detail applied to {stats['detail_applied_pct']:.1f}% of terrain")
            print(f"  Mean detail amplitude: {stats['mean_detail_amplitude']:.4f}")
            print(f"  Max detail amplitude: {stats['max_detail_amplitude']:.4f}")
            print(f"  Processing time: {stats['processing_time']:.2f}s")

        return detailed_terrain.astype(np.float32), stats

    def _generate_detail_noise(
        self,
        wavelength: float,
        octaves: int,
        persistence: float,
        lacunarity: float
    ) -> np.ndarray:
        """
        Generate high-frequency detail noise.

        Args:
            wavelength: Base wavelength in meters
            octaves: Number of octaves
            persistence: Amplitude decay
            lacunarity: Frequency multiplier

        Returns:
            Detail noise array, range [-1, 1]
        """
        # Calculate scale from wavelength
        # scale = wavelength / map_size (normalized units)
        scale = wavelength / self.map_size_meters

        # Generate Perlin noise with specified parameters
        detail = self.noise_gen.generate_perlin(
            resolution=self.resolution,
            scale=scale,
            octaves=octaves,
            persistence=persistence,
            lacunarity=lacunarity
        )

        # Normalize to [-1, 1] range
        detail_min, detail_max = detail.min(), detail.max()
        if detail_max > detail_min:
            detail = 2.0 * (detail - detail_min) / (detail_max - detail_min) - 1.0
        else:
            detail = np.zeros_like(detail)

        return detail.astype(np.float32)

    def _calculate_scaling_factors(
        self,
        slopes: np.ndarray,
        min_threshold: float,
        max_threshold: float
    ) -> np.ndarray:
        """
        Calculate proportional scaling factors based on slopes.

        Formula: scaling = max(0, (slope - min) / (max - min))
        - slope < min_threshold: scaling = 0 (no detail)
        - min_threshold <= slope <= max_threshold: scaling = linear 0->1
        - slope > max_threshold: scaling = 1 (full detail)

        Args:
            slopes: Slope array (fractional units, e.g., 0.05 = 5%)
            min_threshold: Minimum slope for detail
            max_threshold: Maximum slope for full detail

        Returns:
            Scaling factors array [0, 1]
        """
        # Vectorized calculation
        slope_range = max_threshold - min_threshold
        scaling = (slopes - min_threshold) / slope_range
        scaling = np.clip(scaling, 0.0, 1.0)

        return scaling.astype(np.float32)

    def _calculate_statistics(
        self,
        original_terrain: np.ndarray,
        detailed_terrain: np.ndarray,
        scaling_factors: np.ndarray,
        detail_contribution: np.ndarray,
        slopes: np.ndarray,
        min_slope: float,
        elapsed_time: float
    ) -> Dict:
        """
        Calculate comprehensive statistics for detail addition.

        Args:
            original_terrain: Original heightmap
            detailed_terrain: Terrain with detail added
            scaling_factors: Applied scaling factors [0, 1]
            detail_contribution: Actual detail heights added
            slopes: Slope array
            min_slope: Minimum slope threshold
            elapsed_time: Processing time in seconds

        Returns:
            Statistics dictionary
        """
        # Calculate where detail was applied (scaling > 0)
        detail_mask = scaling_factors > 0.0
        num_detail_pixels = np.sum(detail_mask)
        total_pixels = scaling_factors.size
        detail_applied_pct = 100.0 * num_detail_pixels / total_pixels

        # Detail amplitude statistics
        if num_detail_pixels > 0:
            mean_detail_amplitude = np.mean(np.abs(detail_contribution[detail_mask]))
            max_detail_amplitude = np.max(np.abs(detail_contribution))
            mean_scaling_factor = np.mean(scaling_factors[detail_mask])
        else:
            mean_detail_amplitude = 0.0
            max_detail_amplitude = 0.0
            mean_scaling_factor = 0.0

        # Terrain change statistics
        terrain_diff = np.abs(detailed_terrain - original_terrain)
        mean_change = np.mean(terrain_diff)
        max_change = np.max(terrain_diff)

        # Flat area preservation check (slope < min_slope should have zero change)
        flat_mask = slopes < min_slope
        if np.any(flat_mask):
            flat_area_change = np.mean(terrain_diff[flat_mask])
            flat_area_max_change = np.max(terrain_diff[flat_mask])
        else:
            flat_area_change = 0.0
            flat_area_max_change = 0.0

        stats = {
            'detail_applied_pct': detail_applied_pct,
            'num_detail_pixels': int(num_detail_pixels),
            'mean_detail_amplitude': float(mean_detail_amplitude),
            'max_detail_amplitude': float(max_detail_amplitude),
            'mean_scaling_factor': float(mean_scaling_factor),
            'mean_terrain_change': float(mean_change),
            'max_terrain_change': float(max_change),
            'flat_area_preservation': {
                'mean_change': float(flat_area_change),
                'max_change': float(flat_area_max_change)
            },
            'processing_time': float(elapsed_time)
        }

        return stats


def add_detail_to_terrain(
    terrain: np.ndarray,
    resolution: int,
    map_size_meters: float = 14336.0,
    detail_amplitude: float = 0.02,
    detail_wavelength: float = 75.0,
    seed: int = 42
) -> Tuple[np.ndarray, Dict]:
    """
    Convenience function to add detail to terrain.

    Args:
        terrain: Input terrain heightmap [0, 1]
        resolution: Heightmap resolution
        map_size_meters: Physical map size in meters
        detail_amplitude: Maximum detail height (default: 0.02)
        detail_wavelength: Detail scale in meters (default: 75m)
        seed: Random seed for reproducibility

    Returns:
        Tuple of (detailed_terrain, statistics)
    """
    generator = DetailGenerator(
        resolution=resolution,
        map_size_meters=map_size_meters,
        seed=seed
    )

    return generator.add_detail(
        terrain,
        detail_amplitude=detail_amplitude,
        detail_wavelength=detail_wavelength
    )


if __name__ == "__main__":
    # Example usage and testing
    print("Detail Generator - Example Usage")
    print("=" * 60)

    # Create synthetic test terrain
    resolution = 1024
    x = np.linspace(0, 1, resolution)
    y = np.linspace(0, 1, resolution)
    X, Y = np.meshgrid(x, y)

    # Create terrain with varying slopes
    # Left half: flat (buildable), right half: steep (scenic)
    terrain = np.where(
        X < 0.5,
        0.5 + 0.05 * np.sin(10 * np.pi * Y),  # Gentle rolling (buildable)
        0.3 + 0.3 * np.sin(5 * np.pi * X) * np.cos(5 * np.pi * Y)  # Steep mountains
    ).astype(np.float32)

    # Add detail
    generator = DetailGenerator(resolution=resolution, seed=42)
    detailed, stats = generator.add_detail(
        terrain,
        detail_amplitude=0.02,
        detail_wavelength=75.0
    )

    print("\n" + "=" * 60)
    print("Statistics:")
    print(f"  Detail applied to: {stats['detail_applied_pct']:.1f}% of terrain")
    print(f"  Mean amplitude: {stats['mean_detail_amplitude']:.4f}")
    print(f"  Max amplitude: {stats['max_detail_amplitude']:.4f}")
    print(f"  Flat area preservation:")
    print(f"    Mean change: {stats['flat_area_preservation']['mean_change']:.6f}")
    print(f"    Max change: {stats['flat_area_preservation']['max_change']:.6f}")
    print(f"  Processing time: {stats['processing_time']:.2f}s")
    print("=" * 60)
