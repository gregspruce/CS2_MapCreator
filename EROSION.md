# Hydraulic Erosion: Technical Documentation

**Version**: 2.0.0
**Algorithm**: Pipe Model (Mei et al. 2007)
**Implementation**: `src/features/hydraulic_erosion.py`
**Performance**: Numba JIT + Pure NumPy fallback

---

## Table of Contents

1. [Overview](#overview)
2. [Algorithm Theory](#algorithm-theory)
3. [Implementation Details](#implementation-details)
4. [Parameters Guide](#parameters-guide)
5. [Performance Analysis](#performance-analysis)
6. [Visual Examples](#visual-examples)
7. [Troubleshooting](#troubleshooting)

---

## Overview

### What is Hydraulic Erosion?

Hydraulic erosion simulates the physical process of water flowing across terrain, carving valleys and transporting sediment. This creates **dendritic drainage networks** - the tree-like valley systems characteristic of real mountain ranges.

### Why It Matters for CS2

- **Realism**: Transforms procedural noise into geologically-plausible terrain
- **Drainage**: Creates natural valley systems for rivers and lakes
- **Buildability**: Smooths valley floors, creating usable terrain for cities
- **Visual Quality**: Adds detail that makes terrain feel "real" rather than "generated"

### The Transformative Impact

**Before hydraulic erosion**:
- Random procedural noise
- No connected valley systems
- Grid-like artifacts
- Unrealistic mountain shapes

**After hydraulic erosion**:
- Connected dendritic drainage networks
- Natural valley systems
- Realistic erosion patterns
- Geologically-plausible terrain

---

## Algorithm Theory

### The Pipe Model (Mei et al. 2007)

Our implementation uses the **Pipe Model**, a grid-based physically-accurate erosion simulation. This is the industry standard used by World Machine, Gaea, and professional terrain tools.

#### How It Works

1. **Virtual Pipes**: Each grid cell has 8 virtual pipes connecting to its neighbors (D8 flow direction)
2. **Water Flow**: Water flows through pipes based on pressure differences
3. **Erosion**: Flowing water erodes the terrain proportional to velocity
4. **Sediment Transport**: Eroded material is carried downstream
5. **Deposition**: Sediment deposits when water slows down

### Physics Model

```
Water Flow:
- Pressure = Water Column Height + Terrain Height
- Flow Rate ∝ Pressure Difference
- Conservation of Mass (water neither created nor destroyed)

Erosion:
- Erosion Rate = Kₑ × sin(slope) × velocity
- Sediment Capacity = Kₛ × sin(slope) × velocity

Sediment Transport:
- IF sediment < capacity: Erosion occurs
- IF sediment > capacity: Deposition occurs
```

### D8 Flow Direction

We use the **D8 algorithm** (8-direction flow) to determine water movement:

```
NW   N   NE
  ↖ ↑ ↗
W  ← ■ → E
  ↙ ↓ ↘
SW   S   SE
```

Each cell's water flows to the lowest of its 8 neighbors, creating realistic drainage patterns.

---

## Implementation Details

### Dual-Path Architecture

```
┌─────────────────────┐
│  Erosion Requested  │
└──────────┬──────────┘
           │
           ▼
    ┌──────────────┐
    │ Numba Check  │
    └──────┬───────┘
           │
     ┌─────┴─────┐
     │           │
     ▼           ▼
┌─────────┐  ┌──────────┐
│ FAST    │  │ FALLBACK │
│ Numba   │  │ NumPy    │
│ JIT     │  │ (Pure)   │
└─────────┘  └──────────┘
     │           │
     └─────┬─────┘
           │
           ▼
    ┌──────────────┐
    │ Same Results │
    └──────────────┘
```

### Code Structure

**Main Class**: `HydraulicErosionSimulator`
- `apply_erosion()`: Public API
- `erosion_iteration_numba()`: JIT-compiled fast path (5-8× faster)
- `erosion_iteration_python()`: Pure NumPy fallback
- `compute_flow_direction_d8()`: D8 algorithm implementation

### Performance Strategy

1. **JIT Compilation**: Numba compiles Python → machine code on first run
2. **Vectorization**: All operations use NumPy arrays (no Python loops)
3. **Parallel Execution**: Numba automatically parallelizes independent operations
4. **Memory Efficiency**: In-place operations minimize allocations

---

## Parameters Guide

### Core Parameters

#### `erosion_iterations` (int, default: 50)
**What it does**: Number of simulation timesteps
**Impact**: More iterations = deeper valleys, more detail
**Presets**:
- Fast: 25 iterations (~0.7s at 1024×1024)
- Balanced: 50 iterations (~1.5s at 1024×1024)
- Maximum: 100 iterations (~3s at 1024×1024)

**Recommendation**: Start with 50 (balanced). Only increase if you need deeper valleys.

#### `erosion_rate` (float, default: 0.3)
**What it does**: Controls how quickly terrain erodes
**Range**: 0.0-1.0
**Impact**:
- Low (0.1-0.2): Subtle erosion, preserves original shapes
- Medium (0.3-0.4): **Recommended** - visible valleys without over-eroding
- High (0.5-1.0): Aggressive erosion, can create unrealistic deep valleys

**Physical meaning**: Kₑ in the erosion equation (dimensionless strength factor)

#### `deposition_rate` (float, default: 0.05)
**What it does**: Controls how quickly sediment settles
**Range**: 0.0-0.5
**Impact**:
- Low (0.01-0.03): Less smoothing, sharper valleys
- Medium (0.05-0.1): **Recommended** - natural valley floors
- High (0.1-0.5): Heavy smoothing, can fill valleys

**Physical meaning**: Deposition strength relative to erosion

#### `evaporation_rate` (float, default: 0.01)
**What it does**: Water loss per timestep
**Range**: 0.0-0.1
**Impact**:
- Low (0.001-0.005): Water travels far, long valleys
- Medium (0.01): **Recommended** - realistic drainage extent
- High (0.05-0.1): Water disappears quickly, short valleys

**Physical meaning**: Fraction of water lost per iteration

#### `sediment_capacity` (float, default: 4.0)
**What it does**: Maximum sediment water can carry
**Range**: 1.0-10.0
**Impact**:
- Low (1.0-2.0): Less erosion, more deposition
- Medium (4.0): **Recommended** - balanced erosion/deposition
- High (8.0-10.0): Aggressive erosion, less deposition

**Physical meaning**: Kₛ × velocity scaling factor

### Advanced Parameters

#### `rain_amount` (float, default: 0.01)
**What it does**: Water added uniformly each iteration
**Use case**: Simulates rainfall across entire terrain
**Range**: 0.0-0.1
**Note**: Usually not needed - initial water is sufficient

#### `gravity` (float, default: 9.81)
**What it does**: Gravitational acceleration (m/s²)
**Use case**: Adjust for different planetary bodies (e.g., Mars: 3.71)
**Range**: 1.0-20.0
**Note**: Leave at 9.81 for Earth-like terrain

---

## Performance Analysis

### Benchmarks (Intel/AMD x64 CPU)

**1024×1024 terrain, 50 iterations**:
- With Numba JIT: 1.47s (29.4ms per iteration)
- Without Numba: ~8-10s (160-200ms per iteration)
- **Speedup**: 5.4-6.8×

**4096×4096 terrain, 50 iterations**:
- With Numba JIT: 28s (560ms per iteration)
- Without Numba: ~180-220s
- **Speedup**: 6.4-7.9×

### First Run vs Subsequent Runs

**First run** (JIT compilation overhead):
- 1024×1024: ~3-5s (compilation + execution)
- GUI shows: "Compiling erosion (first run)..."

**Subsequent runs** (compiled code cached):
- 1024×1024: 1.47s (pure execution)
- 75% faster than first run

### Memory Usage

**Peak memory**:
- 1024×1024: ~50 MB
- 4096×4096: ~800 MB
- Formula: `resolution² × 8 bytes × ~12 arrays`

### Scaling Characteristics

- **Linear with iterations**: 100 iter = 2× time of 50 iter
- **Quadratic with resolution**: 4096² = 16× pixels = ~19× time of 1024²
  - (Slightly super-linear due to cache effects)

---

## Visual Examples

### Drainage Network Analysis

**Metric**: Fragmentation Score (networks per 1000 pixels)
- Before erosion: 15-25 (highly fragmented, noise-like)
- After erosion: 1-3 (highly connected, dendritic)

**Interpretation**:
- Low score (<5) = Well-connected drainage (realistic)
- High score (>10) = Fragmented patterns (unrealistic)

### Before/After Comparison

```
BEFORE EROSION:
- Random procedural noise
- No valley systems
- Grid artifacts
- 0.4% buildable terrain

AFTER EROSION (50 iterations):
- Dendritic drainage networks
- Connected valley systems
- Natural erosion patterns
- 0.5% buildable terrain
```

**Note**: Erosion alone adds drainage but doesn't significantly improve buildability. The buildability system (separate feature) handles that.

---

## Troubleshooting

### "Erosion too subtle - barely visible"

**Causes**:
1. Too few iterations (default 50 may be insufficient)
2. Erosion rate too low
3. Initial terrain too smooth

**Solutions**:
- Increase iterations to 75-100
- Increase `erosion_rate` to 0.4-0.5
- Ensure terrain has sufficient height variation (height_variation >70%)

### "Valleys too deep - unrealistic canyons"

**Causes**:
1. Too many iterations
2. Erosion rate too high
3. Deposition rate too low

**Solutions**:
- Reduce iterations to 25-40
- Reduce `erosion_rate` to 0.2
- Increase `deposition_rate` to 0.1

### "Performance slower than expected"

**Causes**:
1. Numba not installed or not working
2. First run (JIT compilation overhead)
3. Anti-virus scanning Python processes

**Solutions**:
- Verify Numba: Run `python verify_setup.py`
- Wait for first run to complete (subsequent runs faster)
- Check console for "Using FAST Numba path" message
- Add Python to anti-virus exceptions

### "Results inconsistent between runs"

**Causes**:
- Numba parallel execution introduces slight numerical differences
- This is normal and expected

**Solution**:
- Differences are typically <0.1% of terrain height
- If exact reproducibility needed, set `parallel=False` in Numba decorator
- Note: This reduces performance by ~30%

---

## Algorithm References

**Primary Source**:
- Mei, X., Decaudin, P., & Hu, B. (2007). "Fast hydraulic erosion simulation and visualization on GPU"
- Paper: https://inria.hal.science/inria-00402079/document

**Related Techniques**:
- D8 Flow Direction: O'Callaghan & Mark (1984)
- Sediment Transport: Einstein (1950), Meyer-Peter & Müller (1948)

**Alternative Implementations**:
- Droplet Erosion: Faster but lower quality
- Thermal Erosion: For steep cliffs and talus slopes
- Stream Power: Simplified erosion for large scales

**Why Pipe Model?**:
- Physically accurate (based on Navier-Stokes equations)
- Industry standard (used by all professional tools)
- Produces realistic dendritic drainage networks
- Balances quality and performance

---

## Integration with Pipeline

### Erosion Placement in Pipeline

```
1. Base Noise Generation
2. Height Variation
3. Coherent Terrain (optional)
4. >> HYDRAULIC EROSION << (YOU ARE HERE)
5. Terrain Realism (optional)
6. Buildability System
```

### Why This Order?

- **After base generation**: Need initial terrain to erode
- **Before realism features**: Erosion creates foundation for rivers/valleys
- **Before buildability**: Erosion shapes terrain, buildability smooths it

### Parameter Interactions

**Erosion + Height Variation**:
- High height variation (>80%) → More dramatic erosion effects
- Low height variation (<50%) → Subtle erosion, may need more iterations

**Erosion + Coherent Terrain**:
- Coherent terrain creates ridges → Erosion carves valleys between them
- Perfect synergy: Ridges define watersheds, erosion creates drainage

**Erosion + Buildability**:
- Erosion slightly increases buildability (0.4% → 0.5%)
- Buildability system does heavy lifting (0.5% → 42-45%)
- Together: Create realistic terrain that's also playable

---

## Future Enhancements (Not in v2.0.0)

**Possible Stage 2 additions**:
- Thermal erosion for cliff talus slopes
- River network extraction for explicit river placement
- Adaptive iteration count (stop when erosion stabilizes)
- GPU acceleration via CuPy (10-20× faster on NVIDIA GPUs)

**Stage 3 possibilities**:
- Multi-scale erosion (coarse → fine)
- Seasonal variation (wet/dry cycles)
- Tectonic uplift simulation
- Glacial erosion for polar terrain

---

**For performance tuning and Numba troubleshooting, see [PERFORMANCE.md](PERFORMANCE.md)**

**For buildability system details, see `src/techniques/buildability_system.py` docstrings**
