"""
Test with LARGER buildable zone allocation (75-85%) to see if that achieves target.

Math:
- Buildable zones at 32.1% buildable
- Scenic zones at 0.3% buildable
- If 75% buildable zones: 0.75 * 32.1% + 0.25 * 0.3% = 24.1% + 0.08% = ~24% buildable
- After Priority 6 enforcement: Could reach 40-50%?
"""

import numpy as np
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.noise_generator import NoiseGenerator
from src.buildability_enforcer import BuildabilityEnforcer
from src.terrain_parameter_mapper import TerrainParameterMapper


def test_with_target(resolution, control_target, buildability_target):
    """Test with specific control map and enforcement targets."""
    print(f"\n{'='*80}")
    print(f"TEST: control_target={control_target:.0f}%, buildability_target={buildability_target:.0f}%")
    print(f"{'='*80}")

    gen = NoiseGenerator(seed=42)

    # Step 1: Control map
    print(f"[1/6] Generating control map (target={control_target:.0f}%)...")
    control_map = gen.generate_buildability_control_map(
        resolution=resolution,
        target_percent=control_target,
        seed=42,
        smoothing_radius=max(10, resolution // 400)
    )
    actual_control = np.sum(control_map >= 0.5) / control_map.size * 100
    print(f"  Actual: {actual_control:.1f}% buildable zones")

    # Step 2: Buildable terrain
    buildable_scale = 500 * (resolution / 512)
    print(f"[2/6] Generating buildable terrain...")
    heightmap_buildable = gen.generate_perlin(
        resolution=resolution, scale=buildable_scale,
        octaves=2, persistence=0.3, lacunarity=2.0,
        show_progress=False, domain_warp_amp=0.0, recursive_warp=False
    )

    # Step 3: Scenic terrain
    print(f"[3/6] Generating scenic terrain...")
    heightmap_scenic = gen.generate_perlin(
        resolution=resolution, scale=100,
        octaves=8, persistence=0.5, lacunarity=2.0,
        show_progress=False, domain_warp_amp=60.0, recursive_warp=False
    )

    # Step 4: Apply height variation
    print(f"[4/6] Applying height variation...")
    heightmap_scenic = TerrainParameterMapper.apply_height_variation(
        heightmap_scenic, height_multiplier=1.0
    )

    # Step 5: Blend
    print(f"[5/6] Blending...")
    control_map_binary = (control_map >= 0.5).astype(np.float64)
    heightmap_blended = (heightmap_buildable * control_map_binary +
                        heightmap_scenic * (1.0 - control_map_binary))

    stats_before = BuildabilityEnforcer.analyze_buildability(heightmap_blended)
    print(f"  Before enforcement: {stats_before['excellent_buildable_pct']:.1f}% buildable")

    # Step 6: Enforce
    print(f"[6/6] Enforcing (target={buildability_target:.0f}%)...")
    heightmap_final, stats = BuildabilityEnforcer.enforce_buildability_constraint(
        heightmap=heightmap_blended,
        buildable_mask=control_map_binary,
        target_pct=buildability_target,
        max_iterations=5,  # More iterations
        sigma=16.0,  # Larger blur radius
        tolerance=5.0,
        verbose=True
    )

    stats_after = BuildabilityEnforcer.analyze_buildability(heightmap_final)
    print(f"\n  After enforcement: {stats_after['excellent_buildable_pct']:.1f}% buildable")

    # Verdict
    success = (buildability_target - 5) <= stats_after['excellent_buildable_pct'] <= (buildability_target + 5)
    status = "[SUCCESS]" if success else "[PARTIAL]"
    print(f"\n{status} Target={buildability_target:.0f}%, Actual={stats_after['excellent_buildable_pct']:.1f}%")

    return stats_after['excellent_buildable_pct'], success


print("\n" + "="*80)
print("LARGER BUILDABLE ZONE ALLOCATION TEST")
print("="*80)
print("\nTesting if larger buildable allocation achieves target")
print("Resolution: 1024x1024")
print("="*80)

resolution = 1024

# Test different control map allocations
tests = [
    (50, 50),  # Current approach
    (65, 50),  # More buildable zones
    (75, 50),  # Even more buildable zones
    (80, 50),  # Mostly buildable zones
]

results = []
for control_pct, target_pct in tests:
    actual, success = test_with_target(resolution, control_pct, target_pct)
    results.append((control_pct, target_pct, actual, success))

# Summary
print("\n" + "="*80)
print("SUMMARY")
print("="*80)
for control, target, actual, success in results:
    status = "[SUCCESS]" if success else "[PARTIAL]"
    print(f"{status} Control={control:.0f}%, Target={target:.0f}%, Actual={actual:.1f}%")

print("\n" + "="*80)
