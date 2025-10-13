"""
Test each pipeline stage individually to diagnose 0.0% buildability issue.

This script tests each stage in isolation and in combination to identify
which stages cause buildability to collapse when enabled together.

Per user requirement: ALL stages must work correctly (implementation plan is non-negotiable).
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.generation.pipeline import TerrainGenerationPipeline
import time

print("=" * 80)
print("STAGE-BY-STAGE DIAGNOSTIC TEST")
print("=" * 80)
print("\nObjective: Identify which stages cause 0.0% buildability")
print("Testing with 512x512 resolution for speed...")
print("=" * 80)

# Create pipeline
pipeline = TerrainGenerationPipeline(
    resolution=512,
    map_size_meters=14336.0,
    seed=42
)

# Test configurations
tests = [
    {
        'name': 'Zones + Terrain ONLY',
        'params': {
            'apply_ridges': False,
            'apply_erosion': False,
            'apply_detail': False,
            'apply_rivers': False,
            'verbose': True
        }
    },
    {
        'name': 'Zones + Terrain + Ridges',
        'params': {
            'apply_ridges': True,
            'apply_erosion': False,
            'apply_detail': False,
            'apply_rivers': False,
            'verbose': True
        }
    },
    {
        'name': 'Zones + Terrain + Erosion',
        'params': {
            'apply_ridges': False,
            'apply_erosion': True,
            'apply_detail': False,
            'apply_rivers': False,
            'verbose': True
        }
    },
    {
        'name': 'Zones + Terrain + Detail',
        'params': {
            'apply_ridges': False,
            'apply_erosion': False,
            'apply_detail': True,
            'apply_rivers': False,
            'verbose': True
        }
    },
    {
        'name': 'ALL STAGES ENABLED',
        'params': {
            'apply_ridges': True,
            'apply_erosion': True,
            'apply_detail': True,
            'apply_rivers': True,
            'verbose': True
        }
    }
]

results = []

for test in tests:
    print("\n" + "=" * 80)
    print(f"TEST: {test['name']}")
    print("=" * 80)

    start = time.time()
    terrain, stats = pipeline.generate(**test['params'])
    elapsed = time.time() - start

    buildability = stats.get('final_buildable_pct', 0.0)
    mean_slope = stats.get('final_mean_slope', 0.0)

    results.append({
        'test': test['name'],
        'buildability': buildability,
        'mean_slope': mean_slope,
        'time': elapsed
    })

    print(f"\n[RESULT]")
    print(f"  Buildability: {buildability:.1f}%")
    print(f"  Mean slope: {mean_slope:.2f}%")
    print(f"  Time: {elapsed:.2f}s")

    if buildability < 1.0:
        print(f"  [FAILURE] Buildability collapsed to {buildability:.1f}%!")
    elif buildability < 55.0:
        print(f"  [BELOW TARGET] Got {buildability:.1f}%, need 55-65%")
    elif buildability > 65.0:
        print(f"  [ABOVE TARGET] Got {buildability:.1f}%, need 55-65%")
    else:
        print(f"  [SUCCESS] Within target range (55-65%)")

# Summary
print("\n" + "=" * 80)
print("SUMMARY OF RESULTS")
print("=" * 80)
print(f"{'Test':<35} {'Buildability':<15} {'Mean Slope':<15} {'Time'}")
print("-" * 80)

for r in results:
    status = ""
    if r['buildability'] < 1.0:
        status = " [FAIL]"
    elif r['buildability'] < 55.0:
        status = " [BELOW]"
    elif r['buildability'] > 65.0:
        status = " [ABOVE]"
    else:
        status = " [OK]"

    print(f"{r['test']:<35} {r['buildability']:>6.1f}%{status:<8} {r['mean_slope']:>6.2f}%       {r['time']:>6.2f}s")

# Diagnosis
print("\n" + "=" * 80)
print("DIAGNOSIS")
print("=" * 80)

# Check which stage(s) cause failure
zones_terrain_only = results[0]['buildability']
with_ridges = results[1]['buildability']
with_erosion = results[2]['buildability']
with_detail = results[3]['buildability']
all_enabled = results[4]['buildability']

print(f"\nBaseline (Zones + Terrain): {zones_terrain_only:.1f}%")

if with_ridges < 1.0:
    print(f"  ❌ Ridges destroy buildability ({zones_terrain_only:.1f}% → {with_ridges:.1f}%)")
else:
    print(f"  ✅ Ridges work ({zones_terrain_only:.1f}% → {with_ridges:.1f}%)")

if with_erosion < 1.0:
    print(f"  ❌ Erosion destroys buildability ({zones_terrain_only:.1f}% → {with_erosion:.1f}%)")
else:
    print(f"  ✅ Erosion works ({zones_terrain_only:.1f}% → {with_erosion:.1f}%)")

if with_detail < 1.0:
    print(f"  ❌ Detail destroys buildability ({zones_terrain_only:.1f}% → {with_detail:.1f}%)")
else:
    print(f"  ✅ Detail works ({zones_terrain_only:.1f}% → {with_detail:.1f}%)")

if all_enabled < 1.0:
    print(f"\n❌ CRITICAL: All stages together produce {all_enabled:.1f}% buildability")
    print(f"   This suggests stages interact destructively when combined")
else:
    print(f"\n✅ All stages work together: {all_enabled:.1f}% buildability")

print("\n" + "=" * 80)
print("Next Step: Fix the failing stage(s) identified above")
print("=" * 80)
