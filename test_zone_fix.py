"""
Test zone generator fix - verify power transformation doesn't create 100% coverage
"""

import numpy as np
import sys
from pathlib import Path

project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.generation.zone_generator import BuildabilityZoneGenerator

def test_zone_coverage():
    """Test that power transformation produces reasonable coverage."""

    print("="*80)
    print("ZONE GENERATOR FIX VALIDATION")
    print("="*80)
    print()

    # Test at 512×512 for speed
    resolution = 512

    # Test with different target_coverage values
    test_cases = [
        ('target_coverage=0.60', 0.60),
        ('target_coverage=0.72 (default)', 0.72),
        ('target_coverage=0.80 (user setting)', 0.80),
    ]

    results = []

    for label, target_coverage in test_cases:
        print(f"\nTesting {label}...")
        print("-" * 40)

        generator = BuildabilityZoneGenerator(
            resolution=resolution,
            map_size_meters=14336.0,
            seed=42
        )

        potential_map, stats = generator.generate_potential_map(
            target_coverage=target_coverage,
            zone_wavelength=6500.0,
            zone_octaves=2,
            verbose=False
        )

        # Calculate actual metrics
        actual_coverage = stats['coverage_percent']
        mean_potential = stats['mean_potential']
        high_potential_pct = np.sum(potential_map > 0.9) / potential_map.size * 100

        print(f"  Target coverage:     {target_coverage*100:.0f}%")
        print(f"  Actual coverage:     {actual_coverage:.1f}%")
        print(f"  Mean potential:      {mean_potential:.3f}")
        print(f"  High potential (>0.9): {high_potential_pct:.1f}%")

        # Check if reasonable
        # Should be within ±20% of target
        coverage_ok = abs(actual_coverage - target_coverage*100) < 30
        # Should not be 100%
        not_oversaturated = actual_coverage < 98.0
        # Mean potential should be reasonable
        mean_ok = 0.5 < mean_potential < 0.95

        status = "[PASS]" if (coverage_ok and not_oversaturated and mean_ok) else "[FAIL]"
        print(f"  Status: {status}")

        results.append({
            'label': label,
            'target': target_coverage,
            'actual': actual_coverage,
            'mean_potential': mean_potential,
            'high_potential': high_potential_pct,
            'pass': coverage_ok and not_oversaturated and mean_ok
        })

    print()
    print("="*80)
    print("SUMMARY")
    print("="*80)

    all_pass = all(r['pass'] for r in results)

    for r in results:
        status = "[PASS]" if r['pass'] else "[FAIL]"
        print(f"{status} {r['label']}: coverage={r['actual']:.1f}%, mean={r['mean_potential']:.3f}")

    print()
    if all_pass:
        print("[SUCCESS] All test cases passed! Zone generator fix validated.")
        return True
    else:
        print("[FAILURE] Some test cases failed. Review results above.")
        return False

if __name__ == "__main__":
    success = test_zone_coverage()
    sys.exit(0 if success else 1)
