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
                       domain_warp_type: int = 0) -> np.ndarray:
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

        Returns:
            2D numpy array normalized to 0.0-1.0

        How it works:
        - Scale controls the "wavelength" of terrain features
        - Each octave adds finer detail at half the amplitude
        - More octaves = more computational cost but richer detail
        - Persistence < 0.5 = smooth terrain, > 0.5 = rough terrain
        - Domain warping (if enabled) distorts sampling coordinates to eliminate patterns

        Performance:
        - FastNoiseLite (if available): ~10-100x faster than pure Python
        - Pure Python fallback: Guaranteed to work on all systems
        - Domain warping adds minimal overhead (~0.5-1.0s at 4096x4096)

        Phase 1.1 - Domain Warping Feature:
        To enable domain warping and eliminate grid patterns, use domain_warp_amp=60.0
        Research shows strength 40-80 produces realistic tectonic-looking terrain.
        """
        # Try fast path first
        if FASTNOISE_AVAILABLE:
            print(f"[DEBUG] Using FAST vectorized path (FASTNOISE_AVAILABLE=True)")
            if domain_warp_amp > 0.0:
                print(f"[PHASE1] Domain warping ENABLED (strength={domain_warp_amp:.1f})")
            return self._generate_perlin_fast(resolution, scale, octaves,
                                             persistence, lacunarity, show_progress,
                                             domain_warp_amp, domain_warp_type)

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
                             domain_warp_type: int = 0) -> np.ndarray:
        """
        Generate terrain using FastNoiseLite (C++/Cython implementation) - VECTORIZED.

        This is 10-100x faster than the pure Python implementation.

        Args:
            Same as generate_perlin(), plus:
            domain_warp_amp: Domain warping strength (0.0 = disabled, 40-80 recommended, default: 0.0)
            domain_warp_type: Warping algorithm (integer or enum)
                Integer: 0 = OpenSimplex2, 1 = OpenSimplex2Reduced, 2 = BasicGrid
                Enum: DomainWarpType.DomainWarpType_OpenSimplex2, etc.

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
        - Eliminates obvious grid-aligned procedural patterns
        - Creates organic, meandering ridges and valleys
        - Strength 40-80 produces realistic tectonic-looking terrain
        - WHY: Basic Perlin noise has uniform directional artifacts.
          Domain warping distorts the sampling coordinates before evaluation,
          breaking up regular patterns and creating natural-looking curves.
          This single technique transforms "obviously procedural" terrain
          into geographically plausible landscapes. Research: Quilez (2008)
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

        # Stack coordinates in format (2, num_points) as required by gen_from_coords
        # Ravel() flattens the 2D grids into 1D arrays for batch processing
        coords = np.stack([xx.ravel(), yy.ravel()], axis=0)

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
