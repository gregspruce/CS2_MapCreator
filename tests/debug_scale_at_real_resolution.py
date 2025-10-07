"""
Debug: Test scale parameter at 4096 resolution to find what actually works
"""

import numpy as np
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.noise_generator import NoiseGenerator


def calculate_buildability(heightmap: np.ndarray) -> float:
    """Quick buildability calculation."""
    resolution = heightmap.shape[0]
    pixel_size = 14336.0 / resolution
    heightmap_m = heightmap * 1024.0
    dy, dx = np.gradient(heightmap_m)
    slopes = np.sqrt(dx**2 + dy**2) / pixel_size * 100
    return (np.sum(slopes <= 5.0) / slopes.size) * 100


print("\n" + "="*80)
print("SCALE PARAMETER DEBUG - Finding What Actually Works at 4096")
print("="*80)

# The evidence: scale=500 at 512 gives 32% buildable (no domain warp, no coherent)
# If we scale proportionally: 500 * (4096/512) = 4000
# But tests show this doesn't work

# Let's test what DOES work at 4096
gen = NoiseGenerator(seed=42)
resolution = 1024  # Use 1024 for faster tests (will scale up mentally)

scales = [500, 1000, 2000, 4000, 8000, 16000]

print(f"\nTesting at {resolution}x{resolution} (octaves=2, persistence=0.3, NO domain warp)")
print("Scale proportional formula: optimal_scale = 500 * (resolution / 512)")
print(f"For {resolution}: predicted optimal = {500 * (resolution/512):.0f}\n")

for scale in scales:
    print(f"Testing scale={scale}...", end=" ", flush=True)
    heightmap = gen.generate_perlin(
        resolution=resolution,
        scale=scale,
        octaves=2,
        persistence=0.3,
        lacunarity=2.0,
        show_progress=False,
        domain_warp_amp=0.0,  # NO warping for pure test
        recursive_warp=False
    )
    buildable = calculate_buildability(heightmap)
    mean_slope = np.mean(np.gradient(heightmap * 1024)[0]) * 100
    print(f"Build={buildable:.1f}%, mean_slope={mean_slope:.2f}%")

print("\n" + "-"*80)
print("Key insight: The formula might be wrong! Let me test exponentially.")
print("-"*80)

# Maybe scale needs to grow FASTER than linear with resolution?
# Test: scale = 500 * (resolution / 512)^2 ?
print(f"\nAlternative formula: optimal_scale = 500 * ((resolution / 512) ^ 2)")
print(f"For {resolution}: predicted = {500 * ((resolution/512)**2):.0f}")

print("\n" + "="*80)
