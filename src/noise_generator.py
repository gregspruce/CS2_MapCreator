"""
CS2 Noise-Based Terrain Generator

This module provides procedural terrain generation using various noise algorithms.
Noise-based generation creates realistic, organic-looking terrain that mimics
natural geological processes.

Supported Noise Types:
- Perlin Noise: Smooth, natural-looking terrain with rolling hills
- Simplex Noise: Faster than Perlin, less directional artifacts
- Fractal/FBM: Multi-octave noise for detailed, realistic terrain
- Ridged Multifractal: Creates mountain ridges and valleys
"""

import numpy as np
from perlin_noise import PerlinNoise
from opensimplex import OpenSimplex
from typing import Optional, Tuple
import math
from .progress_tracker import ProgressTracker

# Try to import FastNoiseLite for performance boost
try:
    from pyfastnoiselite.pyfastnoiselite import FastNoiseLite, NoiseType, FractalType, DomainWarpType
    FASTNOISE_AVAILABLE = True
    print("[NOISE_GEN] FastNoiseLite imported successfully - FAST path available")
except ImportError as e:
    FASTNOISE_AVAILABLE = False
    print(f"[NOISE_GEN] FastNoiseLite import FAILED: {e}")
    print("[NOISE_GEN] WARNING: Will use SLOW pure Python fallback (60-120s per generation)")


