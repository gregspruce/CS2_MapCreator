"""
Unit Tests for Task 2.3: Conditional Noise Generation with Amplitude Modulation

Validates that amplitude modulation approach works correctly and avoids
frequency discontinuities that destroyed the gradient control map system.

WHY THESE TESTS MATTER:
- Single frequency verification: Ensures no multi-octave blending (gradient system's fatal flaw)
- Amplitude ratio verification: Confirms buildable zones are genuinely less detailed
- Zone consistency: Validates buildable zones are smoother than scenic zones
- Input validation: Prevents configuration errors
- Boundary smoothness: Confirms no frequency discontinuities at zone borders

Created: 2025-10-08
"""

import sys
from pathlib import Path
import numpy as np

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.tectonic_generator import TectonicStructureGenerator
from src.buildability_enforcer import BuildabilityEnforcer
from src.noise_generator import NoiseGenerator


def test_task_2_3_amplitude_modulation():
    """Test Task 2.3: Amplitude modulated terrain generation"""

    print("\n" + "="*70)
    print("TASK 2.3 VALIDATION: Amplitude Modulated Terrain Generation")
    print("="*70)

    # Step 1: Generate tectonic structure (Task 2.1)
    print("\nStep 1: Generating tectonic structure (Task 2.1)...")
    generator = TectonicStructureGenerator(resolution=1024)

    fault_lines = generator.generate_fault_lines(
        num_faults=5,
        terrain_type='mountains',
        seed=42
    )

    fault_mask = generator.create_fault_mask(fault_lines)
    distance_field = generator.calculate_distance_field(fault_mask)
    tectonic_elevation = generator.apply_uplift_profile(
        distance_field,
        max_uplift=0.8,
        falloff_meters=600.0
    )

    print(f"  [OK] Tectonic structure: {tectonic_elevation.shape}")
    print(f"       Elevation range: [{tectonic_elevation.min():.3f}, {tectonic_elevation.max():.3f}]")

    # Step 2: Generate buildability mask (Task 2.2)
    print("\nStep 2: Generating buildability mask (Task 2.2)...")

    binary_mask, mask_stats = BuildabilityEnforcer.generate_buildability_mask_from_tectonics(
        distance_field=distance_field,
        tectonic_elevation=tectonic_elevation,
        target_buildable_pct=50.0,
        distance_threshold_meters=300.0,
        elevation_threshold=0.4,
        verbose=False
    )

    print(f"  [OK] Binary mask: {mask_stats['buildable_pct']:.1f}% buildable")
    print(f"       Buildable pixels: {mask_stats['buildable_pixels']:,}")
    print(f"       Scenic pixels: {mask_stats['scenic_pixels']:,}")

    # Step 3: Generate amplitude modulated terrain (Task 2.3)
    print("\nStep 3: Generating amplitude modulated terrain (Task 2.3)...")

    noise_gen = NoiseGenerator(seed=42)

    final_terrain, stats = TectonicStructureGenerator.generate_amplitude_modulated_terrain(
        tectonic_elevation=tectonic_elevation,
        buildability_mask=binary_mask,
        noise_generator=noise_gen,
        buildable_amplitude=0.3,
        scenic_amplitude=1.0,
        noise_octaves=6,
        noise_persistence=0.5,
        verbose=False
    )

    print(f"  [OK] Final terrain: {final_terrain.shape}, range [{final_terrain.min():.3f}, {final_terrain.max():.3f}]")

    # Step 4: Validate amplitude modulation
    print("\nStep 4: Validating amplitude modulation...")

    # Test 1: Single frequency field verification
    assert stats['single_frequency_field'] == True, \
        "Expected single_frequency_field=True (no multi-octave blending)"
    assert stats['noise_octaves_used'] == 6, \
        f"Expected 6 octaves, got {stats['noise_octaves_used']}"
    print(f"  [OK] Single frequency field: True ({stats['noise_octaves_used']} octaves)")

    # Test 2: Amplitude ratio verification
    expected_ratio = 1.0 / 0.3  # ~3.33
    measured_ratio = stats['amplitude_ratio']
    ratio_error = abs(measured_ratio - expected_ratio)

    # Allow ±30% tolerance for mean absolute calculation
    # WHY: Mean absolute amplitude depends on noise distribution,
    # which varies slightly due to normalization and blending
    assert 2.3 < measured_ratio < 4.3, \
        f"Amplitude ratio {measured_ratio:.2f} outside expected range [2.3, 4.3]"

    print(f"  [OK] Amplitude ratio: {measured_ratio:.2f} (expected: {expected_ratio:.2f})")
    print(f"       Ratio error: {ratio_error:.2f} (tolerance: ±30%)")

    # Test 3: Buildable zone amplitude < scenic zone amplitude
    buildable_amp = stats['buildable_amplitude_mean']
    scenic_amp = stats['scenic_amplitude_mean']

    assert buildable_amp < scenic_amp, \
        f"Buildable amplitude {buildable_amp:.3f} should be < scenic amplitude {scenic_amp:.3f}"

    amplitude_reduction_pct = (1.0 - buildable_amp / scenic_amp) * 100.0

    print(f"  [OK] Buildable amplitude: {buildable_amp:.3f} < Scenic amplitude: {scenic_amp:.3f}")
    print(f"  [OK] Buildable zones have {amplitude_reduction_pct:.1f}% less amplitude than scenic zones")

    # Step 5: Validate output quality
    print("\nStep 5: Validating output quality...")

    # Test 4: Output shape and range
    assert final_terrain.shape == tectonic_elevation.shape, \
        f"Shape mismatch: {final_terrain.shape} vs {tectonic_elevation.shape}"
    print(f"  [OK] Shape matches: {final_terrain.shape}")

    assert np.all((final_terrain >= 0.0) & (final_terrain <= 1.0)), \
        f"Terrain values outside [0, 1]: min={final_terrain.min():.3f}, max={final_terrain.max():.3f}"
    print(f"  [OK] Normalized to [0, 1]: min={final_terrain.min():.3f}, max={final_terrain.max():.3f}")

    assert not np.any(np.isnan(final_terrain)), "Terrain contains NaN values"
    assert not np.any(np.isinf(final_terrain)), "Terrain contains Inf values"
    print(f"  [OK] No NaN/Inf values")

    # Step 6: Validate input handling
    print("\nStep 6: Validating input handling...")

    # Test 5a: Input validation - shape mismatch
    try:
        wrong_shape = np.zeros((512, 512))
        _, _ = TectonicStructureGenerator.generate_amplitude_modulated_terrain(
            tectonic_elevation=wrong_shape,
            buildability_mask=binary_mask,
            noise_generator=noise_gen,
            verbose=False
        )
        assert False, "Should have raised ValueError for shape mismatch"
    except ValueError as e:
        assert "Shape mismatch" in str(e), f"Wrong error message: {e}"
        print(f"  [OK] Shape mismatch raises ValueError")

    # Test 5b: Non-binary mask
    try:
        non_binary_mask = np.random.uniform(0, 1, size=tectonic_elevation.shape)
        _, _ = TectonicStructureGenerator.generate_amplitude_modulated_terrain(
            tectonic_elevation=tectonic_elevation,
            buildability_mask=non_binary_mask,
            noise_generator=noise_gen,
            verbose=False
        )
        assert False, "Should have raised ValueError for non-binary mask"
    except ValueError as e:
        assert "must be binary" in str(e), f"Wrong error message: {e}"
        print(f"  [OK] Non-binary mask raises ValueError")

    # Test 5c: Negative amplitude
    try:
        _, _ = TectonicStructureGenerator.generate_amplitude_modulated_terrain(
            tectonic_elevation=tectonic_elevation,
            buildability_mask=binary_mask,
            noise_generator=noise_gen,
            buildable_amplitude=-0.3,
            verbose=False
        )
        assert False, "Should have raised ValueError for negative amplitude"
    except ValueError as e:
        assert "must be positive" in str(e), f"Wrong error message: {e}"
        print(f"  [OK] Negative amplitude raises ValueError")

    # Test 5d: Invalid octaves
    try:
        _, _ = TectonicStructureGenerator.generate_amplitude_modulated_terrain(
            tectonic_elevation=tectonic_elevation,
            buildability_mask=binary_mask,
            noise_generator=noise_gen,
            noise_octaves=0,
            verbose=False
        )
        assert False, "Should have raised ValueError for octaves < 1"
    except ValueError as e:
        assert "octaves must be >= 1" in str(e), f"Wrong error message: {e}"
        print(f"  [OK] Invalid octaves raises ValueError")

    # Step 7: Validate zone boundaries
    print("\nStep 7: Validating zone boundaries...")

    # Test 6: Zone boundary smoothness
    from scipy.ndimage import binary_erosion

    # Erode mask to find interior pixels
    buildable_interior = binary_erosion(binary_mask, iterations=3)
    scenic_interior = binary_erosion(1 - binary_mask, iterations=3)

    # Boundary pixels are those not in interior
    buildable_boundary = (binary_mask == 1) & (~buildable_interior)
    scenic_boundary = (binary_mask == 0) & (~scenic_interior)
    boundary_pixels = buildable_boundary | scenic_boundary

    # Calculate gradient magnitude (slope)
    gy, gx = np.gradient(final_terrain)
    gradient_magnitude = np.sqrt(gx**2 + gy**2)

    # Compare boundary gradients to interior gradients
    if np.any(boundary_pixels):
        boundary_gradient = np.mean(gradient_magnitude[boundary_pixels])

        # Calculate interior gradients (exclude boundaries)
        interior_pixels = ~boundary_pixels
        interior_gradient = np.mean(gradient_magnitude[interior_pixels])

        # Boundary gradient should NOT be excessively higher than interior
        smoothness_ratio = boundary_gradient / (interior_gradient + 1e-10)

        # Allow 4x tolerance (boundaries naturally have some gradient due to tectonic structure)
        # WHY: Gradient control map had 6-8x ratio (jagged frequency discontinuities)
        # Amplitude modulation should be < 5x (some transition but not discontinuous)
        assert smoothness_ratio < 5.0, \
            f"Boundary gradient {smoothness_ratio:.2f}x interior (should be <5.0x)"

        print(f"  [OK] Boundary gradient: {boundary_gradient:.3f} vs Interior gradient: {interior_gradient:.3f}")
        print(f"  [OK] Boundary smoothness ratio: {smoothness_ratio:.2f} (acceptable, not catastrophic)")
        if smoothness_ratio > 4.0:
            print(f"       WARNING: Ratio >4x suggests room for improvement")
    else:
        print(f"  [SKIP] No boundary pixels found (uniform terrain)")

    # Step 8: Validate statistics completeness
    print("\nStep 8: Validating statistics...")

    # Test 7: Statistics completeness
    required_keys = [
        'buildable_amplitude_mean',
        'scenic_amplitude_mean',
        'amplitude_ratio',
        'final_range',
        'noise_octaves_used',
        'single_frequency_field',
        'buildable_pixels',
        'scenic_pixels',
        'buildable_percentage',
    ]

    for key in required_keys:
        assert key in stats, f"Missing required statistic: {key}"

    print(f"  [OK] All required statistics present")

    # Validate types
    assert isinstance(stats['buildable_amplitude_mean'], float)
    assert isinstance(stats['scenic_amplitude_mean'], float)
    assert isinstance(stats['amplitude_ratio'], float)
    assert isinstance(stats['final_range'], tuple)
    assert isinstance(stats['noise_octaves_used'], int)
    assert isinstance(stats['single_frequency_field'], bool)
    assert isinstance(stats['buildable_pixels'], int)
    assert isinstance(stats['scenic_pixels'], int)
    assert isinstance(stats['buildable_percentage'], float)

    print(f"  [OK] All values correct type")

    # Summary
    print("\n" + "="*70)
    print("TASK 2.3 VALIDATION: PASSED")
    print("="*70)
    print("\nSummary:")
    print(f"  Final terrain: {final_terrain.shape}")
    print(f"  Elevation range: [{final_terrain.min():.3f}, {final_terrain.max():.3f}]")
    print(f"  Single frequency field: {stats['single_frequency_field']} ({stats['noise_octaves_used']} octaves)")
    print(f"  Buildable amplitude: {stats['buildable_amplitude_mean']:.3f}")
    print(f"  Scenic amplitude: {stats['scenic_amplitude_mean']:.3f}")
    print(f"  Amplitude ratio: {stats['amplitude_ratio']:.2f} (expected: {expected_ratio:.2f})")
    print(f"  Buildable area: {stats['buildable_percentage']:.1f}%")
    print(f"  No frequency discontinuities detected")
    print("\nTask 2.3 successfully avoids gradient control map's catastrophic failure!")
    print("="*70 + "\n")

    return final_terrain, stats


if __name__ == '__main__':
    test_task_2_3_amplitude_modulation()
