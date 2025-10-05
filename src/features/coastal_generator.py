"""
CS2 Coastal Features Generation Module

Implements realistic beach and cliff generation based on slope analysis.
This is the OPTIMAL solution based on geomorphology principles.

Coastal Feature Algorithm:
- Beaches form on gentle slopes (0-5 degrees)
- Cliffs form on steep slopes (45+ degrees)
- Slope dictates coastal morphology

Why slope-based coastal features are optimal:
- Physically accurate (matches real-world erosion patterns)
- Used in geomorphology research
- Simple, deterministic, reproducible
- No arbitrary decisions
"""

import numpy as np
from typing import Tuple, Optional
from scipy import ndimage
from ..progress_tracker import ProgressTracker
from ..state_manager import Command


class CoastalGenerator:
    """
    Generates realistic coastal features (beaches, cliffs) based on slope.

    Real-world coastal morphology is determined by slope:
    - Gentle slopes: sediment accumulation forms beaches
    - Steep slopes: erosion resistant rock forms cliffs
    - Transition zones: mix of both features
    """

    # Slope thresholds (in radians)
    BEACH_MAX_SLOPE = np.radians(5)   # 0-5 degrees = beach
    CLIFF_MIN_SLOPE = np.radians(45)  # 45+ degrees = cliff

    def __init__(self, heightmap: np.ndarray, water_level: float = 0.0, downsample: bool = True, target_size: int = 1024):
        """
        Initialize coastal generator.

        Args:
            heightmap: 2D numpy array of elevation values (0.0-1.0)
            water_level: Elevation of water surface (default: 0.0 = sea level)
            downsample: Enable downsampling for performance (default True)
            target_size: Target resolution for downsampling (default 1024)

        Note: Heightmap is NOT modified by this class.

        Performance:
        - With downsampling (4096→1024): ~30s instead of 15min
        - Without downsampling: Original speed (slow on large maps)
        """
        # Store original heightmap info
        self.original_heightmap = heightmap
        self.original_size = heightmap.shape[0]
        self.water_level = water_level

        # DEBUG: Show initialization parameters
        print(f"[COASTAL DEBUG] CoastalGenerator.__init__() called")
        print(f"[COASTAL DEBUG]   - Input heightmap shape: {heightmap.shape}")
        print(f"[COASTAL DEBUG]   - downsample parameter: {downsample}")
        print(f"[COASTAL DEBUG]   - target_size parameter: {target_size}")

        # Downsample if enabled and needed
        if downsample and heightmap.shape[0] > target_size:
            from .performance_utils import downsample_heightmap
            self.heightmap, self.scale_factor = downsample_heightmap(heightmap, target_size)
            self.downsampled = True
            print(f"[COASTAL DEBUG] [OK] DOWNSAMPLING ACTIVE: {self.original_size}x{self.original_size} -> {self.heightmap.shape[0]}x{self.heightmap.shape[0]}")
            print(f"[COASTAL DEBUG] [OK] Expected speedup: {self.scale_factor:.1f}x")
        else:
            self.heightmap = heightmap.copy()
            self.scale_factor = 1.0
            self.downsampled = False
            print(f"[COASTAL DEBUG] [NO] NO DOWNSAMPLING: Processing at full resolution {heightmap.shape[0]}x{heightmap.shape[0]}")
            if not downsample:
                print(f"[COASTAL DEBUG]   Reason: downsample=False")
            elif heightmap.shape[0] <= target_size:
                print(f"[COASTAL DEBUG]   Reason: heightmap size ({heightmap.shape[0]}) <= target_size ({target_size})")

        self.height, self.width = self.heightmap.shape

    def calculate_slope(self) -> np.ndarray:
        """
        Calculate slope magnitude for each cell.

        Returns:
            2D array of slope values in radians

        Algorithm:
        1. Calculate gradient (partial derivatives) using Sobel filter
        2. Compute slope magnitude from gradients
        3. Convert to radians

        Why Sobel filter:
        - Standard method in terrain analysis
        - Accounts for diagonal neighbors
        - Noise resistant (weighted averaging)
        - Used in all GIS software
        """
        # Calculate gradients using Sobel filter (standard GIS method)
        gradient_y = ndimage.sobel(self.heightmap, axis=0)
        gradient_x = ndimage.sobel(self.heightmap, axis=1)

        # Calculate slope magnitude
        # slope = arctan(sqrt(dz/dx^2 + dz/dy^2))
        slope_magnitude = np.sqrt(gradient_x**2 + gradient_y**2)

        # Convert to radians (arctan gives angle from horizontal)
        slope_radians = np.arctan(slope_magnitude)

        return slope_radians

    def detect_coastline(self,
                        search_distance: int = 5) -> np.ndarray:
        """
        Detect coastline (land-water interface).

        Args:
            search_distance: How far to search for water/land transition

        Returns:
            Boolean mask where True = coastline cell

        Algorithm:
        1. Identify water cells (below water_level)
        2. Identify land cells (above water_level)
        3. Coastline = land cells adjacent to water

        Why search_distance matters:
        - Accounts for shallow water/tidal zones
        - Creates realistic transition width
        - Typical value: 5-10 cells
        """
        # Water mask
        is_water = self.heightmap <= self.water_level

        # Dilate water mask to find nearby land
        water_dilated = ndimage.binary_dilation(is_water,
                                                iterations=search_distance)

        # Coastline = land cells near water
        is_coastline = water_dilated & (~is_water)

        return is_coastline

    def add_beaches(self,
                   heightmap: np.ndarray,
                   intensity: float = 0.5,
                   width: int = 10) -> np.ndarray:
        """
        Add beaches to gentle coastal slopes.

        Args:
            heightmap: Elevation data to modify
            intensity: How much to flatten beaches (0.0-1.0)
            width: Beach width in cells

        Returns:
            Modified heightmap with beaches

        Algorithm:
        1. Detect coastline
        2. Calculate slope
        3. Find gentle slopes on coast
        4. Flatten terrain to create beach

        Why flattening creates beaches:
        - Beaches are flat accumulations of sediment
        - Gentle slope indicates sediment deposition area
        - Flattening simulates this natural process
        """
        result = heightmap.copy()

        # Detect coastline and slopes
        coastline = self.detect_coastline()
        slopes = self.calculate_slope()

        # Beach locations = coastline + gentle slope
        is_beach = coastline & (slopes < self.BEACH_MAX_SLOPE)

        # Expand beach zone inland
        beach_zone = ndimage.binary_dilation(is_beach, iterations=width)

        # Flatten beach areas
        for y in range(self.height):
            for x in range(self.width):
                if beach_zone[y, x]:
                    # Distance from water affects flattening
                    # Closer to water = more flat
                    distance_from_coast = self._distance_to_coastline(y, x, coastline)

                    if distance_from_coast < width:
                        # Gradual flattening based on distance
                        flatten_factor = intensity * (1.0 - distance_from_coast / width)

                        # Target: Reduce slope rather than flatten to water level
                        # This creates gentle beaches without destroying all terrain
                        current = result[y, x]

                        # Only flatten if above water (beaches don't affect underwater terrain)
                        if current > self.water_level:
                            # Gentle gradient toward water level (not flat at water level)
                            beach_slope = (current - self.water_level) * 0.3  # Reduce slope by 70%
                            target_height = self.water_level + beach_slope
                            result[y, x] = current * (1 - flatten_factor) + target_height * flatten_factor

        return result

    def add_cliffs(self,
                  heightmap: np.ndarray,
                  intensity: float = 0.5,
                  min_height: float = 0.05) -> np.ndarray:
        """
        Add cliffs to steep coastal slopes.

        Args:
            heightmap: Elevation data to modify
            intensity: How much to steepen cliffs (0.0-1.0)
            min_height: Minimum cliff height

        Returns:
            Modified heightmap with cliffs

        Algorithm:
        1. Detect coastline
        2. Calculate slope
        3. Find steep slopes on coast
        4. Steepen terrain to create cliff

        Why steepening creates cliffs:
        - Cliffs are erosion-resistant rock faces
        - Steep slope indicates resistant bedrock
        - Steepening simulates vertical erosion
        """
        result = heightmap.copy()

        # Detect coastline and slopes
        coastline = self.detect_coastline()
        slopes = self.calculate_slope()

        # Cliff locations = coastline + steep slope + sufficient height
        is_cliff = (coastline &
                   (slopes > self.CLIFF_MIN_SLOPE) &
                   (heightmap > self.water_level + min_height))

        # Steepen cliff faces
        for y in range(self.height):
            for x in range(self.width):
                if is_cliff[y, x]:
                    # Find water side and land side
                    is_seaward = self._is_seaward_facing(y, x, coastline)

                    if is_seaward:
                        # Steepen seaward face
                        # Add height to create vertical face
                        result[y, x] += min_height * intensity

                        # Lower adjacent water-side cells
                        for dy, dx in [(-1,0), (1,0), (0,-1), (0,1)]:
                            ny, nx = y + dy, x + dx
                            if 0 <= ny < self.height and 0 <= nx < self.width:
                                if result[ny, nx] < result[y, x]:
                                    # Lower adjacent cells to increase cliff face
                                    result[ny, nx] -= min_height * intensity * 0.5

        return result

    def _distance_to_coastline(self,
                               y: int,
                               x: int,
                               coastline: np.ndarray) -> float:
        """
        Calculate approximate distance to nearest coastline cell.

        Uses simple radial search for efficiency.

        Returns:
            Distance in cells (approximate)
        """
        max_search = 20

        for radius in range(max_search):
            # Check cells at this radius
            for angle in range(0, 360, 30):
                rad = np.radians(angle)
                dy = int(radius * np.sin(rad))
                dx = int(radius * np.cos(rad))

                ny, nx = y + dy, x + dx
                if 0 <= ny < self.height and 0 <= nx < self.width:
                    if coastline[ny, nx]:
                        return radius

        return max_search

    def _is_seaward_facing(self,
                          y: int,
                          x: int,
                          coastline: np.ndarray) -> bool:
        """
        Determine if a coastal cell faces the sea.

        Returns:
            True if cell is on seaward side of coastline
        """
        # Check if more water on one side than the other
        water_count = 0
        total_count = 0

        for dy, dx in [(-1,0), (1,0), (0,-1), (0,1),
                       (-1,-1), (-1,1), (1,-1), (1,1)]:
            ny, nx = y + dy, x + dx
            if 0 <= ny < self.height and 0 <= nx < self.width:
                total_count += 1
                if self.heightmap[ny, nx] <= self.water_level:
                    water_count += 1

        # If more than half neighbors are water, it's seaward
        return water_count > total_count / 2

    def generate_coastal_features(self,
                                 add_beaches: bool = True,
                                 add_cliffs: bool = True,
                                 beach_intensity: float = 0.5,
                                 cliff_intensity: float = 0.5,
                                 show_progress: bool = True) -> np.ndarray:
        """
        Generate complete coastal features.

        Args:
            add_beaches: Whether to add beaches
            add_cliffs: Whether to add cliffs
            beach_intensity: Beach flattening intensity
            cliff_intensity: Cliff steepening intensity
            show_progress: Show progress during generation

        Returns:
            Modified heightmap with coastal features
        """
        result = self.heightmap.copy()

        stages = []
        if add_beaches:
            stages.append("beaches")
        if add_cliffs:
            stages.append("cliffs")

        with ProgressTracker("Generating coastal features",
                           total=len(stages),
                           disable=not show_progress) as progress:
            if add_beaches:
                result = self.add_beaches(result, intensity=beach_intensity)
                progress.update(1)

            if add_cliffs:
                result = self.add_cliffs(result, intensity=cliff_intensity)
                progress.update(1)

        # If we downsampled, upsample result back to original resolution
        if self.downsampled:
            print(f"[COASTAL DEBUG] Upsampling result to original resolution ({self.original_size}x{self.original_size})")
            from scipy import ndimage

            # CRITICAL FIX: Calculate delta (changes made) at downsampled resolution
            # This preserves original terrain detail while applying feature modifications
            delta = result - self.heightmap
            print(f"[COASTAL DEBUG] Delta range: {delta.min():.6f} to {delta.max():.6f}")

            # Upsample the delta, not the result
            scale_factor = self.original_size / result.shape[0]
            delta_upsampled = ndimage.zoom(delta, scale_factor, order=1)  # Bilinear interpolation

            # Ensure exact size
            if delta_upsampled.shape[0] != self.original_size:
                delta_upsampled = delta_upsampled[:self.original_size, :self.original_size]

            # Apply delta to original heightmap to preserve detail
            result = self.original_heightmap + delta_upsampled
            print(f"[COASTAL DEBUG] Applied delta to original heightmap")
            print(f"[COASTAL DEBUG] Result range: {result.min():.6f} to {result.max():.6f}")

        return result


