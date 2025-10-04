"""
CS2 Worldmap Generator

This module handles the creation of worldmaps - extended heightmaps that show
terrain beyond the playable area. The worldmap provides visual context and
makes the playable area feel like part of a larger world.

Worldmap Specifications (from CS2 Wiki):
- Resolution: 4096x4096 (same as heightmap)
- Center 1024x1024 area matches the playable heightmap
- Surrounding area shows unplayable terrain
- Format: 16-bit grayscale PNG (same as heightmap)
"""

import numpy as np
from typing import Optional, Tuple
from PIL import Image


class WorldmapGenerator:
    """
    Generates worldmaps that embed playable heightmaps in larger terrain.

    The worldmap gives context to the playable area - for example, if your
    playable map is a valley, the worldmap can show the surrounding mountains.
    This creates better visual continuity when players look toward the map edges.
    """

    def __init__(self,
                 world_resolution: int = 4096,
                 playable_resolution: int = 4096):
        """
        Initialize worldmap generator.

        Args:
            world_resolution: Size of full worldmap (typically 4096)
            playable_resolution: Size of playable area (typically 4096)

        Note: In CS2, both are typically 4096x4096, with the playable area
        scaled down to fit in the center 1024x1024 region of the worldmap.
        """
        self.world_resolution = world_resolution
        self.playable_resolution = playable_resolution

        # CS2 specifies playable area is center 1024x1024 of worldmap
        self.playable_world_size = 1024

        # Initialize empty worldmap
        self.worldmap = np.zeros((world_resolution, world_resolution), dtype=np.float64)

    def embed_playable_heightmap(self,
                                 playable_heightmap: np.ndarray,
                                 blend_radius: int = 50) -> None:
        """
        Embed the playable heightmap into the center of the worldmap.

        Args:
            playable_heightmap: The 4096x4096 playable heightmap
            blend_radius: Pixels to blend at boundary (for smooth transition)

        The playable heightmap is scaled down from 4096x4096 to 1024x1024
        and placed in the center of the worldmap. This creates the correct
        scale relationship specified by CS2.
        """
        # Scale playable heightmap from 4096x4096 to 1024x1024
        from PIL import Image

        playable_img = Image.fromarray((playable_heightmap * 65535).astype(np.uint16), mode='I;16')
        playable_scaled = playable_img.resize((self.playable_world_size, self.playable_world_size),
                                             Image.LANCZOS)
        playable_scaled_array = np.array(playable_scaled, dtype=np.float64) / 65535.0

        # Calculate position to center the playable area
        center_offset = (self.world_resolution - self.playable_world_size) // 2

        # Create a mask for blending at edges
        if blend_radius > 0:
            mask = self._create_blend_mask(self.playable_world_size, blend_radius)

            # Blend the playable area into the worldmap
            world_section = self.worldmap[
                center_offset:center_offset + self.playable_world_size,
                center_offset:center_offset + self.playable_world_size
            ]

            self.worldmap[
                center_offset:center_offset + self.playable_world_size,
                center_offset:center_offset + self.playable_world_size
            ] = playable_scaled_array * mask + world_section * (1 - mask)
        else:
            # Direct placement without blending
            self.worldmap[
                center_offset:center_offset + self.playable_world_size,
                center_offset:center_offset + self.playable_world_size
            ] = playable_scaled_array

    def _create_blend_mask(self, size: int, blend_radius: int) -> np.ndarray:
        """
        Create a mask for smooth edge blending.

        Args:
            size: Size of the mask
            blend_radius: Width of blend zone in pixels

        Returns:
            2D array with smooth falloff at edges

        The blend mask is 1.0 in the center and smoothly transitions to 0.0
        at the edges over the blend_radius distance.
        """
        mask = np.ones((size, size), dtype=np.float64)

        # Create gradients for each edge
        for i in range(blend_radius):
            alpha = i / blend_radius
            mask[i, :] *= alpha  # Top edge
            mask[-(i+1), :] *= alpha  # Bottom edge
            mask[:, i] *= alpha  # Left edge
            mask[:, -(i+1)] *= alpha  # Right edge

        return mask

    def generate_surrounding_terrain(self,
                                    noise_generator,
                                    scale: float = 300.0,
                                    octaves: int = 5,
                                    persistence: float = 0.5,
                                    lacunarity: float = 2.0) -> None:
        """
        Generate procedural terrain for the surrounding unplayable area.

        Args:
            noise_generator: NoiseGenerator instance
            scale: Noise scale (larger = smoother)
            octaves: Number of detail layers
            persistence: Detail falloff
            lacunarity: Detail frequency multiplier

        This creates terrain that extends beyond the playable area, giving
        visual context when players look toward the map boundaries.
        """
        # Generate noise for the entire worldmap
        surrounding = noise_generator.generate_perlin(
            resolution=self.world_resolution,
            scale=scale,
            octaves=octaves,
            persistence=persistence,
            lacunarity=lacunarity
        )

        self.worldmap = surrounding

    def generate_ocean_around_playable(self,
                                      playable_heightmap: np.ndarray,
                                      sea_level: float = 0.3,
                                      shore_width: int = 200) -> None:
        """
        Create an ocean surrounding the playable area.

        Args:
            playable_heightmap: The playable heightmap to embed
            sea_level: Height value for ocean (0.0-1.0)
            shore_width: Width of coastal transition zone

        Creates an island-style map where the playable area is surrounded
        by ocean, with a gradual transition from land to sea.
        """
        # Fill worldmap with ocean
        self.worldmap.fill(sea_level)

        # Embed playable area with coastal blending
        center_offset = (self.world_resolution - self.playable_world_size) // 2

        # Scale playable heightmap to 1024x1024
        from PIL import Image
        playable_img = Image.fromarray((playable_heightmap * 65535).astype(np.uint16), mode='I;16')
        playable_scaled = playable_img.resize((self.playable_world_size, self.playable_world_size),
                                             Image.LANCZOS)
        playable_scaled_array = np.array(playable_scaled, dtype=np.float64) / 65535.0

        # Create coastal gradient
        coastal_mask = self._create_coastal_mask(self.playable_world_size, shore_width, sea_level)

        # Apply coastal gradient to playable heightmap
        playable_with_coast = playable_scaled_array * coastal_mask + sea_level * (1 - coastal_mask)

        # Place in worldmap
        self.worldmap[
            center_offset:center_offset + self.playable_world_size,
            center_offset:center_offset + self.playable_world_size
        ] = playable_with_coast

    def _create_coastal_mask(self,
                            size: int,
                            shore_width: int,
                            sea_level: float) -> np.ndarray:
        """
        Create a radial mask for coastal transitions.

        Args:
            size: Size of the mask
            shore_width: Width of coastal zone
            sea_level: Ocean height level

        Returns:
            Mask with smooth coastal falloff

        This creates a circular mask that transitions from land (1.0) in the
        center to sea level at the edges, creating natural-looking coastlines.
        """
        center = size / 2
        y, x = np.ogrid[0:size, 0:size]
        distance = np.sqrt((x - center)**2 + (y - center)**2)

        # Create smooth transition from land to sea
        land_radius = size / 2 - shore_width
        max_radius = size / 2

        mask = np.ones((size, size), dtype=np.float64)

        # Calculate falloff
        shore_zone = (distance > land_radius) & (distance < max_radius)
        mask[shore_zone] = (max_radius - distance[shore_zone]) / shore_width

        # Beyond max radius = ocean
        mask[distance >= max_radius] = 0.0

        return mask

    def extend_terrain_seamlessly(self,
                                  playable_heightmap: np.ndarray,
                                  noise_generator,
                                  blend_distance: int = 300) -> None:
        """
        Create surrounding terrain that seamlessly extends from playable area.

        Args:
            playable_heightmap: The playable heightmap
            noise_generator: NoiseGenerator instance
            blend_distance: Distance over which to blend with new terrain

        This method creates terrain that naturally continues from the playable
        area's edges, rather than abruptly changing. Great for maps that should
        feel like part of a larger continuous landscape.
        """
        # Generate base surrounding terrain
        self.generate_surrounding_terrain(noise_generator)

        center_offset = (self.world_resolution - self.playable_world_size) // 2

        # Scale playable heightmap
        from PIL import Image
        playable_img = Image.fromarray((playable_heightmap * 65535).astype(np.uint16), mode='I;16')
        playable_scaled = playable_img.resize((self.playable_world_size, self.playable_world_size),
                                             Image.LANCZOS)
        playable_scaled_array = np.array(playable_scaled, dtype=np.float64) / 65535.0

        # Extract edge values from playable area for matching
        top_edge = playable_scaled_array[0, :]
        bottom_edge = playable_scaled_array[-1, :]
        left_edge = playable_scaled_array[:, 0]
        right_edge = playable_scaled_array[:, -1]

        # Calculate average edge height to match surrounding terrain
        avg_edge_height = np.mean([top_edge.mean(), bottom_edge.mean(),
                                   left_edge.mean(), right_edge.mean()])

        # Adjust surrounding terrain to match edge heights
        current_avg = self.worldmap.mean()
        height_adjustment = avg_edge_height - current_avg
        self.worldmap += height_adjustment
        self.worldmap = np.clip(self.worldmap, 0.0, 1.0)

        # Embed playable area with blending
        mask = self._create_blend_mask(self.playable_world_size, blend_distance)

        world_section = self.worldmap[
            center_offset:center_offset + self.playable_world_size,
            center_offset:center_offset + self.playable_world_size
        ]

        self.worldmap[
            center_offset:center_offset + self.playable_world_size,
            center_offset:center_offset + self.playable_world_size
        ] = playable_scaled_array * mask + world_section * (1 - mask)

    def get_worldmap(self) -> np.ndarray:
        """
        Get the current worldmap data (normalized 0.0 to 1.0).

        Returns:
            2D numpy array of normalized height values
        """
        return self.worldmap.copy()

    def export_png(self, filepath: str) -> None:
        """
        Export worldmap as 16-bit grayscale PNG.

        Args:
            filepath: Output file path

        Worldmaps use the same format as heightmaps: 16-bit grayscale PNG.
        """
        import os

        # Convert to 16-bit
        data_16bit = (self.worldmap * 65535).astype(np.uint16)

        # Create PIL Image
        img = Image.fromarray(data_16bit, mode='I;16')

        # Ensure directory exists
        os.makedirs(os.path.dirname(filepath) if os.path.dirname(filepath) else '.', exist_ok=True)

        # Save as PNG
        img.save(filepath, format='PNG')

        print(f"Exported worldmap to: {filepath}")
        print(f"  Resolution: {self.world_resolution}x{self.world_resolution}")
        print(f"  Playable area: center {self.playable_world_size}x{self.playable_world_size}")


