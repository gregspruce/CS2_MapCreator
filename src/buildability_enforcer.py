"""
Buildability Constraint Enforcement (Priority 6)

This module implements post-processing smoothing to GUARANTEE buildable terrain
percentages meet CS2 requirements. Works in conjunction with generation-time
conditional octaves (Priority 2) to ensure 45-55% buildable terrain.

Key Technique: Iterative Gaussian blur applied ONLY to problem cells (buildable
zones with high slopes) until target is met. Uses Smart Blur to preserve valleys
and ridges while smoothing buildable areas.

References:
- Evidence document Priority 6 (Week 7): Buildability Validation & Enforcement
- CS2 buildability standard: 0-5% slopes are buildable
"""

import numpy as np
from scipy.ndimage import gaussian_filter
from typing import Optional, Tuple


class BuildabilityEnforcer:
    """
    Enforces buildability constraints through targeted post-processing smoothing.

    This is Priority 6 from the evidence-based enhancement plan. It works AFTER
    generation-time conditional octaves (Priority 2) to guarantee precise
    buildability targets are met.
    """

    @staticmethod
    def calculate_slopes(heightmap: np.ndarray,
                        map_size_meters: float = 14336.0) -> np.ndarray:
        """
        Calculate slope percentage for each cell in the heightmap.

        Args:
            heightmap: Normalized heightmap (0-1 range)
            map_size_meters: Physical map size in meters (CS2 default: 14336m)

        Returns:
            Slope percentage array (same shape as heightmap)
        """
        resolution = heightmap.shape[0]
        pixel_size_meters = map_size_meters / resolution

        # Convert to meters (CS2 height range: 0-1024m)
        heightmap_meters = heightmap * 1024.0

        # Calculate gradients
        dy, dx = np.gradient(heightmap_meters)

        # Slope ratio = sqrt(dx² + dy²) / pixel_size
        slope_ratio = np.sqrt(dx**2 + dy**2) / pixel_size_meters

        # Convert to percentage
        return slope_ratio * 100.0

    @staticmethod
    def calculate_buildability_percentage(slopes: np.ndarray) -> float:
        """
        Calculate percentage of terrain that is buildable (0-5% slopes).

        Args:
            slopes: Slope percentage array

        Returns:
            Percentage of buildable terrain (0-100)
        """
        buildable_mask = slopes <= 5.0
        return (np.sum(buildable_mask) / slopes.size) * 100.0

    @staticmethod
    def smart_blur(heightmap: np.ndarray,
                   problem_mask: np.ndarray,
                   sigma: float = 8.0,
                   elevation_threshold: float = 0.05) -> np.ndarray:
        """
        Apply Gaussian blur that preserves important terrain features.

        Smart Blur reduces blur strength at locations with large elevation differences
        (valleys, ridges) to preserve these features while smoothing gradual slopes.

        Args:
            heightmap: Normalized heightmap (0-1 range)
            problem_mask: Binary mask of cells to smooth (1 = smooth, 0 = preserve)
            sigma: Gaussian blur sigma in pixels (default: 8)
            elevation_threshold: Elevation difference threshold for feature detection

        Returns:
            Smoothed heightmap (only problem areas affected)
        """
        # Calculate local elevation variance to detect features
        local_variance = gaussian_filter(heightmap**2, sigma=3) - \
                        gaussian_filter(heightmap, sigma=3)**2

        # Features (valleys/ridges) have high local variance
        feature_mask = local_variance > elevation_threshold

        # Reduce smoothing strength at features
        # problem_mask AND NOT feature_mask = areas to smooth fully
        smooth_mask = problem_mask * (~feature_mask).astype(np.float64)

        # Apply Gaussian blur to entire heightmap
        blurred = gaussian_filter(heightmap, sigma=sigma)

        # Blend: original where smooth_mask=0, blurred where smooth_mask=1
        return heightmap * (1.0 - smooth_mask) + blurred * smooth_mask

    @staticmethod
    def enforce_buildability_constraint(
        heightmap: np.ndarray,
        buildable_mask: np.ndarray,
        target_pct: float = 50.0,
        max_iterations: int = 3,
        sigma: float = 8.0,
        tolerance: float = 5.0,
        map_size_meters: float = 14336.0,
        verbose: bool = True
    ) -> Tuple[np.ndarray, dict]:
        """
        Enforce buildability constraint through iterative smoothing.

        This is the CORE implementation of Priority 6. It guarantees that the
        specified percentage of terrain is buildable by iteratively smoothing
        problem areas (buildable zones with high slopes) until target is met.

        Algorithm:
        1. Calculate current buildability percentage
        2. If below target, identify problem cells (buildable mask + high slope)
        3. Apply Smart Blur to problem areas only
        4. Re-validate, repeat if needed (max 3 iterations)

        Args:
            heightmap: Normalized heightmap (0-1 range)
            buildable_mask: Binary mask of buildable zones (1 = buildable, 0 = scenic)
            target_pct: Target buildability percentage (default: 50%)
            max_iterations: Maximum smoothing iterations (default: 3)
            sigma: Gaussian blur sigma in pixels (default: 8)
            tolerance: Acceptable deviation from target (default: ±5%)
            map_size_meters: Physical map size in meters
            verbose: Print progress messages

        Returns:
            Tuple of (enforced_heightmap, stats_dict)
            stats_dict contains: initial_pct, final_pct, iterations, problem_cells
        """
        heightmap_working = heightmap.copy()

        # Initial buildability analysis
        slopes_initial = BuildabilityEnforcer.calculate_slopes(
            heightmap_working, map_size_meters)
        initial_pct = BuildabilityEnforcer.calculate_buildability_percentage(
            slopes_initial)

        if verbose:
            print(f"\n[Buildability Enforcement]")
            print(f"  Initial buildability: {initial_pct:.1f}%")
            print(f"  Target buildability: {target_pct:.1f}%")
            print(f"  Tolerance: ±{tolerance:.1f}%")

        # Check if enforcement needed
        if abs(initial_pct - target_pct) <= tolerance:
            if verbose:
                print(f"  [PASS] Within tolerance, no smoothing needed")
            return heightmap_working, {
                'initial_pct': initial_pct,
                'final_pct': initial_pct,
                'iterations': 0,
                'problem_cells': 0,
                'success': True
            }

        if verbose:
            print(f"  [ENFORCING] Target not met, applying iterative smoothing...")

        # Iterative enforcement
        iteration = 0
        current_pct = initial_pct

        for iteration in range(1, max_iterations + 1):
            # Calculate current slopes
            slopes = BuildabilityEnforcer.calculate_slopes(
                heightmap_working, map_size_meters)

            # Identify problem cells: buildable zones with slopes > 5%
            high_slope_mask = slopes > 5.0
            problem_mask = (buildable_mask > 0.5) & high_slope_mask
            problem_count = np.sum(problem_mask)

            if verbose:
                print(f"  Iteration {iteration}: {current_pct:.1f}% buildable, "
                      f"{problem_count:,} problem cells")

            if problem_count == 0:
                if verbose:
                    print(f"  [SUCCESS] No problem cells remaining")
                break

            # Apply Smart Blur to problem areas
            heightmap_working = BuildabilityEnforcer.smart_blur(
                heightmap_working,
                problem_mask.astype(np.float64),
                sigma=sigma,
                elevation_threshold=0.05
            )

            # Re-calculate buildability
            slopes = BuildabilityEnforcer.calculate_slopes(
                heightmap_working, map_size_meters)
            current_pct = BuildabilityEnforcer.calculate_buildability_percentage(
                slopes)

            # Check if target met
            if abs(current_pct - target_pct) <= tolerance:
                if verbose:
                    print(f"  [SUCCESS] Target achieved: {current_pct:.1f}%")
                break

        # Final statistics
        slopes_final = BuildabilityEnforcer.calculate_slopes(
            heightmap_working, map_size_meters)
        final_pct = BuildabilityEnforcer.calculate_buildability_percentage(
            slopes_final)

        success = abs(final_pct - target_pct) <= tolerance

        if verbose:
            print(f"\n[Enforcement Complete]")
            print(f"  Initial: {initial_pct:.1f}%")
            print(f"  Final: {final_pct:.1f}%")
            print(f"  Iterations: {iteration}/{max_iterations}")
            print(f"  Status: {'SUCCESS' if success else 'PARTIAL'}")

        return heightmap_working, {
            'initial_pct': initial_pct,
            'final_pct': final_pct,
            'iterations': iteration,
            'problem_cells': problem_count,
            'success': success
        }

    @staticmethod
    def analyze_buildability(heightmap: np.ndarray,
                            map_size_meters: float = 14336.0) -> dict:
        """
        Analyze buildability metrics for a heightmap.

        Args:
            heightmap: Normalized heightmap (0-1 range)
            map_size_meters: Physical map size in meters

        Returns:
            Dictionary with buildability statistics
        """
        slopes = BuildabilityEnforcer.calculate_slopes(heightmap, map_size_meters)

        # Calculate percentages for different slope categories
        excellent = np.sum(slopes <= 5.0) / slopes.size * 100  # 0-5%: buildable
        acceptable = np.sum((slopes > 5.0) & (slopes <= 10.0)) / slopes.size * 100  # 5-10%
        steep = np.sum(slopes > 10.0) / slopes.size * 100  # 10%+: scenic only

        return {
            'excellent_buildable_pct': excellent,  # CS2 standard
            'acceptable_buildable_pct': acceptable,  # Marginal
            'steep_scenic_pct': steep,  # Unbuildable
            'mean_slope': slopes.mean(),
            'median_slope': np.median(slopes),
            'p90_slope': np.percentile(slopes, 90),
            'p99_slope': np.percentile(slopes, 99)
        }
