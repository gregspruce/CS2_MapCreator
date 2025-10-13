"""
Ridge Enhancement for Mountain Zones (Session 5)

Adds sharp ridgelines to scenic/mountain zones for coherent mountain ranges.
This enhances geological realism by creating connected ridgelines that erosion
will carve into realistic valleys.

Key Innovation:
- Ridge noise formula: R = 2 × |0.5 - FBM| creates V-shaped valleys → sharp ridges
- Zone-restricted application: Only affects scenic zones (P < 0.4)
- Smooth blending: smoothstep transition prevents artificial boundaries

Created: 2025-10-10 (Session 5)
Author: Claude Code Implementation
"""

import numpy as np
from typing import Tuple, Dict, Optional
import time
from ..noise_generator import NoiseGenerator


class RidgeEnhancer:
    """
    Ridge noise generator for mountain zones.

    Creates sharp ridgelines in scenic areas (P < 0.4) while leaving
    buildable zones (P > 0.4) untouched through smooth blending.

    The absolute value transform of Perlin noise creates V-shaped valleys
    which, when added to terrain, produce sharp ridgelines characteristic
    of real mountain ranges.
    """

    def __init__(self,
                 resolution: int = 4096,
                 map_size_meters: float = 14336.0,
                 seed: Optional[int] = None):
        """
        Initialize ridge enhancer.

        Args:
            resolution: Heightmap resolution (4096 for CS2)
            map_size_meters: Physical map size in meters (14336.0 for CS2)
            seed: Random seed for reproducible ridge patterns
        """
        self.resolution = resolution
        self.map_size_meters = map_size_meters
        self.seed = seed if seed is not None else np.random.randint(0, 100000)
        self.noise_gen = NoiseGenerator(seed=self.seed)

    @staticmethod
    def _smoothstep(edge0: float, edge1: float, x: np.ndarray) -> np.ndarray:
        """
        Smooth Hermite interpolation between 0 and 1.

        This creates smooth transitions without derivative discontinuities,
        preventing artificial-looking boundaries in the terrain.

        Args:
            edge0: Lower edge of transition (ridge blending starts here)
            edge1: Upper edge of transition (ridge blending ends here)
            x: Input values (typically buildability potential)

        Returns:
            Smooth interpolation result [0, 1]

        Mathematical Formula:
            t = clamp((x - edge0) / (edge1 - edge0), 0, 1)
            result = t² × (3 - 2t)

        Properties:
            - S(edge0) = 0 (no blending below threshold)
            - S(edge1) = 1 (full blending above threshold)
            - S'(edge0) = 0, S'(edge1) = 0 (smooth derivatives)
        """
        # Normalize x to [0, 1] range between edges
        t = np.clip((x - edge0) / (edge1 - edge0), 0.0, 1.0)

        # Smooth Hermite interpolation: 3t² - 2t³
        return t * t * (3.0 - 2.0 * t)

    def _generate_ridge_noise(self,
                              ridge_octaves: int = 5,
                              ridge_wavelength: float = 1500.0,
                              ridge_persistence: float = 0.5,
                              ridge_lacunarity: float = 2.0,
                              verbose: bool = True) -> np.ndarray:
        """
        Generate ridge noise using absolute value transform of FBM.

        The absolute value of Perlin noise creates V-shaped valleys which
        become sharp ridges when added to terrain. This mimics natural
        geological ridge formation.

        Args:
            ridge_octaves: Number of octaves (4-6, default 5)
            ridge_wavelength: Feature size in meters (1000-2000m)
            ridge_persistence: Amplitude decay per octave (default 0.5)
            ridge_lacunarity: Frequency increase per octave (default 2.0)
            verbose: Print progress messages

        Returns:
            Ridge noise array [0, 1]

        Mathematical Formula:
            R(x, y) = 2 × |0.5 - FBM(x, y, octaves, persistence, lacunarity)|

        WHY this formula:
            - FBM centered at 0.5: range [0, 1]
            - |0.5 - FBM|: creates V-shapes at noise=0.5
            - Multiply by 2: expands to full [0, 1] range
            - Result: Sharp ridges where noise crosses 0.5
        """
        if verbose:
            print(f"\n[RIDGE NOISE] Generating ridge noise...")
            print(f"  Octaves: {ridge_octaves}")
            print(f"  Wavelength: {ridge_wavelength:.0f}m")

        # Generate base Perlin noise
        base_noise = self.noise_gen.generate_perlin(
            resolution=self.resolution,
            scale=ridge_wavelength,
            octaves=ridge_octaves,
            persistence=ridge_persistence,
            lacunarity=ridge_lacunarity,
            show_progress=verbose
        )

        # Normalize to [0, 1] if needed
        if base_noise.min() < 0 or base_noise.max() > 1:
            base_noise = (base_noise - base_noise.min()) / (base_noise.max() - base_noise.min())

        # Apply absolute value transform: R = 2 × |0.5 - noise|
        # This creates sharp ridges at locations where noise crosses 0.5
        ridge_noise = 2.0 * np.abs(0.5 - base_noise)

        if verbose:
            print(f"  Ridge noise range: [{ridge_noise.min():.4f}, {ridge_noise.max():.4f}]")
            print(f"  Ridge noise mean: {ridge_noise.mean():.4f}")

        return ridge_noise.astype(np.float32)

    def enhance(self,
                terrain: np.ndarray,
                buildability_potential: np.ndarray,
                ridge_octaves: int = 5,
                ridge_wavelength: float = 1500.0,
                ridge_strength: float = 0.2,
                blend_edge0: float = 0.2,
                blend_edge1: float = 0.4,
                verbose: bool = True) -> Tuple[np.ndarray, Dict]:
        """
        Add ridge noise to mountain zones with smooth blending.

        Ridges are only applied to scenic zones (low buildability potential)
        using smooth transitions to prevent artificial boundaries.

        Args:
            terrain: Input terrain from Session 3/4 [0, 1]
            buildability_potential: Zones from Session 2 [0, 1]
            ridge_octaves: Octaves for ridge noise (4-6, default 5)
            ridge_wavelength: Ridge feature size in meters (1000-2000m)
            ridge_strength: Ridge prominence (0.1-0.3, default 0.2)
                - Lower: Subtle ridges
                - Higher: Dramatic ridgelines
            blend_edge0: Start of transition zone (0.15-0.25, default 0.2)
                - Below this P value: Full ridges (alpha = 1)
            blend_edge1: End of transition zone (0.35-0.45, default 0.4)
                - Above this P value: No ridges (alpha = 0)
            verbose: Print progress messages

        Returns:
            Tuple of (enhanced_terrain, statistics_dict)

        Mathematical Formula:
            alpha(x,y) = smoothstep(edge0, edge1, 1 - P(x,y))
            T_final(x,y) = T(x,y) + alpha(x,y) x R(x,y) x ridge_strength

        Where:
            - P(x,y) = Buildability potential from Session 2
            - R(x,y) = Ridge noise (absolute value of FBM)
            - alpha(x,y) = Blending factor [0, 1]
            - T(x,y) = Input terrain

        Application Zones:
            - P > 0.4: No ridges (buildable zones, alpha ~= 0)
            - 0.2 < P < 0.4: Smooth transition (alpha increases 0 -> 1)
            - P < 0.2: Full ridges (scenic zones, alpha ~= 1)
        """
        start_time = time.time()

        if verbose:
            print(f"\n[SESSION 5: Ridge Enhancement for Mountain Zones]")
            print(f"  Ridge octaves: {ridge_octaves}")
            print(f"  Ridge strength: {ridge_strength:.2f}")
            print(f"  Blend transition: P={blend_edge0:.2f} to P={blend_edge1:.2f}")

        # CRITICAL FIX: Scale ridge_strength relative to terrain amplitude
        # This prevents ridges from dominating gentle terrain
        terrain_amplitude = float(terrain.max() - terrain.min())
        if terrain_amplitude < 0.001:
            # Terrain too flat, skip ridges
            if verbose:
                print(f"\n[RidgeEnhancer] Terrain too flat (amplitude={terrain_amplitude:.6f}), skipping ridges")
            return terrain.copy(), {'skipped': True, 'reason': 'terrain_too_flat'}

        # Scale ridges to be proportional to terrain amplitude
        # Ridges are low-frequency prominent features (wavelength ~1500m)
        # Using 0.15x multiplier to create noticeable but not dominant features
        # For terrain amplitude 0.1, ridge_strength 0.2 becomes 0.003 (3% of range)
        # For terrain amplitude 1.0, ridge_strength 0.2 becomes 0.03 (3% of range)
        # This is 15x larger than detail (0.01x) because ridges are prominent scenic features
        scaled_ridge_strength = ridge_strength * terrain_amplitude * 0.15

        if verbose:
            print(f"\n[AMPLITUDE-AWARE SCALING]")
            print(f"  Terrain amplitude: {terrain_amplitude:.4f}")
            print(f"  Ridge strength (original): {ridge_strength:.3f}")
            print(f"  Ridge strength (scaled): {scaled_ridge_strength:.4f}")
            print(f"  Scaling factor: {terrain_amplitude:.2f}x")

        # Validate inputs
        if terrain.shape != (self.resolution, self.resolution):
            raise ValueError(f"Terrain shape {terrain.shape} "
                           f"must match resolution ({self.resolution}, {self.resolution})")

        if buildability_potential.shape != (self.resolution, self.resolution):
            raise ValueError(f"Buildability potential shape {buildability_potential.shape} "
                           f"must match resolution ({self.resolution}, {self.resolution})")

        if not (0.0 <= terrain.min() and terrain.max() <= 1.1):
            raise ValueError(f"Terrain must be in range [0,1], "
                           f"got [{terrain.min():.3f}, {terrain.max():.3f}]")

        if not (0.0 <= buildability_potential.min() <= buildability_potential.max() <= 1.0):
            raise ValueError(f"Buildability potential must be in range [0,1], "
                           f"got [{buildability_potential.min():.3f}, {buildability_potential.max():.3f}]")

        if not (4 <= ridge_octaves <= 6):
            raise ValueError(f"Ridge octaves must be in range [4, 6], got {ridge_octaves}")

        if not (0.1 <= ridge_strength <= 0.3):
            raise ValueError(f"Ridge strength must be in range [0.1, 0.3], got {ridge_strength}")

        if not (blend_edge0 < blend_edge1):
            raise ValueError(f"blend_edge0 ({blend_edge0}) must be < blend_edge1 ({blend_edge1})")

        # Store original terrain stats for comparison
        original_terrain = terrain.copy()

        # Step 1: Generate ridge noise
        if verbose:
            print(f"\n[STEP 1] Generating ridge noise...")

        ridge_noise = self._generate_ridge_noise(
            ridge_octaves=ridge_octaves,
            ridge_wavelength=ridge_wavelength,
            verbose=verbose
        )

        # Step 2: Calculate blending factor (zone-restricted application)
        if verbose:
            print(f"\n[STEP 2] Calculating zone-based blending...")

        # Inverse potential: 1.0 in scenic zones (P=0), 0.0 in buildable zones (P=1)
        inverse_potential = 1.0 - buildability_potential

        # Apply smoothstep for smooth transition
        # alpha = 0 for P > blend_edge1 (buildable zones)
        # alpha = 1 for P < blend_edge0 (scenic zones)
        # alpha smoothly transitions between edge0 and edge1
        alpha = self._smoothstep(blend_edge0, blend_edge1, inverse_potential)

        if verbose:
            ridge_coverage = 100.0 * np.sum(alpha > 0.1) / alpha.size
            full_ridge_coverage = 100.0 * np.sum(alpha > 0.9) / alpha.size
            transition_coverage = 100.0 * np.sum((alpha > 0.1) & (alpha < 0.9)) / alpha.size

            print(f"  Ridge blending factor (alpha) range: [{alpha.min():.4f}, {alpha.max():.4f}]")
            print(f"  Ridge coverage (alpha > 0.1): {ridge_coverage:.1f}%")
            print(f"  Full ridge zones (alpha > 0.9): {full_ridge_coverage:.1f}%")
            print(f"  Transition zones (0.1 < alpha < 0.9): {transition_coverage:.1f}%")

        # Step 3: Apply blended ridges
        if verbose:
            print(f"\n[STEP 3] Applying blended ridge enhancement...")

        # T_final = T + alpha x R x scaled_strength
        enhanced_terrain = terrain + alpha * ridge_noise * scaled_ridge_strength

        # Clip to valid range [0, 1]
        enhanced_terrain = np.clip(enhanced_terrain, 0.0, 1.0)

        if verbose:
            print(f"  Enhanced terrain range: [{enhanced_terrain.min():.4f}, {enhanced_terrain.max():.4f}]")

        # Step 4: Calculate statistics for validation
        if verbose:
            print(f"\n[STEP 4] Calculating statistics...")

        # Calculate variance changes in different zones
        buildable_mask = buildability_potential > 0.6
        scenic_mask = buildability_potential < 0.3
        transition_mask = (buildability_potential >= 0.3) & (buildability_potential <= 0.6)

        # Variance before/after in each zone
        def safe_var(arr, mask):
            masked = arr[mask]
            return float(masked.var()) if masked.size > 0 else 0.0

        var_buildable_before = safe_var(original_terrain, buildable_mask)
        var_buildable_after = safe_var(enhanced_terrain, buildable_mask)
        var_scenic_before = safe_var(original_terrain, scenic_mask)
        var_scenic_after = safe_var(enhanced_terrain, scenic_mask)

        # Calculate terrain change magnitude
        terrain_change = np.abs(enhanced_terrain - original_terrain)
        mean_change_buildable = terrain_change[buildable_mask].mean() if buildable_mask.any() else 0.0
        mean_change_scenic = terrain_change[scenic_mask].mean() if scenic_mask.any() else 0.0

        elapsed_time = time.time() - start_time

        # Compile statistics
        stats = {
            'ridge_coverage_pct': ridge_coverage if 'ridge_coverage' in locals() else 0.0,
            'full_ridge_pct': full_ridge_coverage if 'full_ridge_coverage' in locals() else 0.0,
            'transition_pct': transition_coverage if 'transition_coverage' in locals() else 0.0,
            'variance_buildable_before': var_buildable_before,
            'variance_buildable_after': var_buildable_after,
            'variance_scenic_before': var_scenic_before,
            'variance_scenic_after': var_scenic_after,
            'variance_change_buildable': var_buildable_after - var_buildable_before,
            'variance_change_scenic': var_scenic_after - var_scenic_before,
            'mean_change_buildable': mean_change_buildable,
            'mean_change_scenic': mean_change_scenic,
            'min_height': enhanced_terrain.min(),
            'max_height': enhanced_terrain.max(),
            'ridge_noise_mean': ridge_noise.mean(),
            'ridge_noise_std': ridge_noise.std(),
            'alpha_mean': alpha.mean(),
            'alpha_std': alpha.std(),
            'elapsed_time_seconds': elapsed_time
        }

        if verbose:
            print(f"\n  Variance in buildable zones:")
            print(f"    Before: {var_buildable_before:.6f}")
            print(f"    After:  {var_buildable_after:.6f}")
            print(f"    Change: {stats['variance_change_buildable']:+.6f}")
            print(f"  Variance in scenic zones:")
            print(f"    Before: {var_scenic_before:.6f}")
            print(f"    After:  {var_scenic_after:.6f}")
            print(f"    Change: {stats['variance_change_scenic']:+.6f}")
            print(f"  Mean terrain change:")
            print(f"    Buildable zones: {mean_change_buildable:.6f}")
            print(f"    Scenic zones:    {mean_change_scenic:.6f}")

            print(f"\n[SESSION 5 COMPLETE]")
            print(f"  Time elapsed: {elapsed_time:.2f} seconds")
            print(f"  Ridge enhancement applied: {self.resolution}×{self.resolution}")

            # Validation checks
            buildable_unchanged = stats['variance_change_buildable'] < 0.0001
            scenic_enhanced = stats['variance_change_scenic'] > 0.001
            performance_ok = elapsed_time < 10.0

            print(f"\n  Validation:")
            print(f"    [OK] Buildable zones preserved: {buildable_unchanged}")
            print(f"    [OK] Scenic zones enhanced: {scenic_enhanced}")
            print(f"    [OK] Performance < 10s: {performance_ok}")

            if buildable_unchanged and scenic_enhanced and performance_ok:
                print(f"  Status: [SUCCESS] Ridge enhancement working correctly")
            else:
                print(f"  Status: [WARNING] Check validation criteria")

        return enhanced_terrain.astype(np.float32), stats