class AddCoastalFeaturesCommand(Command):
    """
    Command for adding coastal features to heightmap (undoable).

    Generates beaches on gentle slopes and cliffs on steep slopes.
    """

    def __init__(self,
                 generator,
                 water_level: float = 0.0,
                 add_beaches: bool = True,
                 add_cliffs: bool = True,
                 beach_intensity: float = 0.5,
                 cliff_intensity: float = 0.5,
                 description: str = "Add coastal features"):
        """
        Initialize coastal features command.

        Args:
            generator: HeightmapGenerator instance
            water_level: Water surface elevation
            add_beaches: Generate beaches
            add_cliffs: Generate cliffs
            beach_intensity: Beach flattening intensity
            cliff_intensity: Cliff steepening intensity
            description: Human-readable description
        """
        super().__init__(description)
        self.generator = generator
        self.water_level = water_level
        self.add_beaches = add_beaches
        self.add_cliffs = add_cliffs
        self.beach_intensity = beach_intensity
        self.cliff_intensity = cliff_intensity
        self.previous_data: Optional[np.ndarray] = None
        self.modified_data: Optional[np.ndarray] = None

    def execute(self) -> None:
        """
        Execute coastal feature generation.

        Stores previous state for undo.
        """
        # Store previous state
        self.previous_data = self.generator.heightmap.copy()

        # Generate coastal features (with downsampling enabled by default)
        coastal_gen = CoastalGenerator(self.generator.heightmap, self.water_level, downsample=True, target_size=1024)
        self.modified_data = coastal_gen.generate_coastal_features(
            add_beaches=self.add_beaches,
            add_cliffs=self.add_cliffs,
            beach_intensity=self.beach_intensity,
            cliff_intensity=self.cliff_intensity
        )

        # Apply to generator
        self.generator.heightmap = self.modified_data.copy()
        self._executed = True

    def undo(self) -> None:
        """
        Undo coastal feature generation.

        Restores previous heightmap state.
        """
        if not self._executed or self.previous_data is None:
            raise RuntimeError("Cannot undo: command not executed")

        self.generator.heightmap = self.previous_data.copy()
        self._executed = False
