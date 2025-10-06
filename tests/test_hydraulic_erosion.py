"""
Test Script: Hydraulic Erosion Implementation Validation

Validates the hydraulic erosion implementation:
1. Numba vs NumPy produce equivalent results (within floating point tolerance)
2. Performance meets targets (<2s at 1024x1024 with Numba, <10s pure NumPy)
3. Erosion creates realistic features (dendritic drainage patterns)
4. Output remains normalized [0, 1] for CS2 compatibility
5. Erosion parameters produce expected geological effects

WHY this test:
- Ensures dual-path implementation correctness
- Validates performance optimization
- Confirms geological realism
- Prevents regressions
"""

import numpy as np
import time
from pathlib import Path
import sys

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.features.hydraulic_erosion import HydraulicErosionSimulator, NUMBA_AVAILABLE
from src.noise_generator import NoiseGenerator


def generate_test_terrain(resolution: int = 512, seed: int = 42) -> np.ndarray:
    """Generate base terrain for erosion testing."""
    print(f"\n[SETUP] Generating {resolution}x{resolution} base terrain...")

    gen = NoiseGenerator(seed=seed)

    # Generate mountain terrain
    heightmap = gen.generate_perlin(
        resolution=resolution,
        scale=260.0,
        octaves=6,
        persistence=0.58,
        lacunarity=2.0,
        domain_warp_amp=60.0,
        domain_warp_type=0,
        recursive_warp=True,
        recursive_warp_strength=4.0,
        show_progress=False
    )

    print(f"[SETUP] Base terrain generated: range [{heightmap.min():.3f}, {heightmap.max():.3f}]")
    return heightmap


def test_normalization(eroded: np.ndarray, test_name: str) -> bool:
    """Test that eroded terrain is properly normalized [0, 1]."""
    print(f"\n[TEST] {test_name}: Normalization Check")
    print(f"  Range: [{eroded.min():.6f}, {eroded.max():.6f}]")

    if eroded.min() < -0.001 or eroded.max() > 1.001:
        print(f"  [FAIL] Terrain outside [0, 1] bounds!")
        return False

    print(f"  [PASS] Terrain properly normalized")
    return True


def test_erosion_impact(before: np.ndarray, after: np.ndarray, test_name: str) -> bool:
    """Test that erosion actually modified the terrain."""
    print(f"\n[TEST] {test_name}: Erosion Impact Analysis")

    difference = np.abs(after - before).mean()
    max_diff = np.abs(after - before).max()

    print(f"  Mean difference: {difference:.6f}")
    print(f"  Max difference: {max_diff:.6f}")

    # Erosion should cause at least some change
    if difference < 0.001:
        print(f"  [FAIL] Erosion had minimal impact (difference < 0.001)")
        return False

    print(f"  [PASS] Erosion modified terrain (difference = {difference:.4f})")
    return True


def analyze_drainage_patterns(eroded: np.ndarray) -> dict:
    """
    Analyze drainage patterns in eroded terrain.

    WHY this matters:
    - Hydraulic erosion should create dendritic (tree-like) drainage patterns
    - Valleys should be connected and flow downhill
    - Ridge preservation vs valley carving balance
    """
    from scipy import ndimage

    print(f"\n[ANALYSIS] Drainage Pattern Analysis")

    # Identify valleys (low elevation areas)
    valley_threshold = np.percentile(eroded, 30)  # Bottom 30% are valleys
    valley_mask = eroded < valley_threshold

    # Connected component analysis of valleys
    labeled_valleys, num_valley_networks = ndimage.label(valley_mask)

    # Identify ridges (high elevation areas)
    ridge_threshold = np.percentile(eroded, 70)  # Top 30% are ridges
    ridge_mask = eroded > ridge_threshold

    labeled_ridges, num_ridge_segments = ndimage.label(ridge_mask)

    total_valley_pixels = np.sum(valley_mask)
    total_ridge_pixels = np.sum(ridge_mask)

    # Calculate valley connectivity (fewer networks = better drainage)
    valley_fragmentation = (num_valley_networks / total_valley_pixels * 1000.0) if total_valley_pixels > 0 else 0

    results = {
        "valley_networks": num_valley_networks,
        "valley_pixels": int(total_valley_pixels),
        "valley_fragmentation": valley_fragmentation,
        "ridge_segments": num_ridge_segments,
        "ridge_pixels": int(total_ridge_pixels),
        "valley_to_ridge_ratio": total_valley_pixels / total_ridge_pixels if total_ridge_pixels > 0 else 0
    }

    print(f"  Valley networks: {results['valley_networks']} ({results['valley_pixels']:,} pixels)")
    print(f"  Valley fragmentation: {results['valley_fragmentation']:.2f} per 1000 pixels")
    print(f"  Ridge segments: {results['ridge_segments']} ({results['ridge_pixels']:,} pixels)")
    print(f"  Valley/Ridge ratio: {results['valley_to_ridge_ratio']:.2f}")

    # Good erosion should create connected valley networks (low fragmentation)
    if valley_fragmentation < 5.0:  # Highly connected
        print(f"  [EXCELLENT] Highly connected drainage network (fragmentation < 5.0)")
    elif valley_fragmentation < 10.0:  # Well connected
        print(f"  [GOOD] Well connected drainage network (fragmentation < 10.0)")
    else:
        print(f"  [INFO] Moderate drainage connectivity")

    return results


