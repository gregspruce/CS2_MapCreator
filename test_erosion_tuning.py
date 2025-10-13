"""
Test script to verify erosion parameter tuning achieves 55-65% buildability.

This test validates the optimized erosion parameters that favor deposition
over erosion, filling valleys to create buildable flat areas.

Expected results:
- Initial buildability: 40-50% (from zone-weighted terrain)
- Final buildability: 55-65% (after valley-filling erosion)
- Improvement: +10-20 percentage points
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.generation.pipeline import TerrainGenerationPipeline
import time

print("="*80)
print("EROSION PARAMETER TUNING TEST")
print("="*80)
print("\nObjective: Verify erosion parameters achieve 55-65% buildability")
print("Key changes:")
print("  - erosion_rate: 0.5 -> 0.2 (gentler carving)")
print("  - deposition_rate: 0.3 -> 0.6 (stronger valley filling)")
print("  - evaporation_rate: 0.02 -> 0.005 (longer particle life)")
print("  - sediment_capacity: 4.0 -> 6.0 (carry more sediment)")
print("  - terrain_scale: 10.0 -> 2.5 (gentler overall erosion)")
print("\nTesting with 512x512 resolution for speed...")
print("="*80)

# Create pipeline
pipeline = TerrainGenerationPipeline(
    resolution=512,
    map_size_meters=14336.0,
    seed=42
)

# Test with NEW optimized parameters
print("\n[TEST 1] NEW PARAMETERS (deposition-favored)")
print("-"*80)
start = time.time()
terrain_new, stats_new = pipeline.generate(
    # Use new defaults (erosion_rate=0.2, deposition_rate=0.6)
    apply_erosion=True,
    verbose=True
)
elapsed_new = time.time() - start

print("\n" + "="*80)
print("RESULTS SUMMARY")
print("="*80)
print(f"\nExecution time: {elapsed_new:.2f}s")
print(f"Initial buildability (after terrain): {stats_new['terrain_stats']['buildable_percent']:.1f}%")
if 'erosion_stats' in stats_new and not stats_new['erosion_stats'].get('skipped'):
    print(f"Final buildability (after erosion): {stats_new['erosion_stats']['final_buildable_pct']:.1f}%")
    print(f"Erosion improvement: +{stats_new['erosion_stats']['improvement_pct']:.1f} percentage points")
print(f"Final buildability (after all stages): {stats_new['final_buildable_pct']:.1f}%")

# Validation
target_achieved = 55.0 <= stats_new['final_buildable_pct'] <= 65.0
print(f"\nTarget achieved (55-65%): {target_achieved}")

if target_achieved:
    print("\n✓ SUCCESS: Erosion parameters correctly tuned!")
    print("  Buildability is within target range.")
    sys.exit(0)
elif stats_new['final_buildable_pct'] < 55.0:
    deficit = 55.0 - stats_new['final_buildable_pct']
    print(f"\n✗ BELOW TARGET by {deficit:.1f}%")
    print("  Recommendations:")
    print("    - Increase deposition_rate to 0.7-0.8")
    print("    - Decrease erosion_rate to 0.1-0.15")
    print("    - Increase num_particles to 150k-200k")
    sys.exit(1)
else:
    excess = stats_new['final_buildable_pct'] - 65.0
    print(f"\n✗ ABOVE TARGET by {excess:.1f}%")
    print("  Recommendations:")
    print("    - Decrease deposition_rate to 0.4-0.5")
    print("    - Increase erosion_rate to 0.3-0.4")
    print("    - Decrease num_particles to 50k-75k")
    sys.exit(1)
