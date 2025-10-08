"""
Tectonic Structure Generator for Realistic Mountain Terrain

WHY THIS MODULE EXISTS:
Real-world mountains form along tectonic fault lines, creating linear mountain ranges
rather than random scattered peaks. This module generates geologically-justified terrain
by simulating fault lines and their associated uplift patterns.

GEOLOGICAL PRINCIPLES:
1. Convergent plate boundaries create linear mountain ranges (Himalayas, Andes)
2. Uplift decreases exponentially with distance from fault
3. Multiple parallel/intersecting faults create complex mountain systems
4. Fault orientation and density determine overall terrain character

Created: 2025-10-07
Author: CS2 Map Generator Project
"""

from typing import List, Tuple, Optional, Dict
import numpy as np
from scipy.interpolate import splprep, splev
from scipy.ndimage import distance_transform_edt


class TectonicStructureGenerator:
    """
    Generates tectonic fault lines and mountain ranges for realistic terrain.

    WHY: Real mountains follow tectonic faults, not random noise blobs.
    This creates geologically-justified linear mountain ranges with proper
    spatial relationships and elevation profiles.

    The generator uses:
    - Bezier/B-spline curves for smooth, natural-looking fault traces
    - Euclidean distance fields for calculating proximity to faults
    - Exponential decay functions for realistic elevation falloff

    Attributes:
        resolution (int): Heightmap resolution in pixels (typically 4096)
        map_size_meters (float): Physical map size in meters (typically 14336)
        meters_per_pixel (float): Conversion factor for distance calculations
        edge_margin_meters (float): Keep faults away from map edges
        min_fault_spacing_meters (float): Prevent fault clustering
    """

    def __init__(
        self,
        resolution: int = 4096,
        map_size_meters: float = 14336.0,
        edge_margin_meters: float = 1000.0,
        min_fault_spacing_meters: float = 2000.0
    ):
        """
        Initialize the tectonic structure generator.

        Args:
            resolution: Heightmap resolution in pixels (must be power of 2)
            map_size_meters: Physical size of the map in meters
            edge_margin_meters: Minimum distance from map boundaries for fault endpoints
            min_fault_spacing_meters: Minimum distance between fault starting points

        WHY THESE DEFAULTS:
        - 4096x4096 is CS2's standard heightmap resolution
        - 14336m is CS2's maximum playable map size
        - 1000m edge margin prevents faults from being cut off at boundaries
        - 2000m spacing prevents unrealistic fault clustering
        """
        self.resolution = resolution
        self.map_size_meters = map_size_meters
        self.meters_per_pixel = map_size_meters / resolution
        self.edge_margin_meters = edge_margin_meters
        self.min_fault_spacing_meters = min_fault_spacing_meters

        # Calculate edge margin in pixels for internal calculations
        self.edge_margin_pixels = int(edge_margin_meters / self.meters_per_pixel)
        self.min_fault_spacing_pixels = int(min_fault_spacing_meters / self.meters_per_pixel)

    def generate_fault_lines(
        self,
        num_faults: int,
        terrain_type: str,
        seed: int
    ) -> List[np.ndarray]:
        """
        Generate Bezier curve fault lines across the map.

        WHY BEZIER CURVES:
        Real fault lines are smooth but not perfectly straight. Bezier curves
        with 3-5 control points create the right balance of smoothness and
        natural variation observed in real mountain ranges.

        Args:
            num_faults: Number of fault lines to generate (typically 3-7)
            terrain_type: Influences fault characteristics:
                - 'mountains': Longer, straighter faults (major ranges)
                - 'hills': Shorter, more curved faults (foothills)
                - 'mixed': Combination of both types
            seed: Random seed for reproducible generation

        Returns:
            List of fault line arrays, each shape (2, N) containing:
            - fault[0]: x-coordinates in pixels
            - fault[1]: y-coordinates in pixels

        WHY THIS APPROACH:
        Multiple separate fault lines allow complex mountain systems with
        realistic spacing and orientation variation, matching real-world
        tectonic patterns.
        """
        # WHY PCG64: Modern, high-quality PRNG with good statistical properties
        rng = np.random.Generator(np.random.PCG64(seed))

        fault_lines = []

        # Track fault starting positions to enforce minimum spacing
        # WHY: Prevents unrealistic clustering of parallel faults
        fault_start_positions = []

        # Determine fault characteristics based on terrain type
        # WHY: Different terrain types result from different tectonic regimes
        if terrain_type == 'mountains':
            length_range = (0.7, 0.8)  # Major mountain ranges are long
            control_points_range = (3, 4)  # Straighter faults
        elif terrain_type == 'hills':
            length_range = (0.5, 0.65)  # Shorter faults
            control_points_range = (4, 5)  # More curved
        else:  # 'mixed'
            length_range = (0.5, 0.8)  # Variable lengths
            control_points_range = (3, 5)  # Variable complexity

        # Calculate map diagonal for length scaling
        # WHY: Faults should scale with map size, not be fixed length
        map_diagonal = np.sqrt(2 * self.resolution**2)

        attempts = 0
        max_attempts = num_faults * 10  # Prevent infinite loops

        while len(fault_lines) < num_faults and attempts < max_attempts:
            attempts += 1

            # Generate random fault parameters
            num_control_points = rng.integers(
                control_points_range[0],
                control_points_range[1] + 1
            )

            # Generate starting point with edge margin
            # WHY: Starting points determine fault spacing and coverage
            start_x = rng.uniform(
                self.edge_margin_pixels,
                self.resolution - self.edge_margin_pixels
            )
            start_y = rng.uniform(
                self.edge_margin_pixels,
                self.resolution - self.edge_margin_pixels
            )

            # Check minimum spacing from existing faults
            # WHY: Prevents unrealistic clustering of mountain ranges
            if fault_start_positions:
                distances = [
                    np.sqrt((start_x - px)**2 + (start_y - py)**2) * self.meters_per_pixel
                    for px, py in fault_start_positions
                ]
                if min(distances) < self.min_fault_spacing_meters:
                    continue  # Too close to existing fault, try again

            # Generate control points for Bezier curve
            # WHY: Control points define the fault's path and curvature
            control_points = self._generate_control_points(
                start_x, start_y,
                num_control_points,
                length_range,
                map_diagonal,
                rng
            )

            # Rasterize the curve into pixel coordinates
            # WHY: Convert mathematical curve to discrete heightmap coordinates
            fault_x, fault_y = self._rasterize_curve(control_points)

            # Validate fault line is within bounds
            # WHY: Edge cases can create out-of-bounds coordinates due to curve interpolation
            if (np.all(fault_x >= 0) and np.all(fault_x < self.resolution) and
                np.all(fault_y >= 0) and np.all(fault_y < self.resolution)):

                fault_lines.append(np.array([fault_x, fault_y]))
                fault_start_positions.append((start_x, start_y))

        if len(fault_lines) < num_faults:
            # WHY: Warn but continue with what we generated - better than failing
            print(f"Warning: Only generated {len(fault_lines)}/{num_faults} faults "
                  f"after {attempts} attempts. Consider adjusting spacing constraints.")

        return fault_lines

    def _generate_control_points(
        self,
        start_x: float,
        start_y: float,
        num_points: int,
        length_range: Tuple[float, float],
        map_diagonal: float,
        rng: np.random.Generator
    ) -> List[Tuple[float, float]]:
        """
        Generate control points for a Bezier curve fault line.

        WHY: Control points determine fault characteristics:
        - First/last points: fault endpoints
        - Middle points: control fault curvature and direction

        Args:
            start_x: Starting x-coordinate in pixels
            start_y: Starting y-coordinate in pixels
            num_points: Number of control points (3-5)
            length_range: Min/max fault length as fraction of diagonal
            map_diagonal: Map diagonal length in pixels
            rng: Random number generator

        Returns:
            List of (x, y) control point tuples

        ALGORITHM:
        1. Pick random direction and length
        2. Generate intermediate points along approximate path
        3. Add perpendicular offset for curvature
        """
        # Choose random direction (angle in radians)
        # WHY: Real faults can have any orientation depending on plate motion
        direction = rng.uniform(0, 2 * np.pi)

        # Choose fault length
        # WHY: Length variation creates diverse mountain range scales
        length_fraction = rng.uniform(length_range[0], length_range[1])
        fault_length = map_diagonal * length_fraction

        # Calculate end point
        # WHY: End point defines overall fault direction and extent
        end_x = start_x + fault_length * np.cos(direction)
        end_y = start_y + fault_length * np.sin(direction)

        # Clamp end point within bounds with margin
        # WHY: Keep fault endpoints away from map edges
        end_x = np.clip(
            end_x,
            self.edge_margin_pixels,
            self.resolution - self.edge_margin_pixels
        )
        end_y = np.clip(
            end_y,
            self.edge_margin_pixels,
            self.resolution - self.edge_margin_pixels
        )

        # Generate intermediate control points
        # WHY: Intermediate points create natural curvature in fault trace
        control_points = [(start_x, start_y)]

        for i in range(1, num_points - 1):
            # Linear interpolation along fault direction
            t = i / (num_points - 1)
            base_x = start_x + t * (end_x - start_x)
            base_y = start_y + t * (end_y - start_y)

            # Add perpendicular offset for curvature
            # WHY: Real faults have gentle curves, not perfectly straight lines
            perpendicular_angle = direction + np.pi / 2
            offset_magnitude = rng.uniform(-fault_length * 0.1, fault_length * 0.1)

            offset_x = base_x + offset_magnitude * np.cos(perpendicular_angle)
            offset_y = base_y + offset_magnitude * np.sin(perpendicular_angle)

            # Clamp to valid range
            offset_x = np.clip(offset_x, 0, self.resolution - 1)
            offset_y = np.clip(offset_y, 0, self.resolution - 1)

            control_points.append((offset_x, offset_y))

        control_points.append((end_x, end_y))

        return control_points

    def _rasterize_curve(
        self,
        control_points: List[Tuple[float, float]]
    ) -> Tuple[np.ndarray, np.ndarray]:
        """
        Convert control points to pixel coordinates using B-spline interpolation.

        WHY B-SPLINES:
        B-splines provide C2 continuity (smooth curvature) which matches
        the smooth nature of real geological fault traces. They're more
        stable than high-order Bezier curves.

        Args:
            control_points: List of (x, y) control point tuples

        Returns:
            Tuple of (x_pixels, y_pixels) arrays containing rasterized curve

        IMPLEMENTATION DETAILS:
        - Uses scipy.interpolate.splprep for B-spline parameter fitting
        - Evaluates at 1000+ points for smooth, continuous curves
        - Handles edge case of too few control points gracefully
        """
        # Separate x and y coordinates
        # WHY: splprep expects separate coordinate arrays
        x_coords = np.array([p[0] for p in control_points])
        y_coords = np.array([p[1] for p in control_points])

        # Handle edge case: need at least 2 points for interpolation
        if len(control_points) < 2:
            return x_coords, y_coords

        try:
            # Fit B-spline to control points
            # WHY k=min(3, len-1): Use cubic splines when possible, lower order if needed
            # WHY s=0: Interpolate exactly through control points (no smoothing)
            k = min(3, len(control_points) - 1)
            tck, u = splprep([x_coords, y_coords], s=0, k=k)

            # Evaluate spline at many points for smooth curve
            # WHY 1000 points: Ensures smooth rasterization even for long faults
            # More points = smoother curve but same computational cost for distance field
            num_eval_points = max(1000, int(np.sqrt(
                (x_coords[-1] - x_coords[0])**2 +
                (y_coords[-1] - y_coords[0])**2
            ) * 2))

            u_fine = np.linspace(0, 1, num_eval_points)
            curve_points = splev(u_fine, tck)

            # Convert to integer pixel coordinates
            # WHY round: Nearest pixel gives best representation
            x_pixels = np.round(curve_points[0]).astype(int)
            y_pixels = np.round(curve_points[1]).astype(int)

            # Remove duplicate consecutive points
            # WHY: Duplicates waste memory and don't affect distance field
            unique_indices = np.concatenate([
                [True],
                (x_pixels[1:] != x_pixels[:-1]) | (y_pixels[1:] != y_pixels[:-1])
            ])

            return x_pixels[unique_indices], y_pixels[unique_indices]

        except Exception as e:
            # Fallback to linear interpolation if spline fails
            # WHY: Better to have straight fault than no fault
            print(f"Warning: B-spline interpolation failed ({e}), using linear interpolation")

            # Linear interpolation between consecutive control points
            all_x, all_y = [], []
            for i in range(len(control_points) - 1):
                x1, y1 = control_points[i]
                x2, y2 = control_points[i + 1]

                num_points = max(100, int(np.sqrt((x2 - x1)**2 + (y2 - y1)**2)))
                t = np.linspace(0, 1, num_points)

                all_x.extend(x1 + t * (x2 - x1))
                all_y.extend(y1 + t * (y2 - y1))

            x_pixels = np.round(all_x).astype(int)
            y_pixels = np.round(all_y).astype(int)

            return x_pixels, y_pixels

    def create_fault_mask(self, fault_lines: List[np.ndarray]) -> np.ndarray:
        """
        Create binary mask from all fault line pixels.

        WHY: Binary mask is required input for distance transform algorithm.
        Marks all pixels that lie on or near fault traces.

        Args:
            fault_lines: List of fault line coordinate arrays from generate_fault_lines()

        Returns:
            Binary array of shape (resolution, resolution) where:
            - True (1): pixel is on a fault line
            - False (0): pixel is away from faults

        USAGE:
        This mask feeds into calculate_distance_field() to compute
        proximity-based elevation profiles.
        """
        # Initialize empty mask
        # WHY bool dtype: Memory efficient for binary data
        mask = np.zeros((self.resolution, self.resolution), dtype=bool)

        # Mark all fault line pixels
        # WHY: Each fault contributes to the overall tectonic structure
        for fault in fault_lines:
            x_pixels, y_pixels = fault[0], fault[1]

            # Bounds check (defensive programming)
            # WHY: Prevents crashes from edge cases in curve generation
            valid = (
                (x_pixels >= 0) & (x_pixels < self.resolution) &
                (y_pixels >= 0) & (y_pixels < self.resolution)
            )

            mask[y_pixels[valid], x_pixels[valid]] = True

        return mask

    def calculate_distance_field(self, fault_mask: np.ndarray) -> np.ndarray:
        """
        Calculate Euclidean distance to nearest fault pixel.

        WHY DISTANCE FIELDS:
        Elevation should decrease smoothly with distance from fault.
        Distance fields provide exact distance to nearest fault at every pixel,
        enabling smooth, continuous elevation profiles.

        ALGORITHM:
        Uses scipy.ndimage.distance_transform_edt (Exact Euclidean Distance Transform)
        which implements the efficient Saito-Toriwaki algorithm.

        Args:
            fault_mask: Binary mask from create_fault_mask()

        Returns:
            Float array of shape (resolution, resolution) where each value
            is the distance in METERS to the nearest fault pixel

        COMPUTATIONAL COMPLEXITY:
        O(N) where N = number of pixels, regardless of number of faults.
        WHY: Distance transform is inherently efficient for this use case.
        """
        # Calculate distance in pixels
        # WHY invert mask: distance_transform_edt measures distance to False values
        distance_pixels = distance_transform_edt(~fault_mask)

        # Convert to meters
        # WHY: Physical units make parameters (like falloff distance) intuitive
        distance_meters = distance_pixels * self.meters_per_pixel

        return distance_meters

    def apply_uplift_profile(
        self,
        distance_field: np.ndarray,
        max_uplift: float = 0.8,
        falloff_meters: float = 600.0
    ) -> np.ndarray:
        """
        Apply exponential uplift based on distance to faults.

        WHY EXPONENTIAL DECAY:
        Real mountain elevations follow approximately exponential decay
        from fault zones due to:
        1. Mechanical stress distribution in crust
        2. Erosion patterns (steeper slopes erode faster)
        3. Isostatic equilibrium principles

        FORMULA:
        elevation(x) = max_uplift * exp(-distance(x) / falloff_meters)

        WHERE:
        - distance(x): meters to nearest fault (from distance field)
        - max_uplift: peak elevation at fault (normalized 0-1)
        - falloff_meters: e-folding distance (elevation drops to 37% at this distance)

        Args:
            distance_field: Distance in meters from calculate_distance_field()
            max_uplift: Maximum elevation at fault lines (0-1 normalized)
            falloff_meters: Distance at which elevation drops to 1/e of maximum
                          - 600m: Steep, dramatic mountains (Alps, Rockies)
                          - 1200m: Gentler mountains (Appalachians)
                          - 2400m: Rolling hills (Scottish Highlands)

        Returns:
            Float array of shape (resolution, resolution) with normalized
            elevation values (0-1) representing tectonic uplift contribution

        PHYSICAL INTERPRETATION:
        - At fault (distance=0): elevation = max_uplift
        - At falloff_meters: elevation = max_uplift * 0.368
        - At 2*falloff_meters: elevation = max_uplift * 0.135
        - At 3*falloff_meters: elevation = max_uplift * 0.050

        WHY NORMALIZED VALUES:
        Allows blending with other terrain layers (erosion, noise, etc.)
        without requiring denormalization/renormalization cycles.
        """
        # Apply exponential decay function
        # WHY negative exponent: Creates decay, not growth
        # WHY safe from division by zero: falloff_meters is positive parameter
        elevation = max_uplift * np.exp(-distance_field / falloff_meters)

        # Defensive clipping to normalized range
        # WHY: Floating point arithmetic can create small over/undershoots
        elevation = np.clip(elevation, 0.0, 1.0)

        return elevation

    def generate_tectonic_terrain(
        self,
        num_faults: int = 5,
        terrain_type: str = 'mountains',
        max_uplift: float = 0.8,
        falloff_meters: float = 600.0,
        seed: int = 42
    ) -> np.ndarray:
        """
        Complete pipeline: generate faults and apply uplift profile.

        WHY CONVENIENCE METHOD:
        Most users want the complete tectonic terrain, not intermediate steps.
        This method provides a simple interface while allowing advanced users
        to call individual methods for custom workflows.

        Args:
            num_faults: Number of fault lines (3-7 typical)
            terrain_type: 'mountains', 'hills', or 'mixed'
            max_uplift: Peak elevation at faults (0-1)
            falloff_meters: Elevation decay rate
            seed: Random seed for reproducibility

        Returns:
            Normalized elevation array (0-1) ready for blending with other layers

        TYPICAL USAGE:
        ```python
        generator = TectonicStructureGenerator(resolution=4096)

        # Generate steep mountain range
        terrain = generator.generate_tectonic_terrain(
            num_faults=5,
            terrain_type='mountains',
            max_uplift=0.8,
            falloff_meters=600.0,
            seed=42
        )
        ```
        """
        # Step 1: Generate fault line traces
        # WHY: Defines where mountains will form
        fault_lines = self.generate_fault_lines(num_faults, terrain_type, seed)

        if not fault_lines:
            # WHY: Return flat terrain if no faults generated (edge case)
            print("Warning: No fault lines generated, returning flat terrain")
            return np.zeros((self.resolution, self.resolution), dtype=np.float32)

        # Step 2: Create binary mask of fault locations
        # WHY: Required input for distance transform
        fault_mask = self.create_fault_mask(fault_lines)

        # Step 3: Calculate distance field
        # WHY: Needed for elevation falloff calculation
        distance_field = self.calculate_distance_field(fault_mask)

        # Step 4: Apply uplift profile
        # WHY: Converts distance to actual elevation values
        elevation = self.apply_uplift_profile(distance_field, max_uplift, falloff_meters)

        return elevation.astype(np.float32)

    @staticmethod
    def generate_amplitude_modulated_terrain(
        tectonic_elevation: np.ndarray,
        buildability_mask: np.ndarray,
        noise_generator,  # NoiseGenerator instance
        buildable_amplitude: float = 0.3,
        scenic_amplitude: float = 1.0,
        noise_octaves: int = 6,
        noise_persistence: float = 0.5,
        verbose: bool = True
    ) -> Tuple[np.ndarray, Dict]:
        """
        Generate terrain using amplitude modulation (Task 2.3).

        WHY THIS APPROACH:
        Uses SINGLE noise field with SAME octaves everywhere. Only amplitude
        varies (0.3 in buildable zones, 1.0 in scenic zones). This prevents
        frequency discontinuities that destroyed the gradient control map system.

        CRITICAL CONTEXT:
        The gradient control map approach failed catastrophically (3.4% buildable
        vs 50% target, 6x more jagged) because it blended 2-octave, 5-octave,
        and 7-octave noise, creating frequency discontinuities at zone boundaries.
        This method uses SAME frequency content everywhere, varying only the
        amplitude of that content.

        ALGORITHM:
        1. Generate single Perlin noise field (6 octaves by default)
        2. Center noise around 0 (convert from [0,1] to [-1,1])
        3. Create amplitude modulation map (0.3 buildable, 1.0 scenic)
        4. Multiply noise by amplitude map (modulate amplitude, not frequency)
        5. Add modulated noise to tectonic base structure
        6. Normalize result to [0,1]

        Args:
            tectonic_elevation: Base structure from Task 2.1 (0-1 normalized)
            buildability_mask: Binary mask from Task 2.2 (1=buildable, 0=scenic)
            noise_generator: NoiseGenerator instance for Perlin generation
            buildable_amplitude: Amplitude for buildable zones (default: 0.3)
            scenic_amplitude: Amplitude for scenic zones (default: 1.0)
            noise_octaves: Octaves for noise (SAME everywhere, default: 6)
            noise_persistence: Persistence for noise (SAME everywhere, default: 0.5)
            verbose: Print progress messages

        Returns:
            Tuple of (final_terrain, stats_dict)
            - final_terrain: Combined terrain (0-1 normalized)
            - stats_dict: Statistics about the generation including:
                - buildable_amplitude_mean: Mean absolute amplitude in buildable zones
                - scenic_amplitude_mean: Mean absolute amplitude in scenic zones
                - amplitude_ratio: Ratio of scenic/buildable amplitudes (~3.33)
                - final_range: (min, max) of final terrain
                - noise_octaves_used: Octaves used (confirmation)
                - single_frequency_field: True (confirms no multi-octave blending)

        DESIGN RATIONALE:
        - Single noise field: Ensures frequency continuity across all zones
        - Amplitude modulation only: Varies intensity, not character of terrain
        - 0.3 vs 1.0 ratio: 3.33x amplitude difference creates distinct zones
          while maintaining same frequency content (smooth transitions)
        - Octave consistency: Same octaves everywhere prevents jagged boundaries

        VALIDATION:
        Method validates inputs before processing:
        - Shapes must match between tectonic_elevation and buildability_mask
        - Mask must be binary (only 0 and 1 values)
        - Amplitudes must be positive
        - Octaves must be >= 1
        """
        # Validate inputs
        # WHY: Catch configuration errors early with clear error messages
        if tectonic_elevation.shape != buildability_mask.shape:
            raise ValueError(
                f"Shape mismatch: tectonic_elevation {tectonic_elevation.shape} "
                f"vs buildability_mask {buildability_mask.shape}"
            )

        if not np.all(np.isin(buildability_mask, [0, 1])):
            raise ValueError("buildability_mask must be binary (only 0 and 1 values)")

        if buildable_amplitude <= 0 or scenic_amplitude <= 0:
            raise ValueError(
                f"Amplitudes must be positive: buildable={buildable_amplitude}, "
                f"scenic={scenic_amplitude}"
            )

        if noise_octaves < 1:
            raise ValueError(f"noise_octaves must be >= 1, got {noise_octaves}")

        resolution = tectonic_elevation.shape[0]

        if verbose:
            print(f"\n[Task 2.3: Amplitude Modulated Terrain Generation]")
            print(f"  Resolution: {resolution}x{resolution}")
            print(f"  Noise octaves (SAME everywhere): {noise_octaves}")
            print(f"  Noise persistence: {noise_persistence}")
            print(f"  Buildable amplitude: {buildable_amplitude}")
            print(f"  Scenic amplitude: {scenic_amplitude}")
            print(f"  Amplitude ratio: {scenic_amplitude/buildable_amplitude:.2f}")

        # Step 1: Generate single Perlin noise field
        # WHY: One noise field with consistent octaves everywhere prevents
        # frequency discontinuities that plagued the gradient system
        if verbose:
            print(f"  Generating single Perlin noise field...")

        base_noise = noise_generator.generate_perlin(
            resolution=resolution,
            octaves=noise_octaves,
            persistence=noise_persistence,
            scale=200.0  # Reasonable scale for terrain detail
        )

        # Step 2: Center noise around 0
        # WHY: Perlin returns [0, 1], but we need signed values for symmetric
        # modulation (both positive and negative variations from base elevation)
        noise_centered = (base_noise - 0.5) * 2.0

        if verbose:
            print(f"  Noise range (centered): [{noise_centered.min():.3f}, {noise_centered.max():.3f}]")

        # Step 3: Create amplitude modulation map
        # WHY: Binary mask defines where to apply different amplitudes
        # buildability_mask: 1 = buildable (low amplitude), 0 = scenic (high amplitude)
        amplitude_map = np.where(
            buildability_mask == 1,
            buildable_amplitude,
            scenic_amplitude
        )

        # Step 4: Apply amplitude modulation
        # WHY: Multiply noise by amplitude map to scale noise intensity
        # This modulates AMPLITUDE only, not frequency content
        modulated_noise = noise_centered * amplitude_map

        # Calculate statistics for buildable and scenic zones
        # WHY: Verify amplitude modulation is working as expected
        buildable_indices = buildability_mask == 1
        scenic_indices = buildability_mask == 0

        buildable_amplitude_mean = np.mean(np.abs(modulated_noise[buildable_indices]))
        scenic_amplitude_mean = np.mean(np.abs(modulated_noise[scenic_indices]))

        if verbose:
            print(f"  Buildable zone amplitude (mean absolute): {buildable_amplitude_mean:.3f}")
            print(f"  Scenic zone amplitude (mean absolute): {scenic_amplitude_mean:.3f}")
            print(f"  Measured amplitude ratio: {scenic_amplitude_mean/buildable_amplitude_mean:.2f}")

        # Step 5: Combine with tectonic base
        # WHY: Tectonic structure provides the large-scale form,
        # modulated noise adds appropriate detail level per zone
        combined = tectonic_elevation + modulated_noise

        if verbose:
            print(f"  Combined range (before normalization): [{combined.min():.3f}, {combined.max():.3f}]")

        # Step 6: Smart normalization to avoid gradient amplification
        # WHY: Traditional normalization can amplify gradients when range is small
        # CRITICAL FIX: If combined terrain is already in reasonable range,
        # use clipping instead of stretching to avoid gradient amplification
        combined_min = combined.min()
        combined_max = combined.max()
        combined_range = combined_max - combined_min

        # If range is already close to [0, 1], just clip to avoid stretching
        if combined_min >= -0.1 and combined_max <= 1.1:
            # Already in good range, clip to [0, 1] without stretching
            final_terrain = np.clip(combined, 0.0, 1.0)
            if verbose:
                print(f"  [SMART NORM] Range acceptable, using clip (no gradient amplification)")
        elif combined_range > 0:
            # Range too large or shifted, normalize to [0, 1]
            final_terrain = (combined - combined_min) / combined_range
            if verbose:
                print(f"  [SMART NORM] Range requires normalization: [{combined_min:.3f}, {combined_max:.3f}]")
        else:
            # WHY: Handle edge case of perfectly flat terrain (unlikely but possible)
            final_terrain = np.zeros_like(combined)
            if verbose:
                print(f"  [SMART NORM] Flat terrain detected")

        if verbose:
            print(f"  Final terrain range: [{final_terrain.min():.3f}, {final_terrain.max():.3f}]")

        # Step 7: Calculate comprehensive statistics
        # WHY: Provide verification that method is working correctly
        # and enable debugging if results are unexpected
        stats = {
            'buildable_amplitude_mean': float(buildable_amplitude_mean),
            'scenic_amplitude_mean': float(scenic_amplitude_mean),
            'amplitude_ratio': float(scenic_amplitude_mean / buildable_amplitude_mean),
            'final_range': (float(final_terrain.min()), float(final_terrain.max())),
            'noise_octaves_used': noise_octaves,
            'single_frequency_field': True,  # Confirms no multi-octave blending
            'buildable_pixels': int(np.sum(buildable_indices)),
            'scenic_pixels': int(np.sum(scenic_indices)),
            'buildable_percentage': float(100 * np.sum(buildable_indices) / buildable_indices.size),
        }

        if verbose:
            print(f"  Buildable pixels: {stats['buildable_pixels']:,} ({stats['buildable_percentage']:.1f}%)")
            print(f"  Scenic pixels: {stats['scenic_pixels']:,}")
            print(f"  [Task 2.3 Complete]")

        return final_terrain.astype(np.float32), stats
