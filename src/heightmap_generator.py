"""
CS2 Heightmap Generator - Core Module

This module provides the core functionality for generating Cities Skylines 2 compatible heightmaps.
CS2 requires 4096x4096 pixel, 16-bit grayscale PNG images where each pixel represents elevation.

Key Specifications:
- Resolution: 4096x4096 pixels (playable area)
- Format: 16-bit grayscale PNG
- Height Scale: Default 4096 meters (0 = lowest, 4096 = highest)
- Bit Depth: 16-bit allows 65,536 discrete elevation levels
"""

import numpy as np
from PIL import Image
from typing import Tuple, Optional, Callable
import os


class HeightmapGenerator:
    """
    Main class for generating CS2-compatible heightmaps.

    The heightmap is stored as a normalized float array (0.0 to 1.0) internally,
    then converted to 16-bit when exporting. This allows for easier manipulation
    and ensures precision isn't lost during generation.
    """

    # CS2 Standard specifications
    PLAYABLE_RESOLUTION = 4096  # pixels
    WORLD_RESOLUTION = 4096     # pixels (can be same or larger)
    DEFAULT_HEIGHT_SCALE = 4096  # meters
    BIT_DEPTH = 16
    MAX_VALUE = (2 ** BIT_DEPTH) - 1  # 65535 for 16-bit

    def __init__(self,
                 resolution: int = PLAYABLE_RESOLUTION,
                 height_scale: float = DEFAULT_HEIGHT_SCALE,
                 seed: Optional[int] = None):
        """
        Initialize the heightmap generator.

        Args:
            resolution: Size of the heightmap in pixels (default: 4096x4096)
            height_scale: Maximum height in meters (default: 4096m)
            seed: Random seed for reproducible generation (optional)

        Why normalize internally?
        Working with 0.0-1.0 float values makes mathematical operations
        (smoothing, blending, erosion) much easier than working with
        16-bit integers. We only convert to 16-bit at export time.
        """
        self.resolution = resolution
        self.height_scale = height_scale
        self.seed = seed

        if seed is not None:
            np.random.seed(seed)

        # Initialize empty heightmap (normalized 0.0 to 1.0)
        self.heightmap = np.zeros((resolution, resolution), dtype=np.float64)

    def set_height_data(self, data: np.ndarray) -> None:
        """
        Set the heightmap from a numpy array.

        Args:
            data: 2D numpy array of height values

        The input data is automatically normalized to 0.0-1.0 range.
        This allows importing data from any source (DEM files, etc.)
        without worrying about the original value range.
        """
        if data.shape != (self.resolution, self.resolution):
            raise ValueError(f"Data must be {self.resolution}x{self.resolution}, got {data.shape}")

        # Normalize to 0.0-1.0 range
        data_min = np.min(data)
        data_max = np.max(data)

        if data_max - data_min > 0:
            self.heightmap = (data - data_min) / (data_max - data_min)
        else:
            self.heightmap = np.zeros_like(data, dtype=np.float64)

    def get_height_data(self) -> np.ndarray:
        """
        Get the current heightmap data (normalized 0.0 to 1.0).

        Returns:
            2D numpy array of normalized height values
        """
        return self.heightmap.copy()

    def apply_function(self, func: Callable[[np.ndarray], np.ndarray]) -> None:
        """
        Apply a custom function to the heightmap data.

        Args:
            func: Function that takes and returns a 2D numpy array

        This allows for custom transformations like erosion simulation,
        thermal weathering, or artistic adjustments.
        """
        self.heightmap = func(self.heightmap)
        # Re-normalize after function application
        self.heightmap = np.clip(self.heightmap, 0.0, 1.0)

    def create_flat(self, height: float = 0.5) -> None:
        """
        Create a flat heightmap at specified height.

        Args:
            height: Height value from 0.0 (lowest) to 1.0 (highest)

        Useful as a base layer for additive terrain generation.
        """
        self.heightmap.fill(height)

    def create_gradient(self,
                       start_height: float = 0.0,
                       end_height: float = 1.0,
                       direction: str = 'vertical') -> None:
        """
        Create a linear gradient heightmap.

        Args:
            start_height: Starting height (0.0 to 1.0)
            end_height: Ending height (0.0 to 1.0)
            direction: 'vertical', 'horizontal', or 'diagonal'

        Gradients are useful for creating slopes, valleys, or as base
        layers for more complex terrain.
        """
        if direction == 'vertical':
            gradient = np.linspace(start_height, end_height, self.resolution)
            self.heightmap = np.tile(gradient, (self.resolution, 1)).T
        elif direction == 'horizontal':
            gradient = np.linspace(start_height, end_height, self.resolution)
            self.heightmap = np.tile(gradient, (self.resolution, 1))
        elif direction == 'diagonal':
            x = np.linspace(start_height, end_height, self.resolution)
            y = np.linspace(start_height, end_height, self.resolution)
            xx, yy = np.meshgrid(x, y)
            self.heightmap = (xx + yy) / 2.0
        else:
            raise ValueError("Direction must be 'vertical', 'horizontal', or 'diagonal'")

    def add_circle(self,
                   center_x: float,
                   center_y: float,
                   radius: float,
                   height: float,
                   blend: bool = True) -> None:
        """
        Add a circular hill or depression.

        Args:
            center_x: X coordinate (0.0 to 1.0, as fraction of width)
            center_y: Y coordinate (0.0 to 1.0, as fraction of height)
            radius: Radius (0.0 to 1.0, as fraction of map size)
            height: Height modifier (-1.0 to 1.0)
            blend: If True, smooth falloff; if False, sharp edges

        This creates natural-looking hills or craters. The blend option
        uses a smooth cosine falloff for realistic terrain.
        """
        cx = int(center_x * self.resolution)
        cy = int(center_y * self.resolution)
        r = int(radius * self.resolution)

        y, x = np.ogrid[-cy:self.resolution-cy, -cx:self.resolution-cx]
        distance = np.sqrt(x*x + y*y)

        if blend:
            # Smooth cosine falloff for natural appearance
            mask = np.where(distance <= r,
                          (np.cos(distance / r * np.pi) + 1) / 2,
                          0)
        else:
            # Sharp circular edge
            mask = np.where(distance <= r, 1, 0)

        self.heightmap += mask * height
        self.heightmap = np.clip(self.heightmap, 0.0, 1.0)

    def smooth(self, iterations: int = 1, kernel_size: int = 3) -> None:
        """
        Apply smoothing to reduce sharp edges.

        Args:
            iterations: Number of smoothing passes
            kernel_size: Size of smoothing kernel (3, 5, 7, etc.)

        CS2's terrain renderer works best with smooth transitions.
        This uses a simple box blur for efficiency. Multiple iterations
        create more aggressive smoothing.
        """
        from scipy import ndimage

        for _ in range(iterations):
            self.heightmap = ndimage.uniform_filter(self.heightmap, size=kernel_size)

    def normalize_range(self, min_height: float = 0.0, max_height: float = 1.0) -> None:
        """
        Normalize heightmap to specific range.

        Args:
            min_height: Minimum height (0.0 to 1.0)
            max_height: Maximum height (0.0 to 1.0)

        Useful for ensuring your terrain uses the full height range,
        or for constraining it to a specific elevation band.
        """
        current_min = np.min(self.heightmap)
        current_max = np.max(self.heightmap)

        if current_max - current_min > 0:
            # First normalize to 0-1
            normalized = (self.heightmap - current_min) / (current_max - current_min)
            # Then scale to desired range
            self.heightmap = normalized * (max_height - min_height) + min_height
        else:
            self.heightmap.fill(min_height)

    def to_16bit_array(self) -> np.ndarray:
        """
        Convert normalized heightmap to 16-bit unsigned integer array.

        Returns:
            2D numpy array of uint16 values (0 to 65535)

        This is the final conversion step before export. CS2 interprets
        these values linearly: 0 = lowest elevation, 65535 = highest.
        """
        return (self.heightmap * self.MAX_VALUE).astype(np.uint16)

    def export_png(self, filepath: str) -> None:
        """
        Export heightmap as 16-bit grayscale PNG.

        Args:
            filepath: Output file path (should end in .png)

        CS2 requires PNG format with 16-bit depth. TIFF is also supported
        but PNG is more universal and has better tool support.
        """
        # Convert to 16-bit
        data_16bit = self.to_16bit_array()

        # Create PIL Image in 16-bit mode ('I;16')
        # Mode 'I;16' is 16-bit unsigned integer
        img = Image.fromarray(data_16bit, mode='I;16')

        # Ensure directory exists
        os.makedirs(os.path.dirname(filepath) if os.path.dirname(filepath) else '.', exist_ok=True)

        # Save as PNG
        img.save(filepath, format='PNG')

        print(f"Exported heightmap to: {filepath}")
        print(f"  Resolution: {self.resolution}x{self.resolution}")
        print(f"  Height Scale: {self.height_scale}m")
        print(f"  Min elevation: 0m")
        print(f"  Max elevation: {self.height_scale}m")

    def get_statistics(self) -> dict:
        """
        Get statistical information about the heightmap.

        Returns:
            Dictionary with min, max, mean, std elevation in meters

        Useful for understanding the terrain characteristics and
        ensuring it meets design requirements.
        """
        return {
            'min_elevation_m': 0.0,
            'max_elevation_m': self.height_scale,
            'mean_elevation_m': float(np.mean(self.heightmap) * self.height_scale),
            'std_elevation_m': float(np.std(self.heightmap) * self.height_scale),
            'min_normalized': float(np.min(self.heightmap)),
            'max_normalized': float(np.max(self.heightmap)),
            'mean_normalized': float(np.mean(self.heightmap)),
        }

    def import_png(self, filepath: str) -> None:
        """
        Import an existing heightmap from PNG file.

        Args:
            filepath: Path to PNG file

        This allows importing heightmaps from external tools or previous
        exports for further modification.
        """
        img = Image.open(filepath)

        # Convert to numpy array
        if img.mode == 'I;16':
            data = np.array(img, dtype=np.uint16)
        elif img.mode in ('L', 'I'):
            data = np.array(img)
        else:
            img = img.convert('L')
            data = np.array(img)

        # Resize if needed
        if data.shape != (self.resolution, self.resolution):
            img_resized = Image.fromarray(data).resize((self.resolution, self.resolution), Image.LANCZOS)
            data = np.array(img_resized)

        # Normalize to 0.0-1.0
        self.set_height_data(data.astype(np.float64))
