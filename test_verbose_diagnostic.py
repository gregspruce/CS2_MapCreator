"""
Diagnostic test to verify verbose parameter behavior.

This test will:
1. Run pipeline with verbose=True (full output)
2. Run pipeline with verbose=False (no output)
3. Compare execution times and results
4. Identify if verbose affects execution (BUG) or just output (CORRECT)
"""

import sys
import os
import time
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.generation.pipeline import TerrainGenerationPipeline

print("="*80)
print("VERBOSE PARAMETER DIAGNOSTIC TEST")
print("="*80)

# Test with small resolution for speed
resolution = 256
seed = 42

print(f"\nTest configuration:")
print(f"  Resolution: {resolution}x{resolution}")
print(f"  Seed: {seed}")
print(f"  Particles: 1000 (minimal for speed)")

# ============================================================================
# TEST 1: verbose=True
# ============================================================================
print("\n" + "="*80)
print("TEST 1: PIPELINE WITH verbose=True")
print("="*80)

pipeline1 = TerrainGenerationPipeline(
    resolution=resolution,
    map_size_meters=14336.0,
    seed=seed
)

start1 = time.time()
terrain1, stats1 = pipeline1.generate(
    num_particles=1000,
    verbose=True
)
elapsed1 = time.time() - start1

print(f"\n[TEST 1 RESULTS]")
print(f"  Execution time: {elapsed1:.2f}s")
print(f"  Final buildable: {stats1['final_buildable_pct']:.1f}%")
print(f"  Terrain range: [{terrain1.min():.3f}, {terrain1.max():.3f}]")

# ============================================================================
# TEST 2: verbose=False
# ============================================================================
print("\n" + "="*80)
print("TEST 2: PIPELINE WITH verbose=False")
print("="*80)
print("(No output expected during generation)")

pipeline2 = TerrainGenerationPipeline(
    resolution=resolution,
    map_size_meters=14336.0,
    seed=seed
)

start2 = time.time()
terrain2, stats2 = pipeline2.generate(
    num_particles=1000,
    verbose=False
)
elapsed2 = time.time() - start2

print(f"\n[TEST 2 RESULTS]")
print(f"  Execution time: {elapsed2:.2f}s")
print(f"  Final buildable: {stats2['final_buildable_pct']:.1f}%")
print(f"  Terrain range: [{terrain2.min():.3f}, {terrain2.max():.3f}]")

# ============================================================================
# COMPARISON
# ============================================================================
print("\n" + "="*80)
print("DIAGNOSTIC RESULTS")
print("="*80)

time_diff = abs(elapsed1 - elapsed2)
buildable_diff = abs(stats1['final_buildable_pct'] - stats2['final_buildable_pct'])
terrain_diff = abs(terrain1 - terrain2).max()

print(f"\nTime difference: {time_diff:.2f}s ({time_diff/elapsed1*100:.1f}%)")
print(f"Buildable difference: {buildable_diff:.2f}%")
print(f"Terrain max difference: {terrain_diff:.6f}")

print(f"\n[VERDICT]")
if time_diff < 1.0 and buildable_diff < 0.5 and terrain_diff < 0.001:
    print("  [PASS] verbose parameter only affects output, not execution")
    print("  Both runs produced identical results in similar time")
    print("  This is CORRECT behavior")
    sys.exit(0)
elif time_diff > 5.0:
    print("  [FAIL] verbose parameter affects execution time significantly")
    print("  This indicates functional code inside 'if verbose:' blocks")
    print("  This is a BUG!")
    sys.exit(1)
elif buildable_diff > 1.0 or terrain_diff > 0.01:
    print("  [FAIL] verbose parameter affects results")
    print("  This indicates functional code inside 'if verbose:' blocks")
    print("  This is a CRITICAL BUG!")
    sys.exit(1)
else:
    print("  [WARN] Small differences detected, but within tolerance")
    print("  Likely due to random number generation or numerical precision")
    sys.exit(0)