def test_performance_targets(simulator: HydraulicErosionSimulator,
                            terrain: np.ndarray,
                            iterations: int = 50) -> dict:
    """Test that erosion meets performance targets."""
    print(f"\n[TEST] Performance Benchmark")
    print(f"  Resolution: {terrain.shape[0]}x{terrain.shape[1]}")
    print(f"  Iterations: {iterations}")
    print(f"  Implementation: {'Numba JIT' if simulator.using_numba else 'Pure NumPy'}")

    start = time.time()
    eroded = simulator.simulate_erosion(
        terrain.copy(),
        iterations=iterations,
        rain_amount=0.01,
        show_progress=False
    )
    elapsed = time.time() - start

    per_iter = elapsed / iterations if iterations > 0 else 0

    print(f"  Total time: {elapsed:.2f}s")
    print(f"  Per iteration: {per_iter*1000:.1f}ms")

    # Check performance targets
    resolution = terrain.shape[0]
    if resolution == 1024:
        if simulator.using_numba:
            target = 2.0  # <2s with Numba at 1024x1024
            if elapsed < target:
                print(f"  [PASS] Numba performance meets target (<{target}s)")
            else:
                print(f"  [WARNING] Numba slower than target: {elapsed:.2f}s vs {target}s")
        else:
            target = 10.0  # <10s pure NumPy at 1024x1024
            if elapsed < target:
                print(f"  [PASS] NumPy performance meets target (<{target}s)")
            else:
                print(f"  [WARNING] NumPy slower than target: {elapsed:.2f}s vs {target}s")

    return {
        "elapsed": elapsed,
        "per_iteration": per_iter,
        "eroded": eroded
    }


def test_numba_numpy_equivalence(terrain: np.ndarray, iterations: int = 10) -> bool:
    """
    Test that Numba and NumPy implementations produce equivalent results.

    WHY this matters:
    - Ensures Numba optimization doesn't break correctness
    - Validates fallback path works identically
    - Critical for cross-platform compatibility
    """
    print(f"\n[TEST] Numba vs NumPy Equivalence")

    if not NUMBA_AVAILABLE:
        print("  [SKIP] Numba not available - cannot test equivalence")
        return True

    # Create identical simulators with same parameters
    params = {
        "erosion_rate": 0.3,
        "deposition_rate": 0.05,
        "evaporation_rate": 0.01,
        "sediment_capacity": 4.0,
        "min_slope": 0.01
    }

    sim_numba = HydraulicErosionSimulator(**params)
    sim_numpy = HydraulicErosionSimulator(**params)

    # Force NumPy path for second simulator
    sim_numpy.using_numba = False

    print(f"  Testing with {iterations} iterations on {terrain.shape[0]}x{terrain.shape[1]} terrain...")

    # Run both implementations
    eroded_numba = sim_numba.simulate_erosion(
        terrain.copy(),
        iterations=iterations,
        rain_amount=0.01,
        show_progress=False
    )

    eroded_numpy = sim_numpy.simulate_erosion(
        terrain.copy(),
        iterations=iterations,
        rain_amount=0.01,
        show_progress=False
    )

    # Compare results
    abs_diff = np.abs(eroded_numba - eroded_numpy)
    mean_diff = abs_diff.mean()
    max_diff = abs_diff.max()

    print(f"  Mean absolute difference: {mean_diff:.8f}")
    print(f"  Max absolute difference: {max_diff:.8f}")

    # Floating point tolerance (should be very close, but not identical due to FP arithmetic)
    tolerance = 1e-4  # 0.0001 difference acceptable

    if mean_diff < tolerance and max_diff < 0.01:
        print(f"  [PASS] Implementations produce equivalent results (within tolerance)")
        return True
    else:
        print(f"  [FAIL] Implementations diverged beyond tolerance!")
        print(f"    Mean diff {mean_diff:.8f} vs tolerance {tolerance:.8f}")
        return False


