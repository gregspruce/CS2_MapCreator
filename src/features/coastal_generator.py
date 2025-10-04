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

    def __init__(self, heightmap: np.ndarray, water_level: float = 0.0):
        """
        Initialize coastal generator.

        Args:
            heightmap: 2D numpy array of elevation values (0.0-1.0)
            water_level: Elevation of water surface (default: 0.0 = sea level)

        Note: Heightmap is NOT modified by this class.
        """
        self.heightmap = heightmap.copy()
        self.water_level = water_level
        self.height, self.width = heightmap.shape

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

                        # Target height slightly above water
                        target_height = self.water_level + 0.01

                        # Blend toward target
                        current = result[y, x]
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

        # Generate coastal features
        coastal_gen = CoastalGenerator(self.generator.heightmap, self.water_level)
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
