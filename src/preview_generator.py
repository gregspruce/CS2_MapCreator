"""
CS2 Preview Generation Module

Implements hillshade rendering for terrain visualization.
This is the OPTIMAL method used in all GIS software for terrain display.

Hillshade Algorithm:
- Simulates light source at specified azimuth/altitude
- Calculates how much light each cell receives
- Result: realistic 3D-looking visualization of 2D heightmap

Why hillshade is optimal:
- Standard in ArcGIS, QGIS, GRASS GIS, cartography
- Physically accurate light simulation
- Most intuitive terrain visualization method
- Used in all topographic maps
"""

import numpy as np
from PIL import Image
from typing import Optional, Tuple
from .analysis.terrain_analyzer import TerrainAnalyzer
from .progress_tracker import ProgressTracker


class PreviewGenerator:
    """
    Generates visual previews of heightmaps using hillshade rendering.

    Hillshade creates a grayscale image simulating sunlight on terrain.
    This is the standard visualization method in GIS and cartography.
    """

    def __init__(self, heightmap: np.ndarray, height_scale: float = 4096.0):
        """
        Initialize preview generator.

        Args:
            heightmap: 2D numpy array of elevation values (0.0-1.0)
            height_scale: Real-world height in meters (affects shadow intensity)
        """
        self.heightmap = heightmap.copy()
        self.height_scale = height_scale
        self.height, self.width = heightmap.shape

    def generate_hillshade(self,
                          azimuth: float = 315.0,
                          altitude: float = 45.0,
                          z_factor: float = 1.0) -> np.ndarray:
        """
        Generate hillshade visualization.

        Args:
            azimuth: Light source direction (0-360 degrees, 0=N, 90=E, 180=S, 270=W)
            altitude: Light source angle above horizon (0-90 degrees)
            z_factor: Vertical exaggeration (1.0=none, >1.0=more dramatic)

        Returns:
            2D array of hillshade values (0.0-1.0, darker=shadow, lighter=light)

        Algorithm (Standard GIS Method):
        1. Calculate slope and aspect for each cell
        2. Convert light azimuth/altitude to vector
        3. Calculate dot product of surface normal with light vector
        4. Result = intensity of light at each point

        Why this method:
        - Physically accurate (Lambert's cosine law)
        - Standard in cartography for 100+ years
        - Used in all GIS software
        - Proven optimal for terrain visualization

        Parameter meanings:
        - azimuth 315 (NW) = traditional map lighting
        - altitude 45 = sun halfway up (good shadows)
        - z_factor > 1.0 = exaggerate mountains (for flat terrain)
        """
        # Convert angles to radians
        azimuth_rad = np.radians(azimuth)
        altitude_rad = np.radians(altitude)

        # Calculate slope and aspect
        analyzer = TerrainAnalyzer(self.heightmap, self.height_scale * z_factor)
        slope_rad = analyzer.calculate_slope(units='radians')
        aspect_rad = analyzer.calculate_aspect(units='radians')

        # Handle flat areas (aspect = -1)
        # Flat areas get full lighting
        flat_mask = (aspect_rad == -1.0)
        aspect_rad = np.where(flat_mask, 0.0, aspect_rad)

        # Calculate hillshade using standard formula
        # hillshade = cos(zenith) * cos(slope) + sin(zenith) * sin(slope) * cos(azimuth - aspect)
        # where zenith = 90 - altitude

        zenith_rad = np.pi / 2.0 - altitude_rad

        hillshade = (np.cos(zenith_rad) * np.cos(slope_rad) +
                    np.sin(zenith_rad) * np.sin(slope_rad) *
                    np.cos(azimuth_rad - aspect_rad))

        # Flat areas get full brightness
        hillshade = np.where(flat_mask, 1.0, hillshade)

        # Normalize to 0.0-1.0
        hillshade = np.clip(hillshade, 0.0, 1.0)

        return hillshade

    def apply_colormap(self,
                      colormap: str = 'terrain',
                      min_height: Optional[float] = None,
                      max_height: Optional[float] = None) -> np.ndarray:
        """
        Apply color ramp to heightmap.

        Args:
            colormap: Color scheme name
                     'terrain' = green(low) -> brown(mid) -> white(high)
                     'grayscale' = black(low) -> white(high)
                     'elevation' = blue(low) -> green(mid) -> red(high)
            min_height: Minimum height for color scale (None = auto from data)
            max_height: Maximum height for color scale (None = auto from data)

        Returns:
            RGB image array (height x width x 3) with values 0-255

        Why colormaps matter:
        - Intuitive visualization (blue=water, green=land, white=snow)
        - Standard in topographic maps
        - Easier to interpret than grayscale
        """
        # Normalize heightmap to 0-1 range
        if min_height is None:
            min_height = np.min(self.heightmap)
        if max_height is None:
            max_height = np.max(self.heightmap)

        normalized = np.clip(
            (self.heightmap - min_height) / (max_height - min_height + 1e-10),
            0.0, 1.0
        )

        # Apply colormap
        if colormap == 'terrain':
            # Green -> Brown -> White
            rgb = self._terrain_colormap(normalized)
        elif colormap == 'elevation':
            # Blue -> Green -> Red
            rgb = self._elevation_colormap(normalized)
        else:  # grayscale
            rgb = np.stack([normalized * 255] * 3, axis=-1).astype(np.uint8)

        return rgb

    def _terrain_colormap(self, normalized: np.ndarray) -> np.ndarray:
        """
        Terrain colormap: green (low) -> brown (mid) -> white (high).

        Simulates natural terrain colors:
        - 0.0-0.3: Dark green (lowlands, forests)
        - 0.3-0.6: Light green to brown (hills)
        - 0.6-0.8: Brown (mountains)
        - 0.8-1.0: White (snow peaks)
        """
        rgb = np.zeros((self.height, self.width, 3), dtype=np.uint8)

        # Low elevations (0.0-0.3): Dark green -> Light green
        mask_low = normalized < 0.3
        t = normalized / 0.3
        rgb[mask_low, 0] = (34 + t[mask_low] * (100 - 34)).astype(np.uint8)  # R
        rgb[mask_low, 1] = (139 + t[mask_low] * (180 - 139)).astype(np.uint8)  # G
        rgb[mask_low, 2] = (34 + t[mask_low] * (50 - 34)).astype(np.uint8)  # B

        # Mid elevations (0.3-0.6): Light green -> Brown
        mask_mid = (normalized >= 0.3) & (normalized < 0.6)
        t = (normalized[mask_mid] - 0.3) / 0.3
        rgb[mask_mid, 0] = (100 + t * (139 - 100)).astype(np.uint8)  # R
        rgb[mask_mid, 1] = (180 + t * (115 - 180)).astype(np.uint8)  # G
        rgb[mask_mid, 2] = (50 + t * (85 - 50)).astype(np.uint8)  # B

        # High elevations (0.6-0.8): Brown -> Gray
        mask_high = (normalized >= 0.6) & (normalized < 0.8)
        t = (normalized[mask_high] - 0.6) / 0.2
        rgb[mask_high, 0] = (139 + t * (180 - 139)).astype(np.uint8)  # R
        rgb[mask_high, 1] = (115 + t * (180 - 115)).astype(np.uint8)  # G
        rgb[mask_high, 2] = (85 + t * (180 - 85)).astype(np.uint8)  # B

        # Very high (0.8-1.0): Gray -> White (snow)
        mask_peak = normalized >= 0.8
        t = (normalized[mask_peak] - 0.8) / 0.2
        rgb[mask_peak, 0] = (180 + t * (255 - 180)).astype(np.uint8)  # R
        rgb[mask_peak, 1] = (180 + t * (255 - 180)).astype(np.uint8)  # G
        rgb[mask_peak, 2] = (180 + t * (255 - 180)).astype(np.uint8)  # B

        return rgb

    def _elevation_colormap(self, normalized: np.ndarray) -> np.ndarray:
        """
        Elevation colormap: blue (low) -> green (mid) -> red (high).

        Classic elevation visualization:
        - 0.0-0.33: Blue (water/lowlands)
        - 0.33-0.66: Green (land)
        - 0.66-1.0: Red (peaks)
        """
        rgb = np.zeros((self.height, self.width, 3), dtype=np.uint8)

        # Low: Blue
        mask_low = normalized < 0.33
        t = normalized[mask_low] / 0.33
        rgb[mask_low, 0] = (0 + t * 50).astype(np.uint8)
        rgb[mask_low, 1] = (0 + t * 150).astype(np.uint8)
        rgb[mask_low, 2] = (255 - t * 55).astype(np.uint8)

        # Mid: Green
        mask_mid = (normalized >= 0.33) & (normalized < 0.66)
        t = (normalized[mask_mid] - 0.33) / 0.33
        rgb[mask_mid, 0] = (50 - t * 50).astype(np.uint8)
        rgb[mask_mid, 1] = (150 + t * 55).astype(np.uint8)
        rgb[mask_mid, 2] = (200 - t * 200).astype(np.uint8)

        # High: Red
        mask_high = normalized >= 0.66
        t = (normalized[mask_high] - 0.66) / 0.34
        rgb[mask_high, 0] = (0 + t * 255).astype(np.uint8)
        rgb[mask_high, 1] = (205 - t * 205).astype(np.uint8)
        rgb[mask_high, 2] = (0).astype(np.uint8)

        return rgb

    def blend_hillshade_with_colors(self,
                                    hillshade: np.ndarray,
                                    colors: np.ndarray,
                                    blend_factor: float = 0.5) -> np.ndarray:
        """
        Blend hillshade shadows with color heightmap.

        Args:
            hillshade: Grayscale hillshade array (0.0-1.0)
            colors: RGB color array (0-255)
            blend_factor: How much hillshade to apply (0.0=no shadows, 1.0=full shadows)

        Returns:
            Blended RGB image (0-255)

        Why blending:
        - Colors show elevation
        - Hillshade shows 3D shape
        - Combined: best of both worlds
        - Standard technique in cartography
        """
        # Convert hillshade to 0-255 and expand to 3 channels
        hillshade_rgb = (hillshade[:, :, np.newaxis] * 255).astype(np.uint8)
        hillshade_rgb = np.repeat(hillshade_rgb, 3, axis=2)

        # Blend using multiplicative blending
        # result = colors * (1 - blend_factor + blend_factor * hillshade)
        blend = colors.astype(np.float32) * (1.0 - blend_factor + blend_factor * hillshade[:, :, np.newaxis])
        blend = np.clip(blend, 0, 255).astype(np.uint8)

        return blend

    def generate_thumbnail(self,
                          size: Tuple[int, int] = (512, 512),
                          show_hillshade: bool = True,
                          colormap: str = 'terrain',
                          show_progress: bool = False) -> Image.Image:
        """
        Generate thumbnail preview image.

        Args:
            size: Output size in pixels (width, height)
            show_hillshade: Apply hillshade rendering
            colormap: Color scheme to use
            show_progress: Show progress during generation

        Returns:
            PIL Image object ready to save or display

        Use cases:
        - Quick preview before full generation
        - Gallery thumbnails
        - Documentation images
        """
        with ProgressTracker("Generating preview", total=3, disable=not show_progress) as progress:
            # Generate colored heightmap
            colors = self.apply_colormap(colormap=colormap)
            progress.update(1)

            # Generate hillshade if requested
            if show_hillshade:
                hillshade = self.generate_hillshade()
                colors = self.blend_hillshade_with_colors(hillshade, colors, blend_factor=0.7)
            progress.update(1)

            # Create PIL image and resize
            img = Image.fromarray(colors, mode='RGB')
            img = img.resize(size, Image.Resampling.LANCZOS)
            progress.update(1)

        return img

    def save_preview(self,
                    filename: str,
                    size: Tuple[int, int] = (1024, 1024),
                    show_hillshade: bool = True,
                    colormap: str = 'terrain',
                    quality: int = 95) -> None:
        """
        Generate and save preview image to file.

        Args:
            filename: Output file path (extension determines format)
            size: Output size in pixels
            show_hillshade: Apply hillshade rendering
            colormap: Color scheme
            quality: JPEG quality (1-100, ignored for PNG)

        Supported formats:
        - PNG: Lossless, best quality
        - JPEG: Smaller files, good for web
        - BMP: Uncompressed, largest files
        """
        img = self.generate_thumbnail(size, show_hillshade, colormap, show_progress=True)

        # Save with appropriate parameters
        if filename.lower().endswith('.jpg') or filename.lower().endswith('.jpeg'):
            img.save(filename, 'JPEG', quality=quality)
        else:
            img.save(filename)