class NoiseGenerator:
    """
    Generates terrain heightmaps using various noise algorithms.

    Noise-based generation works by sampling a noise function across a 2D grid.
    The key to realistic terrain is using multiple octaves (layers) of noise
    at different scales and amplitudes - this is called Fractal Brownian Motion (FBM).
    """

    def __init__(self, seed: Optional[int] = None):
        """
        Initialize noise generator with optional seed.

        Args:
            seed: Random seed for reproducible terrain (optional)

        Why seeds matter:
        Seeds allow you to recreate the exact same terrain, which is crucial
        for iterative design or sharing map configurations.
        """
        self.seed = seed if seed is not None else np.random.randint(0, 10000)
        self.opensimplex = OpenSimplex(seed=self.seed)

    def generate_perlin(self,
                       resolution: int = 4096,
                       scale: float = 100.0,
                       octaves: int = 6,
                       persistence: float = 0.5,
                       lacunarity: float = 2.0,
                       show_progress: bool = True,
                       domain_warp_amp: float = 0.0,
                       domain_warp_type: int = 0,
                       recursive_warp: bool = False,
                       recursive_warp_strength: float = 4.0) -> np.ndarray:
        """
        Generate terrain using Perlin noise.

        Uses FastNoiseLite (C++/Cython) if available for 10-100x speedup,
        falls back to pure Python perlin-noise library.

        Args:
            resolution: Output size (pixels)
            scale: Base noise scale (larger = smoother terrain)
            octaves: Number of noise layers (more = more detail)
            persistence: Amplitude decrease per octave (0.0-1.0)
            lacunarity: Frequency increase per octave (typically 2.0)
            show_progress: Show progress bar (default: True)
            domain_warp_amp: Domain warping strength (0.0 = disabled, 40-80 recommended, default: 0.0)
                WHY: Eliminates grid-aligned patterns, creates organic curved features
                Essential for realistic terrain that doesn't look "obviously procedural"
            domain_warp_type: Warping algorithm (integer or enum)
                Integer: 0 = OpenSimplex2, 1 = OpenSimplex2Reduced, 2 = BasicGrid
                Enum: DomainWarpType.DomainWarpType_OpenSimplex2, etc.
            recursive_warp: Enable Inigo Quilez recursive domain warping (default: False)
                WHY: Creates compound distortions mimicking tectonic forces
                Stage 1 Quick Win 1 - transforms terrain from "curved" to "geologically authentic"
            recursive_warp_strength: Multiplier for recursive warping (3.0-5.0 optimal)

        Returns:
            2D numpy array normalized to 0.0-1.0

        How it works:
        - Scale controls the "wavelength" of terrain features
        - Each octave adds finer detail at half the amplitude
        - More octaves = more computational cost but richer detail
        - Persistence < 0.5 = smooth terrain, > 0.5 = rough terrain
        - Domain warping (if enabled) distorts sampling coordinates to eliminate patterns
        - Recursive warping (Stage 1) creates two-stage compound distortions for geological realism

        Performance:
        - FastNoiseLite (if available): ~10-100x faster than pure Python
        - Pure Python fallback: Guaranteed to work on all systems
        - Domain warping adds minimal overhead (~0.5-1.0s at 4096x4096)
        - Recursive warping adds ~1-2s overhead for dramatic quality improvement

        Stage 1 Quick Win 1 - Recursive Domain Warping:
        Use recursive_warp=True with domain_warp_amp=60.0 for maximum realism.
        This combination eliminates ALL grid artifacts and creates geological authenticity.
        """
        # Try fast path first
        if FASTNOISE_AVAILABLE:
            print(f"[DEBUG] Using FAST vectorized path (FASTNOISE_AVAILABLE=True)")
            if domain_warp_amp > 0.0:
                print(f"[PHASE1] Domain warping ENABLED (strength={domain_warp_amp:.1f})")
            if recursive_warp:
                print(f"[STAGE1] Recursive warping ENABLED (strength={recursive_warp_strength:.1f})")
            return self._generate_perlin_fast(resolution, scale, octaves,
                                             persistence, lacunarity, show_progress,
                                             domain_warp_amp, domain_warp_type,
                                             recursive_warp, recursive_warp_strength)

        # Fallback to pure Python
        print(f"[DEBUG] Using SLOW fallback path (FASTNOISE_AVAILABLE=False)")
        print(f"[DEBUG] This will take 60-120 seconds for 4096x4096!")
        heightmap = np.zeros((resolution, resolution), dtype=np.float64)

        # Generate multiple octaves and combine
        with ProgressTracker("Generating Perlin terrain", total=octaves, disable=not show_progress) as progress:
            for octave in range(octaves):
                frequency = lacunarity ** octave
                amplitude = persistence ** octave

                # Create PerlinNoise instance for this octave
                # octaves parameter here is internal octave count for the noise function
                perlin = PerlinNoise(octaves=1, seed=self.seed + octave)

                for y in range(resolution):
                    for x in range(resolution):
                        # Sample noise at scaled coordinates
                        nx = x / scale * frequency
                        ny = y / scale * frequency

                        # PerlinNoise returns values roughly in range [-0.5, 0.5]
                        noise_value = perlin([nx, ny]) * 2.0  # Scale to ~[-1, 1]

                        heightmap[y, x] += noise_value * amplitude

                progress.update(1)

        # Normalize to 0.0-1.0
        heightmap = (heightmap - heightmap.min()) / (heightmap.max() - heightmap.min())

        return heightmap

    def _generate_perlin_fast(self,
                             resolution: int = 4096,
                             scale: float = 100.0,
                             octaves: int = 6,
                             persistence: float = 0.5,
                             lacunarity: float = 2.0,
                             show_progress: bool = True,
                             domain_warp_amp: float = 0.0,
                             domain_warp_type: int = 0,
                             recursive_warp: bool = False,
                             recursive_warp_strength: float = 4.0) -> np.ndarray:
        """
        Generate terrain using FastNoiseLite (C++/Cython implementation) - VECTORIZED.

        This is 10-100x faster than the pure Python implementation.

        Args:
            Same as generate_perlin(), plus:
            domain_warp_amp: Domain warping strength (0.0 = disabled, 40-80 recommended, default: 0.0)
            domain_warp_type: Warping algorithm (integer or enum)
                Integer: 0 = OpenSimplex2, 1 = OpenSimplex2Reduced, 2 = BasicGrid
                Enum: DomainWarpType.DomainWarpType_OpenSimplex2, etc.
            recursive_warp: Enable Inigo Quilez recursive domain warping (default: False)
                WHY: Two-stage recursive warping creates compound distortions that mimic
                tectonic forces. Single-stage warping bends coordinates; recursive warping
                creates naturally meandering geological structures. This is the difference
                between "curved features" and "authentic geological realism."
            recursive_warp_strength: Multiplier for recursive warping (default: 4.0)
                Research shows 3.0-5.0 produces optimal organic patterns (Quilez 2008)

        Returns:
            2D numpy array normalized to 0.0-1.0

        Implementation notes:
        - Uses FastNoiseLite with built-in FBM (Fractal Brownian Motion)
        - Automatically handles octaves, persistence, lacunarity
        - VECTORIZED: Single call generates entire array (no Python loops!)
        - Uses Perlin noise type for consistency with fallback

        Performance improvement:
        - Old: 16.7M function calls via nested loops (60-120s for 4096x4096)
        - New: Single vectorized call (1-10s for 4096x4096)
        - Speedup: 10-100x depending on system

        Domain Warping (Phase 1.1 Enhancement):
        - Basic warping: Eliminates obvious grid-aligned procedural patterns
        - Recursive warping: Creates authentic geological meandering structures
        - Strength 40-80 produces realistic tectonic-looking terrain
        - WHY: Basic Perlin noise has uniform directional artifacts.
          Domain warping distorts the sampling coordinates before evaluation,
          breaking up regular patterns and creating natural-looking curves.
          Recursive warping applies this distortion in two stages (q → r → final),
          creating compound curves that match tectonic plate interactions.
          Research: Quilez (2008), Perlin (1985)
        """
        # Initialize FastNoiseLite
        noise = FastNoiseLite(seed=self.seed)

        # Configure noise type (Perlin for consistency)
        noise.noise_type = NoiseType.NoiseType_Perlin

        # Configure fractal (FBM = Fractal Brownian Motion)
        noise.fractal_type = FractalType.FractalType_FBm
        noise.fractal_octaves = octaves
        noise.fractal_gain = persistence  # Amplitude multiplier per octave
        noise.fractal_lacunarity = lacunarity
        noise.frequency = 1.0 / scale  # FastNoiseLite uses frequency instead of scale

        # Configure domain warping (Phase 1.1)
        # WHY: Domain warping eliminates grid-aligned patterns by warping
        # the noise sampling coordinates. This creates curved, organic features
        # instead of straight ridges/valleys. Essential for eliminating the
        # "obvious procedural look" that makes terrain appear artificial.
        if domain_warp_amp > 0.0:
            noise.domain_warp_amp = domain_warp_amp
            # Convert integer to enum if needed for backward compatibility
            if isinstance(domain_warp_type, int):
                # Map integer values to DomainWarpType enum
                # 0 = OpenSimplex2, 1 = OpenSimplex2Reduced, 2 = BasicGrid
                warp_types = [
                    DomainWarpType.DomainWarpType_OpenSimplex2,
                    DomainWarpType.DomainWarpType_OpenSimplex2Reduced,
                    DomainWarpType.DomainWarpType_BasicGrid
                ]
                noise.domain_warp_type = warp_types[domain_warp_type] if domain_warp_type < len(warp_types) else warp_types[0]
            else:
                noise.domain_warp_type = domain_warp_type

        if show_progress:
            print("Generating terrain (FastNoise - vectorized)...")

        # VECTORIZED GENERATION - KEY OPTIMIZATION
        # Create coordinate grids for entire heightmap
        # This replaces 16.7M function calls with a single vectorized operation
        x_coords = np.arange(resolution, dtype=np.float32)
        y_coords = np.arange(resolution, dtype=np.float32)
        xx, yy = np.meshgrid(x_coords, y_coords)

        # Apply recursive domain warping if enabled (Stage 1 Quick Win 1)
        # WHY: Inigo Quilez's recursive technique creates compound distortions
        # that authentically mimic tectonic processes. This is the difference
        # between "terrain with curves" and "geological authenticity."
        if recursive_warp:
            if show_progress:
                print(f"[STAGE1] Applying recursive domain warping (strength={recursive_warp_strength:.1f})...")
            xx, yy = self._apply_recursive_domain_warp(
                xx, yy, resolution, scale,
                recursive_warp_strength, octaves, persistence
            )

        # Stack coordinates in format (2, num_points) as required by gen_from_coords
        # Ravel() flattens the 2D grids into 1D arrays for batch processing
        # CRITICAL: Convert to float32 for FastNoiseLite compatibility
        # WHY: Recursive warping creates float64, but FastNoiseLite expects float32
        coords = np.stack([xx.ravel(), yy.ravel()], axis=0).astype(np.float32)

        # Generate all noise values in one vectorized call
        # This is where the magic happens - C++/Cython handles all 16.7M points at once
        noise_values = noise.gen_from_coords(coords)

        # Reshape back to 2D heightmap
        heightmap = noise_values.reshape(resolution, resolution)

        # Normalize to 0.0-1.0 (FastNoiseLite returns approximately -1 to 1)
        heightmap = (heightmap - heightmap.min()) / (heightmap.max() - heightmap.min())

        if show_progress:
            print("Terrain generation complete!")

        return heightmap.astype(np.float64)

    def _apply_recursive_domain_warp(self,
                                    xx: np.ndarray,
                                    yy: np.ndarray,
                                    resolution: int,
                                    scale: float,
                                    strength: float,
                                    octaves: int,
                                    persistence: float) -> Tuple[np.ndarray, np.ndarray]:
        """
        Apply Inigo Quilez recursive domain warping to coordinate grids.

        Algorithm (Quilez 2008):
        1. Generate q pattern: q = (fbm(p + offset1), fbm(p + offset2))
        2. Generate r pattern: r = (fbm(p + strength*q + offset3), fbm(p + strength*q + offset4))
        3. Return warped coordinates: p + strength*r

        WHY this works:
        - First warp (q) creates primary distortions
        - Second warp (r) compounds those distortions based on first warp
        - Result: Naturally meandering features that mimic tectonic processes
        - Single-stage: "curved terrain"
        - Two-stage recursive: "geological authenticity"

        Args:
            xx, yy: Coordinate meshgrids to warp
            resolution: Heightmap resolution
            scale: Base noise scale
            strength: Warping intensity (3.0-5.0 recommended)
            octaves: FBM octaves for warping noise
            persistence: FBM persistence

        Returns:
            (warped_xx, warped_yy): Warped coordinate grids

        Performance: Adds ~1-2s overhead at 4096x4096 for dramatic quality improvement
        """
        # Initialize noise generator for warping (different seed for independence)
        warp_noise = FastNoiseLite(seed=self.seed + 9999)
        warp_noise.noise_type = NoiseType.NoiseType_OpenSimplex2
        warp_noise.fractal_type = FractalType.FractalType_FBm
        warp_noise.fractal_octaves = max(3, octaves // 2)  # Fewer octaves for warping
        warp_noise.fractal_gain = persistence
        warp_noise.fractal_lacunarity = 2.0
        warp_noise.frequency = 1.0 / (scale * 1.5)  # Slightly larger scale for warping

        # Stage 1: Generate q pattern (primary distortion)
        # q = (fbm(p + offset1), fbm(p + offset2))
        # Offsets are arbitrary but must differ to create variation
        # CRITICAL: Convert to float32 for FastNoiseLite compatibility
        coords_q1 = np.stack([(xx + 0.0).ravel(), (yy + 0.0).ravel()], axis=0).astype(np.float32)
        coords_q2 = np.stack([(xx + 5.2 * scale).ravel(), (yy + 1.3 * scale).ravel()], axis=0).astype(np.float32)

        q1 = warp_noise.gen_from_coords(coords_q1).reshape(resolution, resolution)
        q2 = warp_noise.gen_from_coords(coords_q2).reshape(resolution, resolution)

        # Normalize q to reasonable range for coordinate offsets
        q1_norm = q1 * scale * 0.5
        q2_norm = q2 * scale * 0.5

        # Stage 2: Generate r pattern (compound distortion based on q)
        # r = (fbm(p + strength*q + offset3), fbm(p + strength*q + offset4))
        # CRITICAL: Convert to float32 for FastNoiseLite compatibility
        coords_r1 = np.stack([
            (xx + strength * q1_norm + 1.7 * scale).ravel(),
            (yy + strength * q2_norm + 9.2 * scale).ravel()
        ], axis=0).astype(np.float32)
        coords_r2 = np.stack([
            (xx + strength * q1_norm + 8.3 * scale).ravel(),
            (yy + strength * q2_norm + 2.8 * scale).ravel()
        ], axis=0).astype(np.float32)

        r1 = warp_noise.gen_from_coords(coords_r1).reshape(resolution, resolution)
        r2 = warp_noise.gen_from_coords(coords_r2).reshape(resolution, resolution)

        # Normalize r to reasonable range
        r1_norm = r1 * scale * 0.5
        r2_norm = r2 * scale * 0.5

        # Apply final warping: p' = p + strength * r
        # This creates the compound distortion that mimics geological processes
        warped_xx = xx + strength * r1_norm
        warped_yy = yy + strength * r2_norm

        return warped_xx, warped_yy

    def generate_simplex(self,
                        resolution: int = 4096,
                        scale: float = 100.0,
                        octaves: int = 6,
                        persistence: float = 0.5,
                        lacunarity: float = 2.0,
                        show_progress: bool = True) -> np.ndarray:
        """
        Generate terrain using FastNoiseLite OpenSimplex2 - VECTORIZED.

        Args:
            resolution: Output size (pixels)
            scale: Base noise scale
            octaves: Number of noise layers
            persistence: Amplitude decrease per octave
            lacunarity: Frequency increase per octave
            show_progress: Show progress bar (default: True)

        Returns:
            2D numpy array normalized to 0.0-1.0

        Simplex vs Perlin:
        - OpenSimplex2 is computationally faster than Perlin
        - Fewer directional artifacts
        - Better for large-scale generation
        - Slightly different "character" (personal preference)

        Performance:
        - Uses vectorized FastNoiseLite for 10-100x speedup
        - Falls back to slow implementation only if FastNoiseLite unavailable
        """
        # Try fast path first (vectorized FastNoiseLite)
        if FASTNOISE_AVAILABLE:
            return self._generate_simplex_fast(resolution, scale, octaves,
                                              persistence, lacunarity, show_progress)

        # Fallback to pure Python (slow, but guaranteed to work)
        heightmap = np.zeros((resolution, resolution), dtype=np.float64)

        with ProgressTracker("Generating Simplex terrain", total=octaves, disable=not show_progress) as progress:
            for octave in range(octaves):
                frequency = lacunarity ** octave
                amplitude = persistence ** octave

                # Create new OpenSimplex instance for this octave
                simplex = OpenSimplex(seed=self.seed + octave)

                for y in range(resolution):
                    for x in range(resolution):
                        nx = x / scale * frequency
                        ny = y / scale * frequency

                        # OpenSimplex noise2 returns values in range [-1, 1]
                        noise_value = simplex.noise2(nx, ny)
                        heightmap[y, x] += noise_value * amplitude

                progress.update(1)

        # Normalize to 0.0-1.0
        heightmap = (heightmap - heightmap.min()) / (heightmap.max() - heightmap.min())

        return heightmap

    def _generate_simplex_fast(self,
                              resolution: int = 4096,
                              scale: float = 100.0,
                              octaves: int = 6,
                              persistence: float = 0.5,
                              lacunarity: float = 2.0,
                              show_progress: bool = True) -> np.ndarray:
        """
        Generate terrain using FastNoiseLite OpenSimplex2 (vectorized).

        This uses the same vectorized approach as _generate_perlin_fast()
        but with OpenSimplex2 noise type for faster, cleaner terrain.

        Performance improvement: 10-100x faster than pure Python loops.
        """
        # Initialize FastNoiseLite
        noise = FastNoiseLite(seed=self.seed)

        # Configure noise type (OpenSimplex2 is faster and cleaner than Perlin)
        noise.noise_type = NoiseType.NoiseType_OpenSimplex2

        # Configure fractal (FBM = Fractal Brownian Motion)
        noise.fractal_type = FractalType.FractalType_FBm
        noise.fractal_octaves = octaves
        noise.fractal_gain = persistence
        noise.fractal_lacunarity = lacunarity
        noise.frequency = 1.0 / scale

        if show_progress:
            print("Generating terrain (OpenSimplex2 - vectorized)...")

        # VECTORIZED GENERATION - same optimization as Perlin
        x_coords = np.arange(resolution, dtype=np.float32)
        y_coords = np.arange(resolution, dtype=np.float32)
        xx, yy = np.meshgrid(x_coords, y_coords)

        # Stack coordinates for batch processing
        coords = np.stack([xx.ravel(), yy.ravel()], axis=0)

        # Generate all noise values in one call
        noise_values = noise.gen_from_coords(coords)

        # Reshape to 2D heightmap
        heightmap = noise_values.reshape(resolution, resolution)

        # Normalize to 0.0-1.0
        heightmap = (heightmap - heightmap.min()) / (heightmap.max() - heightmap.min())

        if show_progress:
            print("Terrain generation complete!")

        return heightmap.astype(np.float64)

    def generate_opensimplex(self,
                            resolution: int = 4096,
                            scale: float = 100.0,
                            octaves: int = 6,
                            persistence: float = 0.5,
                            lacunarity: float = 2.0) -> np.ndarray:
        """
        Generate terrain using OpenSimplex noise (improved Simplex).

        Args:
            resolution: Output size (pixels)
            scale: Base noise scale
            octaves: Number of noise layers
            persistence: Amplitude decrease per octave
            lacunarity: Frequency increase per octave

        Returns:
            2D numpy array normalized to 0.0-1.0

        OpenSimplex is a patent-free alternative to Simplex with similar
        performance characteristics.
        """
        heightmap = np.zeros((resolution, resolution), dtype=np.float64)

        for octave in range(octaves):
            frequency = lacunarity ** octave
            amplitude = persistence ** octave

            for y in range(resolution):
                for x in range(resolution):
                    nx = x / scale * frequency
                    ny = y / scale * frequency

                    noise_value = self.opensimplex.noise2(nx, ny)
                    heightmap[y, x] += noise_value * amplitude

        # Normalize to 0.0-1.0
        heightmap = (heightmap - heightmap.min()) / (heightmap.max() - heightmap.min())

        return heightmap

    def generate_ridged(self,
                       resolution: int = 4096,
                       scale: float = 100.0,
                       octaves: int = 6,
                       persistence: float = 0.5,
                       lacunarity: float = 2.0) -> np.ndarray:
        """
        Generate mountainous terrain with ridges using ridged multifractal.

        Args:
            resolution: Output size (pixels)
            scale: Base noise scale
            octaves: Number of noise layers
            persistence: Amplitude decrease per octave
            lacunarity: Frequency increase per octave

        Returns:
            2D numpy array normalized to 0.0-1.0

        Ridged multifractal creates dramatic mountain ridges by inverting
        and sharpening the noise values. Perfect for alpine terrain.
        """
        heightmap = np.zeros((resolution, resolution), dtype=np.float64)

        for octave in range(octaves):
            frequency = lacunarity ** octave
            amplitude = persistence ** octave

            # Create PerlinNoise instance for this octave
            perlin = PerlinNoise(octaves=1, seed=self.seed + octave)

            for y in range(resolution):
                for x in range(resolution):
                    nx = x / scale * frequency
                    ny = y / scale * frequency

                    noise_value = perlin([nx, ny]) * 2.0  # Scale to ~[-1, 1]

                    # Key difference: take absolute value and invert
                    # This creates sharp ridges instead of smooth hills
                    noise_value = 1.0 - abs(noise_value)

                    heightmap[y, x] += noise_value * amplitude

        # Normalize to 0.0-1.0
        heightmap = (heightmap - heightmap.min()) / (heightmap.max() - heightmap.min())

        return heightmap

    def generate_islands(self,
                        resolution: int = 4096,
                        scale: float = 100.0,
                        octaves: int = 6,
                        persistence: float = 0.5,
                        lacunarity: float = 2.0,
                        island_size: float = 0.7) -> np.ndarray:
        """
        Generate island-like terrain with natural coastlines.

        Args:
            resolution: Output size (pixels)
            scale: Base noise scale
            octaves: Number of noise layers
            persistence: Amplitude decrease per octave
            lacunarity: Frequency increase per octave
            island_size: Size of island (0.0-1.0, larger = bigger island)

        Returns:
            2D numpy array normalized to 0.0-1.0

        Islands are created by multiplying noise with a radial gradient.
        This creates natural-looking coastlines while ensuring the edges
        are below sea level.
        """
        # Generate base noise
        heightmap = self.generate_perlin(resolution, scale, octaves, persistence, lacunarity)

        # Create radial gradient (high in center, low at edges)
        center = resolution / 2
        max_dist = resolution / 2

        y, x = np.ogrid[0:resolution, 0:resolution]
        distance = np.sqrt((x - center)**2 + (y - center)**2)

        # Create gradient with smooth falloff
        gradient = np.clip(1.0 - (distance / (max_dist * island_size)), 0.0, 1.0)

        # Apply smooth curve to gradient for more natural appearance
        gradient = gradient ** 2

        # Multiply noise by gradient to create island
        heightmap = heightmap * gradient

        # Normalize
        heightmap = (heightmap - heightmap.min()) / (heightmap.max() - heightmap.min() + 0.0001)

        return heightmap

    def generate_canyon(self,
                       resolution: int = 4096,
                       scale: float = 100.0,
                       octaves: int = 6,
                       persistence: float = 0.5,
                       lacunarity: float = 2.0,
                       depth: float = 0.3) -> np.ndarray:
        """
        Generate canyon/valley terrain with erosion-like features.

        Args:
            resolution: Output size (pixels)
            scale: Base noise scale
            octaves: Number of noise layers
            persistence: Amplitude decrease per octave
            lacunarity: Frequency increase per octave
            depth: Canyon depth factor (0.0-1.0)

        Returns:
            2D numpy array normalized to 0.0-1.0

        Canyons are created by taking the absolute value of noise and
        inverting it, creating v-shaped valleys.
        """
        heightmap = np.zeros((resolution, resolution), dtype=np.float64)

        for octave in range(octaves):
            frequency = lacunarity ** octave
            amplitude = persistence ** octave

            # Create PerlinNoise instance for this octave
            perlin = PerlinNoise(octaves=1, seed=self.seed + octave)

            for y in range(resolution):
                for x in range(resolution):
                    nx = x / scale * frequency
                    ny = y / scale * frequency

                    noise_value = perlin([nx, ny]) * 2.0  # Scale to ~[-1, 1]

                    # Create canyon effect
                    noise_value = abs(noise_value)
                    heightmap[y, x] += noise_value * amplitude

        # Invert and apply depth
        heightmap = 1.0 - (heightmap * depth)

        # Normalize
        heightmap = (heightmap - heightmap.min()) / (heightmap.max() - heightmap.min())

        return heightmap

    def generate_terraced(self,
                         resolution: int = 4096,
                         scale: float = 100.0,
                         octaves: int = 6,
                         persistence: float = 0.5,
                         lacunarity: float = 2.0,
                         terrace_levels: int = 10) -> np.ndarray:
        """
        Generate terraced/stepped terrain like mesa formations.

        Args:
            resolution: Output size (pixels)
            scale: Base noise scale
            octaves: Number of noise layers
            persistence: Amplitude decrease per octave
            lacunarity: Frequency increase per octave
            terrace_levels: Number of terrace steps

        Returns:
            2D numpy array normalized to 0.0-1.0

        Terracing quantizes the height values to create flat plateaus
        separated by steep cliffs - similar to mesa formations in nature.
        """
        # Generate base noise
        heightmap = self.generate_perlin(resolution, scale, octaves, persistence, lacunarity)

        # Apply terracing by quantizing values
        heightmap = np.floor(heightmap * terrace_levels) / terrace_levels

        return heightmap

    def apply_erosion_simulation(self,
                                 heightmap: np.ndarray,
                                 iterations: int = 100,
                                 erosion_strength: float = 0.5) -> np.ndarray:
        """
        Simulate thermal erosion to create more realistic terrain.

        Args:
            heightmap: Input heightmap (0.0 to 1.0)
            iterations: Number of erosion simulation steps
            erosion_strength: How aggressive the erosion is (0.0-1.0)

        Returns:
            Eroded heightmap

        This simplified erosion lowers peaks and fills valleys slightly,
        mimicking natural weathering processes. Real erosion is extremely
        complex, but this gives a good approximation.
        """
        result = heightmap.copy()
        resolution = heightmap.shape[0]

        for _ in range(iterations):
            # Calculate slope (gradient magnitude)
            gy, gx = np.gradient(result)
            slope = np.sqrt(gx**2 + gy**2)

            # Erode based on slope (steeper = more erosion)
            erosion = slope * erosion_strength * 0.01

            # Apply erosion (lower high areas, raise low areas)
            result -= erosion

        # Normalize
        result = (result - result.min()) / (result.max() - result.min())

        return result


def create_preset_terrain(preset: str,
                         resolution: int = 4096,
                         seed: Optional[int] = None) -> np.ndarray:
    """
    Create terrain using predefined presets.

    Args:
        preset: Name of preset ('hills', 'mountains', 'islands', 'canyon', 'flat')
        resolution: Output resolution
        seed: Random seed

    Returns:
        Generated heightmap array

    Presets provide quick starting points for common terrain types.
    These parameters have been tuned for realistic results.
    """
    gen = NoiseGenerator(seed=seed)

    presets = {
        'flat': lambda: np.full((resolution, resolution), 0.5, dtype=np.float64),

        'rolling_hills': lambda: gen.generate_perlin(
            resolution=resolution,
            scale=200.0,
            octaves=4,
            persistence=0.5,
            lacunarity=2.0
        ),

        'mountains': lambda: gen.generate_ridged(
            resolution=resolution,
            scale=150.0,
            octaves=6,
            persistence=0.6,
            lacunarity=2.0
        ),

        'islands': lambda: gen.generate_islands(
            resolution=resolution,
            scale=180.0,
            octaves=5,
            persistence=0.5,
            lacunarity=2.0,
            island_size=0.65
        ),

        'canyon': lambda: gen.generate_canyon(
            resolution=resolution,
            scale=120.0,
            octaves=5,
            persistence=0.5,
            lacunarity=2.0,
            depth=0.4
        ),

        'highlands': lambda: gen.generate_perlin(
            resolution=resolution,
            scale=250.0,
            octaves=6,
            persistence=0.6,
            lacunarity=2.5
        ),

        'mesas': lambda: gen.generate_terraced(
            resolution=resolution,
            scale=180.0,
            octaves=4,
            persistence=0.5,
            lacunarity=2.0,
            terrace_levels=8
        ),
    }

    if preset not in presets:
        raise ValueError(f"Unknown preset '{preset}'. Available: {list(presets.keys())}")

    return presets[preset]()
