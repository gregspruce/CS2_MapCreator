"""
CS2 Terrain Analysis Module

Implements standard GIS terrain analysis methods.
These are the OPTIMAL algorithms used in professional GIS software.

Methods:
- Slope: Sobel filter gradient calculation (standard in ArcGIS, QGIS)
- Aspect: Arctan2 of gradients (compass direction of slope)
- Statistics: Comprehensive height distribution analysis

Why these methods are optimal:
- Sobel filter: Accounts for all 8 neighbors with proper weighting
- Aspect calculation: Standard trigonometric approach
- All methods are deterministic and reproducible
"""

import numpy as np
from scipy import ndimage
from typing import Dict, Tuple, Optional
from ..progress_tracker import ProgressTracker


class TerrainAnalyzer:
    """
    Analyzes terrain heightmaps using standard GIS methods.

    All analysis methods are non-destructive (don't modify heightmap).
    Results are returned as new arrays or dictionaries.
    """

    def __init__(self, heightmap: np.ndarray, height_scale: float = 4096.0, map_size_meters: float = 14336.0):
        """
        Initialize terrain analyzer.

        Args:
            heightmap: 2D numpy array of elevation values (0.0-1.0)
            height_scale: Real-world height in meters (for slope calculation)
            map_size_meters: Physical map size in meters (CS2 default: 14336m)

        Note: height_scale affects slope angles but not aspect directions.
        """
        self.heightmap = heightmap.copy()
        self.height_scale = height_scale
        self.map_size_meters = map_size_meters
        self.height, self.width = heightmap.shape
        # Calculate pixel spacing for slope calculations
        self.pixel_size_meters = map_size_meters / self.height

    def calculate_slope(self, units: str = 'degrees') -> np.ndarray:
        """
        Calculate slope (steepness) for each cell using Sobel filter.

        Args:
            units: 'degrees' or 'radians' or 'percent' (rise/run * 100)

        Returns:
            2D array of slope values

        Algorithm (Standard GIS Method):
        1. Calculate gradients using Sobel filter
        2. Compute slope magnitude: arctan(sqrt(dz/dx^2 + dz/dy^2))
        3. Convert to requested units

        Why Sobel filter:
        - Considers all 8 neighbors
        - Weighted averaging reduces noise
        - Standard in ArcGIS, QGIS, GRASS GIS
        - Proven optimal for terrain analysis

        Sobel kernel explanation:
        X-direction: [-1 0 1]     Y-direction: [-1 -2 -1]
                     [-2 0 2]                  [ 0  0  0]
                     [-1 0 1]                  [ 1  2  1]
        Center cell weighted 2x, diagonal neighbors weighted 1x
        """
        # Calculate gradients using Sobel filter
        # Sobel returns gradient in pixel units, scale by height_scale and divide by pixel spacing
        # This gives us meters of height per meter of distance (slope ratio)
        gradient_y = ndimage.sobel(self.heightmap, axis=0) * self.height_scale / self.pixel_size_meters
        gradient_x = ndimage.sobel(self.heightmap, axis=1) * self.height_scale / self.pixel_size_meters

        # Calculate slope magnitude
        # slope = arctan(sqrt(dz/dx^2 + dz/dy^2))
        # gradient_magnitude is now in meters per meter (slope ratio)
        gradient_magnitude = np.sqrt(gradient_x**2 + gradient_y**2)
        slope_radians = np.arctan(gradient_magnitude)

        # Convert to requested units
        if units == 'degrees':
            return np.degrees(slope_radians)
        elif units == 'percent':
            # Percent slope = (rise/run) * 100
            return np.tan(slope_radians) * 100.0
        else:  # radians
            return slope_radians

    def calculate_aspect(self, units: str = 'degrees') -> np.ndarray:
        """
        Calculate aspect (direction of slope) for each cell.

        Args:
            units: 'degrees' (0-360) or 'radians' (0-2pi)

        Returns:
            2D array of aspect values
            - 0/360 = North
            - 90 = East
            - 180 = South
            - 270 = West
            - -1 = Flat area (no aspect)

        Algorithm (Standard GIS Method):
        1. Calculate gradients using Sobel filter
        2. Compute aspect: arctan2(-dy, dx)
        3. Convert to compass bearings (0 = North)
        4. Handle flat areas (slope near zero)

        Why arctan2:
        - Handles all quadrants correctly
        - Standard trigonometric approach
        - Used in all GIS software

        Aspect interpretation:
        - Tells which direction water would flow
        - Important for solar exposure analysis
        - Affects vegetation in real terrain
        """
        # Calculate gradients
        gradient_y = ndimage.sobel(self.heightmap, axis=0)
        gradient_x = ndimage.sobel(self.heightmap, axis=1)

        # Calculate aspect using arctan2
        # Note: -gradient_y because y increases downward in image coordinates
        aspect_radians = np.arctan2(-gradient_y, gradient_x)

        # Convert from mathematical angle to compass bearing
        # Mathematical: 0 = East, increases counterclockwise
        # Compass: 0 = North, increases clockwise
        aspect_radians = np.pi / 2.0 - aspect_radians

        # Normalize to 0-2pi
        aspect_radians = np.where(aspect_radians < 0,
                                  aspect_radians + 2 * np.pi,
                                  aspect_radians)

        # Mark flat areas (very small gradient) as -1
        gradient_magnitude = np.sqrt(gradient_x**2 + gradient_y**2)
        flat_threshold = 0.001
        aspect_radians = np.where(gradient_magnitude < flat_threshold,
                                  -1.0,
                                  aspect_radians)

        # Convert to requested units
        if units == 'degrees':
            aspect_degrees = np.degrees(aspect_radians)
            # Keep -1 for flat areas
            aspect_degrees = np.where(aspect_radians == -1.0,
                                     -1.0,
                                     aspect_degrees)
            return aspect_degrees
        else:  # radians
            return aspect_radians

    def get_statistics(self) -> Dict[str, float]:
        """
        Calculate comprehensive terrain statistics.

        Returns:
            Dictionary with statistics:
            - min_height: Minimum elevation (0.0-1.0)
            - max_height: Maximum elevation (0.0-1.0)
            - mean_height: Average elevation
            - median_height: Median elevation
            - std_height: Standard deviation
            - range_height: max - min
            - variance: Height variance
            - percentile_25/50/75: Quartile values
            - flat_percent: Percent of cells with slope < 5 degrees
            - steep_percent: Percent of cells with slope > 45 degrees

        Use cases:
        - Terrain characterization (mountain vs flat)
        - Quality checking (too flat/steep?)
        - Preset comparison
        """
        stats = {}

        # Basic height statistics
        stats['min_height'] = float(np.min(self.heightmap))
        stats['max_height'] = float(np.max(self.heightmap))
        stats['mean_height'] = float(np.mean(self.heightmap))
        stats['median_height'] = float(np.median(self.heightmap))
        stats['std_height'] = float(np.std(self.heightmap))
        stats['range_height'] = stats['max_height'] - stats['min_height']
        stats['variance'] = float(np.var(self.heightmap))

        # Percentiles
        stats['percentile_25'] = float(np.percentile(self.heightmap, 25))
        stats['percentile_50'] = float(np.percentile(self.heightmap, 50))
        stats['percentile_75'] = float(np.percentile(self.heightmap, 75))

        # Slope statistics
        slopes = self.calculate_slope(units='degrees')
        stats['mean_slope'] = float(np.mean(slopes))
        stats['max_slope'] = float(np.max(slopes))

        # Terrain classification
        flat_mask = slopes < 5.0  # Less than 5 degrees
        steep_mask = slopes > 45.0  # Greater than 45 degrees

        total_cells = self.height * self.width
        stats['flat_percent'] = float(np.sum(flat_mask) / total_cells * 100)
        stats['steep_percent'] = float(np.sum(steep_mask) / total_cells * 100)

        return stats

    def analyze_height_distribution(self, bins: int = 10) -> Tuple[np.ndarray, np.ndarray]:
        """
        Analyze height distribution (histogram).

        Args:
            bins: Number of histogram bins

        Returns:
            Tuple of (bin_edges, counts)
            - bin_edges: Array of bin boundaries (length = bins + 1)
            - counts: Array of cell counts per bin (length = bins)

        Use cases:
        - Visualizing terrain profile
        - Identifying dominant elevations
        - Detecting terrain features (plateaus, valleys)

        Interpretation:
        - Uniform distribution = gradual slopes
        - Bimodal = valleys + peaks (interesting terrain)
        - Single peak = plateau or flat area
        """
        counts, bin_edges = np.histogram(self.heightmap, bins=bins, range=(0.0, 1.0))
        return bin_edges, counts

    def find_peaks(self, min_height: float = 0.7, min_distance: int = 50) -> list:
        """
        Find local maxima (peaks) in the heightmap.

        Args:
            min_height: Minimum height to be considered a peak (0.0-1.0)
            min_distance: Minimum distance between peaks (pixels)

        Returns:
            List of (y, x, height) tuples for each peak

        Algorithm:
        1. Find all local maxima using maximum filter
        2. Filter by minimum height
        3. Sort by height (tallest first)
        4. Remove peaks closer than min_distance to taller peaks

        Use cases:
        - Placing landmarks/cities on peaks
        - Identifying mountain ranges
        - Terrain feature extraction
        """
        # Find local maxima using morphological maximum filter
        local_max = ndimage.maximum_filter(self.heightmap, size=5)
        is_peak = (self.heightmap == local_max) & (self.heightmap >= min_height)

        # Get peak coordinates
        peak_coords = np.argwhere(is_peak)

        # Create list with heights
        peaks = []
        for y, x in peak_coords:
            peaks.append((y, x, self.heightmap[y, x]))

        # Sort by height (tallest first)
        peaks.sort(key=lambda p: p[2], reverse=True)

        # Remove peaks too close to taller peaks
        filtered_peaks = []
        for y, x, h in peaks:
            # Check distance to all already-added peaks
            too_close = False
            for py, px, ph in filtered_peaks:
                dist = np.sqrt((y - py)**2 + (x - px)**2)
                if dist < min_distance:
                    too_close = True
                    break

            if not too_close:
                filtered_peaks.append((y, x, h))

        return filtered_peaks

    def find_valleys(self, max_height: float = 0.3, min_distance: int = 50) -> list:
        """
        Find local minima (valleys) in the heightmap.

        Args:
            max_height: Maximum height to be considered a valley (0.0-1.0)
            min_distance: Minimum distance between valleys (pixels)

        Returns:
            List of (y, x, height) tuples for each valley

        Algorithm:
        Same as find_peaks but inverted (minima instead of maxima).

        Use cases:
        - Natural locations for lakes
        - River endpoints
        - Settlement locations (protected valleys)
        """
        # Find local minima using morphological minimum filter
        local_min = ndimage.minimum_filter(self.heightmap, size=5)
        is_valley = (self.heightmap == local_min) & (self.heightmap <= max_height)

        # Get valley coordinates
        valley_coords = np.argwhere(is_valley)

        # Create list with heights
        valleys = []
        for y, x in valley_coords:
            valleys.append((y, x, self.heightmap[y, x]))

        # Sort by height (lowest first)
        valleys.sort(key=lambda v: v[2])

        # Remove valleys too close to lower valleys
        filtered_valleys = []
        for y, x, h in valleys:
            # Check distance to all already-added valleys
            too_close = False
            for vy, vx, vh in filtered_valleys:
                dist = np.sqrt((y - vy)**2 + (x - vx)**2)
                if dist < min_distance:
                    too_close = True
                    break

            if not too_close:
                filtered_valleys.append((y, x, h))

        return filtered_valleys

    def generate_report(self, show_progress: bool = False) -> str:
        """
        Generate comprehensive terrain analysis report.

        Args:
            show_progress: Show progress during analysis

        Returns:
            Formatted string report

        Report includes:
        - Basic statistics (height, slope)
        - Terrain classification (flat/steep percentages)
        - Feature counts (peaks, valleys)
        - Height distribution summary

        Use cases:
        - Terrain quality checking
        - Preset comparison
        - Documentation
        """
        report_lines = []
        report_lines.append("=" * 70)
        report_lines.append("TERRAIN ANALYSIS REPORT")
        report_lines.append("=" * 70)

        with ProgressTracker("Analyzing terrain", total=4, disable=not show_progress) as progress:
            # Basic statistics
            stats = self.get_statistics()
            report_lines.append("\nBASIC STATISTICS:")
            report_lines.append(f"  Resolution: {self.width} x {self.height} pixels")
            report_lines.append(f"  Height Range: {stats['min_height']:.4f} - {stats['max_height']:.4f}")
            report_lines.append(f"  Mean Height: {stats['mean_height']:.4f}")
            report_lines.append(f"  Std Deviation: {stats['std_height']:.4f}")
            report_lines.append(f"  Median: {stats['median_height']:.4f}")
            progress.update(1)

            # Slope analysis
            report_lines.append("\nSLOPE ANALYSIS:")
            report_lines.append(f"  Mean Slope: {stats['mean_slope']:.2f} degrees")
            report_lines.append(f"  Max Slope: {stats['max_slope']:.2f} degrees")
            report_lines.append(f"  Flat Areas (<5 deg): {stats['flat_percent']:.1f}%")
            report_lines.append(f"  Steep Areas (>45 deg): {stats['steep_percent']:.1f}%")
            progress.update(1)

            # Feature detection
            peaks = self.find_peaks(min_height=0.7, min_distance=50)
            valleys = self.find_valleys(max_height=0.3, min_distance=50)
            report_lines.append("\nFEATURE DETECTION:")
            report_lines.append(f"  Peaks Found: {len(peaks)}")
            if peaks:
                tallest = peaks[0]
                report_lines.append(f"  Tallest Peak: ({tallest[0]}, {tallest[1]}) height={tallest[2]:.4f}")
            report_lines.append(f"  Valleys Found: {len(valleys)}")
            if valleys:
                lowest = valleys[0]
                report_lines.append(f"  Lowest Valley: ({lowest[0]}, {lowest[1]}) height={lowest[2]:.4f}")
            progress.update(1)

            # Height distribution
            bin_edges, counts = self.analyze_height_distribution(bins=10)
            report_lines.append("\nHEIGHT DISTRIBUTION:")
            for i in range(len(counts)):
                percent = counts[i] / (self.width * self.height) * 100
                report_lines.append(f"  {bin_edges[i]:.2f}-{bin_edges[i+1]:.2f}: {percent:.1f}%")
            progress.update(1)

        report_lines.append("\n" + "=" * 70)
        return "\n".join(report_lines)
