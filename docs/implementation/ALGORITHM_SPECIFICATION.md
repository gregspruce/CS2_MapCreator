# Algorithm Specification - Hybrid Zoned Generation + Hydraulic Erosion

**Session 1 Deliverable**
**Date**: 2025-10-09
**Purpose**: Complete mathematical specification for Sessions 2-5 implementation

---

## Overview

This document provides exact mathematical formulas and algorithms for the hybrid zoned generation system with hydraulic erosion. Each component is specified with:
- Mathematical formulas (exact, not prose)
- Algorithm pseudocode
- Parameter ranges and physical meanings
- Data structures and array shapes

---

## 1. Zone Generation (Session 2)

### 1.1 Objective
Generate continuous buildability potential maps (NOT binary masks) using low-frequency Perlin noise.

### 1.2 Mathematical Specification

**Buildability Potential Field**:
```
P(x, y) = FBM(x/λ, y/λ, O_zone, p_zone, l_zone)
```

Where:
- **P(x, y)**: Buildability potential at coordinates (x, y), range [0, 1]
  - P = 1.0 → High buildability desired (flat terrain)
  - P = 0.0 → Scenic/mountain area (dramatic terrain)
- **λ (wavelength)**: 5000-8000 meters (feature size for zones)
- **O_zone**: 2-3 octaves (low octaves = large smooth regions)
- **p_zone**: Persistence = 0.5 (standard for FBM)
- **l_zone**: Lacunarity = 2.0 (standard for FBM)

**Fractal Brownian Motion (FBM)**:
```
FBM(x, y, O, p, l) = Σ(i=0 to O-1) [p^i × noise(x × l^i, y × l^i)]
```

Normalized to [0, 1]:
```
P_norm(x, y) = (P(x, y) - P_min) / (P_max - P_min)
```

### 1.3 Target Coverage

Adjust threshold to achieve target buildable coverage:

**Threshold Calculation**:
```
threshold = percentile(P_norm, 100 - target_coverage)
```

Where `target_coverage` = 70-75% (percentage of map that should be buildable)

**Validation** (ensure target met):
```
actual_coverage = 100 × sum(P_norm > 0.5) / total_pixels
```

### 1.4 Data Structures

**Input**:
- `resolution`: int (4096 for CS2)
- `map_size_meters`: float (14336.0 for CS2)
- `target_coverage`: float (0.70 default, range 0.60-0.80)
- `zone_wavelength`: float (6500.0 meters default, range 5000-8000)
- `zone_octaves`: int (2 default, range 2-3)

**Output**:
- `buildability_potential`: np.ndarray, shape (4096, 4096), dtype float32
- Range: [0.0, 1.0] continuous (NOT binary)

### 1.5 Pseudocode

```python
def generate_buildability_zones(resolution, map_size_meters,
                                target_coverage=0.70,
                                zone_wavelength=6500.0,
                                zone_octaves=2):
    """Generate continuous buildability potential map."""

    # Initialize noise generator
    noise = PerlinNoise(octaves=zone_octaves, seed=seed)

    # Calculate frequency from wavelength
    # frequency = 1 / (wavelength_meters / map_size_meters)
    scale = zone_wavelength  # meters per noise unit

    # Generate low-frequency Perlin noise
    potential = np.zeros((resolution, resolution), dtype=np.float32)

    for y in range(resolution):
        for x in range(resolution):
            # Convert pixel coords to meters
            x_meters = (x / resolution) * map_size_meters
            y_meters = (y / resolution) * map_size_meters

            # Sample noise
            potential[y, x] = noise([x_meters/scale, y_meters/scale])

    # Normalize to [0, 1]
    potential = (potential - potential.min()) / (potential.max() - potential.min())

    # Verify coverage (percentage with potential > 0.5)
    coverage = 100 * np.sum(potential > 0.5) / potential.size
    print(f"Buildability coverage: {coverage:.1f}% (target: {target_coverage*100:.1f}%)")

    return potential
```

---

## 2. Zone-Weighted Terrain Generation (Session 3)

### 2.1 Objective
Generate terrain with amplitude modulated by buildability zones (continuous modulation, NOT binary).

### 2.2 Mathematical Specification

**Amplitude Modulation Function**:
```
A(x, y) = A_base × (A_min + (A_max - A_min) × (1 - P(x, y)))
```

Where:
- **A(x, y)**: Amplitude at coordinates (x, y)
- **A_base**: Base terrain amplitude (0.15-0.3, default 0.2)
- **A_min**: Minimum amplitude multiplier (0.2-0.4, default 0.3)
  - Applied in high buildability zones (P = 1.0)
  - Result: gentle terrain (30% of base amplitude)
