"""
Test recursive warping vs basic domain warping.

Hypothesis: The 618% slopes are caused by RECURSIVE warp, not domain warp amp!
"""

import numpy as np
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.noise_generator import NoiseGenerator
from src.buildability_enforcer import BuildabilityEnforcer


print("\n" + "="*80)
print("RECURSIVE WARPING TEST")
print("="*80)
print("\nTesting basic domain warp vs recursive warp")
print("Config: 1024 resolution, scale=100, octaves=8, persistence=0.5")
print("="*80)

gen = NoiseGenerator(seed=42)
resolution = 1024
scale = 100
octaves = 8
persistence = 0.5

print("\n[TEST 1] Basic domain warp (NO recursive):")
print("-"*80)

# No warping at all
heightmap = gen.generate_perlin(
    resolution=resolution, scale=scale, octaves=octaves,
    persistence=persistence, lacunarity=2.0, show_progress=False,
    domain_warp_amp=0.0, recursive_warp=False
)
stats = BuildabilityEnforcer.analyze_buildability(heightmap)
print(f"No warp at all:                     {stats['excellent_buildable_pct']:5.1f}% buildable, {stats['mean_slope']:6.1f}% mean")

# Basic domain warp, no recursive
heightmap = gen.generate_perlin(
    resolution=resolution, scale=scale, octaves=octaves,
    persistence=persistence, lacunarity=2.0, show_progress=False,
    domain_warp_amp=60.0, recursive_warp=False
)
stats = BuildabilityEnforcer.analyze_buildability(heightmap)
print(f"Domain warp 60, NO recursive:       {stats['excellent_buildable_pct']:5.1f}% buildable, {stats['mean_slope']:6.1f}% mean")

print("\n[TEST 2] Recursive warp WITH domain warp:")
print("-"*80)

# Recursive warp with domain warp
heightmap = gen.generate_perlin(
    resolution=resolution, scale=scale, octaves=octaves,
    persistence=persistence, lacunarity=2.0, show_progress=False,
    domain_warp_amp=60.0, recursive_warp=True, recursive_warp_strength=4.0
)
stats = BuildabilityEnforcer.analyze_buildability(heightmap)
print(f"Domain warp 60 + Recursive (str=4): {stats['excellent_buildable_pct']:5.1f}% buildable, {stats['mean_slope']:6.1f}% mean")

print("\n[TEST 3] Testing recursive warp strength:")
print("-"*80)

for strength in [1.0, 2.0, 3.0, 4.0, 5.0]:
    heightmap = gen.generate_perlin(
        resolution=resolution, scale=scale, octaves=octaves,
        persistence=persistence, lacunarity=2.0, show_progress=False,
        domain_warp_amp=60.0, recursive_warp=True, recursive_warp_strength=strength
    )
    stats = BuildabilityEnforcer.analyze_buildability(heightmap)
    print(f"Recursive strength={strength:.1f}:            {stats['excellent_buildable_pct']:5.1f}% buildable, {stats['mean_slope']:6.1f}% mean")

print("\n[TEST 4] Recursive warp WITHOUT domain warp (just recursive):")
print("-"*80)

heightmap = gen.generate_perlin(
    resolution=resolution, scale=scale, octaves=octaves,
    persistence=persistence, lacunarity=2.0, show_progress=False,
    domain_warp_amp=0.0, recursive_warp=True, recursive_warp_strength=4.0
)
stats = BuildabilityEnforcer.analyze_buildability(heightmap)
print(f"NO domain warp, YES recursive:      {stats['excellent_buildable_pct']:5.1f}% buildable, {stats['mean_slope']:6.1f}% mean")

print("\n" + "="*80)
print("CONCLUSION")
print("="*80)
print("Identifying which warping method causes the 618% slopes")
print("="*80)