def create_worldmap_preset(preset: str,
                           playable_heightmap: np.ndarray,
                           noise_generator,
                           world_resolution: int = 4096) -> WorldmapGenerator:
    """
    Create worldmap using predefined preset configurations.

    Args:
        preset: Preset name ('ocean', 'seamless', 'mountains', 'minimal')
        playable_heightmap: The playable heightmap to embed
        noise_generator: NoiseGenerator instance
        world_resolution: Worldmap resolution

    Returns:
        Configured WorldmapGenerator

    Presets provide quick ways to create different worldmap styles:
    - 'ocean': Surround with water (island map)
    - 'seamless': Extend terrain naturally
    - 'mountains': Surround with mountainous terrain
    - 'minimal': Just embed playable area with minimal surrounding
    """
    worldgen = WorldmapGenerator(world_resolution=world_resolution)

    if preset == 'ocean':
        worldgen.generate_ocean_around_playable(
            playable_heightmap=playable_heightmap,
            sea_level=0.25,
            shore_width=200
        )

    elif preset == 'seamless':
        worldgen.extend_terrain_seamlessly(
            playable_heightmap=playable_heightmap,
            noise_generator=noise_generator,
            blend_distance=250
        )

    elif preset == 'mountains':
        worldgen.generate_surrounding_terrain(
            noise_generator=noise_generator,
            scale=200.0,
            octaves=6,
            persistence=0.6,
            lacunarity=2.0
        )
        worldgen.embed_playable_heightmap(playable_heightmap, blend_radius=100)

    elif preset == 'minimal':
        # Just embed with slight blending
        worldgen.worldmap.fill(0.4)  # Mid-level gray
        worldgen.embed_playable_heightmap(playable_heightmap, blend_radius=50)

    else:
        raise ValueError(f"Unknown preset '{preset}'. Available: ocean, seamless, mountains, minimal")

    return worldgen
