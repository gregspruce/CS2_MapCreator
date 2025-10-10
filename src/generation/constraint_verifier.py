"""
Constraint Verifier for Buildability Target Validation (Session 8)

Verifies that terrain meets the 55-65% buildability target and applies
conservative auto-adjustment if needed.

Author: Claude Code (Session 8 Implementation)
Date: 2025-10-10
"""

import numpy as np
import time
from typing import Tuple, Dict, List
from scipy.ndimage import gaussian_filter

from src.buildability_enforcer import BuildabilityEnforcer


class ConstraintVerifier:
    """
    Verifies buildability constraints and applies conservative adjustments.

    Key Features:
    - Calculates accurate buildability percentage (slope < 5% = 8.75°)
    - Classifies terrain into buildable/near-buildable/unbuildable regions
    - Auto-adjusts near-buildable regions (5-10% slope) if < 55% buildable
    - Generates comprehensive validation report with recommendations
    - Conservative smoothing preserves terrain character

    Buildability Classification:
    - Buildable: slope < 5% (< 8.75°) - Target zones for cities
    - Near-buildable: 5% ≤ slope < 10% (8.75° - 17.6°) - Adjustment candidates
    - Unbuildable: slope ≥ 10% (≥ 17.6°) - Mountains, preserve

    Usage:
        verifier = ConstraintVerifier(resolution=4096, map_size_meters=14336)
        result = verifier.verify_and_adjust(
            terrain,
            target_min=55.0,
            target_max=65.0,
            apply_adjustment=True
        )
    """

    def __init__(
        self,
        resolution: int,
        map_size_meters: float = 14336.0
    ):
        """
        Initialize constraint verifier.

        Args:
            resolution: Heightmap resolution (e.g., 4096 for 4096x4096)
            map_size_meters: Physical map size in meters (default: 14336m = 14.3km)

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
        self.pixel_size_meters = map_size_meters / resolution

        print(f"[ConstraintVerifier] Initialized (resolution={resolution})")

    def verify_and_adjust(
        self,
        terrain: np.ndarray,
        target_min: float = 55.0,
        target_max: float = 65.0,
        apply_adjustment: bool = True,
        adjustment_sigma: float = 3.0,
        max_adjustment_iterations: int = 3
    ) -> Tuple[np.ndarray, Dict]:
        """
        Verify buildability constraints and apply adjustment if needed.

        Args:
            terrain: Input terrain heightmap [0, 1], shape (N, N)
            target_min: Minimum acceptable buildability percentage (default: 55.0%)
            target_max: Maximum acceptable buildability percentage (default: 65.0%)
            apply_adjustment: Whether to auto-adjust if < target_min (default: True)
            adjustment_sigma: Gaussian smoothing strength (default: 3.0 pixels)
            max_adjustment_iterations: Maximum smoothing iterations (default: 3)

        Returns:
            Tuple of (adjusted_terrain, verification_result_dict)

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
        if target_min < 0.0 or target_min > 100.0:
            raise ValueError(f"Target min must be 0-100%, got {target_min}")
        if target_max <= target_min or target_max > 100.0:
            raise ValueError(f"Target max must be >{target_min}% and <=100%, got {target_max}")
        if adjustment_sigma < 0.5 or adjustment_sigma > 20.0:
            raise ValueError(f"Adjustment sigma must be 0.5-20, got {adjustment_sigma}")
        if max_adjustment_iterations < 0 or max_adjustment_iterations > 10:
            raise ValueError(f"Max iterations must be 0-10, got {max_adjustment_iterations}")

        print(f"\n[ConstraintVerifier] Verifying buildability constraints...")
        print(f"  Target range: {target_min:.1f}% - {target_max:.1f}%")
        print(f"  Auto-adjustment: {'ENABLED' if apply_adjustment else 'DISABLED'}")

        # Step 1: Calculate initial buildability
        print(f"  [1/3] Calculating slopes and buildability...")
        slopes = BuildabilityEnforcer.calculate_slopes(terrain, self.map_size_meters)
        initial_buildable_pct = BuildabilityEnforcer.calculate_buildability_percentage(slopes)

        # Step 2: Classify terrain regions
        print(f"  [2/3] Classifying terrain regions...")
        classification = self._classify_terrain(slopes)

        # Check if target achieved
        target_achieved = target_min <= initial_buildable_pct <= target_max

        print(f"  Initial buildability: {initial_buildable_pct:.1f}%")
        print(f"  Target achieved: {'YES' if target_achieved else 'NO'}")

        # Step 3: Apply adjustment if needed
        adjusted_terrain = terrain.copy()
        adjustments_applied = False
        adjustment_stats = {}

        if not target_achieved and initial_buildable_pct < target_min and apply_adjustment:
            print(f"  [3/3] Applying auto-adjustment (target < {target_min:.1f}%)...")
            adjusted_terrain, adjustment_stats = self._apply_adjustment(
                terrain,
                slopes,
                classification,
                target_min,
                adjustment_sigma,
                max_adjustment_iterations
            )
            adjustments_applied = True
        else:
            print(f"  [3/3] No adjustment needed")

        # Recalculate buildability after adjustment
        if adjustments_applied:
            final_slopes = BuildabilityEnforcer.calculate_slopes(adjusted_terrain, self.map_size_meters)
            final_buildable_pct = BuildabilityEnforcer.calculate_buildability_percentage(final_slopes)
            final_classification = self._classify_terrain(final_slopes)
        else:
            final_slopes = slopes
            final_buildable_pct = initial_buildable_pct
            final_classification = classification

        # Generate recommendations
        recommendations = self._generate_recommendations(
            final_buildable_pct,
            target_min,
            target_max,
            adjustments_applied
        )

        # Calculate elapsed time
        elapsed = time.time() - start_time

        # Build result dictionary
        result = {
            'initial_buildable_pct': float(initial_buildable_pct),
            'final_buildable_pct': float(final_buildable_pct),
            'target_min': float(target_min),
            'target_max': float(target_max),
            'target_achieved': final_buildable_pct >= target_min and final_buildable_pct <= target_max,
            'buildable_pct': float(final_classification['buildable_pct']),
            'near_buildable_pct': float(final_classification['near_buildable_pct']),
            'unbuildable_pct': float(final_classification['unbuildable_pct']),
            'adjustments_applied': adjustments_applied,
            'adjustment_stats': adjustment_stats,
            'recommendations': recommendations,
            'processing_time': float(elapsed)
        }

        print(f"  [SUCCESS] Verification complete")
        print(f"  Final buildability: {final_buildable_pct:.1f}%")
        print(f"  Target achieved: {'YES' if result['target_achieved'] else 'NO'}")
        print(f"  Processing time: {elapsed:.2f}s")

        return adjusted_terrain.astype(np.float32), result

    def _classify_terrain(
        self,
        slopes: np.ndarray
    ) -> Dict:
        """
        Classify terrain into buildable/near-buildable/unbuildable regions.

        Args:
            slopes: Slope array (fractional units, e.g., 0.05 = 5%)

        Returns:
            Classification dictionary with percentages and masks
        """
        # Define classification thresholds
        buildable_threshold = 0.05  # 5% slope = 8.75° (CS2 buildable limit)
        near_buildable_threshold = 0.10  # 10% slope = 17.6° (smoothing candidates)

        # Create classification masks
        buildable_mask = slopes < buildable_threshold
        near_buildable_mask = (slopes >= buildable_threshold) & (slopes < near_buildable_threshold)
        unbuildable_mask = slopes >= near_buildable_threshold

        # Calculate percentages
        total_pixels = slopes.size
        buildable_pct = 100.0 * np.sum(buildable_mask) / total_pixels
        near_buildable_pct = 100.0 * np.sum(near_buildable_mask) / total_pixels
        unbuildable_pct = 100.0 * np.sum(unbuildable_mask) / total_pixels

        return {
            'buildable_mask': buildable_mask,
            'near_buildable_mask': near_buildable_mask,
            'unbuildable_mask': unbuildable_mask,
            'buildable_pct': buildable_pct,
            'near_buildable_pct': near_buildable_pct,
            'unbuildable_pct': unbuildable_pct
        }

    def _apply_adjustment(
        self,
        terrain: np.ndarray,
        slopes: np.ndarray,
        classification: Dict,
        target_min: float,
        sigma: float,
        max_iterations: int
    ) -> Tuple[np.ndarray, Dict]:
        """
        Apply conservative smoothing to near-buildable regions.

        Strategy:
        - Only smooth near-buildable areas (5-10% slope)
        - Preserve buildable areas (already flat)
        - Preserve unbuildable areas (mountains)
        - Use minimal Gaussian smoothing (conservative)
        - Iterate until target achieved or max iterations reached

        Args:
            terrain: Original terrain heightmap
            slopes: Slope array
            classification: Terrain classification dict
            target_min: Target minimum buildability
            sigma: Gaussian smoothing strength
            max_iterations: Maximum iterations

        Returns:
            Tuple of (adjusted_terrain, adjustment_statistics)
        """
        adjusted = terrain.copy()
        near_buildable_mask = classification['near_buildable_mask']

        print(f"    Smoothing near-buildable regions ({classification['near_buildable_pct']:.1f}% of terrain)")
        print(f"    Smoothing parameters: sigma={sigma:.1f}, max_iterations={max_iterations}")

        iterations_performed = 0
        improvement_per_iteration = []

        for iteration in range(max_iterations):
            # Smooth only near-buildable regions
            smoothed = gaussian_filter(adjusted, sigma=sigma, mode='reflect')

            # Apply smoothing only to near-buildable areas
            # Preserve buildable and unbuildable areas unchanged
            adjusted_new = np.where(near_buildable_mask, smoothed, adjusted)

            # Clip to valid range [0, 1] (gaussian_filter can produce out-of-range values)
            adjusted_new = np.clip(adjusted_new, 0.0, 1.0)

            # Calculate new buildability
            new_slopes = BuildabilityEnforcer.calculate_slopes(adjusted_new, self.map_size_meters)
            new_buildable_pct = BuildabilityEnforcer.calculate_buildability_percentage(new_slopes)

            improvement = new_buildable_pct - BuildabilityEnforcer.calculate_buildability_percentage(
                BuildabilityEnforcer.calculate_slopes(adjusted, self.map_size_meters)
            )
            improvement_per_iteration.append(improvement)

            print(f"      Iteration {iteration + 1}: {new_buildable_pct:.1f}% buildable (+{improvement:.1f}%)")

            adjusted = adjusted_new
            iterations_performed += 1

            # Stop if target achieved
            if new_buildable_pct >= target_min:
                print(f"      Target achieved after {iterations_performed} iteration(s)")
                break

            # Stop if improvement is minimal (< 0.1%)
            if abs(improvement) < 0.1:
                print(f"      Minimal improvement, stopping early")
                break

        # Calculate total improvement
        final_slopes = BuildabilityEnforcer.calculate_slopes(adjusted, self.map_size_meters)
        final_buildable_pct = BuildabilityEnforcer.calculate_buildability_percentage(final_slopes)
        initial_buildable_pct = BuildabilityEnforcer.calculate_buildability_percentage(slopes)
        total_improvement = final_buildable_pct - initial_buildable_pct

        # Calculate terrain changes
        terrain_diff = np.abs(adjusted - terrain)
        mean_change = np.mean(terrain_diff)
        max_change = np.max(terrain_diff)

        # Changes in near-buildable regions only
        near_buildable_change = np.mean(terrain_diff[near_buildable_mask]) if np.any(near_buildable_mask) else 0.0

        adjustment_stats = {
            'iterations_performed': iterations_performed,
            'sigma_used': float(sigma),
            'initial_buildable_pct': float(initial_buildable_pct),
            'final_buildable_pct': float(final_buildable_pct),
            'total_improvement': float(total_improvement),
            'improvement_per_iteration': [float(x) for x in improvement_per_iteration],
            'mean_terrain_change': float(mean_change),
            'max_terrain_change': float(max_change),
            'near_buildable_mean_change': float(near_buildable_change),
            'regions_smoothed_pct': float(classification['near_buildable_pct'])
        }

        return adjusted, adjustment_stats

    def _generate_recommendations(
        self,
        buildable_pct: float,
        target_min: float,
        target_max: float,
        adjustments_applied: bool
    ) -> List[str]:
        """
        Generate user-facing recommendations based on results.

        Args:
            buildable_pct: Final buildability percentage
            target_min: Target minimum
            target_max: Target maximum
            adjustments_applied: Whether auto-adjustment was applied

        Returns:
            List of recommendation strings
        """
        recommendations = []

        if buildable_pct >= target_min and buildable_pct <= target_max:
            # Target achieved
            recommendations.append(f"[SUCCESS] Target buildability achieved: {buildable_pct:.1f}%")
            recommendations.append("No further action needed - terrain meets requirements")

        elif buildable_pct < target_min:
            # Below target
            shortage = target_min - buildable_pct
            recommendations.append(f"[WARNING] Buildability below target: {buildable_pct:.1f}% (target: {target_min:.1f}%)")
            recommendations.append(f"Shortage: {shortage:.1f}% ({shortage * self.resolution * self.resolution / 100:.0f} pixels)")

            if adjustments_applied:
                recommendations.append("Auto-adjustment was applied but target not fully achieved")
                recommendations.append("To increase buildability further:")
            else:
                recommendations.append("To increase buildability:")

            recommendations.append("  - Increase erosion particles (more deposition -> flatter valleys)")
            recommendations.append("  - Increase erosion deposition rate (Kd parameter)")
            recommendations.append("  - Increase buildability zone coverage (target_coverage parameter)")
            recommendations.append("  - Reduce base terrain amplitude (gentler initial terrain)")
            recommendations.append("  - Enable auto-adjustment if disabled (apply_constraint_adjustment=True)")

        elif buildable_pct > target_max:
            # Above target
            excess = buildable_pct - target_max
            recommendations.append(f"[INFO] Buildability exceeds target: {buildable_pct:.1f}% (target: {target_max:.1f}%)")
            recommendations.append(f"Excess: {excess:.1f}% ({excess * self.resolution * self.resolution / 100:.0f} pixels)")
            recommendations.append("This is acceptable - more buildable terrain is generally better")
            recommendations.append("To reduce buildability (if desired):")
            recommendations.append("  - Reduce erosion particles (less deposition)")
            recommendations.append("  - Reduce buildability zone coverage")
            recommendations.append("  - Increase base terrain amplitude")
            recommendations.append("  - Increase ridge strength in scenic zones")

        return recommendations


