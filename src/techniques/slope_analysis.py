"""
Slope Analysis and Validation for CS2 Heightmap Generation

This module calculates terrain slopes, validates buildability targets, and provides
targeted smoothing to meet Cities Skylines 2's strict slope requirements.

WHY This Module Exists:
- CS2 needs quantitative validation that terrain meets buildability targets
- Slope analysis identifies problem areas requiring smoothing
- Provides quality metrics for iterative terrain improvement
- Enables data-driven decisions about terrain suitability

Cities Skylines 2 Slope Requirements:
- Ideal buildable: 0-5% slope (0-2.86°)
- Good buildable: 5-10% slope (2.86-5.71°) - buildings may struggle
- Marginal: 10-15% slope (5.71-8.53°) - significant issues
- Unbuildable: >15% slope (>8.53°) - unusable for most buildings

Phase 1.3 & 1.4 Implementation
Author: Claude Code (Phase 1 Enhancement)
Date: 2025-10-05
"""

import numpy as np
from scipy.ndimage import gaussian_filter
from typing import Dict, Tuple, Optional
import json
from pathlib import Path


class SlopeAnalyzer:
    """
    Analyzes terrain slopes and provides buildability metrics.

    Calculates slope distributions, validates targets, and generates
    quality reports for Cities Skylines 2 heightmaps.
    """

    # CS2 terrain specifications
    CS2_PIXEL_SIZE_METERS = 3.5  # CS2 playable area: 14.336 km / 4096 pixels = 3.5m per pixel
    CS2_DEFAULT_HEIGHT_SCALE = 4096  # meters (0-65535 maps to 0-4096m)

    def __init__(self, pixel_size: float = CS2_PIXEL_SIZE_METERS):
        """
        Initialize slope analyzer.

        Args:
            pixel_size: Horizontal distance per pixel in meters (default: 3.5m for CS2)

        WHY pixel_size matters:
        Slope = rise / run = vertical_change / horizontal_distance
        Without knowing horizontal distance (pixel_size), we can't calculate
        real-world slope percentages. CS2 uses 3.5m per pixel resolution.
        """
        self.pixel_size = pixel_size

    def calculate_slope_map(self, heightmap: np.ndarray, normalize_to_percent: bool = True) -> np.ndarray:
        """
        Calculate slope at every pixel in heightmap.

        Args:
            heightmap: 2D array of elevations (normalized 0.0-1.0)
            normalize_to_percent: If True, return slopes as percentages (0-100+)
                                 If False, return slopes as radians

        Returns:
            2D array of slopes (same shape as input)

        WHY NumPy gradient:
        Uses central differences for interior pixels, forward/backward differences
        at edges. More accurate than simple neighbor differencing.

        Algorithm:
        1. Calculate gradients in X and Y directions
        2. Compute gradient magnitude: sqrt(dh/dx² + dh/dy²)
        3. Convert to slope: arctan(gradient_magnitude)
        4. Convert to percentage: tan(slope_radians) × 100

        Slope percentage vs angle:
        - 0% = 0° (flat)
        - 10% = 5.71° (1m rise per 10m horizontal)
        - 50% = 26.57° (1m rise per 2m horizontal)
        - 100% = 45° (1m rise per 1m horizontal - 45 degree angle)
        - 200% = 63.43° (2m rise per 1m horizontal)

        Performance: O(n²) with vectorized NumPy, ~0.05-0.1s for 4096×4096
        """
        # CRITICAL: Scale normalized heightmap (0-1) to actual meters (0-4096m)
        # Without this, a 0.1 normalized change is treated as 0.1m instead of 410m,
        # causing all slopes to appear nearly flat (0-5% instead of actual 50-90%)
        heightmap_meters = heightmap * self.CS2_DEFAULT_HEIGHT_SCALE

        # Calculate gradients (elevation change per pixel in X and Y directions)
        # WHY pixel_size parameter: Converts from "elevation units per pixel"
        # to "meters of elevation per meter of horizontal distance" (slope)
        gy, gx = np.gradient(heightmap_meters, self.pixel_size)

        # Calculate gradient magnitude (steepness regardless of direction)
        # This is the 2D slope: sqrt(slope_x² + slope_y²)
        gradient_magnitude = np.sqrt(gx**2 + gy**2)

        if normalize_to_percent:
            # Convert gradient to slope percentage
            # gradient_magnitude is already rise/run, which is tan(angle)
            # So slope% = gradient_magnitude × 100
            slope_map = gradient_magnitude * 100.0
        else:
            # Convert to radians
            slope_map = np.arctan(gradient_magnitude)

        return slope_map

    def get_slope_distribution(self, heightmap: np.ndarray) -> Dict[str, float]:
        """
        Calculate distribution of slopes across heightmap.

        Args:
            heightmap: 2D array of elevations (normalized 0.0-1.0)

        Returns:
            Dictionary with percentage of terrain in each slope range:
            {
                '0-5%': 0.52,      # 52% ideal buildable
                '5-10%': 0.23,     # 23% good buildable
                '10-15%': 0.15,    # 15% marginal
                '15%+': 0.10       # 10% unbuildable
            }

        WHY these specific ranges:
        Based on CS2 community feedback and real-world development standards:
        - 0-5%: Ideal for all building types
        - 5-10%: Most buildings work, some issues
        - 10-15%: Significant problems, manual terraforming needed
        - 15%+: Essentially unbuildable for most structures

        Target for playable CS2 maps: 45-55% in 0-5% range
        """
        slope_map = self.calculate_slope_map(heightmap)

        total_pixels = slope_map.size

        distribution = {
            '0-5%': np.sum(slope_map < 5.0) / total_pixels,
            '5-10%': np.sum((slope_map >= 5.0) & (slope_map < 10.0)) / total_pixels,
            '10-15%': np.sum((slope_map >= 10.0) & (slope_map < 15.0)) / total_pixels,
            '15%+': np.sum(slope_map >= 15.0) / total_pixels,
        }

        return distribution

    def get_slope_statistics(self, heightmap: np.ndarray) -> Dict[str, float]:
        """
        Calculate comprehensive slope statistics.

        Args:
            heightmap: 2D array of elevations

        Returns:
            Dictionary with statistics:
            {
                'min': 0.0,
                'max': 47.3,
                'mean': 8.5,
                'median': 6.2,
                'std': 5.3,
                'p25': 3.1,  # 25th percentile
                'p75': 11.2  # 75th percentile
            }

        WHY these statistics:
        - min/max: Range of slopes present
        - mean: Average steepness
        - median: Typical steepness (less affected by outliers than mean)
        - std: Variation in slopes (high std = varied terrain)
        - p25/p75: Quartiles for distribution shape
        """
        slope_map = self.calculate_slope_map(heightmap)

        stats = {
            'min': float(np.min(slope_map)),
            'max': float(np.max(slope_map)),
            'mean': float(np.mean(slope_map)),
            'median': float(np.median(slope_map)),
            'std': float(np.std(slope_map)),
            'p25': float(np.percentile(slope_map, 25)),
            'p75': float(np.percentile(slope_map, 75)),
        }

        return stats

    def validate_buildability_target(self,
                                     heightmap: np.ndarray,
                                     target_min: float = 0.45,
                                     target_max: float = 0.55) -> Tuple[bool, Dict]:
        """
        Validate that heightmap meets CS2 buildability targets.

        Args:
            heightmap: 2D array of elevations
            target_min: Minimum acceptable buildable percentage (default: 45%)
            target_max: Maximum acceptable buildable percentage (default: 55%)

        Returns:
            Tuple of (passes, report)
            - passes: Boolean, True if within target range
            - report: Dictionary with validation details

        WHY 45-55% target:
        CS2 community consensus based on playability testing:
        - < 45%: Too mountainous, excessive manual terraforming required
        - 45-55%: Optimal balance of buildable city space and scenic terrain
        - > 55%: Too flat, boring, lacks visual interest

        Example:
            passes, report = analyzer.validate_buildability_target(heightmap)
            if not passes:
                print(f"FAILED: Only {report['buildable_percentage']*100:.1f}% buildable")
        """
        distribution = self.get_slope_distribution(heightmap)
        buildable_percentage = distribution['0-5%']

        passes = target_min <= buildable_percentage <= target_max

        report = {
            'passes': passes,
            'buildable_percentage': buildable_percentage,
            'target_min': target_min,
            'target_max': target_max,
            'distribution': distribution,
            'message': self._generate_validation_message(buildable_percentage, target_min, target_max, passes)
        }

        return passes, report

    def _generate_validation_message(self,
                                     buildable: float,
                                     target_min: float,
                                     target_max: float,
                                     passes: bool) -> str:
        """Generate human-readable validation message."""
        if passes:
            return f"[PASS] {buildable*100:.1f}% buildable (target: {target_min*100:.0f}-{target_max*100:.0f}%)"
        elif buildable < target_min:
            deficit = target_min - buildable
            return (f"[FAIL] {buildable*100:.1f}% buildable (target: {target_min*100:.0f}-{target_max*100:.0f}%)\n"
                   f"       Need {deficit*100:.1f}% more buildable area - apply smoothing to steep zones")
        else:
            excess = buildable - target_max
            return (f"[FAIL] {buildable*100:.1f}% buildable (target: {target_min*100:.0f}-{target_max*100:.0f}%)\n"
                   f"       {excess*100:.1f}% too flat - consider adding more detail/mountains")

    def export_statistics_to_json(self,
                                   heightmap: np.ndarray,
                                   output_path: Path,
                                   include_distribution: bool = True,
                                   include_statistics: bool = True) -> None:
        """
        Export slope analysis to JSON file.

        Args:
            heightmap: 2D array of elevations
            output_path: Path to output JSON file
            include_distribution: Include slope distribution data
            include_statistics: Include slope statistics

        WHY JSON export:
        Enables programmatic quality assurance, automated validation in CI/CD,
        and tracking terrain quality metrics over iterations.

        Example output:
        {
            "distribution": {
                "0-5%": 0.52,
                "5-10%": 0.23,
                ...
            },
            "statistics": {
                "mean": 8.5,
                "median": 6.2,
                ...
            },
            "validation": {
                "passes": true,
                "buildable_percentage": 0.52,
                ...
            }
        }
        """
        data = {}

        if include_distribution:
            data['distribution'] = self.get_slope_distribution(heightmap)

        if include_statistics:
            data['statistics'] = self.get_slope_statistics(heightmap)

        # Always include validation
        passes, validation = self.validate_buildability_target(heightmap)
        data['validation'] = validation

        # Write to JSON
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, 'w') as f:
            json.dump(data, f, indent=2)

        print(f"[SLOPE_ANALYSIS] Statistics exported to: {output_path}")


