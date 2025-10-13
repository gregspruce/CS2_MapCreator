"""
Simulate GUI pipeline call to understand the 2-second execution mystery.

This test will:
1. Call pipeline EXACTLY as GUI does (verbose=False, full 4096x4096)
2. Measure timing for each stage
3. Check if all stages executed
4. Identify why it might be fast (or if it's actually slow)
"""

import sys
import os
import time
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.generation.pipeline import TerrainGenerationPipeline

print("="*80)
print("GUI SIMULATION TEST - FULL 4096x4096 PIPELINE")
print("="*80)
print("This simulates EXACTLY what the GUI calls with verbose=False")
print("Expected: 3-5 minutes for full resolution with 100k particles")
print("User reported: ~2 seconds")
print("="*80)

# Exact GUI configuration
resolution = 4096
seed = 42
params = {
    # Zone Generation (Session 2)
    'target_coverage': 0.70,
    'zone_wavelength': 6500.0,
    'zone_octaves': 2,

    # Terrain Generation (Session 3)
    'base_amplitude': 0.2,
    'min_amplitude_mult': 0.3,
    'max_amplitude_mult': 1.0,
    'terrain_wavelength': 1000.0,
    'terrain_octaves': 6,

    # Ridge Enhancement (Session 5)
    'ridge_strength': 0.2,
    'ridge_octaves': 5,
    'ridge_wavelength': 1500.0,
    'apply_ridges': True,

    # Hydraulic Erosion (Session 4)
    'num_particles': 100000,
    'erosion_rate': 0.5,
    'deposition_rate': 0.3,
    'apply_erosion': True,

    # River Analysis (Session 7)
    'river_threshold_percentile': 99.0,
    'min_river_length': 10,
    'apply_rivers': True,

    # Detail Addition (Session 8)
    'detail_amplitude': 0.02,
    'detail_wavelength': 75.0,
    'apply_detail': True,

    # Constraint Verification (Session 8)
    'target_buildable_min': 55.0,
    'target_buildable_max': 65.0,
    'apply_constraint_adjustment': True,

    # Control - CRITICAL: This is what GUI uses
    'verbose': False  # Disable console output (use progress dialog instead)
}

print(f"\nConfiguration:")
print(f"  Resolution: {resolution}x{resolution}")
print(f"  Seed: {seed}")
print(f"  Particles: {params['num_particles']:,}")
print(f"  verbose: {params['verbose']}")

# Create pipeline
pipeline = TerrainGenerationPipeline(
    resolution=resolution,
    map_size_meters=14336.0,
    seed=seed
)

print(f"\n[STARTING PIPELINE]")
print(f"Start time: {time.strftime('%H:%M:%S')}")
print(f"This will take 3-5 minutes...")
print()

start_time = time.time()

# Generate terrain EXACTLY as GUI does
terrain, stats = pipeline.generate(**params)

elapsed = time.time() - start_time

print(f"\n[PIPELINE COMPLETE]")
print(f"End time: {time.strftime('%H:%M:%S')}")
print(f"Total time: {elapsed:.1f}s ({elapsed/60:.1f} minutes)")

# Analyze stats to see which stages executed
print(f"\n{'='*80}")
print("STAGE EXECUTION ANALYSIS")
print(f"{'='*80}")

print(f"\nStage timings from stats:")
print(f"  Stage 1 (Zones):       {stats.get('stage1_zone_time', 'N/A'):>6}s")
print(f"  Stage 2 (Terrain):     {stats.get('stage2_terrain_time', 'N/A'):>6}s")
print(f"  Stage 3 (Ridges):      {stats.get('stage3_ridge_time', 'N/A'):>6}s")
print(f"  Stage 4 (Erosion):     {stats.get('stage4_erosion_time', 'N/A'):>6}s")
print(f"  Stage 4.5 (Rivers):    {stats.get('stage4_5_river_time', 'N/A'):>6}s")
print(f"  Stage 5.5 (Detail+Ver):{stats.get('stage5_5_detail_verification_time', 'N/A'):>6}s")
print(f"  Stage 6 (Normalization):{stats.get('stage6_normalization_time', 'N/A'):>6}s")

print(f"\nBuildability progression:")
print(f"  After terrain:  {stats.get('terrain_stats', {}).get('buildable_percent', 'N/A'):>6}%")
if 'erosion_stats' in stats and not stats['erosion_stats'].get('skipped'):
    print(f"  After erosion:  {stats['erosion_stats'].get('final_buildable_pct', 'N/A'):>6}%")
else:
    print(f"  After erosion:  SKIPPED")
print(f"  Final:          {stats.get('final_buildable_pct', 'N/A'):>6}%")

print(f"\nTerrain properties:")
print(f"  Range: [{terrain.min():.4f}, {terrain.max():.4f}]")
print(f"  Mean slope: {stats.get('final_mean_slope', 'N/A')}%")
print(f"  Target achieved: {stats.get('target_achieved', 'N/A')}")

print(f"\n{'='*80}")
print("VERDICT")
print(f"{'='*80}")

if elapsed < 30:
    print(f"[SUSPICIOUS] Pipeline completed in {elapsed:.1f}s")
    print(f"Expected time: 180-300s (3-5 minutes)")
    print(f"Actual time: {elapsed:.1f}s")
    print(f"\nPossible causes:")
    print(f"  1. Stages being skipped due to exceptions")
    print(f"  2. Early return in pipeline code")
    print(f"  3. apply_* flags set to False")
    print(f"  4. Hardware is EXTREMELY fast (unlikely)")
elif elapsed < 120:
    print(f"[FAST] Pipeline completed in {elapsed:.1f}s")
    print(f"Faster than expected, but within reasonable range")
    print(f"Possible causes:")
    print(f"  1. Fast hardware (good CPU/SSD)")
    print(f"  2. Numba JIT optimizations")
elif elapsed < 360:
    print(f"[NORMAL] Pipeline completed in {elapsed:.1f}s")
    print(f"This is expected performance for full resolution")
else:
    print(f"[SLOW] Pipeline completed in {elapsed:.1f}s")
    print(f"Slower than expected")
    print(f"Possible causes:")
    print(f"  1. Slow hardware")
    print(f"  2. Background processes")
    print(f"  3. Numba JIT not available")

# Check if erosion actually ran
erosion_ran = (
    'erosion_stats' in stats and
    not stats['erosion_stats'].get('skipped', False) and
    stats.get('stage4_erosion_time', 0) > 0
)

if not erosion_ran:
    print(f"\n[CRITICAL] Erosion stage did NOT execute!")
    print(f"This explains the fast execution time")
else:
    print(f"\n[OK] Erosion stage executed ({stats.get('stage4_erosion_time', 0):.1f}s)")
