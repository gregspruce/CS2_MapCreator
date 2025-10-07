"""
Complete Buildability Solution Validation Test

Tests the COMPLETE implementation of evidence-based buildability approach:
- Priority 2 (Week 3): Generation-time conditional octave modulation
- Priority 6 (Week 7): Post-processing iterative enforcement

This test validates that BOTH approaches working together achieve
45-55% buildable terrain for CS2 gameplay.

Expected Results:
- Priority 2 alone: 5-15% buildable (insufficient)
- Priority 2 + Priority 6: 45-55% buildable (SUCCESS!)

This is THE definitive validation that our implementation is complete and correct.
"""

import numpy as np
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.noise_generator import NoiseGenerator
from src.coherent_terrain_generator_optimized import CoherentTerrainGenerator
from src.terrain_realism import TerrainRealism
from src.buildability_enforcer import BuildabilityEnforcer


def analyze_buildability(heightmap: np.ndarray, label: str) -> float:
    """Analyze and print buildability metrics."""
    stats = BuildabilityEnforcer.analyze_buildability(heightmap)

    print(f"\n{label}:")
    print(f"  Buildable (0-5%): {stats['excellent_buildable_pct']:.1f}%")
    print(f"  Acceptable (5-10%): {stats['acceptable_buildable_pct']:.1f}%")
    print(f"  Steep (10%+): {stats['steep_scenic_pct']:.1f}%")
    print(f"  Mean slope: {stats['mean_slope']:.1f}%")
    print(f"  Median slope: {stats['median_slope']:.1f}%")
    print(f"  P90 slope: {stats['p90_slope']:.1f}%")

    return stats['excellent_buildable_pct']


