"""
Test scenic zone parameters to find reasonable settings.

The scenic zones should be interesting but not impossibly steep.
"""

import numpy as np
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.noise_generator import NoiseGenerator
from src.buildability_enforcer import BuildabilityEnforcer


def test_scenic_config(resolution, scale, octaves, persistence, domain_warp, label):
    """Test a specific scenic configuration."""
    gen = NoiseGenerator(seed=42)

    heightmap = gen.generate_perlin(
        resolution=resolution,
        scale=scale,
        octaves=octaves,
        persistence=persistence,
        lacunarity=2.0,
        show_progress=False,
        domain_warp_amp=domain_warp,
        recursive_warp=(domain_warp > 0)
    )

    stats = BuildabilityEnforcer.analyze_buildability(heightmap)
    print(f"{label:50s}: {stats['excellent_buildable_pct']:5.1f}% buildable, mean={stats['mean_slope']:6.1f}%")
    return stats['excellent_buildable_pct']


print("\n" + "="*80)
print("SCENIC ZONE PARAMETER TESTING")
print("="*80)
print("\nFinding reasonable scenic parameters (should be interesting but not impossibly steep)")
print("Target: 5-15% buildable in scenic zones (interesting but not unbuildable)")
print("="*80)

resolution = 1024

print("\n[TEST 1] Varying domain warp strength (octaves=8, persistence=0.5):")
print("-"*80)
test_scenic_config(resolution, 100, 8, 0.5, 0.0, "No domain warp")
test_scenic_config(resolution, 100, 8, 0.5, 20.0, "Weak domain warp (20)")
test_scenic_config(resolution, 100, 8, 0.5, 40.0, "Moderate domain warp (40)")
test_scenic_config(resolution, 100, 8, 0.5, 60.0, "Strong domain warp (60) [current]")
test_scenic_config(resolution, 100, 8, 0.5, 80.0, "Very strong domain warp (80)")

print("\n[TEST 2] Varying octaves (domain_warp=40, persistence=0.5):")
print("-"*80)
test_scenic_config(resolution, 100, 4, 0.5, 40.0, "4 octaves")
test_scenic_config(resolution, 100, 6, 0.5, 40.0, "6 octaves")
test_scenic_config(resolution, 100, 8, 0.5, 40.0, "8 octaves [current]")

print("\n[TEST 3] Varying persistence (octaves=6, domain_warp=40):")
print("-"*80)
test_scenic_config(resolution, 100, 6, 0.3, 40.0, "Persistence 0.3")
test_scenic_config(resolution, 100, 6, 0.4, 40.0, "Persistence 0.4")
test_scenic_config(resolution, 100, 6, 0.5, 40.0, "Persistence 0.5 [current]")

print("\n[TEST 4] Varying scale (octaves=6, persistence=0.4, domain_warp=40):")
print("-"*80)
test_scenic_config(resolution, 200, 6, 0.4, 40.0, "Scale 200")
test_scenic_config(resolution, 300, 6, 0.4, 40.0, "Scale 300")
test_scenic_config(resolution, 500, 6, 0.4, 40.0, "Scale 500")

print("\n" + "="*80)
print("CONCLUSION")
print("="*80)
print("Finding optimal scenic parameters that balance interest with buildability")
print("="*80)
