"""
Test EXTREMELY smooth parameters to find what gives 70-80% buildable
(So that when control map selects 50%, we maintain ~40% buildable overall)
"""

import numpy as np
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.noise_generator import NoiseGenerator


def calc_buildable(heightmap):
    resolution = heightmap.shape[0]
    pixel_size = 14336.0 / resolution
    hm = heightmap * 1024.0
    dy, dx = np.gradient(hm)
    slopes = np.sqrt(dx**2 + dy**2) / pixel_size * 100
    return (np.sum(slopes <= 5.0) / slopes.size) * 100


print("\n" + "="*80)
print("EXTREME SMOOTHING TEST - Finding Parameters for 70-80% Buildable")
print("="*80)

gen = NoiseGenerator(seed=42)
resolution = 1024
scale = 1000  # Already proven optimal

# Test different octave/persistence combinations
configs = [
    (2, 0.3, "Current"),
    (2, 0.2, "Lower persistence"),
    (2, 0.1, "Very low persistence"),
    (1, 0.3, "Single octave"),
    (1, 0.2, "Single octave, low pers"),
    (1, 0.1, "Single octave, very low"),
]

print(f"\nResolution: {resolution}, Scale: {scale}, domain_warp=0\n")

for octaves, persistence, label in configs:
    heightmap = gen.generate_perlin(
        resolution=resolution,
        scale=scale,
        octaves=octaves,
        persistence=persistence,
        lacunarity=2.0,
        show_progress=False,
        domain_warp_amp=0.0,
        recursive_warp=False
    )
    buildable = calc_buildable(heightmap)
    print(f"{label:30s} (oct={octaves}, pers={persistence:.1f}): {buildable:5.1f}% buildable")

print("\n" + "="*80)
print("Target: 70-80% buildable for smooth zones")
print("="*80)