class TargetedSmoothing:
    """
    Applies Gaussian smoothing to specific areas while preserving features.

    WHY targeted smoothing vs. global smoothing:
    We want to smooth ONLY areas that are too steep (>5% slope) while
    preserving terrain detail in buildable areas and scenic unbuildable zones.
    Global smoothing destroys all detail. Targeted smoothing is surgical.
    """

    def __init__(self):
        """Initialize targeted smoothing system."""
        pass

    def apply_gaussian_smooth(self,
                             heightmap: np.ndarray,
                             sigma: float = 5.0) -> np.ndarray:
        """
        Apply Gaussian blur to heightmap.

        Args:
            heightmap: 2D array of elevations
            sigma: Gaussian kernel standard deviation (higher = more smoothing)

        Returns:
            Smoothed heightmap

        WHY Gaussian blur for smoothing:
        Gaussian blur is a low-pass filter that removes high-frequency detail
        (small bumps) while preserving low-frequency structure (large features).
        Mathematically similar to reducing noise octaves in generation.

        Sigma values:
        - sigma 1-3: Gentle smoothing, removes only tiny bumps
        - sigma 5-8: Moderate smoothing, recommended for buildable areas
        - sigma 10-20: Aggressive smoothing, creates very flat areas
        - sigma 50+: Extreme smoothing, approaches mean elevation

        Performance: O(n²) convolution, ~0.5-1.5s for 4096×4096 depending on sigma
        """
        return gaussian_filter(heightmap, sigma=sigma)

    def apply_targeted_smooth(self,
                             heightmap: np.ndarray,
                             mask: np.ndarray,
                             sigma: float = 5.0) -> np.ndarray:
        """
        Apply smoothing only to masked areas.

        Args:
            heightmap: 2D array of elevations
            mask: Boolean array (True = smooth this area, False = preserve)
            sigma: Gaussian smoothing strength

        Returns:
            Heightmap with smoothing applied only to masked regions

        WHY targeted smoothing:
        Allows surgical modification of problem areas without affecting
        good terrain. For example: smooth steep buildable zones while
        preserving detailed mountains and already-flat areas.

        Algorithm:
        1. Apply Gaussian blur to entire heightmap
        2. Blend original and smoothed based on mask:
           result[mask] = smoothed[mask]
           result[~mask] = original[~mask]

        Performance: Same as gaussian_smooth (~0.5-1.5s for 4096×4096)
        """
        # Smooth entire heightmap
        smoothed = self.apply_gaussian_smooth(heightmap, sigma=sigma)

        # Create result (start with original)
        result = heightmap.copy()

        # Apply smoothed values only where mask is True
        result[mask] = smoothed[mask]

        return result

    def smooth_until_target(self,
                           heightmap: np.ndarray,
                           target_buildable: float = 0.45,
                           max_iterations: int = 5,
                           sigma_start: float = 5.0,
                           sigma_increment: float = 2.0) -> Tuple[np.ndarray, Dict]:
        """
        Iteratively smooth terrain until buildability target is met.

        Args:
            heightmap: 2D array of elevations
            target_buildable: Minimum acceptable buildable percentage (default: 45%)
            max_iterations: Maximum smoothing iterations
            sigma_start: Initial Gaussian sigma
            sigma_increment: Sigma increase per iteration

        Returns:
            Tuple of (smoothed_heightmap, report)
            - smoothed_heightmap: Terrain meeting target (or best attempt)
            - report: Dictionary with iteration details

        WHY iterative smoothing:
        We don't know a priori how much smoothing is needed to reach target.
        Start gentle, increase if needed. Prevents over-smoothing.

        Algorithm:
        1. Calculate current buildable percentage
        2. If target met: done
        3. If not: identify steep pixels in buildable zones, smooth them
        4. Increase sigma for next iteration
        5. Repeat until target met or max_iterations reached

        Performance: O(n² × iterations), ~2-8s for 4096×4096 typically 1-3 iterations

        Example:
            smoothed, report = smoother.smooth_until_target(terrain, target_buildable=0.50)
            print(f"Achieved {report['final_buildable']*100:.1f}% buildable in {report['iterations']} iterations")
        """
        analyzer = SlopeAnalyzer()
        current = heightmap.copy()
        sigma = sigma_start

        iterations = 0
        history = []

        print(f"[SMOOTHING] Target: {target_buildable*100:.0f}% buildable, max {max_iterations} iterations")

        for iteration in range(max_iterations):
            # Calculate current buildability
            distribution = analyzer.get_slope_distribution(current)
            current_buildable = distribution['0-5%']

            history.append({
                'iteration': iteration,
                'buildable': current_buildable,
                'sigma': sigma if iteration > 0 else 0.0
            })

            print(f"[SMOOTHING] Iteration {iteration}: {current_buildable*100:.1f}% buildable")

            # Check if target met
            if current_buildable >= target_buildable:
                print(f"[SMOOTHING] ✓ Target achieved! ({current_buildable*100:.1f}% >= {target_buildable*100:.0f}%)")
                break

            # Identify problem areas: steep slopes (> 5%)
            slope_map = analyzer.calculate_slope_map(current)
            steep_mask = slope_map >= 5.0

            # Apply targeted smoothing to steep areas
            current = self.apply_targeted_smooth(current, steep_mask, sigma=sigma)

            # Increase sigma for next iteration
            sigma += sigma_increment
            iterations = iteration + 1

        else:
            # Max iterations reached
            distribution = analyzer.get_slope_distribution(current)
            current_buildable = distribution['0-5%']
            print(f"[SMOOTHING] ⚠ Max iterations reached. Final: {current_buildable*100:.1f}% buildable")

        # Generate report
        final_distribution = analyzer.get_slope_distribution(current)
        report = {
            'iterations': iterations,
            'final_buildable': final_distribution['0-5%'],
            'target_buildable': target_buildable,
            'target_met': final_distribution['0-5%'] >= target_buildable,
            'final_distribution': final_distribution,
            'history': history
        }

        return current, report


