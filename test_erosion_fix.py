"""
Quick test to verify erosion fix works correctly.

Tests zones + terrain + erosion to see if auto-calculated terrain_scale
fixes the near-vertical terrain issue.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.generation.pipeline import TerrainGenerationPipeline
import time

print("=" * 80)
print("EROSION FIX VALIDATION TEST")
print("=" * 80)
print("\nObjective: Verify terrain_scale auto-calculation fixes erosion")
print("Testing with 512x512 resolution for speed...")
print("=" * 80)

# Create pipeline
pipeline = TerrainGenerationPipeline(
    resolution=512,
    map_size_meters=14336.0,
    seed=42
)

print("\n" + "=" * 80)
print("TEST: Zones + Terrain + Erosion (WITH AUTO-SCALING FIX)")
print("=" * 80)

start = time.time()
terrain, stats = pipeline.generate(
    apply_ridges=False,
    apply_erosion=True,  # Enable erosion with new fix
    apply_detail=False,
    apply_rivers=False,
    verbose=True
)
elapsed = time.time() - start

buildability = stats.get('final_buildable_pct', 0.0)
mean_slope = stats.get('final_mean_slope', 0.0)

print(f"\n[RESULT]")
print(f"  Buildability: {buildability:.1f}%")
print(f"  Mean slope: {mean_slope:.2f}%")
print(f"  Time: {elapsed:.2f}s")

# Check if fix worked
print("\n" + "=" * 80)
print("VALIDATION")
print("=" * 80)

if buildability < 1.0:
    print(f"[FAILURE] Buildability still collapsed: {buildability:.1f}%")
    print(f"  Erosion fix did NOT work - terrain_scale multiplier needs adjustment")
    print(f"  Mean slope: {mean_slope:.2f}% (should be <15%)")
elif buildability < 40.0:
    print(f"[PARTIAL] Buildability low: {buildability:.1f}%")
    print(f"  Erosion may be too aggressive - consider smaller terrain_scale multiplier")
elif buildability < 55.0:
    print(f"[GOOD] Buildability recovered: {buildability:.1f}%")
    print(f"  Close to target, may need parameter tuning")
elif buildability <= 65.0:
    print(f"[SUCCESS] Buildability within target: {buildability:.1f}%")
    print(f"  Erosion fix WORKS! terrain_scale auto-calculation successful")
else:
    print(f"[ABOVE TARGET] Buildability too high: {buildability:.1f}%")
    print(f"  Erosion may be too gentle - consider larger terrain_scale multiplier")

# Show improvement from before erosion
before_erosion = stats.get('terrain_stats', {}).get('buildable_percent', 0.0)
improvement = stats['erosion_stats'].get('improvement_pct', 0.0)

print(f"\nBuildability progression:")
print(f"  Before erosion: {before_erosion:.1f}%")
print(f"  After erosion:  {stats['erosion_stats'].get('final_buildable_pct', 0.0):.1f}%")
print(f"  Final:          {buildability:.1f}%")
print(f"  Change:         {improvement:+.1f} percentage points")

if improvement > 0:
    print(f"\n[GOOD] Erosion IMPROVED buildability (as intended)")
elif improvement > -10:
    print(f"\n[OK] Erosion slightly decreased buildability (acceptable)")
else:
    print(f"\n[BAD] Erosion significantly decreased buildability (not working correctly)")

print("\n" + "=" * 80)
