"""
Test MUCH more aggressive Priority 6 enforcement parameters.

Current: sigma=16, iterations=5 → only +2% improvement
Try: sigma=64, iterations=20 → should be able to flatten anything
"""

import numpy as np
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.noise_generator import NoiseGenerator
from src.buildability_enforcer import BuildabilityEnforcer
from src.terrain_parameter_mapper import TerrainParameterMapper


print("\n" + "="*80)
print("AGGRESSIVE ENFORCEMENT TEST")
print("="*80)
print("\nTesting much more aggressive Priority 6 parameters")
print("Control: 80% buildable zones, Resolution: 1024")
print("="*80)

resolution = 1024
gen = NoiseGenerator(seed=42)

# Generate terrain
print("\n[1-5] Generating terrain...")
control_map = gen.generate_buildability_control_map(
    resolution=resolution, target_percent=80.0, seed=42,
    smoothing_radius=max(10, resolution // 400)
)

buildable_scale = 500 * (resolution / 512)
heightmap_buildable = gen.generate_perlin(
    resolution=resolution, scale=buildable_scale,
    octaves=2, persistence=0.3, lacunarity=2.0,
    show_progress=False, domain_warp_amp=0.0, recursive_warp=False
)

heightmap_scenic = gen.generate_perlin(
    resolution=resolution, scale=100,
    octaves=8, persistence=0.5, lacunarity=2.0,
    show_progress=False, domain_warp_amp=60.0, recursive_warp=False
)

heightmap_scenic = TerrainParameterMapper.apply_height_variation(
    heightmap_scenic, height_multiplier=1.0
)

control_map_binary = (control_map >= 0.5).astype(np.float64)
heightmap_blended = (heightmap_buildable * control_map_binary +
                    heightmap_scenic * (1.0 - control_map_binary))

stats_before = BuildabilityEnforcer.analyze_buildability(heightmap_blended)
print(f"Before enforcement: {stats_before['excellent_buildable_pct']:.1f}% buildable\n")

# Test different enforcement configurations
configs = [
    (16, 5, "Current (sigma=16, iter=5)"),
    (32, 10, "Moderate (sigma=32, iter=10)"),
    (64, 20, "Aggressive (sigma=64, iter=20)"),
    (128, 30, "Extreme (sigma=128, iter=30)"),
]

for sigma, iterations, label in configs:
    print(f"\n{'='*80}")
    print(f"{label}")
    print(f"{'='*80}")

    heightmap_test = heightmap_blended.copy()
    heightmap_final, stats = BuildabilityEnforcer.enforce_buildability_constraint(
        heightmap=heightmap_test,
        buildable_mask=control_map_binary,
        target_pct=50.0,
        max_iterations=iterations,
        sigma=sigma,
        tolerance=5.0,
        verbose=True
    )

    stats_after = BuildabilityEnforcer.analyze_buildability(heightmap_final)
    improvement = stats_after['excellent_buildable_pct'] - stats_before['excellent_buildable_pct']
    print(f"\nResult: {stats_after['excellent_buildable_pct']:.1f}% buildable (+{improvement:.1f}%)")

    if 45 <= stats_after['excellent_buildable_pct'] <= 55:
        print(f"[SUCCESS] Within target range (45-55%)!")

print("\n" + "="*80)
print("CONCLUSION")
print("="*80)
