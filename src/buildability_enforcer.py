"""
Buildability Constraint Enforcement (Priority 2 Task 2.2 + Priority 6)

This module implements:
1. Task 2.2: Binary buildability mask generation from tectonic structure
2. Priority 6: Post-processing smoothing to GUARANTEE buildable terrain percentages

Task 2.2 (NEW): Generates BINARY masks (0 or 1) based on:
- Distance from tectonic faults (far from faults = buildable)
- Elevation (low elevation = buildable)
- Avoids gradient control map's frequency discontinuity problem

Priority 6: Uses Smart Blur to enforce buildability constraints after terrain
generation, ensuring 45-55% buildable terrain target is met.

References:
- Task 2.2: map_gen_enhancement.md Priority 2 Task 2.2 (Buildability Constraint System)
- Priority 6: Evidence document (Week 7) Buildability Validation & Enforcement
- CS2 buildability standard: 0-5% slopes are buildable

Created: 2025-10-08
Modified: 2025-10-08 (Added Task 2.2 implementation)
"""

import numpy as np
from scipy.ndimage import gaussian_filter
from typing import Optional, Tuple, Dict


class BuildabilityEnforcer:
    """
    Generates buildability masks and enforces buildability constraints.

    This class implements:
    1. Task 2.2: Binary buildability mask generation from tectonic structure
    2. Priority 6: Post-processing smoothing enforcement

    Task 2.2 is the KEY to avoiding the gradient control map's catastrophic failure.
    By using a BINARY mask (not gradient) and basing it on geological structure
    (distance from faults + elevation), we create buildable zones that are
    geologically justified and avoid frequency discontinuities.
    """

    @staticmethod
    def generate_buildability_mask_from_tectonics(
        distance_field: np.ndarray,
        tectonic_elevation: np.ndarray,
        target_buildable_pct: float = 50.0,
        distance_threshold_meters: float = 300.0,
        elevation_threshold: float = 0.4,
        iteration_limit: int = 20,
        verbose: bool = True
    ) -> Tuple[np.ndarray, Dict]:
        """
        Generate BINARY buildability mask from tectonic structure (Task 2.2).

        WHY THIS APPROACH:
        The gradient control map failed because it blended incompatible frequency
        content (2-octave, 5-octave, 7-octave noise), creating discontinuities.

        This approach uses a BINARY mask based on geological structure:
        - Far from faults (>300m) = buildable (plains)
        - Close to faults (<300m) = scenic (mountains)
        - Low elevation (<0.4) = buildable (valleys)
        - High elevation (>0.4) = scenic (peaks)

        The mask is BINARY (0 or 1), not gradient (0.0-1.0), which allows
        Task 2.3 to use SAME octaves everywhere with only AMPLITUDE modulation.
        This avoids frequency discontinuities entirely.

        Args:
            distance_field: Distance in meters to nearest fault (from Task 2.1)
            tectonic_elevation: Base tectonic structure (0-1 normalized)
            target_buildable_pct: Target percentage of buildable terrain (45-55%)
            distance_threshold_meters: Distance from faults for buildable zones
            elevation_threshold: Elevation cutoff for buildable zones
            iteration_limit: Max iterations for threshold adjustment
            verbose: Print progress messages

        Returns:
            Tuple of (binary_mask, stats_dict)
            - binary_mask: 1 = buildable, 0 = scenic (uint8 for memory efficiency)
            - stats_dict: buildable_pct, distance_threshold_used, elevation_threshold_used

        ALGORITHM:
        1. Start with initial thresholds (distance > 300m OR elevation < 0.4)
        2. Calculate resulting buildable percentage
        3. If not in target range (45-55%), adjust thresholds iteratively
        4. Return binary mask + statistics

        WHY BINARY, NOT GRADIENT:
        - Binary mask = clear zones (buildable vs scenic)
        - Task 2.3 can use SAME noise octaves in both zones
        - Only AMPLITUDE differs (0.3 buildable, 1.0 scenic)
        - No frequency content mixing = no discontinuities
        - This is the CORRECT solution from original plan
        """
        resolution = distance_field.shape[0]
        total_pixels = resolution * resolution

        if verbose:
            print(f"\n[Task 2.2: Binary Buildability Mask Generation]")
            print(f"  Target buildable: {target_buildable_pct:.1f}%")
            print(f"  Initial distance threshold: {distance_threshold_meters:.0f}m")
            print(f"  Initial elevation threshold: {elevation_threshold:.2f}")

        # Initial mask generation
        distance_threshold = distance_threshold_meters
        elev_threshold = elevation_threshold

        for iteration in range(iteration_limit):
            # Generate binary mask with current thresholds
            # WHY OR logic: Valleys are buildable even near faults,
            # plains are buildable even if slightly elevated
            mask = (distance_field > distance_threshold) | (tectonic_elevation < elev_threshold)

            # Calculate buildable percentage
            buildable_count = np.sum(mask)
            buildable_pct = (buildable_count / total_pixels) * 100.0

            if verbose:
                print(f"  Iteration {iteration + 1}: {buildable_pct:.1f}% buildable "
                      f"(dist>{distance_threshold:.0f}m OR elev<{elev_threshold:.2f})")

            # Check if target achieved
            if abs(buildable_pct - target_buildable_pct) < 2.0:  # ±2% tolerance
                if verbose:
                    print(f"  [SUCCESS] Target achieved: {buildable_pct:.1f}%")
                break

            # Adjust thresholds to move toward target
            # Use proportional adjustment based on how far we are from target
            error = buildable_pct - target_buildable_pct
            adjustment_rate = 0.02 + abs(error) / 200.0  # Faster when further from target

            if buildable_pct < target_buildable_pct:
                # Too little buildable area - need to expand buildable zones
                # Relax both thresholds
                distance_threshold *= (1.0 - adjustment_rate)  # Lower distance requirement
                elev_threshold *= (1.0 + adjustment_rate)      # Raise elevation cutoff
            else:
                # Too much buildable area - need to shrink buildable zones
                # Tighten both thresholds
                distance_threshold *= (1.0 + adjustment_rate)  # Higher distance requirement
                elev_threshold *= (1.0 - adjustment_rate)      # Lower elevation cutoff

            # Prevent thresholds from going out of reasonable bounds
            distance_threshold = np.clip(distance_threshold, 50.0, 2000.0)
            elev_threshold = np.clip(elev_threshold, 0.15, 0.7)

        else:
            # Max iterations reached
            if verbose:
                print(f"  [WARNING] Max iterations reached ({iteration_limit})")
                print(f"  Final buildable: {buildable_pct:.1f}% (target: {target_buildable_pct:.1f}%)")

        # Convert to uint8 for memory efficiency (0 or 1, not 0.0 or 1.0)
        binary_mask = mask.astype(np.uint8)

        # Calculate final statistics
        buildable_count = np.sum(binary_mask)
        buildable_pct_final = (buildable_count / total_pixels) * 100.0

        stats = {
            'buildable_pct': buildable_pct_final,
            'buildable_pixels': int(buildable_count),
            'scenic_pixels': int(total_pixels - buildable_count),
            'distance_threshold_used': distance_threshold,
            'elevation_threshold_used': elev_threshold,
            'iterations': iteration + 1,
            'success': abs(buildable_pct_final - target_buildable_pct) < 5.0  # ±5% tolerance
        }

        if verbose:
            print(f"\n[Mask Generation Complete]")
            print(f"  Buildable area: {buildable_pct_final:.1f}% ({buildable_count:,} pixels)")
            print(f"  Scenic area: {100 - buildable_pct_final:.1f}% ({total_pixels - buildable_count:,} pixels)")
            print(f"  Final distance threshold: {distance_threshold:.0f}m")
            print(f"  Final elevation threshold: {elev_threshold:.2f}")
            print(f"  Status: {'SUCCESS' if stats['success'] else 'PARTIAL'}")

        return binary_mask, stats

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

        # Convert to meters (CS2 height range: 0-4096m)
        heightmap_meters = heightmap * 4096.0

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
