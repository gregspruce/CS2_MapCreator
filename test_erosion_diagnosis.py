"""
Erosion Diagnosis Test - Find out why erosion isn't modifying terrain

This test will:
1. Check if particles are moving correctly
2. Check if erosion/deposition amounts are meaningful
3. Check if heightmap is being modified in-place
4. Verify Numba JIT is working
5. Check zone modulation
"""

import numpy as np
import sys
import os

# Change to project directory
os.chdir(r'C:\VSCode\CS2_Map')
sys.path.insert(0, r'C:\VSCode\CS2_Map')

from src.generation.hydraulic_erosion import HydraulicErosionSimulator, simulate_particle_numba, NUMBA_AVAILABLE
from src.buildability_enforcer import BuildabilityEnforcer

print("="*80)
print("EROSION DIAGNOSIS TEST")
print("="*80)
print(f"\nNumba available: {NUMBA_AVAILABLE}")

# Create small test terrain (128x128 for fast diagnosis)
resolution = 128
map_size_meters = 14336.0

# Create simple test terrain: sloped plane from 0.0 to 1.0
terrain = np.zeros((resolution, resolution), dtype=np.float32)
for y in range(resolution):
    terrain[y, :] = y / (resolution - 1)  # Slope from top to bottom

print(f"\nInitial terrain:")
print(f"  Shape: {terrain.shape}")
print(f"  Range: [{terrain.min():.3f}, {terrain.max():.3f}]")
print(f"  Top row (y=0): {terrain[0, 64]:.3f}")
print(f"  Bottom row (y=127): {terrain[127, 64]:.3f}")

# Calculate initial buildability
initial_slopes = BuildabilityEnforcer.calculate_slopes(terrain, map_size_meters)
initial_buildable = BuildabilityEnforcer.calculate_buildability_percentage(initial_slopes)
print(f"  Initial buildability: {initial_buildable:.1f}%")

# Create uniform buildability potential (all areas equally buildable)
zones = np.ones((resolution, resolution), dtype=np.float32)

# Test 1: Single particle simulation with diagnostics
print("\n" + "="*80)
print("TEST 1: Single Particle with Diagnostics")
print("="*80)

# Make a copy for single particle test
terrain_copy = terrain.copy()

# Create Gaussian kernel
from src.generation.hydraulic_erosion import create_gaussian_kernel
kernel = create_gaussian_kernel(radius=3, sigma=1.5).astype(np.float32)

# Parameters
params = np.array([
    0.1,     # inertia
    0.5,     # erosion_rate
    0.3,     # deposition_rate
    0.02,    # evaporation_rate
    4.0,     # sediment_capacity
    0.0005,  # min_slope
    1000,    # max_steps
    100.0    # terrain_scale (NEW)
], dtype=np.float32)

# Spawn particle at top center (where slope is steep)
start_x, start_y = 64.0, 10.0

# Get initial height at spawn
initial_height = terrain_copy[int(start_y), int(start_x)]
print(f"\nParticle spawn: ({start_x:.1f}, {start_y:.1f})")
print(f"Initial height at spawn: {initial_height:.4f}")

# Simulate ONE particle
simulate_particle_numba(
    terrain_copy, zones, kernel,
    start_x, start_y,
    params
)

# Check if terrain was modified
final_height = terrain_copy[int(start_y), int(start_x)]
terrain_diff = np.abs(terrain_copy - terrain).max()
modified_pixels = np.sum(np.abs(terrain_copy - terrain) > 1e-6)

print(f"\nAfter 1 particle:")
print(f"  Height at spawn: {final_height:.4f} (change: {final_height - initial_height:.6f})")
print(f"  Max terrain change: {terrain_diff:.6f}")
print(f"  Modified pixels: {modified_pixels}")
print(f"  Terrain range: [{terrain_copy.min():.3f}, {terrain_copy.max():.3f}]")

if terrain_diff < 1e-6:
    print("\n  [ERROR] NO TERRAIN MODIFICATION - Particle had no effect!")
else:
    print(f"\n  [OK] Terrain was modified by single particle")

# Test 2: Check gradient calculation
print("\n" + "="*80)
print("TEST 2: Gradient Calculation")
print("="*80)

from src.generation.hydraulic_erosion import calculate_gradient

# Test gradient at several points
test_points = [
    (64.0, 10.0, "Top (steep)"),
    (64.0, 64.0, "Middle"),
    (64.0, 120.0, "Bottom (flat)")
]

