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

    def generate_color_scale_legend(self,
                                   colormap: str = 'terrain',
                                   width: int = 30,
                                   height: int = 200,
                                   show_labels: bool = True,
                                   height_scale_meters: Optional[float] = None) -> np.ndarray:
        """
        Generate a vertical color scale legend showing elevation colors.

        Args:
            colormap: Color scheme to use ('terrain', 'elevation', 'grayscale')
            width: Width of legend bar in pixels
            height: Height of legend bar in pixels
            show_labels: Add elevation labels to the legend
            height_scale_meters: Real height scale for labels (default: self.height_scale)

        Returns:
            RGB image array with legend (includes labels if show_labels=True)

        Why a legend is essential:
        - Users need to know what colors represent what elevations
        - Standard practice in all mapping software
        - Enables quantitative interpretation of terrain
        """
        if height_scale_meters is None:
            height_scale_meters = self.height_scale

        # Create vertical gradient (high elevation at top, low at bottom)
        gradient = np.linspace(1.0, 0.0, height)[:, np.newaxis]
        gradient = np.repeat(gradient, width, axis=1)

        # Create temporary preview generator with gradient
        temp_heightmap = gradient
        temp_gen = PreviewGenerator(temp_heightmap, height_scale_meters)

        # Apply the same colormap
        legend_colors = temp_gen.apply_colormap(colormap=colormap, min_height=0.0, max_height=1.0)

        if show_labels:
            # Add labels: will be added by the GUI overlay
            # For now, just return the color bar
            # Labels are added by draw_legend_with_labels() in the GUI
            pass

        return legend_colors

    def draw_legend_with_labels(self,
                               preview_image: np.ndarray,
                               colormap: str = 'terrain',
                               position: str = 'right',
                               height_scale_meters: Optional[float] = None) -> np.ndarray:
        """
        Draw color scale legend with labels on the preview image.

        Args:
            preview_image: Base preview image (RGB array)
            colormap: Color scheme used in preview
            position: 'right', 'left', 'top', 'bottom'
            height_scale_meters: Real height scale for labels

        Returns:
            Preview image with legend overlay

        Legend design:
        - Semi-transparent background for legend area
        - Color gradient bar showing elevation colors
        - Text labels at key elevations (0m, 1000m, 2000m, etc.)
        - Positioned to not obscure terrain details
        """
        from PIL import Image, ImageDraw, ImageFont

        if height_scale_meters is None:
            height_scale_meters = self.height_scale

        # Convert to PIL Image for drawing
        img = Image.fromarray(preview_image)
        draw = ImageDraw.Draw(img, 'RGBA')

        # Legend dimensions
        legend_width = 60
        legend_height = 250
        margin = 20

        # Position legend
        img_height, img_width = preview_image.shape[:2]

        if position == 'right':
            legend_x = img_width - legend_width - margin
            legend_y = margin
        elif position == 'left':
            legend_x = margin
            legend_y = margin
        elif position == 'bottom':
            legend_x = img_width - legend_width - margin
            legend_y = img_height - legend_height - margin
        else:  # top
            legend_x = img_width - legend_width - margin
            legend_y = margin

        # Draw semi-transparent background
        background_padding = 10
        draw.rectangle(
            [legend_x - background_padding, legend_y - background_padding,
             legend_x + legend_width + background_padding + 80,
             legend_y + legend_height + background_padding],
            fill=(255, 255, 255, 200)
        )

        # Generate color scale legend
        legend_colors = self.generate_color_scale_legend(
            colormap=colormap,
            width=30,
            height=legend_height,
            show_labels=False,
            height_scale_meters=height_scale_meters
        )

        # Paste legend colors
        legend_img = Image.fromarray(legend_colors)
        img.paste(legend_img, (legend_x, legend_y))

        # Add labels
        try:
            # Try to use a nice font
            font = ImageFont.truetype("arial.ttf", 12)
        except:
            # Fallback to default
            font = ImageFont.load_default()

        # Draw elevation labels
        num_labels = 5
        for i in range(num_labels):
            # Calculate elevation for this label
            fraction = i / (num_labels - 1)  # 0.0 to 1.0
            elevation_meters = height_scale_meters * (1.0 - fraction)  # High at top

            # Position for label
            label_y = legend_y + int(fraction * legend_height)
            label_x = legend_x + 35

            # Format elevation
            if elevation_meters >= 1000:
                label_text = f"{elevation_meters/1000:.1f}km"
            else:
                label_text = f"{int(elevation_meters)}m"

            # Draw label with shadow for readability
            draw.text((label_x + 1, label_y - 6 + 1), label_text, fill=(0, 0, 0, 180), font=font)
            draw.text((label_x, label_y - 6), label_text, fill=(0, 0, 0, 255), font=font)

        # Add title
        try:
            title_font = ImageFont.truetype("arial.ttf", 10)
        except:
            title_font = font

        title = "Elevation"
        title_bbox = draw.textbbox((0, 0), title, font=title_font)
        title_width = title_bbox[2] - title_bbox[0]
        title_x = legend_x + (legend_width - title_width) // 2
        title_y = legend_y - 18

        draw.text((title_x + 1, title_y + 1), title, fill=(0, 0, 0, 180), font=title_font)
        draw.text((title_x, title_y), title, fill=(0, 0, 0, 255), font=title_font)

        return np.array(img)

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
