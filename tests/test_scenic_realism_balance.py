"""
Find the balance between scenic realism and buildability.

The evidence document specifies recursive warping for scenic zones.
We shouldn't disable it - we should tune it to be less aggressive.

Test:
1. Lower octave counts (4, 6 vs 8)
2. Lower recursive warp strength (1.0, 2.0 vs 4.0)
3. Find configuration that looks realistic but doesn't destroy buildability
"""

import numpy as np
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.noise_generator import NoiseGenerator
from src.buildability_enforcer import BuildabilityEnforcer


def test_scenic_config(resolution, scale, octaves, persistence, domain_warp,
                       recursive_warp, recursive_strength, label):
    """Test a scenic configuration."""
    gen = NoiseGenerator(seed=42)

    heightmap = gen.generate_perlin(
        resolution=resolution,
        scale=scale,
        octaves=octaves,
        persistence=persistence,
        lacunarity=2.0,
        show_progress=False,
        domain_warp_amp=domain_warp,
        recursive_warp=recursive_warp,
        recursive_warp_strength=recursive_strength if recursive_warp else 0.0
    )

    stats = BuildabilityEnforcer.analyze_buildability(heightmap)
    print(f"{label:60s}: {stats['excellent_buildable_pct']:5.1f}% build, "
          f"{stats['mean_slope']:6.1f}% mean, {stats['p90_slope']:6.1f}% p90")

    return stats['excellent_buildable_pct'], stats['mean_slope']


print("\n" + "="*80)
print("SCENIC REALISM vs BUILDABILITY BALANCE")
print("="*80)
print("\nFinding configuration that provides realism WITHOUT destroying buildability")
print("Target: 5-15% buildable in scenic zones (interesting but not impossible)")
print("="*80)

resolution = 1024
scale = 100
domain_warp = 60.0

print("\n[TEST 1] Varying octaves (with recursive warp strength=1.0):")
print("-"*80)
for octaves in [4, 5, 6, 7, 8]:
    test_scenic_config(resolution, scale, octaves, 0.5, domain_warp,
                      True, 1.0, f"Octaves={octaves}, recursive_strength=1.0")

print("\n[TEST 2] Varying recursive strength (octaves=6):")
print("-"*80)
for strength in [0.5, 1.0, 1.5, 2.0, 2.5, 3.0, 4.0]:
    test_scenic_config(resolution, scale, 6, 0.5, domain_warp,
                      True, strength, f"Octaves=6, recursive_strength={strength:.1f}")

print("\n[TEST 3] Lower octaves + lower strength combinations:")
print("-"*80)
configs = [
    (4, 0.5, "Low detail, gentle warp"),
    (4, 1.0, "Low detail, moderate warp"),
    (5, 0.5, "Moderate detail, gentle warp"),
    (5, 1.0, "Moderate detail, moderate warp"),
    (6, 0.5, "Good detail, gentle warp"),
    (6, 1.0, "Good detail, moderate warp"),
]

best_config = None
best_score = 0

for octaves, strength, label_desc in configs:
    buildable, mean = test_scenic_config(
        resolution, scale, octaves, 0.5, domain_warp,
        True, strength, f"{label_desc:30s} (oct={octaves}, str={strength:.1f})"
    )

    # Score: prefer 5-15% buildable with reasonable mean slopes (<200%)
    if 5 <= buildable <= 15 and mean < 200:
        score = buildable + (200 - mean) / 10  # Reward buildability and lower slopes
        if score > best_score:
            best_score = score
            best_config = (octaves, strength, buildable, mean)

print("\n" + "="*80)
print("RECOMMENDATION")
print("="*80)

if best_config:
    octaves, strength, buildable, mean = best_config
    print(f"\nBest configuration found:")
    print(f"  Octaves: {octaves}")
    print(f"  Recursive warp strength: {strength:.1f}")
    print(f"  Domain warp: {domain_warp:.0f}")
    print(f"  Result: {buildable:.1f}% buildable, {mean:.1f}% mean slope")
    print(f"\nThis provides scenic realism while maintaining some buildability")
else:
    print("\nNo configuration met criteria (5-15% buildable, <200% mean)")
    print("Consider using domain warp without recursive warp, or further reduce parameters")

print("\n" + "="*80)
print("GRADIENT CONTROL MAP APPROACH")
print("="*80)
print("\nAlternative: Use gradient control map (0.0-1.0) instead of binary (0 or 1)")
print("This would blend smoothly from buildable → moderately scenic → highly scenic")
print("Could apply recursive warp strength proportional to 'scenic intensity'")
print("="*80)
