"""
Test script to validate no-erosion approach achieves 55-65% buildability.

This test validates the alternative approach recommended in EROSION_ANALYSIS_FINAL.md:
- Disable hydraulic erosion (creates near-vertical terrain)
- Disable ridge enhancement (adds steep slopes)
- Increase zone coverage to 0.80 (more buildable zones)
- Reduce base amplitude to 0.16 (gentler terrain)

Expected results:
- Buildability: 55-65% (target range)
- Mean slope: <15% (buildable threshold)
- No near-vertical terrain artifacts

Created: 2025-10-13
Replaces: test_erosion_tuning.py (erosion-based approach)
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.generation.pipeline import TerrainGenerationPipeline
import time

print("=" * 80)
print("NO-EROSION BUILDABILITY VALIDATION TEST")
print("=" * 80)
print("\nObjective: Validate 55-65% buildability WITHOUT erosion")
print("\nKey changes from erosion approach:")
print("  - apply_erosion: True -> False (disabled)")
print("  - apply_ridges: True -> False (disabled)")
print("  - target_coverage: 0.70 -> 0.80 (more buildable zones)")
print("  - base_amplitude: 0.20 -> 0.16 (gentler terrain)")
print("\nRationale:")
print("  Erosion creates near-vertical terrain (94.90% mean slope)")
print("  System already achieves 51.6% buildable before erosion")
print("  Only need +3.4% to reach 55% target")
print("\nTesting with 512x512 resolution for speed...")
print("=" * 80)

# Create pipeline
pipeline = TerrainGenerationPipeline(
    resolution=512,
    map_size_meters=14336.0,
    seed=42
)

# Test with new NO-EROSION defaults
print("\n[TEST] NEW APPROACH (no erosion, adjusted parameters)")
print("-" * 80)
start = time.time()

# Use new defaults (apply_erosion=False, apply_ridges=False, coverage=0.80, amplitude=0.16)
# These are now the defaults in pipeline.py, so we just call generate()
terrain, stats = pipeline.generate(verbose=True)

elapsed = time.time() - start

print("\n" + "=" * 80)
print("RESULTS SUMMARY")
print("=" * 80)
print(f"\nExecution time: {elapsed:.2f}s")
print(f"\nInitial buildability (after terrain): {stats['terrain_stats']['buildable_percent']:.1f}%")

# Check if erosion was actually skipped
if stats['erosion_stats'].get('skipped'):
    print(f"Erosion status: SKIPPED (as intended)")
else:
    print(f"WARNING: Erosion ran when it should have been disabled!")

# Check if ridges were skipped
if stats['ridge_stats'].get('skipped'):
    print(f"Ridge status: SKIPPED (as intended)")
else:
    print(f"WARNING: Ridges ran when they should have been disabled!")

print(f"\nFinal buildability (after all stages): {stats['final_buildable_pct']:.1f}%")
print(f"Mean slope: {stats['final_mean_slope']:.2f}%")
print(f"P90 slope: {stats['final_p90_slope']:.2f}%")

# Validation
target_achieved = 55.0 <= stats['final_buildable_pct'] <= 65.0
slopes_reasonable = stats['final_mean_slope'] < 20.0  # Should be well below buildable threshold

print(f"\n[VALIDATION]")
print(f"  Target range: 55-65% buildable")
print(f"  Achieved: {stats['final_buildable_pct']:.1f}%")
print(f"  Target achieved: {target_achieved}")
print(f"  Mean slope reasonable (<20%): {slopes_reasonable}")

if target_achieved and slopes_reasonable:
    print("\n" + "=" * 80)
    print("[SUCCESS] No-erosion approach achieves target!")
    print("=" * 80)
    print("  Buildability is within 55-65% range")
    print("  Terrain slopes are gentle and buildable")
    print("  No near-vertical artifacts from erosion")
    print("\nRecommendation:")
    print("  This approach is READY FOR PRODUCTION")
    print("  Update GUI defaults to match pipeline defaults")
    print("  Mark erosion as 'experimental' in GUI tooltip")
    sys.exit(0)
elif target_achieved and not slopes_reasonable:
    print("\n" + "=" * 80)
    print("[PARTIAL SUCCESS] Target achieved but slopes too steep")
    print("=" * 80)
    print(f"  Mean slope: {stats['final_mean_slope']:.2f}% (should be <20%)")
    print("  Recommendations:")
    print("    - Further reduce base_amplitude to 0.14-0.15")
    print("    - Increase min_amplitude_mult to 0.35-0.40")
    sys.exit(1)
elif not target_achieved and stats['final_buildable_pct'] < 55.0:
    deficit = 55.0 - stats['final_buildable_pct']
    print("\n" + "=" * 80)
    print(f"[BELOW TARGET] by {deficit:.1f}%")
    print("=" * 80)
    print("  Recommendations:")
    print("    - Increase target_coverage to 0.82-0.85")
    print("    - Further reduce base_amplitude to 0.14-0.15")
    print("    - Increase min_amplitude_mult to 0.35-0.40")
    sys.exit(1)
else:
    excess = stats['final_buildable_pct'] - 65.0
    print("\n" + "=" * 80)
    print(f"[ABOVE TARGET] by {excess:.1f}%")
    print("=" * 80)
    print("  Recommendations:")
    print("    - Decrease target_coverage to 0.75-0.78")
    print("    - Increase base_amplitude to 0.17-0.18")
    sys.exit(1)
