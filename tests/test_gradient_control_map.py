"""
Test gradient control map approach for smooth buildable-to-scenic transitions.

Instead of binary (0 or 1), use continuous (0.0-1.0) where:
- 1.0 = fully buildable (low octaves, no recursive warp)
- 0.5 = moderately scenic (medium octaves, gentle recursive warp)
- 0.0 = highly scenic (high octaves, strong recursive warp)

This creates smooth visual transitions and avoids the "oscillating" problem.
"""

import numpy as np
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.noise_generator import NoiseGenerator
from src.buildability_enforcer import BuildabilityEnforcer
from src.terrain_parameter_mapper import TerrainParameterMapper


def generate_with_gradient_control(resolution, control_map, seed=42):
    """
    Generate terrain using gradient control map.

    control_map values:
    - 1.0 = fully buildable
    - 0.5 = moderately scenic
    - 0.0 = highly scenic

    Interpolate octaves and recursive warp strength based on control value.
    """
    gen = NoiseGenerator(seed=seed)

    # Generate multiple terrain layers with different characteristics
    print("  Generating buildable layer (octaves=2, no warp)...")
    layer_buildable = gen.generate_perlin(
        resolution=resolution,
        scale=500 * (resolution / 512),
        octaves=2,
        persistence=0.3,
        lacunarity=2.0,
        show_progress=False,
        domain_warp_amp=0.0,
        recursive_warp=False
    )

    print("  Generating moderate layer (octaves=5, gentle recursive)...")
    layer_moderate = gen.generate_perlin(
        resolution=resolution,
        scale=200,
        octaves=5,
        persistence=0.4,
        lacunarity=2.0,
        show_progress=False,
        domain_warp_amp=60.0,
        recursive_warp=True,
        recursive_warp_strength=0.5  # Gentle
    )

    print("  Generating scenic layer (octaves=7, moderate recursive)...")
    layer_scenic = gen.generate_perlin(
        resolution=resolution,
        scale=100,
        octaves=7,
        persistence=0.5,
        lacunarity=2.0,
        show_progress=False,
        domain_warp_amp=60.0,
        recursive_warp=True,
        recursive_warp_strength=1.0  # Moderate (not 4.0!)
    )

    # Blend layers based on control map using smooth interpolation
    # control=1.0 → 100% buildable
    # control=0.5 → 50% buildable, 25% moderate, 25% scenic
    # control=0.0 → 100% scenic

    # Quadratic blending for smoother transitions
    control_squared = control_map ** 2
    control_inv = 1.0 - control_map
    control_inv_squared = control_inv ** 2

    heightmap = (layer_buildable * control_squared +
                 layer_moderate * 2 * control_map * control_inv +
                 layer_scenic * control_inv_squared)

    return heightmap


print("\n" + "="*80)
print("GRADIENT CONTROL MAP APPROACH")
print("="*80)
print("\nUsing continuous control values (0.0-1.0) instead of binary (0 or 1)")
print("Creates smooth transitions from buildable to scenic terrain")
print("="*80)

resolution = 1024
gen = NoiseGenerator(seed=42)

# Test different control map configurations
test_configs = [
    (50.0, "50% average (balanced)"),
    (60.0, "60% average (more buildable)"),
    (70.0, "70% average (mostly buildable)"),
]

for target_pct, label in test_configs:
    print(f"\n{'='*80}")
    print(f"Testing: {label}")
    print(f"{'='*80}")

    # Generate gradient control map (NOT binary)
    print(f"\n[1/3] Generating gradient control map (target={target_pct:.0f}%)...")
    control_map_raw = gen.generate_buildability_control_map(
        resolution=resolution,
        target_percent=target_pct,
        seed=42,
        smoothing_radius=max(10, resolution // 100)  # More smoothing for gradients
    )

    # DON'T binarize - keep as gradient!
    # Normalize to 0-1 range
    control_map = (control_map_raw - control_map_raw.min()) / (control_map_raw.max() - control_map_raw.min())

    print(f"  Control map: min={control_map.min():.2f}, max={control_map.max():.2f}, mean={control_map.mean():.2f}")

    # Generate terrain with gradient control
    print(f"\n[2/3] Generating terrain with gradient control...")
    heightmap = generate_with_gradient_control(resolution, control_map, seed=42)

    # Apply height variation
    heightmap = TerrainParameterMapper.apply_height_variation(heightmap, 1.0)

    # Analyze
    print(f"\n[3/3] Analyzing buildability...")
    stats_before = BuildabilityEnforcer.analyze_buildability(heightmap)
    print(f"  Before enforcement: {stats_before['excellent_buildable_pct']:.1f}% buildable")
    print(f"  Mean slope: {stats_before['mean_slope']:.1f}%")

    # Apply gentle enforcement (sigma=64, not 128)
    print(f"\n  Applying gentle enforcement (sigma=64)...")
    control_binary = (control_map >= 0.5).astype(np.float64)
    heightmap_final, enforcement_stats = BuildabilityEnforcer.enforce_buildability_constraint(
        heightmap=heightmap,
        buildable_mask=control_binary,
        target_pct=target_pct,
        max_iterations=20,
        sigma=64.0,
        tolerance=5.0,
        map_size_meters=14336.0,
        verbose=False
    )

    stats_after = BuildabilityEnforcer.analyze_buildability(heightmap_final)
    print(f"  After enforcement: {stats_after['excellent_buildable_pct']:.1f}% buildable")
    print(f"  Mean slope: {stats_after['mean_slope']:.1f}%")

    success = (target_pct - 10) <= stats_after['excellent_buildable_pct'] <= (target_pct + 10)
    status = "[SUCCESS]" if success else "[PARTIAL]"
    print(f"\n{status} Target={target_pct:.0f}%, Actual={stats_after['excellent_buildable_pct']:.1f}%")

print("\n" + "="*80)
print("CONCLUSION")
print("="*80)
print("\nGradient control map creates smooth transitions between:")
print("  - Buildable zones (low detail, no recursive warp)")
print("  - Moderate zones (medium detail, gentle recursive warp)")
print("  - Scenic zones (high detail, moderate recursive warp)")
print("\nThis avoids the 'oscillating' problem and looks more natural")
print("="*80)