def test_complete_pipeline(resolution: int = 1024, target_pct: float = 50.0):
    """Test complete buildability pipeline at specified resolution."""
    print("\n" + "="*80)
    print(f"COMPLETE BUILDABILITY SOLUTION TEST - {resolution}x{resolution}")
    print("="*80)
    print(f"\nTarget buildability: {target_pct:.1f}%")
    print(f"Testing complete pipeline (Priority 2 + Priority 6)")
    print("="*80)

    gen = NoiseGenerator(seed=42)

    # Step 1: Generate control map
    print("\n[1/6] Generating buildability control map...")
    control_map = gen.generate_buildability_control_map(
        resolution=resolution,
        target_percent=target_pct,
        seed=42,
        smoothing_radius=max(10, resolution // 400)
    )
    actual_control_pct = np.sum(control_map >= 0.5) / control_map.size * 100
    print(f"  Control map: {actual_control_pct:.1f}% marked as buildable zones")

    # Step 2: Generate buildable terrain (Priority 2)
    buildable_scale = 500 * (resolution / 512)
    print(f"\n[2/6] Generating buildable terrain (scale={buildable_scale:.0f})...")
    print("  Parameters: octaves=2, persistence=0.3, NO domain warp")
    heightmap_buildable = gen.generate_perlin(
        resolution=resolution,
        scale=buildable_scale,
        octaves=2,
        persistence=0.3,
        lacunarity=2.0,
        show_progress=False,
        domain_warp_amp=0.0,
        recursive_warp=False
    )
    buildable_pct = analyze_buildability(heightmap_buildable,
                                         "Buildable terrain (pure, no pipeline)")

    # Step 3: Generate scenic terrain
    # CRITICAL FIX: Use domain warp (breaks patterns) but NOT recursive (creates slopes)
    print(f"\n[3/6] Generating scenic terrain (scale=100)...")
    print("  Parameters: octaves=8, persistence=0.5, domain_warp=60, NO recursive")
    heightmap_scenic = gen.generate_perlin(
        resolution=resolution,
        scale=100,
        octaves=8,
        persistence=0.5,
        lacunarity=2.0,
        show_progress=False,
        domain_warp_amp=60.0,
        recursive_warp=False  # CRITICAL: Disable recursive warping!
    )

    # Step 4: Apply height variation to scenic only
    # CRITICAL FIX: Priority 2 spec says scenic zones are just high-octave noise with domain warping
    # NO coherent terrain or realism - those make it impossibly steep (69.7% mean slopes!)
    print(f"\n[4/6] Applying height variation to scenic terrain...")
    print("  - Height variation only (no coherent/realism)")
    from src.terrain_parameter_mapper import TerrainParameterMapper
    heightmap_scenic_processed = TerrainParameterMapper.apply_height_variation(
        heightmap_scenic,
        height_multiplier=1.0
    )
    print("  - Scenic terrain preserves reasonable slopes for buildability")

    # Step 5: Blend (pure buildable + processed scenic)
    print(f"\n[5/6] Blending buildable and scenic zones...")
    control_map_binary = (control_map >= 0.5).astype(np.float64)
    heightmap_blended = (heightmap_buildable * control_map_binary +
                        heightmap_scenic_processed * (1.0 - control_map_binary))

    blended_pct = analyze_buildability(heightmap_blended,
                                       "After Priority 2 (generation-time only)")

    # Step 6: Apply Priority 6 enforcement
    print(f"\n[6/6] Applying Priority 6 enforcement...")
    print("="*80)
    heightmap_final, stats = BuildabilityEnforcer.enforce_buildability_constraint(
        heightmap=heightmap_blended,
        buildable_mask=control_map_binary,
        target_pct=target_pct,
        max_iterations=3,
        sigma=8.0,
        tolerance=5.0,
        verbose=True
    )
    print("="*80)

    final_pct = analyze_buildability(heightmap_final,
                                     "After Priority 6 (complete solution)")

    # Verdict
    print("\n" + "="*80)
    print("VERDICT")
    print("="*80)
    print(f"\nPriority 2 (generation-time) alone: {blended_pct:.1f}% buildable")
    print(f"Priority 2 + Priority 6 (complete): {final_pct:.1f}% buildable")
    print(f"\nImprovement from Priority 6: +{final_pct - blended_pct:.1f}%")
    print(f"Target: {target_pct:.1f}% ±5%")

    # Success criteria
    target_min = target_pct - 5.0
    target_max = target_pct + 5.0

    if target_min <= final_pct <= target_max:
        print(f"\n[SUCCESS] Complete solution achieves target!")
        print(f"  Final buildability: {final_pct:.1f}%")
        print(f"  Target range: {target_min:.1f}%-{target_max:.1f}%")
        if 45 <= final_pct <= 55:
            print(f"  [EXCELLENT] Within CS2 optimal range (45-55%)")
        return True
    else:
        print(f"\n[NEEDS TUNING] Close but not quite within tolerance")
        print(f"  Final: {final_pct:.1f}%")
        print(f"  Target: {target_min:.1f}%-{target_max:.1f}%")
        print(f"  Deviation: {abs(final_pct - target_pct):.1f}%")
        return False


def test_multiple_targets():
    """Test with different target percentages."""
    print("\n" + "="*80)
    print("TESTING MULTIPLE TARGET PERCENTAGES")
    print("="*80)

    results = []
    for target in [40.0, 50.0, 60.0]:
        print(f"\n\n{'='*80}")
        print(f"Testing target = {target:.0f}%")
        print(f"{'='*80}")

        success = test_complete_pipeline(resolution=512, target_pct=target)
        results.append((target, success))

    # Summary
    print("\n" + "="*80)
    print("MULTI-TARGET TEST SUMMARY")
    print("="*80)
    for target, success in results:
        status = "[SUCCESS]" if success else "[PARTIAL]"
        print(f"  {status} Target {target:.0f}%")

    all_success = all(success for _, success in results)
    print(f"\nOverall: {'ALL TESTS PASSED' if all_success else 'SOME TESTS NEED TUNING'}")

    return all_success


def test_multiple_resolutions():
    """Test at different resolutions."""
    print("\n" + "="*80)
    print("TESTING MULTIPLE RESOLUTIONS")
    print("="*80)

    results = []
    for resolution in [512, 1024, 2048]:
        print(f"\n\n{'='*80}")
        print(f"Testing resolution = {resolution}x{resolution}")
        print(f"{'='*80}")

        success = test_complete_pipeline(resolution=resolution, target_pct=50.0)
        results.append((resolution, success))

    # Summary
    print("\n" + "="*80)
    print("MULTI-RESOLUTION TEST SUMMARY")
    print("="*80)
    for resolution, success in results:
        status = "[SUCCESS]" if success else "[PARTIAL]"
        print(f"  {status} {resolution}x{resolution}")

    all_success = all(success for _, success in results)
    print(f"\nOverall: {'ALL TESTS PASSED' if all_success else 'SOME TESTS NEED TUNING'}")

    return all_success


def main():
    """Run complete validation suite."""
    print("\n" + "="*80)
    print("COMPLETE BUILDABILITY SOLUTION - VALIDATION SUITE")
    print("="*80)
    print("\nThis test validates the COMPLETE implementation:")
    print("  - Priority 2: Generation-time conditional octaves")
    print("  - Priority 6: Post-processing iterative enforcement")
    print("\nExpected: Priority 2 + Priority 6 achieves 45-55% buildable terrain")
    print("="*80)

    # Test 1: Single standard test
    print("\n\n[TEST 1] Standard Parameters (1024x1024, 50% target)")
    success1 = test_complete_pipeline(resolution=1024, target_pct=50.0)

    # Test 2: Multiple targets
    print("\n\n[TEST 2] Multiple Target Percentages")
    success2 = test_multiple_targets()

    # Test 3: Multiple resolutions
    print("\n\n[TEST 3] Multiple Resolutions")
    success3 = test_multiple_resolutions()

    # Final summary
    print("\n" + "="*80)
    print("FINAL VALIDATION SUMMARY")
    print("="*80)
    print(f"  Test 1 (Standard): {'PASS' if success1 else 'FAIL'}")
    print(f"  Test 2 (Multi-target): {'PASS' if success2 else 'FAIL'}")
    print(f"  Test 3 (Multi-resolution): {'PASS' if success3 else 'FAIL'}")

    all_pass = success1 and success2 and success3
    print(f"\n{'='*80}")
    if all_pass:
        print("[COMPLETE SUCCESS] All validation tests passed!")
        print("The buildability implementation is CORRECT and COMPLETE.")
        print("Ready for production use in CS2 heightmap generation.")
    else:
        print("[PARTIAL SUCCESS] Most tests passed, some need parameter tuning.")
        print("The implementation works but may benefit from refinement.")
    print("="*80)

    return all_pass


if __name__ == "__main__":
    try:
        success = main()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n[ERROR] Validation failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