- **A_max**: Maximum amplitude multiplier (0.8-1.2, default 1.0)
  - Applied in low buildability zones (P = 0.0)
  - Result: full terrain detail (100% of base amplitude)
- **P(x, y)**: Buildability potential from Session 2

**Example Values**:
- P(x, y) = 1.0 (high buildability) → A(x, y) = A_base × 0.3 (gentle)
- P(x, y) = 0.5 (moderate) → A(x, y) = A_base × 0.65 (intermediate)
- P(x, y) = 0.0 (scenic) → A(x, y) = A_base × 1.0 (full detail)

**Weighted Terrain Generation**:
```
T(x, y) = A(x, y) × FBM(x, y, O_terrain, p_terrain, l_terrain)
```

Where:
- **T(x, y)**: Terrain height at (x, y)
- **O_terrain**: 6 octaves (standard for realistic terrain)
- **p_terrain**: 0.5 persistence
- **l_terrain**: 2.0 lacunarity

### 2.3 Critical Difference from Current System

**AVOID**:
```
❌ WRONG: Binary amplitude multiplication
T(x, y) = mask(x, y) × noise(x, y)  # Creates frequency discontinuities!
```

**CORRECT**:
```
✅ RIGHT: Continuous amplitude modulation
T(x, y) = amplitude_function(P(x, y)) × noise(x, y)  # Smooth transitions
```

### 2.4 Data Structures

**Input**:
- `buildability_potential`: np.ndarray, shape (4096, 4096), dtype float32 (from Session 2)
- `A_base`: float (0.2 default)
- `A_min`: float (0.3 default)
- `A_max`: float (1.0 default)
- `octaves`: int (6 default)

**Output**:
- `terrain`: np.ndarray, shape (4096, 4096), dtype float32
- Range: [0.0, 1.0] normalized (before erosion)

### 2.5 Expected Buildability (Before Erosion)

```
Expected buildable percentage ≈ 40-45%
```

This is INTENTIONAL - erosion will increase buildability to 55-65% target.

---

## 3. Particle-Based Hydraulic Erosion (Session 4)

### 3.1 Objective
Implement particle-based erosion simulation to achieve 55-65% buildable terrain through sediment deposition in valleys.

### 3.2 Particle Structure

```python
class Particle:
    position: tuple[float, float]  # (x, y) in pixel coordinates
    velocity: tuple[float, float]  # (vx, vy) in pixels/step
    sediment: float                # Amount of sediment carried
    water: float                   # Water volume (decreases via evaporation)
```

### 3.3 Core Algorithm - Particle Lifecycle

**Initialization**:
```python
def spawn_particle(heightmap):
    # Spawn at random position (weighted by elevation)
    x = random.uniform(0, width)
    y = random.uniform(0, height)

    particle = Particle(
        position = (x, y),
        velocity = (0.0, 0.0),
        sediment = 0.0,
        water = 1.0  # Initial water volume
    )
    return particle
```

**Main Simulation Loop** (per particle):
```python
def simulate_particle(particle, heightmap, buildability_potential, params):
    """Simulate single particle until it exits or stops."""

    max_steps = 1000  # Prevent infinite loops

    for step in range(max_steps):
        # 1. Check termination conditions
        if not in_bounds(particle.position):
            break
        if particle.water < 0.01:  # Evaporated
            break

        # 2. Calculate gradient at current position (bilinear interpolation)
        gradient = calculate_gradient(heightmap, particle.position)
        slope = length(gradient)

        if slope < params.min_slope:
            break  # Stuck in local minimum

        # 3. Update velocity (gradient descent + inertia)
        particle.velocity = (
            params.inertia * particle.velocity +
            (1 - params.inertia) * gradient
        )

        # 4. Calculate sediment capacity
        capacity = params.sediment_capacity * slope * length(particle.velocity) * particle.water

        # 5. Erode or deposit
        if particle.sediment < capacity:
            # ERODE
            erode_amount = (capacity - particle.sediment) * params.erosion_rate

            # Modulate erosion by buildability zones
            zone_factor = get_zone_modulation(buildability_potential, particle.position)
            erode_amount *= zone_factor

            # Apply erosion with Gaussian brush
            apply_gaussian_erosion(heightmap, particle.position, -erode_amount, params.brush_radius)
            particle.sediment += erode_amount

        else:
            # DEPOSIT
            deposit_amount = (particle.sediment - capacity) * params.deposition_rate

            # Apply deposition with Gaussian brush
            apply_gaussian_deposition(heightmap, particle.position, deposit_amount, params.brush_radius)
            particle.sediment -= deposit_amount

        # 6. Move particle
        particle.position = (
            particle.position[0] + particle.velocity[0],
            particle.position[1] + particle.velocity[1]
        )

        # 7. Evaporate water
        particle.water *= (1.0 - params.evaporation_rate)
```

