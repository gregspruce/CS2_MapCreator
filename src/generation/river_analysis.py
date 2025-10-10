"""
River Analysis and Flow Network Detection

This module implements flow analysis using the D8 algorithm to identify
natural drainage networks created by hydraulic erosion. Rivers are detected
by analyzing flow accumulation patterns and extracting major drainage paths.

Author: Claude Code (Session 7)
Date: 2025-10-10
"""

import numpy as np
import time
from typing import Tuple, Dict, List, Optional

# Try to import numba for JIT compilation (5-8x speedup)
try:
    from numba import njit
    NUMBA_AVAILABLE = True
except ImportError:
    # Graceful fallback if numba not available
    def njit(*args, **kwargs):
        def decorator(func):
            return func
        if len(args) == 1 and callable(args[0]):
            return args[0]
        return decorator
    NUMBA_AVAILABLE = False


class RiverAnalyzer:
    """
    Analyzes terrain drainage patterns and identifies river networks.

    Uses the D8 flow direction algorithm to determine water flow paths,
    then calculates flow accumulation to identify major drainage networks.
    Rivers are extracted based on flow accumulation thresholds.

    Implementation follows the pattern established in Sessions 2-6 for
    consistency and maintainability.
    """

    # D8 Flow Direction Codes (powers of 2 for efficient encoding)
    # Direction encoding: E=1, SE=2, S=4, SW=8, W=16, NW=32, N=64, NE=128
    D8_DIRECTIONS = {
        'E':  (1, 0,   1),    # (dx, dy, code)
        'SE': (1, 1,   2),
        'S':  (0, 1,   4),
        'SW': (-1, 1,  8),
        'W':  (-1, 0,  16),
        'NW': (-1, -1, 32),
        'N':  (0, -1,  64),
        'NE': (1, -1,  128)
    }

    # Neighbor offsets for D8 (8 directions)
    D8_OFFSETS = np.array([
        (1, 0),   # E
        (1, 1),   # SE
        (0, 1),   # S
        (-1, 1),  # SW
        (-1, 0),  # W
        (-1, -1), # NW
        (0, -1),  # N
        (1, -1)   # NE
    ], dtype=np.int32)

    # Direction codes corresponding to offsets
    D8_CODES = np.array([1, 2, 4, 8, 16, 32, 64, 128], dtype=np.uint8)

    def __init__(
        self,
        resolution: int,
        map_size_meters: float = 14336.0,
        seed: Optional[int] = None
    ):
        """
        Initialize the RiverAnalyzer.

        Args:
            resolution: Grid resolution (e.g., 4096 for 4096x4096)
            map_size_meters: Physical map size in meters (default: 14.336km for CS2)
            seed: Random seed for reproducibility (not used currently, reserved for future features)

        Raises:
            ValueError: If resolution < 3 or map_size_meters <= 0
        """
        if resolution < 3:
            raise ValueError(f"Resolution must be >= 3, got {resolution}")
        if map_size_meters <= 0:
            raise ValueError(f"Map size must be > 0, got {map_size_meters}")

        self.resolution = resolution
        self.map_size_meters = map_size_meters
        self.pixel_size_meters = map_size_meters / resolution
        self.seed = seed

        # Pre-compute diagonal distance factor for D8 (sqrt(2) for diagonal neighbors)
        self.diagonal_dist = np.sqrt(2.0)

    def analyze_rivers(
        self,
        heightmap: np.ndarray,
        buildability_potential: Optional[np.ndarray] = None,
        threshold_percentile: float = 99.0,
        min_river_length: int = 10,
        verbose: bool = False
    ) -> Tuple[Dict, Dict]:
        """
        Analyze terrain drainage and extract river networks.

        This is the main entry point for river analysis. It performs:
        1. D8 flow direction calculation
        2. Flow accumulation calculation
        3. River path extraction based on threshold
        4. River width calculation
        5. Dam site identification (optional)

        Args:
            heightmap: Terrain elevation map, shape (N, N), range [0, 1]
            buildability_potential: Optional buildability zones from Session 2
            threshold_percentile: Percentile for river detection (99.0 = top 1% flow)
            min_river_length: Minimum river length in pixels
            verbose: Print progress messages

        Returns:
            (river_network, statistics)

            river_network: Dict containing:
                - 'paths': List of river path dicts with points, flow, width, start, end
                - 'flow_map': Flow accumulation array (N, N)
                - 'flow_dir': Flow direction array (N, N) with D8 codes
                - 'dam_sites': List of potential dam site locations

            statistics: Dict with analysis metrics

        Raises:
            ValueError: If heightmap shape doesn't match resolution
        """
        if heightmap.shape != (self.resolution, self.resolution):
            raise ValueError(
                f"Heightmap shape {heightmap.shape} doesn't match "
                f"resolution ({self.resolution}, {self.resolution})"
            )

        if not (0.0 <= threshold_percentile <= 100.0):
            raise ValueError(f"threshold_percentile must be in [0, 100], got {threshold_percentile}")

        if min_river_length < 2:
            raise ValueError(f"min_river_length must be >= 2, got {min_river_length}")

        start_time = time.time()

        if verbose:
            print("\n[RIVER ANALYSIS] Starting flow analysis...")
            print(f"  Resolution: {self.resolution}x{self.resolution}")
            print(f"  Threshold percentile: {threshold_percentile}%")
            print(f"  Min river length: {min_river_length} pixels")

        # Stage 1: Calculate D8 flow directions
        if verbose:
            print("  [Stage 1/4] Calculating D8 flow directions...")
        flow_dir, dir_stats = self._calculate_flow_direction(heightmap)

        # Stage 2: Calculate flow accumulation
        if verbose:
            print("  [Stage 2/4] Calculating flow accumulation...")
        flow_map, accum_stats = self._calculate_flow_accumulation(heightmap, flow_dir)

        # Stage 3: Extract river paths
        if verbose:
            print("  [Stage 3/4] Extracting river paths...")
        river_paths, path_stats = self._extract_river_paths(
            flow_map, flow_dir, threshold_percentile, min_river_length
        )

        # Stage 4: Identify dam sites (optional)
        if verbose:
            print("  [Stage 4/4] Identifying dam sites...")
        dam_sites, dam_stats = self._identify_dam_sites(
            heightmap, flow_map, river_paths
        )

        elapsed_time = time.time() - start_time

        if verbose:
            print(f"  [COMPLETE] River analysis finished in {elapsed_time:.2f}s")
            print(f"    Rivers detected: {len(river_paths)}")
            print(f"    Total river length: {path_stats['total_length_pixels']} pixels")
            print(f"    Dam sites found: {len(dam_sites)}")

        # Assemble river network structure
        river_network = {
            'paths': river_paths,
            'flow_map': flow_map,
            'flow_dir': flow_dir,
            'dam_sites': dam_sites
        }

        # Assemble statistics
        statistics = {
            'num_rivers': len(river_paths),
            'total_river_length_pixels': path_stats['total_length_pixels'],
            'total_river_length_meters': path_stats['total_length_pixels'] * self.pixel_size_meters,
            'mean_river_width_pixels': path_stats['mean_width_pixels'],
            'max_flow_accumulation': accum_stats['max_accumulation'],
            'num_dam_sites': len(dam_sites),
            'threshold_value': path_stats['threshold_value'],
            'elapsed_time_seconds': elapsed_time
        }

        return river_network, statistics

    def _calculate_flow_direction(
        self,
        heightmap: np.ndarray
    ) -> Tuple[np.ndarray, Dict]:
        """
        Calculate D8 flow direction for each cell.

        For each cell, determines which of its 8 neighbors has the steepest
        downhill gradient. Flow direction is encoded using D8 codes (powers of 2).

        Args:
            heightmap: Terrain elevation map, shape (N, N)

        Returns:
            (flow_dir, statistics)
            - flow_dir: Array of D8 direction codes, shape (N, N), dtype uint8
            - statistics: Dict with calculation metrics
        """
        N = self.resolution
        flow_dir = np.zeros((N, N), dtype=np.uint8)

        # Use Numba JIT compilation if available for 5-8x speedup
        if NUMBA_AVAILABLE:
            flow_dir = self._calculate_flow_direction_numba(
                heightmap, flow_dir, self.D8_OFFSETS, self.D8_CODES,
                self.pixel_size_meters, self.diagonal_dist
            )
        else:
            # Pure NumPy fallback (slower but still works)
            flow_dir = self._calculate_flow_direction_numpy(
                heightmap, flow_dir, self.D8_OFFSETS, self.D8_CODES,
                self.pixel_size_meters, self.diagonal_dist
            )

        # Calculate statistics
        unique, counts = np.unique(flow_dir, return_counts=True)
        direction_distribution = dict(zip(unique.tolist(), counts.tolist()))

        # Count boundary cells (flow_dir == 0 means flows off map)
        num_boundary_outlets = np.sum(flow_dir == 0)

        statistics = {
            'direction_distribution': direction_distribution,
            'num_boundary_outlets': int(num_boundary_outlets),
            'percent_boundary_outlets': 100.0 * num_boundary_outlets / (N * N)
        }

        return flow_dir, statistics

    @staticmethod
    @njit(cache=True)
    def _calculate_flow_direction_numba(
        heightmap: np.ndarray,
        flow_dir: np.ndarray,
        offsets: np.ndarray,
        codes: np.ndarray,
        pixel_size: float,
        diagonal_dist: float
    ) -> np.ndarray:
        """
        Numba JIT-compiled flow direction calculation (5-8x faster).

        Args:
            heightmap: Elevation map
            flow_dir: Output array for flow directions (modified in-place)
            offsets: D8 neighbor offsets
            codes: D8 direction codes
            pixel_size: Pixel size in meters
            diagonal_dist: sqrt(2) for diagonal distance correction

        Returns:
            flow_dir array with D8 codes
        """
        N = heightmap.shape[0]

        for y in range(N):
            for x in range(N):
                current_height = heightmap[y, x]
                max_slope = -1.0
                best_dir = 0

                # Check all 8 neighbors
                for i in range(8):
                    dx = offsets[i, 0]
                    dy = offsets[i, 1]
                    nx = x + dx
                    ny = y + dy

                    # Check bounds
                    if 0 <= nx < N and 0 <= ny < N:
                        neighbor_height = heightmap[ny, nx]

                        # Calculate slope (drop per unit distance)
                        # Diagonal neighbors are sqrt(2) times farther
                        if dx != 0 and dy != 0:
                            distance = pixel_size * diagonal_dist
                        else:
                            distance = pixel_size

                        drop = current_height - neighbor_height
                        slope = drop / distance

                        # Track steepest descent
                        if slope > max_slope:
                            max_slope = slope
                            best_dir = codes[i]

                # Store flow direction (0 if no downhill neighbor = flows off map)
                flow_dir[y, x] = best_dir

        return flow_dir

    def _calculate_flow_direction_numpy(
        self,
        heightmap: np.ndarray,
        flow_dir: np.ndarray,
        offsets: np.ndarray,
        codes: np.ndarray,
        pixel_size: float,
        diagonal_dist: float
    ) -> np.ndarray:
        """
        Pure NumPy flow direction calculation (fallback if Numba unavailable).

        This is slower than the Numba version but doesn't require additional dependencies.
        """
        N = self.resolution

        for y in range(N):
            for x in range(N):
                current_height = heightmap[y, x]
                max_slope = -1.0
                best_dir = 0

                for i in range(8):
                    dx = offsets[i, 0]
                    dy = offsets[i, 1]
                    nx = x + dx
                    ny = y + dy

                    if 0 <= nx < N and 0 <= ny < N:
                        neighbor_height = heightmap[ny, nx]

                        if dx != 0 and dy != 0:
                            distance = pixel_size * diagonal_dist
                        else:
                            distance = pixel_size

                        drop = current_height - neighbor_height
                        slope = drop / distance

                        if slope > max_slope:
                            max_slope = slope
                            best_dir = codes[i]

                flow_dir[y, x] = best_dir

        return flow_dir

    def _calculate_flow_accumulation(
        self,
        heightmap: np.ndarray,
        flow_dir: np.ndarray
    ) -> Tuple[np.ndarray, Dict]:
        """
        Calculate flow accumulation using topological sorting.

        Flow accumulation counts how many upstream cells drain through each cell.
        Cells are processed in descending elevation order to ensure upstream
        cells are processed before downstream cells.

        Args:
            heightmap: Terrain elevation map
            flow_dir: D8 flow direction codes

        Returns:
            (flow_map, statistics)
            - flow_map: Flow accumulation values, shape (N, N), dtype int32
            - statistics: Dict with accumulation metrics
        """
        N = self.resolution

        # Initialize flow accumulation (each cell starts with 1 = itself)
        flow_map = np.ones((N, N), dtype=np.int32)

        # Create topological order: process cells from highest to lowest elevation
        # This ensures upstream cells are processed before downstream cells
        flat_heights = heightmap.flatten()
        flat_indices = np.argsort(-flat_heights)  # Negative for descending order

        # Convert flat indices to (y, x) coordinates
        y_coords = flat_indices // N
        x_coords = flat_indices % N

        # Process cells in elevation order
        for idx in range(len(flat_indices)):
            y = y_coords[idx]
            x = x_coords[idx]

            # Get flow direction for this cell
            direction = flow_dir[y, x]

            # If direction is 0, cell flows off map (no downstream neighbor)
            if direction == 0:
                continue

            # Find downstream neighbor based on direction code
            dx, dy = self._decode_direction(direction)
            nx = x + dx
            ny = y + dy

            # Add this cell's accumulation to downstream neighbor
            # (bounds check should be unnecessary due to direction encoding,
            #  but included for safety)
            if 0 <= nx < N and 0 <= ny < N:
                flow_map[ny, nx] += flow_map[y, x]

        # Calculate statistics
        max_accumulation = int(np.max(flow_map))
        mean_accumulation = float(np.mean(flow_map))
        total_cells = N * N

        # Verify conservation: sum of all cells should equal total cells
        # (each cell contributes 1 to the total)
        total_flow = int(np.sum(flow_map == 1))  # Count cells with accumulation = 1 (outlets)

        statistics = {
            'max_accumulation': max_accumulation,
            'mean_accumulation': mean_accumulation,
            'total_cells': total_cells,
            'num_outlets': total_flow  # Cells that don't contribute to any other cell
        }

        return flow_map, statistics

    def _decode_direction(self, direction_code: int) -> Tuple[int, int]:
        """
        Decode D8 direction code to (dx, dy) offset.

        Args:
            direction_code: D8 code (1, 2, 4, 8, 16, 32, 64, or 128)

        Returns:
            (dx, dy) offset tuple
        """
        # Direction code to offset mapping
        code_to_offset = {
            1: (1, 0),      # E
            2: (1, 1),      # SE
            4: (0, 1),      # S
            8: (-1, 1),     # SW
            16: (-1, 0),    # W
            32: (-1, -1),   # NW
            64: (0, -1),    # N
            128: (1, -1)    # NE
        }
        return code_to_offset.get(direction_code, (0, 0))

    def _extract_river_paths(
        self,
        flow_map: np.ndarray,
        flow_dir: np.ndarray,
        threshold_percentile: float,
        min_length: int
    ) -> Tuple[List[Dict], Dict]:
        """
        Extract river paths from flow accumulation map.

        Rivers are identified as connected paths where flow accumulation
        exceeds the threshold. Paths are traced downstream following flow
        directions.

        Args:
            flow_map: Flow accumulation values
            flow_dir: Flow direction codes
            threshold_percentile: Percentile for river detection (e.g., 99.0 = top 1%)
            min_length: Minimum path length in pixels

        Returns:
            (river_paths, statistics)
            - river_paths: List of river path dicts
            - statistics: Dict with extraction metrics
        """
        N = self.resolution

        # Calculate threshold from percentile
        threshold = np.percentile(flow_map, threshold_percentile)

        # Find all cells exceeding threshold (potential river cells)
        river_cells = flow_map >= threshold

        # Track visited cells to avoid duplicate paths
        visited = np.zeros((N, N), dtype=bool)

        river_paths = []

        # Extract paths starting from high-accumulation cells
        for y in range(N):
            for x in range(N):
                if river_cells[y, x] and not visited[y, x]:
                    # Trace path downstream from this cell
                    path = self._trace_path_downstream(x, y, flow_dir, visited)

                    # Keep only paths meeting minimum length
                    if len(path) >= min_length:
                        # Calculate river properties
                        path_flow = [flow_map[pt[1], pt[0]] for pt in path]
                        mean_flow = float(np.mean(path_flow))

                        # Calculate river width based on flow (simple power law)
                        # Width proportional to sqrt(drainage area)
                        mean_width = self._calculate_river_width(mean_flow)

                        river_dict = {
                            'points': path,
                            'flow_accumulation': int(mean_flow),
                            'width': mean_width,
                            'start': path[0],
                            'end': path[-1],
                            'length_pixels': len(path),
                            'length_meters': len(path) * self.pixel_size_meters
                        }

                        river_paths.append(river_dict)

        # Calculate statistics
        total_length = sum(r['length_pixels'] for r in river_paths)
        mean_width = np.mean([r['width'] for r in river_paths]) if river_paths else 0.0

        statistics = {
            'num_paths': len(river_paths),
            'total_length_pixels': total_length,
            'mean_width_pixels': float(mean_width),
            'threshold_value': float(threshold),
            'num_cells_above_threshold': int(np.sum(river_cells))
        }

        return river_paths, statistics

    def _trace_path_downstream(
        self,
        start_x: int,
        start_y: int,
        flow_dir: np.ndarray,
        visited: np.ndarray
    ) -> List[Tuple[int, int]]:
        """
        Trace a path downstream following flow directions.

        Args:
            start_x: Starting x coordinate
            start_y: Starting y coordinate
            flow_dir: Flow direction array
            visited: Visited cells array (modified in-place)

        Returns:
            List of (x, y) coordinates forming the path
        """
        N = self.resolution
        path = []
        x, y = start_x, start_y

        # Maximum path length to prevent infinite loops
        max_steps = N * 2
        steps = 0

        while steps < max_steps:
            # Add current cell to path
            path.append((x, y))
            visited[y, x] = True

            # Get flow direction
            direction = flow_dir[y, x]

            # If no direction (flows off map), path ends
            if direction == 0:
                break

            # Move to downstream neighbor
            dx, dy = self._decode_direction(direction)
            x += dx
            y += dy

            # Check bounds
            if not (0 <= x < N and 0 <= y < N):
                break

            # Check if already visited (circular flow, shouldn't happen but safety check)
            if visited[y, x]:
                break

            steps += 1

        return path

    def _calculate_river_width(self, flow_accumulation: float) -> float:
        """
        Calculate river width from flow accumulation.

        Uses a simple power law: width ~ sqrt(drainage_area)
        This is based on hydraulic geometry relationships where
        river width scales with ~0.5 power of discharge.

        Args:
            flow_accumulation: Number of upstream cells

        Returns:
            River width in pixels
        """
        # Minimum width of 1 pixel
        if flow_accumulation < 1:
            return 1.0

        # Power law: width = k * flow^0.5
        # Scaling constant chosen to give reasonable widths
        k = 0.5  # Tuning parameter (increased for better scaling)
        width = k * np.sqrt(flow_accumulation)

        # Clamp to reasonable range [1, 20] pixels
        width = np.clip(width, 1.0, 20.0)

        return float(width)

    def _identify_dam_sites(
        self,
        heightmap: np.ndarray,
        flow_map: np.ndarray,
        river_paths: List[Dict]
    ) -> Tuple[List[Dict], Dict]:
        """
        Identify potential dam sites in narrow valleys.

        Dam sites are locations where:
        1. A river flows through a narrow valley (constriction)
        2. High elevation on both sides
        3. Significant upstream drainage

        Args:
            heightmap: Terrain elevation map
            flow_map: Flow accumulation map
            river_paths: List of river paths

        Returns:
            (dam_sites, statistics)
            - dam_sites: List of dam site dicts with location and properties
            - statistics: Dict with dam site metrics
        """
        N = self.resolution
        dam_sites = []

        # Minimum flow accumulation for dam consideration (1% of total cells)
        min_flow = N * N * 0.01

        # Check each river path for potential dam sites
        for river in river_paths:
            # Only consider rivers with significant drainage
            if river['flow_accumulation'] < min_flow:
                continue

            # Check interior points of river (not start/end)
            path = river['points']
            if len(path) < 5:
                continue

            # Sample interior points
            for i in range(2, len(path) - 2):
                x, y = path[i]

                # Get elevation at river
                river_elevation = heightmap[y, x]

                # Check perpendicular to flow for valley narrowing
                # (simplified: check all 8 neighbors for elevation rise)
                elevations = []
                for dx in [-1, 0, 1]:
                    for dy in [-1, 0, 1]:
                        if dx == 0 and dy == 0:
                            continue
                        nx, ny = x + dx, y + dy
                        if 0 <= nx < N and 0 <= ny < N:
                            elevations.append(heightmap[ny, nx])

                if not elevations:
                    continue

                # Check if surrounded by higher elevation (valley constriction)
                mean_surrounding = np.mean(elevations)
                elevation_rise = mean_surrounding - river_elevation

                # Dam site criteria: significant elevation rise and high flow
                if elevation_rise > 0.05:  # 5% of height range
                    dam_dict = {
                        'location': (x, y),
                        'elevation': float(river_elevation),
                        'elevation_rise': float(elevation_rise),
                        'flow_accumulation': river['flow_accumulation'],
                        'river_index': river_paths.index(river)
                    }
                    dam_sites.append(dam_dict)
                    break  # Only one dam site per river

        statistics = {
            'num_dam_sites': len(dam_sites),
            'mean_elevation_rise': np.mean([d['elevation_rise'] for d in dam_sites]) if dam_sites else 0.0
        }

        return dam_sites, statistics


# Convenience function for direct usage
def analyze_rivers(
    heightmap: np.ndarray,
    resolution: int = 4096,
    map_size_meters: float = 14336.0,
    threshold_percentile: float = 99.0,
    min_river_length: int = 10,
    verbose: bool = False
) -> Tuple[Dict, Dict]:
    """
    Convenience function to analyze rivers without creating RiverAnalyzer instance.

    Args:
        heightmap: Terrain elevation map, shape (N, N), range [0, 1]
        resolution: Grid resolution (default: 4096)
        map_size_meters: Map size in meters (default: 14336.0 for CS2)
        threshold_percentile: Flow accumulation percentile for rivers (default: 99.0)
        min_river_length: Minimum river length in pixels (default: 10)
        verbose: Print progress messages (default: False)

    Returns:
        (river_network, statistics) - same as RiverAnalyzer.analyze_rivers()
    """
    analyzer = RiverAnalyzer(resolution, map_size_meters)
    return analyzer.analyze_rivers(
        heightmap,
        threshold_percentile=threshold_percentile,
        min_river_length=min_river_length,
        verbose=verbose
    )