for x, y, label in test_points:
    grad_x, grad_y = calculate_gradient(terrain, x, y)
    slope = np.sqrt(grad_x**2 + grad_y**2)
    print(f"{label:20s} ({x:5.1f}, {y:5.1f}): grad=({grad_x:7.4f}, {grad_y:7.4f}), slope={slope:.4f}")

# Test 3: Multiple particles on fresh terrain
print("\n" + "="*80)
print("TEST 3: Multiple Particles (100)")
print("="*80)

terrain_multi = terrain.copy()
num_test_particles = 100

# Spawn particles randomly
np.random.seed(42)
spawn_x = np.random.uniform(10, resolution - 10, num_test_particles).astype(np.float32)
spawn_y = np.random.uniform(10, resolution - 10, num_test_particles).astype(np.float32)

# Track modifications per particle
modifications = []

for i in range(num_test_particles):
    before = terrain_multi.copy()
    simulate_particle_numba(
        terrain_multi, zones, kernel,
        spawn_x[i], spawn_y[i],
        params
    )
    after = terrain_multi
    max_change = np.abs(after - before).max()
    modifications.append(max_change)

modifications = np.array(modifications)

print(f"\nAfter {num_test_particles} particles:")
print(f"  Particles with effect > 1e-6: {np.sum(modifications > 1e-6)}/{num_test_particles}")
print(f"  Mean modification: {modifications.mean():.6f}")
print(f"  Max modification: {modifications.max():.6f}")
print(f"  Median modification: {np.median(modifications):.6f}")
print(f"  Total terrain change: {np.abs(terrain_multi - terrain).max():.6f}")

# Calculate buildability after multi-particle test
multi_slopes = BuildabilityEnforcer.calculate_slopes(terrain_multi, map_size_meters)
multi_buildable = BuildabilityEnforcer.calculate_buildability_percentage(multi_slopes)

print(f"\n  Initial buildability: {initial_buildable:.1f}%")
print(f"  After 100 particles:  {multi_buildable:.1f}%")
print(f"  Change:               {multi_buildable - initial_buildable:+.1f}%")

# Test 4: Full erosion simulation
print("\n" + "="*80)
print("TEST 4: Full Erosion (10,000 particles)")
print("="*80)

simulator = HydraulicErosionSimulator(
    resolution=resolution,
    map_size_meters=map_size_meters,
    seed=42
)

terrain_full = terrain.copy()
eroded, stats = simulator.erode(
    heightmap=terrain_full,
    buildability_potential=zones,
    num_particles=10000,
    verbose=True
)

print(f"\nResults:")
print(f"  Initial buildability: {stats['initial_buildable_pct']:.1f}%")
print(f"  Final buildability:   {stats['final_buildable_pct']:.1f}%")
print(f"  Improvement:          {stats['improvement_pct']:+.1f}%")

if stats['improvement_pct'] < 1.0:
    print(f"\n  [FAILURE] Erosion improvement < 1% - effectively no change!")
else:
    print(f"\n  [OK] Erosion had measurable effect")

# Test 5: Check if normalization is the problem
print("\n" + "="*80)
print("TEST 5: Normalization Impact")
print("="*80)

# Before normalization (from erosion internals)
print(f"\nBefore final normalization:")
print(f"  Buildability: {stats['final_buildable_pct']:.1f}%")
print(f"  Terrain range: [{terrain_full.min():.3f}, {terrain_full.max():.3f}]")

# After normalization (what erode() returns)
print(f"\nAfter normalization:")
print(f"  Terrain range: [{eroded.min():.3f}, {eroded.max():.3f}]")

# Recalculate buildability
normalized_slopes = BuildabilityEnforcer.calculate_slopes(eroded, map_size_meters)
normalized_buildable = BuildabilityEnforcer.calculate_buildability_percentage(normalized_slopes)
print(f"  Buildability: {normalized_buildable:.1f}%")

if abs(normalized_buildable - stats['final_buildable_pct']) > 1.0:
    print(f"\n  [ERROR] Normalization changed buildability by {normalized_buildable - stats['final_buildable_pct']:+.1f}%!")
else:
    print(f"\n  [OK] Normalization preserved buildability")

print("\n" + "="*80)
print("DIAGNOSIS COMPLETE")
print("="*80)