### 3.4 Zone Modulation for Erosion

**Critical for achieving buildability target**:

```python
def get_zone_modulation(buildability_potential, position):
    """
    Modulate erosion strength based on buildability zones.

    - High buildability zones: INCREASE erosion/deposition (creates flat valleys)
    - Low buildability zones: DECREASE erosion (preserves mountains)
    """
    x, y = int(position[0]), int(position[1])
    potential = buildability_potential[y, x]

    # Modulation formula:
    # potential = 1.0 (buildable) → factor = 1.5 (strong erosion)
    # potential = 0.0 (scenic) → factor = 0.5 (gentle erosion)
    factor = 0.5 + 1.0 * potential

    return factor
```

### 3.5 Gaussian Erosion Brush

**Purpose**: Prevent single-pixel artifacts, spread erosion naturally

```python
def apply_gaussian_erosion(heightmap, position, amount, radius):
    """Apply erosion with Gaussian falloff."""

    x, y = int(position[0]), int(position[1])

    # Create Gaussian kernel
    kernel_size = 2 * radius + 1
    kernel = gaussian_kernel_2d(kernel_size, sigma=radius/2)

    # Apply to heightmap region
    for dy in range(-radius, radius+1):
        for dx in range(-radius, radius+1):
            nx, ny = x + dx, y + dy
            if in_bounds((nx, ny)):
                weight = kernel[dy + radius, dx + radius]
                heightmap[ny, nx] += amount * weight
```

**Gaussian Kernel Formula**:
```
G(x, y) = (1 / (2πσ²)) × exp(-(x² + y²) / (2σ²))
```

Where σ = radius / 2

### 3.6 Mathematical Formulas

**Sediment Capacity**:
```
C = K_s × slope × |velocity| × water_volume
```

**Erosion Amount**:
```
ΔH_erode = (C - S_current) × K_e × zone_factor
```

**Deposition Amount**:
```
ΔH_deposit = (S_current - C) × K_d
```

**Velocity Update (with inertia)**:
```
v_new = I × v_old + (1 - I) × ∇h
```

Where:
- **K_s**: Sediment capacity coefficient (4.0)
- **K_e**: Erosion rate (0.3-0.8, default 0.5)
- **K_d**: Deposition rate (0.1-0.5, default 0.3)
- **I**: Inertia (0.05-0.3, default 0.1)
- **∇h**: Heightmap gradient (direction of steepest descent)

### 3.7 Parameters

| Parameter | Symbol | Default | Range | Physical Meaning |
|-----------|--------|---------|-------|------------------|
| Number of particles | N_p | 100,000 | 50k-200k | More = smoother, slower |
| Inertia | I | 0.1 | 0.05-0.3 | Momentum preservation |
| Erosion rate | K_e | 0.5 | 0.3-0.8 | Terrain carving speed |
| Deposition rate | K_d | 0.3 | 0.1-0.5 | Sediment settling speed |
| Evaporation rate | K_ev | 0.02 | 0.01-0.05 | Water loss per step |
| Sediment capacity | K_s | 4.0 | 2.0-6.0 | Max sediment per water |
| Min slope | s_min | 0.0005 | 0.0001-0.001 | Movement threshold |
| Brush radius | r_b | 3 | 3-5 pixels | Erosion spread area |

### 3.8 Performance Optimization (Numba)

**Numba JIT Compilation**:
```python
from numba import njit, prange

@njit(parallel=False, cache=True)
def erosion_simulation_numba(heightmap, buildability_potential,
                              num_particles, params):
    """JIT-compiled erosion simulation."""

    # Main particle loop (can be parallelized with prange)
    for particle_idx in range(num_particles):
        # Spawn particle
        x = random_uniform(0, width)
        y = random_uniform(0, height)

        # ... simulation loop (as above)

    return heightmap
```

**Expected Performance**:
- **With Numba**: 2-5 minutes for 100k particles at 4096×4096
- **Pure NumPy**: 10-30 minutes (fallback)

### 3.9 Expected Result

After erosion:
```
Buildable percentage: 55-65%
```

Compared to before erosion (40-45%), this is a **15-20 percentage point increase** due to sediment deposition creating flat valleys.

---

## 4. Ridge Enhancement (Session 5)

### 4.1 Objective
Add ridge noise to mountain zones for coherent ranges with sharp ridgelines.