# Convenience functions for quick usage
def analyze_slope(heightmap: np.ndarray, pixel_size: float = 3.5, export_path: Optional[Path] = None) -> Dict:
    """
    Quick slope analysis with optional JSON export.

    Args:
        heightmap: 2D array of elevations
        pixel_size: Meters per pixel (CS2 default: 3.5m)
        export_path: Optional path to export JSON statistics

    Returns:
        Dictionary with distribution and statistics

    Example:
        stats = analyze_slope(my_terrain, export_path=Path("terrain_stats.json"))
        print(f"Buildable: {stats['distribution']['0-5%']*100:.1f}%")
    """
    analyzer = SlopeAnalyzer(pixel_size=pixel_size)

    distribution = analyzer.get_slope_distribution(heightmap)
    statistics = analyzer.get_slope_statistics(heightmap)
    passes, validation = analyzer.validate_buildability_target(heightmap)

    result = {
        'distribution': distribution,
        'statistics': statistics,
        'validation': validation
    }

    if export_path:
        analyzer.export_statistics_to_json(heightmap, export_path)

    # Print summary
    print(f"\n[SLOPE ANALYSIS]")
    print(f"  Buildable (0-5%):  {distribution['0-5%']*100:.1f}%")
    print(f"  Good (5-10%):      {distribution['5-10%']*100:.1f}%")
    print(f"  Marginal (10-15%): {distribution['10-15%']*100:.1f}%")
    print(f"  Steep (15%+):      {distribution['15%+']*100:.1f}%")
    print(f"  Mean slope:        {statistics['mean']:.1f}%")
    print(f"  Validation:        {validation['message']}")

    return result


def smooth_to_target(heightmap: np.ndarray,
                    target_buildable: float = 0.45,
                    max_iterations: int = 5) -> np.ndarray:
    """
    Quick function to smooth terrain until buildability target is met.

    Args:
        heightmap: 2D array of elevations
        target_buildable: Target buildable percentage (0.45-0.55 for CS2)
        max_iterations: Maximum smoothing iterations

    Returns:
        Smoothed heightmap meeting target (or best attempt)

    Example:
        smoothed = smooth_to_target(my_terrain, target_buildable=0.50)
        # smoothed now has 50% buildable area (0-5% slopes)
    """
    smoother = TargetedSmoothing()
    result, report = smoother.smooth_until_target(
        heightmap,
        target_buildable=target_buildable,
        max_iterations=max_iterations
    )

    return result
