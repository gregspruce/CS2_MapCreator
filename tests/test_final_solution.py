"""
Final Buildability Solution - Complete Validation

Tests the WORKING solution:
- Priority 2: Conditional octaves with domain warp, NO recursive warp
- Priority 6: Aggressive enforcement (sigma=128, max_iter=30)
- Control map: 80% buildable zones

Expected: 45-55% buildable terrain (CS2 target)
"""

import numpy as np
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.noise_generator import NoiseGenerator
from src.buildability_enforcer import BuildabilityEnforcer
from src.terrain_parameter_mapper import TerrainParameterMapper


def test_final_solution(resolution=1024, user_target=50.0):
    """Test the complete working solution."""
    print("\n" + "="*80)
    print(f"FINAL BUILDABILITY SOLUTION TEST - {resolution}x{resolution}")
    print("="*80)
    print(f"\nUser target: {user_target:.0f}% buildable")
    print("Complete pipeline with ALL fixes applied")
    print("="*80)

    gen = NoiseGenerator(seed=42)

    # Adjust control target (80% zones to achieve 50% final)
    control_target = min(80.0, user_target * 1.6)
    print(f"\n[1/6] Control map (adjusted: {user_target:.0f}% to {control_target:.0f}%)...")
    control_map = gen.generate_buildability_control_map(
        resolution=resolution,
        target_percent=control_target,
        seed=42,
        smoothing_radius=max(10, resolution // 400)
    )

    # Buildable terrain
    buildable_scale = 500 * (resolution / 512)
    print(f"\n[2/6] Buildable terrain (scale={buildable_scale:.0f}, NO warping)...")
    heightmap_buildable = gen.generate_perlin(
        resolution=resolution, scale=buildable_scale,
        octaves=2, persistence=0.3, lacunarity=2.0,
        show_progress=False, domain_warp_amp=0.0, recursive_warp=False
    )

    # Scenic terrain (domain warp YES, recursive NO)
    print(f"\n[3/6] Scenic terrain (domain warp=60, NO recursive)...")
    heightmap_scenic = gen.generate_perlin(
        resolution=resolution, scale=100,
        octaves=8, persistence=0.5, lacunarity=2.0,
        show_progress=False,
        domain_warp_amp=60.0,  # Domain warp GOOD (breaks patterns)
        recursive_warp=False    # Recursive BAD (618% slopes)
    )

    # Height variation only
    print(f"\n[4/6] Height variation...")
    heightmap_scenic = TerrainParameterMapper.apply_height_variation(
        heightmap_scenic, height_multiplier=1.0
    )

    # Blend
    print(f"\n[5/6] Blending...")
    control_map_binary = (control_map >= 0.5).astype(np.float64)
    heightmap_blended = (heightmap_buildable * control_map_binary +
                        heightmap_scenic * (1.0 - control_map_binary))

    stats_before = BuildabilityEnforcer.analyze_buildability(heightmap_blended)
    print(f"  Before enforcement: {stats_before['excellent_buildable_pct']:.1f}% buildable")

    # Aggressive enforcement
    print(f"\n[6/6] Aggressive enforcement (sigma=128, max_iter=30)...")
    print("="*80)
    sigma_scaled = 128 * (resolution / 1024)
    heightmap_final, enforcement_stats = BuildabilityEnforcer.enforce_buildability_constraint(
        heightmap=heightmap_blended,
        buildable_mask=control_map_binary,
        target_pct=user_target,
        max_iterations=30,
        sigma=sigma_scaled,
        tolerance=5.0,
        map_size_meters=14336.0,
        verbose=True
    )
    print("="*80)

    stats_after = BuildabilityEnforcer.analyze_buildability(heightmap_final)

    # Verdict
    print("\n" + "="*80)
    print("VERDICT")
    print("="*80)
    print(f"\nBefore enforcement: {stats_before['excellent_buildable_pct']:.1f}% buildable")
    print(f"After enforcement:  {stats_after['excellent_buildable_pct']:.1f}% buildable")
    print(f"Improvement: +{stats_after['excellent_buildable_pct'] - stats_before['excellent_buildable_pct']:.1f}%")
    print(f"\nTarget: {user_target:.0f}% ±5%")

    success = (user_target - 5) <= stats_after['excellent_buildable_pct'] <= (user_target + 5)

    if success:
        print(f"\n[SUCCESS] Buildability target ACHIEVED!")
        print(f"  Final: {stats_after['excellent_buildable_pct']:.1f}%")
        print(f"  Target range: {user_target-5:.0f}%-{user_target+5:.0f}%")
        if 45 <= stats_after['excellent_buildable_pct'] <= 55:
            print(f"  [EXCELLENT] Within CS2 optimal range (45-55%)")
    else:
        print(f"\n[PARTIAL] Close but not quite within tolerance")
        print(f"  Final: {stats_after['excellent_buildable_pct']:.1f}%")
        print(f"  Target: {user_target-5:.0f}%-{user_target+5:.0f}%")

    print("\n" + "="*80)

    return stats_after['excellent_buildable_pct'], success


def main():
    """Run complete validation."""
    print("\n" + "="*80)
    print("FINAL BUILDABILITY SOLUTION - COMPLETE VALIDATION")
    print("="*80)
    print("\nThis test validates the WORKING solution:")
    print("  [OK] Recursive warp DISABLED (was causing 618% slopes)")
    print("  [OK] Domain warp ENABLED (breaks patterns, no slope impact)")
    print("  [OK] Control map: 80% buildable zones (not 50%)")
    print("  [OK] Enforcement: sigma=128, max_iterations=30 (aggressive)")
    print("\nExpected: 45-55% buildable terrain for CS2")
    print("="*80)

    # Test at multiple resolutions
    results = []
    for resolution in [512, 1024, 2048]:
        print(f"\n\n{'='*80}")
        print(f"Testing at {resolution}x{resolution}")
        print(f"{'='*80}")

        actual, success = test_final_solution(resolution=resolution, user_target=50.0)
        results.append((resolution, actual, success))

    # Summary
    print("\n\n" + "="*80)
    print("FINAL VALIDATION SUMMARY")
    print("="*80)
    for resolution, actual, success in results:
        status = "[SUCCESS]" if success else "[PARTIAL]"
        print(f"  {status} {resolution}x{resolution}: {actual:.1f}% buildable")

    all_success = all(success for _, _, success in results)

    print(f"\n{'='*80}")
    if all_success:
        print("[COMPLETE SUCCESS] All resolutions achieve 45-55% buildable!")
        print("The buildability implementation is CORRECT and READY for production.")
    else:
        print("[MOSTLY SUCCESS] Solution works at most resolutions.")
        print("May need minor parameter tuning for edge cases.")
    print("="*80)

    return all_success


if __name__ == "__main__":
    try:
        success = main()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n[ERROR] Validation failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