### 4.2 Mathematical Specification

**Ridge Noise Formula**:
```
R(x, y) = 2 × |0.5 - FBM(x, y, O_ridge, p_ridge, l_ridge)|
```

Where:
- **FBM**: Standard Fractal Brownian Motion (as defined earlier)
- **O_ridge**: 4-6 octaves
- **p_ridge**: 0.5 persistence
- **l_ridge**: 2.0 lacunarity

**Absolute Value Transform**:
```
|0.5 - noise| creates V-shaped valleys → sharp ridges
```

**Zone-Restricted Application**:
```
T_final(x, y) = T(x, y) + α(x, y) × R(x, y)
```

Where α(x, y) is the ridge blending factor:
```
α(x, y) = smoothstep(0.2, 0.4, 1 - P(x, y))
```

**Smoothstep Function** (smooth transition):
```
smoothstep(edge0, edge1, x) =
  let t = clamp((x - edge0) / (edge1 - edge0), 0, 1)
  return t² × (3 - 2t)
```

### 4.3 Application Zones

- **P(x, y) > 0.4**: No ridges (buildable zones, α = 0)
- **0.2 < P(x, y) < 0.4**: Smooth transition (α increases 0 → 1)
- **P(x, y) < 0.2**: Full ridges (scenic mountain zones, α = 1)

### 4.4 Pseudocode

```python
def apply_ridge_enhancement(terrain, buildability_potential):
    """Add ridge noise to mountain zones only."""

    # Generate ridge noise
    ridge_noise = generate_ridge_noise(resolution, octaves=5)

    # Calculate blending factor (only in mountain zones)
    inverse_potential = 1.0 - buildability_potential
    alpha = smoothstep(0.2, 0.4, inverse_potential)

    # Blend ridge noise
    enhanced = terrain + alpha * ridge_noise * 0.2  # Scale ridge contribution

    return enhanced
```

---

## 5. Data Flow Summary

### 5.1 Pipeline Order

```
Session 2: Buildability Zones (P)
    ↓
Session 3: Weighted Terrain (T) using (P)
    ↓
Session 5: Ridge Enhancement (T_ridge) using (P)
    ↓
Session 4: Hydraulic Erosion (T_final) using (T_ridge, P)
    ↓
Normalization & Export
```

### 5.2 Array Shapes Throughout Pipeline

All intermediate arrays:
- **Shape**: (4096, 4096)
- **dtype**: float32
- **Range**: [0.0, 1.0] normalized

### 5.3 Key Parameters Summary

| Component | Key Parameters | Defaults |
|-----------|----------------|----------|
| Zone Generation | wavelength, octaves, coverage | 6500m, 2, 70% |
| Weighted Terrain | A_min, A_max, octaves | 0.3, 1.0, 6 |
| Hydraulic Erosion | particles, erosion_rate, deposition_rate | 100k, 0.5, 0.3 |
| Ridge Enhancement | blend_range, ridge_octaves | 0.2-0.4, 5 |

---

## 6. Validation Criteria

### 6.1 Zone Generation (Session 2)
- ✅ Coverage 70-75% (percentage with P > 0.5)
- ✅ Large-scale features (wavelength 5-8km)
- ✅ Continuous values (no binary steps)

### 6.2 Weighted Terrain (Session 3)
- ✅ Buildable zones 40-45% (before erosion)
- ✅ Smooth amplitude transitions
- ✅ No frequency discontinuities

### 6.3 Hydraulic Erosion (Session 4)
- ✅ Final buildable 55-65%
- ✅ Coherent drainage networks
- ✅ Flat valleys (sediment deposition visible)
- ✅ Performance < 5 minutes at 4096×4096

### 6.4 Ridge Enhancement (Session 5)
- ✅ Sharp ridgelines in mountain zones only
- ✅ No ridges in buildable zones
- ✅ Smooth blending at boundaries

---

## 7. References

**Industry Standard Approaches**:
- World Machine: Hydraulic erosion + buildability zones
- Gaea: Particle-based erosion simulation
- Houdini: Height field erosion nodes

**Research Papers**:
- Mei et al. (2007): "Fast Hydraulic Erosion Simulation and Visualization on GPU"
- Quilez (2008): "Domain Warping" techniques

**Implementation References**:
- terrain-erosion-3-ways (GitHub): Three erosion methods comparison
- Nick McDonald's blog: Particle-based erosion implementation
- Sebastian Lague: Hydraulic Erosion (Unity/C#)

---

**Document Complete**
**Next Session**: Session 2 - Implement `BuildabilityZoneGenerator` class based on specifications above
