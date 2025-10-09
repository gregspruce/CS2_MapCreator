"""
Zone-Weighted Terrain Generator for Hybrid System

Generates terrain with smooth amplitude modulation based on buildability zones.
This replaces the binary mask multiplication approach that caused frequency discontinuities.

Key Innovation:
- OLD: Binary mask × noise = frequency discontinuities (pincushion problem)
- NEW: Continuous amplitude modulation = smooth transitions (no artifacts)

Created: 2025-10-09 (Session 3)
Author: Claude Code Implementation
"""

import numpy as np
from typing import Tuple, Dict, Optional
from ..noise_generator import NoiseGenerator
from ..buildability_enforcer import BuildabilityEnforcer


class ZoneWeightedTerrainGenerator:
    """
    Generates terrain with continuous amplitude modulation.

    Key difference from deprecated system:
    - OLD: Binary mask × noise (frequency discontinuities)
    - NEW: Continuous amplitude modulation (smooth transitions)

    The SAME noise octaves are used everywhere - only the amplitude varies
    based on buildability potential. This prevents frequency discontinuities
    and the pincushion problem that plagued the binary mask approach.
    """

    def __init__(self,
                 resolution: int = 4096,
                 map_size_meters: float = 14336.0,
                 seed: Optional[int] = None):
        """
        Initialize weighted terrain generator.

        Args:
            resolution: Heightmap resolution (4096 for CS2)
            map_size_meters: Physical map size in meters (14336.0 for CS2)
            seed: Random seed for reproducible terrain
        """
        self.resolution = resolution
        self.map_size_meters = map_size_meters
        self.seed = seed if seed is not None else np.random.randint(0, 100000)
        self.noise_gen = NoiseGenerator(seed=self.seed)

    def generate(self,
                 buildability_potential: np.ndarray,
                 base_amplitude: float = 0.2,
                 min_amplitude_mult: float = 0.3,
                 max_amplitude_mult: float = 1.0,
                 terrain_wavelength: float = 1000.0,
                 terrain_octaves: int = 6,
                 terrain_persistence: float = 0.5,
                 terrain_lacunarity: float = 2.0,
                 verbose: bool = True) -> Tuple[np.ndarray, Dict]:
        """
        Generate zone-weighted terrain with continuous amplitude modulation.

        Args:
            buildability_potential: Zones from Session 2 (continuous [0,1])
            base_amplitude: Base terrain amplitude (0.15-0.3)
            min_amplitude_mult: Multiplier for buildable zones (0.2-0.4)
                - P=1.0 (high buildability) → amplitude = base × min_mult
                - Creates gentle terrain (30% of base amplitude by default)
            max_amplitude_mult: Multiplier for scenic zones (0.8-1.2)
                - P=0.0 (scenic) → amplitude = base × max_mult
                - Creates full terrain detail (100% of base amplitude by default)
            terrain_wavelength: Terrain feature size in meters (500-2000m)
            terrain_octaves: Number of octaves (4-8, default 6)
                CRITICAL: Same octaves everywhere (no frequency discontinuities)
            terrain_persistence: Persistence for FBM (default 0.5)
            terrain_lacunarity: Lacunarity for FBM (default 2.0)
            verbose: Print progress messages

        Returns:
            Tuple of (terrain_heightmap, stats_dict)

        Mathematical Formula:
            A(x,y) = A_base × (A_min + (A_max - A_min) × (1 - P(x,y)))
            T(x,y) = A(x,y) × FBM(x,y, octaves, persistence, lacunarity)

        Where:
            - A(x,y) = Amplitude at each location (continuous modulation)
            - P(x,y) = Buildability potential [0,1] from Session 2
            - FBM = Fractal Brownian Motion (same parameters everywhere!)
        """
        if verbose:
            print(f"\n[SESSION 3: Zone-Weighted Terrain Generation]")
            print(f"  Base amplitude: {base_amplitude:.3f}")
            print(f"  Amplitude range: {min_amplitude_mult:.2f}× to {max_amplitude_mult:.2f}×")
            print(f"  Terrain octaves: {terrain_octaves} (SAME everywhere)")
            print(f"  Terrain wavelength: {terrain_wavelength:.0f}m")

        # Validate inputs
        if buildability_potential.shape != (self.resolution, self.resolution):
            raise ValueError(f"Buildability potential shape {buildability_potential.shape} "
                           f"must match resolution ({self.resolution}, {self.resolution})")

        if not (0.0 <= buildability_potential.min() <= buildability_potential.max() <= 1.0):
            raise ValueError(f"Buildability potential must be in range [0,1], "
                           f"got [{buildability_potential.min():.3f}, {buildability_potential.max():.3f}]")

        # Step 1: Calculate amplitude map (continuous modulation)
        # Formula: A(x,y) = A_base × (A_min + (A_max - A_min) × (1 - P(x,y)))
        #
        # WHY this formula:
        # - P = 1.0 (buildable) → A = A_base × A_min (gentle)
        # - P = 0.0 (scenic) → A = A_base × A_max (full detail)
        # - Continuous P → Smooth amplitude transitions
        if verbose:
            print(f"\n[STEP 1] Calculating amplitude modulation map...")

        amplitude_map = base_amplitude * (
            min_amplitude_mult + (max_amplitude_mult - min_amplitude_mult) * (1.0 - buildability_potential)
        )

        if verbose:
            print(f"  Amplitude map range: [{amplitude_map.min():.4f}, {amplitude_map.max():.4f}]")
            buildable_amp = amplitude_map[buildability_potential > 0.7].mean() if np.any(buildability_potential > 0.7) else amplitude_map.min()
            scenic_amp = amplitude_map[buildability_potential < 0.3].mean() if np.any(buildability_potential < 0.3) else amplitude_map.max()
            print(f"  Avg buildable zone amplitude: {buildable_amp:.4f}")
            print(f"  Avg scenic zone amplitude: {scenic_amp:.4f}")
            print(f"  Amplitude ratio (scenic/buildable): {scenic_amp/buildable_amp:.2f}×")

        # Step 2: Generate base terrain noise (SAME octaves everywhere!)
        # CRITICAL: Same noise parameters for all zones prevents frequency discontinuities
        if verbose:
            print(f"\n[STEP 2] Generating base terrain noise...")
            print(f"  Using SAME {terrain_octaves} octaves everywhere (key innovation)")

        base_noise = self.noise_gen.generate_perlin(
            resolution=self.resolution,
            scale=terrain_wavelength,
            octaves=terrain_octaves,
            persistence=terrain_persistence,
            lacunarity=terrain_lacunarity,
            show_progress=verbose
        )

        if verbose:
            print(f"  Base noise range: [{base_noise.min():.4f}, {base_noise.max():.4f}]")

        # Step 3: Apply amplitude modulation
        # T(x,y) = A(x,y) × noise(x,y)
        if verbose:
            print(f"\n[STEP 3] Applying amplitude modulation...")

        terrain = amplitude_map * base_noise

        if verbose:
            print(f"  Modulated terrain range: [{terrain.min():.4f}, {terrain.max():.4f}]")

        # Step 4: Smart normalization (prevents gradient amplification)
        if verbose:
            print(f"\n[STEP 4] Smart normalization...")

        terrain_normalized = self._smart_normalize(terrain, verbose=verbose)

        # Step 5: Calculate buildability for validation
        if verbose:
            print(f"\n[STEP 5] Validating buildability...")

        slopes = BuildabilityEnforcer.calculate_slopes(
            terrain_normalized,
            map_size_meters=self.map_size_meters
        )

        buildable_pct = BuildabilityEnforcer.calculate_buildability_percentage(slopes)

        if verbose:
            print(f"  Buildable percentage: {buildable_pct:.1f}% (target: 40-45%)")
            print(f"  Mean slope: {slopes.mean():.2f}%")
            print(f"  Median slope: {np.median(slopes):.2f}%")
            print(f"  90th percentile slope: {np.percentile(slopes, 90):.2f}%")

        # Compile statistics
        stats = {
            'buildable_percent': buildable_pct,
            'mean_slope': slopes.mean(),
            'median_slope': np.median(slopes),
            'p90_slope': np.percentile(slopes, 90),
            'p99_slope': np.percentile(slopes, 99),
            'min_height': terrain_normalized.min(),
            'max_height': terrain_normalized.max(),
            'mean_amplitude_buildable': buildable_amp if 'buildable_amp' in locals() else amplitude_map.min(),
            'mean_amplitude_scenic': scenic_amp if 'scenic_amp' in locals() else amplitude_map.max(),
            'amplitude_ratio': scenic_amp / buildable_amp if 'scenic_amp' in locals() and 'buildable_amp' in locals() else 1.0,
            'normalization_method': 'clipped' if terrain.min() >= -0.1 and terrain.max() <= 1.1 else 'stretched'
        }

        if verbose:
            print(f"\n[SESSION 3 COMPLETE]")
            print(f"  Terrain generated: {self.resolution}×{self.resolution}")
            print(f"  Buildability: {buildable_pct:.1f}%")
            print(f"  Normalization: {stats['normalization_method']}")
            status = "✅ SUCCESS" if 30.0 <= buildable_pct <= 55.0 else "⚠️ OUT OF RANGE"
            print(f"  Status: {status}")

        return terrain_normalized.astype(np.float32), stats

    def _smart_normalize(self, terrain: np.ndarray, verbose: bool = True) -> np.ndarray:
        """
        Smart normalization that avoids gradient amplification.

        Traditional normalization stretches the terrain to [0,1], which can
        amplify gradients when the terrain range is small. This "smart" version
        only normalizes when necessary, otherwise uses clipping.

        Args:
            terrain: Input terrain array
            verbose: Print normalization method

        Returns:
            Normalized terrain array [0.0, 1.0]

        Algorithm:
            If terrain range is already acceptable (-0.1 to 1.1):
                → Use clipping (no gradient amplification)
            Else:
                → Normalize (stretch to [0,1])

        WHY this matters:
            Example: terrain range [0, 0.4]
            - Traditional: (terrain - 0) / 0.4 → multiplies ALL gradients by 2.5×
            - Smart: clip(terrain, 0, 1) → no gradient amplification

        This was the 35× improvement breakthrough from Session 1!
        """
        t_min, t_max = terrain.min(), terrain.max()
        t_range = t_max - t_min

        if t_min >= -0.1 and t_max <= 1.1:
            # Already in acceptable range, clip without stretching
            if verbose:
                print(f"  [SMART NORM] Clipping to [0,1] (no amplification)")
                print(f"  Range: [{t_min:.3f}, {t_max:.3f}] → acceptable")
            return np.clip(terrain, 0.0, 1.0)

        elif t_range > 0:
            # Need normalization
            if verbose:
                print(f"  [SMART NORM] Normalizing [{t_min:.3f}, {t_max:.3f}] → [0,1]")
                print(f"  Gradient amplification factor: {1.0/t_range:.2f}×")
            return (terrain - t_min) / t_range

        else:
            # Edge case: flat terrain
            if verbose:
                print(f"  [SMART NORM] Flat terrain detected (range = 0)")
            return np.zeros_like(terrain)
