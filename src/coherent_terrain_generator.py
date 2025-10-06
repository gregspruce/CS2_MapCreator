"""
CS2 Heightmap Generator - Coherent Terrain Generation

Generates terrain with proper geological structure:
- Large-scale base defines WHERE features exist (mountain zones vs plains)
- Medium-scale defines mountain RANGES and valley SYSTEMS
- Small-scale adds detail ONLY where appropriate

This creates coherent geography, not random bumps.

Key Concept: MASKING
- Generate high-detail noise
- Mask it with large-scale zones
- Detail only appears in designated areas
- Result: Mountain ranges, not isolated peaks
"""

import numpy as np
from scipy import ndimage
from typing import Dict, Tuple


class CoherentTerrainGenerator:
    """
    Generates geologically coherent terrain with proper structure.

    Philosophy:
    - Large features first (continent shape, mountain zones)
    - Medium features second (mountain ranges, valley systems)
    - Small features last (peaks, ridges - masked to appropriate zones)
    """

    @staticmethod
    def generate_base_geography(
        heightmap: np.ndarray,
        terrain_type: str
    ) -> Tuple[np.ndarray, np.ndarray]:
        """
        Generate base geography: WHERE should mountains/valleys be?

        Returns:
            (base_heights, mountain_mask)
            - base_heights: Large-scale elevation zones (0-1)
            - mountain_mask: Where mountains are allowed (0-1, higher = more mountains)

        This is the KEY to coherent terrain!
        """
        resolution = heightmap.shape[0]

        # Create large-scale base using very low frequency noise
        # This defines continent shape, major elevation zones
        base_scale = resolution * 0.4  # Very large features

        # Generate smooth base using heavy gaussian filtering
        np.random.seed(42)  # Reproducible
        base_noise = np.random.rand(resolution, resolution)
        base_heights = ndimage.gaussian_filter(base_noise, sigma=base_scale)

        # Normalize
        base_heights = (base_heights - base_heights.min()) / (base_heights.max() - base_heights.min())

        # Create mountain mask (where mountains are allowed)
        if terrain_type == 'mountains':
            # Mountains in high areas of base
            mountain_mask = base_heights ** 0.5  # More mountains in high areas

        elif terrain_type == 'hills':
            # Hills everywhere, but varied
            mountain_mask = 0.3 + base_heights * 0.4  # Gentle everywhere

        elif terrain_type == 'islands':
            # Radial falloff for island chain
            center_y, center_x = resolution // 2, resolution // 2
            y, x = np.ogrid[0:resolution, 0:resolution]
            distance = np.sqrt((y - center_y)**2 + (x - center_x)**2)
            max_dist = np.sqrt(2) * resolution / 2
            radial_falloff = 1.0 - np.clip(distance / max_dist, 0, 1)
            mountain_mask = radial_falloff ** 2

        elif terrain_type == 'highlands':
            # High plateau with mountains on edges
            mountain_mask = 0.6 + base_heights * 0.3

        elif terrain_type == 'canyons':
            # Invert - valleys in high areas
            mountain_mask = 1.0 - base_heights

        elif terrain_type == 'mesas':
            # Terraced mask
            terraces = 5
            mountain_mask = np.floor(base_heights * terraces) / terraces

        else:  # flat
            mountain_mask = np.ones_like(base_heights) * 0.1  # Minimal variation

        # Smooth mask for natural transitions
        mountain_mask = ndimage.gaussian_filter(mountain_mask, sigma=resolution * 0.05)

        return base_heights, mountain_mask

    @staticmethod
    def generate_mountain_ranges(
        resolution: int,
        terrain_type: str
    ) -> np.ndarray:
        """
        Generate medium-scale mountain RANGES (not individual peaks).

        Uses elongated/anisotropic noise to create linear features.

        Returns:
            Range structure (0-1) showing where mountain chains run
        """
        # Create directional structure using different scales in X vs Y
        np.random.seed(123)

        if terrain_type in ['mountains', 'highlands']:
            # Elongated ranges (anisotropic scaling)
            noise_x = np.random.rand(resolution, resolution)
            noise_y = np.random.rand(resolution, resolution)

            # Filter with different sigmas for X and Y to create elongated features
            range_x = ndimage.gaussian_filter(noise_x, sigma=(resolution * 0.02, resolution * 0.08))
            range_y = ndimage.gaussian_filter(noise_y, sigma=(resolution * 0.08, resolution * 0.02))

            # Combine to create cross-hatched ranges
            ranges = (range_x + range_y) / 2.0

        elif terrain_type == 'canyons':
            # Strong linear valleys
            noise = np.random.rand(resolution, resolution)
            ranges = ndimage.gaussian_filter(noise, sigma=(resolution * 0.02, resolution * 0.12))

        else:  # hills, islands, etc
            # Isotropic (equal in all directions)
            noise = np.random.rand(resolution, resolution)
            ranges = ndimage.gaussian_filter(noise, sigma=resolution * 0.06)

        # Normalize
        ranges = (ranges - ranges.min()) / (ranges.max() - ranges.min())

        return ranges

    @staticmethod
    def compose_terrain(
        detail_noise: np.ndarray,
        base_heights: np.ndarray,
        mountain_mask: np.ndarray,
        ranges: np.ndarray,
        terrain_type: str
    ) -> np.ndarray:
        """
        Compose final terrain from all layers using MASKING.

        This is where coherence happens!

        Algorithm:
        1. Start with base heights (large-scale zones)
        2. Add range structure (medium-scale)
        3. Add detail noise MASKED by mountain_mask
        4. Result: Detail only where it should be

        Returns:
            Coherent heightmap with proper geological structure
        """
        resolution = detail_noise.shape[0]

        # Normalize all inputs
        detail_norm = (detail_noise - detail_noise.min()) / (detail_noise.max() - detail_noise.min())
        base_norm = (base_heights - base_heights.min()) / (base_heights.max() - base_heights.min())
        ranges_norm = (ranges - ranges.min()) / (ranges.max() - ranges.min())

        if terrain_type == 'mountains':
            # Mountains: Base + Ranges + Detail (heavily masked)
            composed = (
                base_norm * 0.3 +                          # Base elevation zones
                ranges_norm * 0.4 * mountain_mask +        # Range structure (masked)
                detail_norm * 0.6 * (mountain_mask ** 2)   # Detail only in mountain zones
            )

        elif terrain_type == 'hills':
            # Hills: Gentle base + light detail everywhere
            composed = (
                base_norm * 0.5 +                          # Gentle base
                detail_norm * 0.5 * mountain_mask          # Moderate detail
            )

        elif terrain_type == 'islands':
            # Islands: Radial base + moderate detail
            composed = (
                base_norm * 0.4 * mountain_mask +          # Island shape
                ranges_norm * 0.3 * mountain_mask +        # Some ranges
                detail_norm * 0.4 * (mountain_mask ** 1.5) # Detail near center
            )

        elif terrain_type == 'highlands':
            # Highlands: High base + moderate ranges
            composed = (
                base_norm * 0.6 +                          # High plateau
                ranges_norm * 0.2 * mountain_mask +        # Some ranges
                detail_norm * 0.3 * mountain_mask          # Moderate detail
            )

        elif terrain_type == 'canyons':
            # Canyons: Inverted ranges with deep cuts
            composed = (
                base_norm * 0.3 +                          # Base
                (1.0 - ranges_norm) * 0.5 * mountain_mask + # Inverted ranges (valleys)
                detail_norm * 0.3                          # Some detail
            )

        elif terrain_type == 'mesas':
            # Mesas: Terraced base + minimal detail
            composed = (
                base_norm * 0.8 +                          # Strong terraced base
                detail_norm * 0.2 * mountain_mask          # Minimal detail
            )

        else:  # flat
            # Flat: Mostly base, minimal detail
            composed = (
                base_norm * 0.9 +
                detail_norm * 0.1 * mountain_mask
            )

        # Normalize final result
        composed = (composed - composed.min()) / (composed.max() - composed.min())

        return composed

    @staticmethod
    def enhance_ridge_continuity(
        heightmap: np.ndarray,
        ridge_threshold: float = 0.6,
        connection_radius: int = 15,
        blend_strength: float = 0.5
    ) -> np.ndarray:
        """
        Enhance continuity of ridge features using selective anisotropic smoothing.

        WHY this approach:
        - Noise-based terrain creates broken ridges with small gaps
        - Anisotropic smoothing along ridge directions connects nearby features
        - Elevation-weighted blending preserves valleys and overall structure
        - Much simpler and more predictable than morphological operations

        Algorithm:
        1. Create smoothed version with elongated kernel (connects nearby features)
        2. Blend smoothed version with original based on elevation
        3. High elevations (ridges) get more smoothing to connect gaps
        4. Low elevations (valleys) stay sharp to preserve structure

        Args:
            heightmap: Input terrain (0-1 normalized)
            ridge_threshold: Elevation threshold for ridge detection (0-1)
                           0.6 = top 40% of terrain gets enhancement
            connection_radius: Smoothing radius in pixels
                             Scales with resolution: 15-20 typical
            blend_strength: Maximum blend amount for ridges (0-1)
                          0.5 = ridges get up to 50% smoothing

        Returns:
            Heightmap with enhanced ridge continuity
        """
        # Step 1: Create smoothed version using gaussian filter
        # WHY gaussian: Natural, gradual smoothing that connects nearby features
        # The sigma is proportional to connection_radius
        sigma = connection_radius / 2.5  # Empirically good ratio
        smoothed = ndimage.gaussian_filter(heightmap, sigma=sigma)

        # Step 2: Create elevation-based blend mask
        # WHY elevation-based: Only enhance high areas (ridges), preserve valleys
        # Elevation weight: 0 below ridge_threshold, ramping to 1 at max elevation
        elevation_normalized = (heightmap - ridge_threshold) / (1.0 - ridge_threshold)
        blend_mask = np.clip(elevation_normalized, 0, 1)

        # Apply blend_strength to control overall effect intensity
        blend_mask = blend_mask * blend_strength

        # Step 3: Blend smoothed terrain with original
        # WHY weighted blending: Smooth transition, preserves detail where needed
        # Low elevations (valleys): mostly original (blend_mask ≈ 0)
        # High elevations (ridges): blend of original and smoothed (blend_mask ≈ blend_strength)
        enhanced = heightmap * (1.0 - blend_mask) + smoothed * blend_mask

        # No normalization needed - weighted blending preserves [0, 1] range naturally
        # This maintains threshold relationships and prevents terrain destruction

        return enhanced

    @staticmethod
    def make_coherent(
        heightmap: np.ndarray,
        terrain_type: str = 'mountains'
    ) -> np.ndarray:
        """
        Transform random noise into coherent terrain with proper structure.

        This is the main entry point - replaces domain warping.

        Args:
            heightmap: Input noise (high-detail Perlin)
            terrain_type: Type of terrain to generate

        Returns:
            Coherent heightmap with mountain ranges, not random bumps

        Process:
        1. Generate base geography (WHERE mountains/valleys go)
        2. Generate mountain ranges (medium-scale linear features)
        3. Compose using masking (detail only where appropriate)
        4. Apply realism enhancements (erosion, etc.)
        """
        print(f"[COHERENT TERRAIN] Making {terrain_type} coherent...")

        # Step 1: Define WHERE features should exist
        base_heights, mountain_mask = CoherentTerrainGenerator.generate_base_geography(
            heightmap,
            terrain_type
        )

        # Step 2: Generate mountain RANGES (linear features)
        ranges = CoherentTerrainGenerator.generate_mountain_ranges(
            heightmap.shape[0],
            terrain_type
        )

        # Step 3: Compose all layers using masking
        coherent = CoherentTerrainGenerator.compose_terrain(
            heightmap,         # Detail noise
            base_heights,      # Large-scale zones
            mountain_mask,     # Where mountains allowed
            ranges,            # Range structure
            terrain_type
        )

        # Step 4: Enhance ridge continuity (Quick Win 2)
        # WHY: Connects broken ridge segments for more realistic mountain chains
        # Scale connection radius with resolution for consistent results
        connection_radius = max(15, int(heightmap.shape[0] / 256))
        coherent = CoherentTerrainGenerator.enhance_ridge_continuity(
            coherent,
            ridge_threshold=0.6,
            connection_radius=connection_radius,
            blend_strength=0.5
        )

        print(f"[COHERENT TERRAIN] Coherence complete!")

        return coherent