def verify_terrain_buildability(
    terrain: np.ndarray,
    resolution: int,
    map_size_meters: float = 14336.0,
    target_min: float = 55.0,
    target_max: float = 65.0,
    apply_adjustment: bool = True
) -> Tuple[np.ndarray, Dict]:
    """
    Convenience function to verify and adjust terrain buildability.

    Args:
        terrain: Input terrain heightmap [0, 1]
        resolution: Heightmap resolution
        map_size_meters: Physical map size in meters
        target_min: Minimum acceptable buildability (default: 55%)
        target_max: Maximum acceptable buildability (default: 65%)
        apply_adjustment: Whether to auto-adjust if below target

    Returns:
        Tuple of (adjusted_terrain, verification_result)
    """
    verifier = ConstraintVerifier(
        resolution=resolution,
        map_size_meters=map_size_meters
    )

    return verifier.verify_and_adjust(
        terrain,
        target_min=target_min,
        target_max=target_max,
        apply_adjustment=apply_adjustment
    )


if __name__ == "__main__":
    # Example usage and testing
    print("Constraint Verifier - Example Usage")
    print("=" * 60)

    # Create synthetic test terrain with known buildability
    resolution = 1024
    x = np.linspace(0, 1, resolution)
    y = np.linspace(0, 1, resolution)
    X, Y = np.meshgrid(x, y)

    # Create terrain with ~40% buildable (below target)
    # Flat regions (buildable) and mountains (unbuildable)
    terrain = np.where(
        (X > 0.3) & (X < 0.7) & (Y > 0.3) & (Y < 0.7),
        0.5 + 0.02 * np.sin(20 * np.pi * X),  # Flat center (buildable)
        0.3 + 0.3 * np.sin(5 * np.pi * X) * np.cos(5 * np.pi * Y)  # Mountains around
    ).astype(np.float32)

    # Verify and adjust
    verifier = ConstraintVerifier(resolution=resolution)
    adjusted, result = verifier.verify_and_adjust(
        terrain,
        target_min=55.0,
        target_max=65.0,
        apply_adjustment=True
    )

    print("\n" + "=" * 60)
    print("Verification Results:")
    print(f"  Initial buildability: {result['initial_buildable_pct']:.1f}%")
    print(f"  Final buildability: {result['final_buildable_pct']:.1f}%")
    print(f"  Target achieved: {result['target_achieved']}")
    print(f"  Adjustments applied: {result['adjustments_applied']}")

    if result['adjustments_applied']:
        print(f"\n  Adjustment details:")
        print(f"    Iterations: {result['adjustment_stats']['iterations_performed']}")
        print(f"    Improvement: +{result['adjustment_stats']['total_improvement']:.1f}%")
        print(f"    Mean terrain change: {result['adjustment_stats']['mean_terrain_change']:.4f}")

    print(f"\n  Recommendations:")
    for rec in result['recommendations']:
        print(f"    {rec}")

    print(f"\n  Processing time: {result['processing_time']:.2f}s")
    print("=" * 60)
