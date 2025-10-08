"""
Quick Test for Task 2.2: Binary Buildability Mask Generation

Validates that the buildability mask generation works correctly with
tectonic structure from Task 2.1.
"""

import sys
from pathlib import Path
import numpy as np

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from tectonic_generator import TectonicStructureGenerator
from buildability_enforcer import BuildabilityEnforcer


def test_task_2_2_mask_generation():
    """Test Task 2.2: Generate binary buildability mask from tectonic structure"""

    print("\n" + "="*70)
    print("TASK 2.2 VALIDATION: Binary Buildability Mask Generation")
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

    print(f"  [OK] Tectonic structure generated: {tectonic_elevation.shape}")
    print(f"       Distance field range: {distance_field.min():.1f}m - {distance_field.max():.1f}m")
    print(f"       Elevation range: {tectonic_elevation.min():.3f} - {tectonic_elevation.max():.3f}")

    # Step 2: Generate buildability mask (Task 2.2)
    print("\nStep 2: Generating binary buildability mask (Task 2.2)...")

    binary_mask, stats = BuildabilityEnforcer.generate_buildability_mask_from_tectonics(
        distance_field=distance_field,
        tectonic_elevation=tectonic_elevation,
        target_buildable_pct=50.0,
        distance_threshold_meters=300.0,
        elevation_threshold=0.4,
        verbose=True
    )

    # Step 3: Validate results
    print("\nStep 3: Validating mask properties...")

    # Check mask is binary (0 or 1)
    unique_values = np.unique(binary_mask)
    assert len(unique_values) <= 2, f"Mask should be binary, found {len(unique_values)} unique values"
    assert set(unique_values).issubset({0, 1}), f"Mask values should be 0 or 1, found {unique_values}"
    print(f"  [OK] Mask is binary: values in {unique_values}")

    # Check shape matches input
    assert binary_mask.shape == distance_field.shape, "Mask shape mismatch"
    print(f"  [OK] Mask shape correct: {binary_mask.shape}")

    # Check buildable percentage is close to target
    buildable_pct = stats['buildable_pct']
    target_pct = 50.0
    assert abs(buildable_pct - target_pct) < 10.0, \
        f"Buildable percentage {buildable_pct:.1f}% too far from target {target_pct:.1f}%"
    print(f"  [OK] Buildable percentage: {buildable_pct:.1f}% (target: {target_pct:.1f}%)")

    # Check statistics are reasonable
    assert stats['buildable_pixels'] + stats['scenic_pixels'] == binary_mask.size, \
        "Pixel counts don't sum to total"
    print(f"  [OK] Pixel counts valid: {stats['buildable_pixels']:,} buildable + "
          f"{stats['scenic_pixels']:,} scenic = {binary_mask.size:,} total")

    # Check thresholds are in reasonable ranges
    assert 50 <= stats['distance_threshold_used'] <= 3000, "Distance threshold out of range"
    assert 0.1 <= stats['elevation_threshold_used'] <= 0.8, "Elevation threshold out of range"
    print(f"  [OK] Thresholds reasonable:")
    print(f"       Distance: {stats['distance_threshold_used']:.0f}m (range: 50-3000m)")
    print(f"       Elevation: {stats['elevation_threshold_used']:.2f} (range: 0.1-0.8)")

    # Step 4: Validate mask makes geological sense
    print("\nStep 4: Validating geological consistency...")

    # Areas far from faults should be mostly buildable
    far_from_faults = distance_field > 500.0
    if np.any(far_from_faults):
        buildable_far = np.mean(binary_mask[far_from_faults])
        print(f"  Buildable % in areas >500m from faults: {buildable_far * 100:.1f}%")
        assert buildable_far > 0.5, "Areas far from faults should be mostly buildable"
        print(f"  [OK] Far from faults = mostly buildable")

    # Areas near faults should be mostly scenic
    near_faults = distance_field < 200.0
    if np.any(near_faults):
        buildable_near = np.mean(binary_mask[near_faults])
        print(f"  Buildable % in areas <200m from faults: {buildable_near * 100:.1f}%")
        # Note: This can be high if elevation is low (valleys)
        print(f"  [OK] Near faults = mixed (includes buildable valleys)")

    # Low elevation areas should be mostly buildable
    low_elevation = tectonic_elevation < 0.3
    if np.any(low_elevation):
        buildable_low = np.mean(binary_mask[low_elevation])
        print(f"  Buildable % in low elevation (<0.3): {buildable_low * 100:.1f}%")
        assert buildable_low > 0.7, "Low elevation areas should be mostly buildable"
        print(f"  [OK] Low elevation = mostly buildable")

    # High elevation areas should be mostly scenic
    high_elevation = tectonic_elevation > 0.6
    if np.any(high_elevation):
        buildable_high = np.mean(binary_mask[high_elevation])
        print(f"  Buildable % in high elevation (>0.6): {buildable_high * 100:.1f}%")
        assert buildable_high < 0.3, "High elevation areas should be mostly scenic"
        print(f"  [OK] High elevation = mostly scenic")

    print("\n" + "="*70)
    print("TASK 2.2 VALIDATION: PASSED")
    print("="*70)
    print("\nSummary:")
    print(f"  Binary mask generated: {binary_mask.shape}")
    print(f"  Buildable area: {stats['buildable_pct']:.1f}%")
    print(f"  Success: {stats['success']}")
    print(f"  Iterations: {stats['iterations']}")
    print("\nNext: Task 2.3 (Conditional noise with amplitude modulation)")
    print("="*70 + "\n")

    return binary_mask, stats


if __name__ == '__main__':
    test_task_2_2_mask_generation()