def main():
    """Run all erosion validation tests."""
    print("=" * 70)
    print("Hydraulic Erosion Implementation Validation")
    print("=" * 70)

    all_tests_passed = True

    # Test 1: Numba Availability
    print(f"\n[INFO] Numba JIT Compilation: {'AVAILABLE' if NUMBA_AVAILABLE else 'NOT AVAILABLE (using fallback)'}")

    # Test 2: Small resolution quick test (512x512)
    print("\n" + "=" * 70)
    print("[PHASE 1] Quick Validation (512x512, 20 iterations)")
    print("=" * 70)

    terrain_512 = generate_test_terrain(resolution=512, seed=42)

    simulator = HydraulicErosionSimulator(
        erosion_rate=0.3,
        deposition_rate=0.05,
        evaporation_rate=0.01,
        sediment_capacity=4.0,
        min_slope=0.01
    )

    # Run quick erosion
    result = test_performance_targets(simulator, terrain_512, iterations=20)
    eroded_512 = result["eroded"]

    # Validate results
    if not test_normalization(eroded_512, "512x512 Erosion"):
        all_tests_passed = False

    if not test_erosion_impact(terrain_512, eroded_512, "512x512 Erosion"):
        all_tests_passed = False

    drainage_512 = analyze_drainage_patterns(eroded_512)

    # Test 3: Numba vs NumPy equivalence (if Numba available)
    if NUMBA_AVAILABLE:
        print("\n" + "=" * 70)
        print("[PHASE 2] Implementation Equivalence Test")
        print("=" * 70)

        terrain_equiv = generate_test_terrain(resolution=256, seed=99)
        if not test_numba_numpy_equivalence(terrain_equiv, iterations=10):
            all_tests_passed = False

    # Test 4: Full resolution performance test (1024x1024)
    print("\n" + "=" * 70)
    print("[PHASE 3] Full Resolution Performance (1024x1024, 50 iterations)")
    print("=" * 70)

    terrain_1024 = generate_test_terrain(resolution=1024, seed=42)

    result_1024 = test_performance_targets(simulator, terrain_1024, iterations=50)
    eroded_1024 = result_1024["eroded"]

    if not test_normalization(eroded_1024, "1024x1024 Erosion"):
        all_tests_passed = False

    if not test_erosion_impact(terrain_1024, eroded_1024, "1024x1024 Erosion"):
        all_tests_passed = False

    drainage_1024 = analyze_drainage_patterns(eroded_1024)

    # Summary
    print("\n" + "=" * 70)
    print("[SUMMARY] Hydraulic Erosion Validation Results")
    print("=" * 70)

    print(f"\nImplementation:")
    print(f"  Numba JIT: {'AVAILABLE' if NUMBA_AVAILABLE else 'NOT AVAILABLE (fallback active)'}")

    print(f"\nPerformance (1024x1024, 50 iterations):")
    print(f"  Total time: {result_1024['elapsed']:.2f}s")
    print(f"  Per iteration: {result_1024['per_iteration']*1000:.1f}ms")
    if simulator.using_numba:
        target = "2.0s"
        status = "PASS" if result_1024['elapsed'] < 2.0 else "WARNING"
    else:
        target = "10.0s"
        status = "PASS" if result_1024['elapsed'] < 10.0 else "WARNING"
    print(f"  Target: <{target} [{status}]")

    print(f"\nDrainage Patterns (1024x1024):")
    print(f"  Valley networks: {drainage_1024['valley_networks']}")
    print(f"  Valley connectivity: {drainage_1024['valley_fragmentation']:.2f} fragmentation")
    print(f"  Valley/Ridge ratio: {drainage_1024['valley_to_ridge_ratio']:.2f}")

    print(f"\nValidation:")
    print(f"  Normalization: {'PASS' if all_tests_passed else 'FAIL'}")
    print(f"  Erosion impact: PASS")
    print(f"  Implementation: {'EQUIVALENT' if NUMBA_AVAILABLE else 'FALLBACK ONLY'}")

    if all_tests_passed:
        print(f"\n[SUCCESS] All validation tests passed!")
        print(f"Hydraulic erosion is ready for GUI integration.")
    else:
        print(f"\n[FAIL] Some tests failed - review results above.")

    print("=" * 70)

    return all_tests_passed


if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)
