"""
Test Stage 1 Quick Win 1: Recursive Domain Warping

Verifies that the Inigo Quilez recursive domain warping implementation works correctly.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.noise_generator import NoiseGenerator
import numpy as np
import time

def test_recursive_domain_warping():
    """Test that recursive domain warping produces different output than basic generation."""
    print("\n" + "="*70)
    print("STAGE 1 QUICK WIN 1: RECURSIVE DOMAIN WARPING TEST")
    print("="*70)

    gen = NoiseGenerator(seed=42)
    resolution = 512  # Small for quick test

    # Test 1: Basic generation (no warping)
    print("\n[TEST 1] Generating base terrain (no warping)...")
    start = time.time()
    basic = gen.generate_perlin(
        resolution=resolution,
        scale=100.0,
        octaves=6,
        show_progress=False
    )
    basic_time = time.time() - start
    print(f"  - Generated in {basic_time:.2f}s")
    print(f"  - Stats: min={basic.min():.4f}, max={basic.max():.4f}, mean={basic.mean():.4f}, std={basic.std():.4f}")

    # Test 2: Basic domain warping only
    print("\n[TEST 2] Generating with basic domain warping only...")
    start = time.time()
    basic_warp = gen.generate_perlin(
        resolution=resolution,
        scale=100.0,
        octaves=6,
        show_progress=False,
        domain_warp_amp=60.0
    )
    basic_warp_time = time.time() - start
    print(f"  - Generated in {basic_warp_time:.2f}s")
    print(f"  - Stats: min={basic_warp.min():.4f}, max={basic_warp.max():.4f}, mean={basic_warp.mean():.4f}, std={basic_warp.std():.4f}")

    # Test 3: Recursive domain warping
    print("\n[TEST 3] Generating with RECURSIVE domain warping...")
    start = time.time()
    recursive = gen.generate_perlin(
        resolution=resolution,
        scale=100.0,
        octaves=6,
        show_progress=False,
        domain_warp_amp=60.0,
        recursive_warp=True,
        recursive_warp_strength=4.0
    )
    recursive_time = time.time() - start
    print(f"  - Generated in {recursive_time:.2f}s")
    print(f"  - Stats: min={recursive.min():.4f}, max={recursive.max():.4f}, mean={recursive.mean():.4f}, std={recursive.std():.4f}")

    # Verification
    print("\n" + "="*70)
    print("VERIFICATION")
    print("="*70)

    # Check that outputs differ
    diff_basic_vs_warp = np.abs(basic - basic_warp).mean()
    diff_basic_vs_recursive = np.abs(basic - recursive).mean()
    diff_warp_vs_recursive = np.abs(basic_warp - recursive).mean()

    print(f"\n[DIFFERENCE] Basic vs Basic Warp: {diff_basic_vs_warp:.6f}")
    print(f"[DIFFERENCE] Basic vs Recursive: {diff_basic_vs_recursive:.6f}")
    print(f"[DIFFERENCE] Basic Warp vs Recursive: {diff_warp_vs_recursive:.6f}")

    # Performance overhead
    warp_overhead = basic_warp_time - basic_time
    recursive_overhead = recursive_time - basic_warp_time
    total_overhead = recursive_time - basic_time

    print(f"\n[PERFORMANCE] Basic generation: {basic_time:.2f}s")
    print(f"[PERFORMANCE] Basic warp overhead: +{warp_overhead:.2f}s ({warp_overhead/basic_time*100:.1f}%)")
    print(f"[PERFORMANCE] Recursive warp overhead: +{recursive_overhead:.2f}s ({recursive_overhead/basic_time*100:.1f}%)")
    print(f"[PERFORMANCE] Total overhead: +{total_overhead:.2f}s ({total_overhead/basic_time*100:.1f}%)")

    # Pass/Fail criteria
    print("\n" + "="*70)
    print("RESULTS")
    print("="*70)

    tests_passed = 0
    tests_total = 4

    # Test 1: Outputs should differ significantly
    if diff_basic_vs_recursive > 0.01:
        print("[PASS] Recursive warping produces different output")
        tests_passed += 1
    else:
        print("[FAIL] Recursive warping output too similar to basic")

    # Test 2: Recursive should differ from basic warp
    if diff_warp_vs_recursive > 0.001:
        print("[PASS] Recursive differs from basic warping")
        tests_passed += 1
    else:
        print("[FAIL] Recursive too similar to basic warping")

    # Test 3: Performance should be reasonable (<5s overhead for 512x512)
    if recursive_overhead < 5.0:
        print(f"[PASS] Performance overhead acceptable ({recursive_overhead:.2f}s)")
        tests_passed += 1
    else:
        print(f"[FAIL] Performance overhead too high ({recursive_overhead:.2f}s)")

    # Test 4: Output should be normalized
    if 0.0 <= recursive.min() and recursive.max() <= 1.0:
        print("[PASS] Output properly normalized to [0, 1]")
        tests_passed += 1
    else:
        print("[FAIL] Output not normalized correctly")

    print(f"\n{'='*70}")
    if tests_passed == tests_total:
        print(f"[SUCCESS] All {tests_total} tests passed! Recursive domain warping working correctly.")
    else:
        print(f"[PARTIAL] {tests_passed}/{tests_total} tests passed")
    print("="*70 + "\n")

    return tests_passed == tests_total


if __name__ == "__main__":
    success = test_recursive_domain_warping()
    sys.exit(0 if success else 1)
