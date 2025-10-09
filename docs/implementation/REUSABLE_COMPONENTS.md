# Reusable Components from Existing Codebase

**Session 1 Deliverable**
**Date**: 2025-10-09
**Purpose**: Identify existing code that can be reused in new hybrid zoned generation + erosion system

---

## Overview

The existing codebase contains high-quality components that can be reused in the new system. This document catalogs reusable code with:
- Location (file:line references)
- Functionality description
- Required adaptations (if any)
- Integration notes

---

## 1. Noise Generation Infrastructure

### 1.1 NoiseGenerator Class
**Location**: `src/noise_generator.py:33-881`

**Reusable Components**:

#### Perlin Noise Generation (Fast Path)
- **Method**: `_generate_perlin_fast()` (lines 157-286)
- **Functionality**: Vectorized Perlin noise using FastNoiseLite
- **Performance**: 10-100× faster than pure Python
- **Reuse For**: Session 2 (zone generation), Session 3 (weighted terrain)
- **Adaptation**: None required - already optimized

**Example Usage**:
```python
from src.noise_generator import NoiseGenerator

gen = NoiseGenerator(seed=42)
zone_noise = gen.generate_perlin(
    resolution=4096,
    scale=6500.0,      # Zone wavelength
    octaves=2,          # Low octaves for large features
    persistence=0.5
)
```

#### Recursive Domain Warping
- **Method**: `_apply_recursive_domain_warp()` (lines 288-371)
- **Functionality**: Inigo Quilez two-stage domain warping
- **Performance**: +1-2s overhead for dramatic quality improvement
- **Reuse For**: Session 3 (optional enhancement for weighted terrain)
- **Adaptation**: Already implemented, can be enabled via parameter

#### OpenSimplex2 Noise (Alternative)
- **Method**: `_generate_simplex_fast()` (lines 569-620)
- **Functionality**: Faster alternative to Perlin
- **Reuse For**: Session 2 (if Perlin performance insufficient)
- **Adaptation**: Drop-in replacement for Perlin

#### Fallback Implementation
- **Method**: `generate_perlin()` with FASTNOISE_AVAILABLE check (lines 112-155)
- **Functionality**: Pure Python fallback for systems without FastNoiseLite
- **Reuse For**: Ensuring portability
- **Adaptation**: None - graceful fallback already implemented

**What NOT to Reuse**:
- ❌ `generate_buildability_control_map()` (lines 373-504) - This implements BINARY masks (deprecated approach)
- ❌ Multi-octave blending from gradient system - Creates frequency discontinuities

---

## 2. Terrain Analysis and Validation

### 2.1 TerrainAnalyzer Class
**Location**: `src/analysis/terrain_analyzer.py`

**Reusable Components**:

#### Slope Calculation (Fixed Implementation)
- **Method**: `calculate_slope()` with pixel spacing
- **Functionality**: Accurate slope calculation in percentage
- **Formula**: `slope% = 100 × sqrt(dx² + dy²) / pixel_size_meters`
- **Reuse For**: Sessions 4, 8 (erosion validation, constraint verification)
- **Adaptation**: Already fixed (critical bugfix in commit 3bddd54)

**Example Usage**:
```python
from src.analysis.terrain_analyzer import TerrainAnalyzer

analyzer = TerrainAnalyzer(
    heightmap=terrain,
    map_size_meters=14336.0
)

slopes = analyzer.calculate_slope()
buildable_pct = np.sum(slopes <= 5.0) / slopes.size * 100
```

#### Buildability Analysis
- **Method**: `calculate_buildability()`
- **Functionality**: Returns percentage of terrain with slope ≤ 5%
- **Reuse For**: All validation (Sessions 2-10)
- **Adaptation**: None required

---

## 3. Buildability Enforcement Infrastructure

### 3.1 BuildabilityEnforcer Class
**Location**: `src/buildability_enforcer.py`

**Reusable Components**:

#### Slope Calculation (Static Method)
- **Method**: `BuildabilityEnforcer.calculate_slopes()` (lines 185-210)
- **Functionality**: Calculate slope percentage with correct pixel spacing
- **Reuse For**: Sessions 4, 6, 8 (erosion validation, pipeline integration, constraint verification)
- **Adaptation**: None required - already static method

**Example Usage**:
```python
from src.buildability_enforcer import BuildabilityEnforcer

slopes = BuildabilityEnforcer.calculate_slopes(
    heightmap=terrain,
    map_size_meters=14336.0
)
```

#### Buildability Percentage Calculation
- **Method**: `BuildabilityEnforcer.calculate_buildability_percentage()` (lines 212-224)
- **Functionality**: Returns percentage with slope ≤ 5%
- **Reuse For**: Validation throughout Sessions 2-10
- **Adaptation**: None required

#### Gaussian Blur (Smart Blur Optional)
- **Method**: `BuildabilityEnforcer.smart_blur()` (lines 227-261)
- **Functionality**: Feature-preserving Gaussian smoothing
- **Reuse For**: Session 8 (optional detail addition smoothing)
- **Adaptation**: Can be used if post-erosion cleanup needed

**What NOT to Reuse**:
- ❌ `generate_buildability_mask_from_tectonics()` - Creates BINARY masks (new system uses continuous zones)
- ❌ `enforce_buildability_constraint()` - Post-processing approach (new system generates buildability directly)

---

## 4. Tectonic Structure Generation

### 4.1 TectonicStructureGenerator Class
**Location**: `src/tectonic_generator.py:25-767`

**Partially Reusable** - Architecture differs but techniques reusable

#### Fault Line Generation
- **Methods**: `generate_fault_lines()`, `_generate_control_points()`, `_rasterize_curve()` (lines 78-368)
- **Functionality**: Bezier curve fault generation
- **Reuse For**: Session 2 (OPTIONAL - could generate zones along fault patterns)
- **Adaptation**: New system uses Perlin noise for zones, but fault-based zones possible

#### Distance Field Calculation
- **Method**: `calculate_distance_field()` (lines 409-441)
- **Functionality**: Euclidean distance transform
- **Reuse For**: Session 2 (if using fault-based zone generation)
- **Adaptation**: None if used

#### Smart Normalization
- **Code**: Lines 719-742 in `generate_amplitude_modulated_terrain()`
- **Functionality**: Prevents gradient amplification during normalization
- **Critical Fix**: Clips instead of stretching when range already acceptable
- **Reuse For**: Sessions 3, 6 (weighted terrain, pipeline integration)
- **Adaptation**: Extract as standalone utility function

**Example Extraction**:
```python
def smart_normalize(terrain, verbose=True):
    """
    Smart normalization that avoids gradient amplification.

    If terrain is already in [0, 1] range (with ±10% tolerance),
    use clipping instead of stretching to avoid amplifying gradients.
    """
    t_min, t_max = terrain.min(), terrain.max()

    if t_min >= -0.1 and t_max <= 1.1:
        # Already acceptable - clip without stretching
        if verbose:
            print(f"[SMART NORM] Clipping to [0,1] (no amplification)")
        return np.clip(terrain, 0.0, 1.0)
    else:
        # Need normalization
        if verbose:
            print(f"[SMART NORM] Normalizing [{t_min:.3f}, {t_max:.3f}] → [0,1]")
        return (terrain - t_min) / (t_max - t_min)
```

**What NOT to Reuse**:
- ❌ `generate_amplitude_modulated_terrain()` - Implements binary mask approach (deprecated)
- Use smart normalization technique ONLY, not full method

---

## 5. Existing Hydraulic Erosion (Analysis Only)

### 5.1 HydraulicErosionSimulator Class
**Location**: `src/features/hydraulic_erosion.py:47-480`

**NOT Directly Reusable** - Uses pipe model instead of particle-based

**Algorithm Difference**:
- **Existing**: Pipe model (Mei et al. 2007) - grid-based water flow
- **Required**: Particle-based (separate water droplets)

**However, Reusable Techniques**:

#### Numba JIT Pattern
- **Code**: `@jit(nopython=True, parallel=False, cache=True)` decorator (line 359)
- **Functionality**: JIT compilation for performance
- **Reuse For**: Session 4 (particle erosion loop optimization)
- **Adaptation**: Apply same pattern to particle simulation

**Example Adaptation**:
```python
from numba import njit

@njit(parallel=False, cache=True)
def particle_erosion_loop(heightmap, buildability_potential,
                          num_particles, params):
    """Numba-optimized particle erosion."""
    # ... particle simulation code ...
    return heightmap
```

#### D8 Flow Directions
- **Code**: `DIRECTIONS` and `DISTANCES` arrays (lines 64-77)
- **Functionality**: 8-neighbor direction offsets and distances
- **Reuse For**: Session 4 (gradient calculation for particle movement)
- **Adaptation**: Can use same direction arrays

#### Distance-Based Lookup
- **Pattern**: Bilinear interpolation for sub-pixel sampling
- **Reuse For**: Session 4 (particle position → heightmap value)
- **Adaptation**: Implement bilinear interpolation utility

---

## 6. GUI Integration Infrastructure

### 6.1 ParameterPanel Class
**Location**: `src/gui/parameter_panel.py`

**Reusable Components**:

#### Parameter Control Pattern
- **Example**: Lines 310-394 (buildability system controls)
- **Functionality**: Slider + label + tooltip pattern
- **Reuse For**: Session 9 (add new system parameters to GUI)
- **Adaptation**: Follow existing pattern for consistency

**Example Pattern**:
```python
# Zone coverage slider (Session 2)
zone_coverage_label = QLabel("Zone Coverage:")
zone_coverage_slider = QSlider(Qt.Horizontal)
zone_coverage_slider.setRange(60, 80)  # 60-80%
zone_coverage_slider.setValue(70)       # Default 70%
zone_coverage_slider.setToolTip(
    "Percentage of map that should be buildable (60-80%)"
)
```

#### Validation and Real-Time Updates
- **Pattern**: `valueChanged` signal connections
- **Reuse For**: Session 9 (parameter updates)
- **Adaptation**: Connect new parameters to generation pipeline

---

## 7. Utility Functions and Patterns

### 7.1 Numpy Operations

#### Array Initialization
**Pattern**:
```python
# Pre-allocate arrays with correct dtype
heightmap = np.zeros((resolution, resolution), dtype=np.float32)
```
**Reuse For**: All sessions
**Rationale**: float32 uses half memory of float64, sufficient precision for heightmaps

#### Safe Array Indexing
**Pattern** (from `tectonic_generator.py:400-407`):
```python
# Bounds check before indexing
valid = (
    (x_pixels >= 0) & (x_pixels < resolution) &
    (y_pixels >= 0) & (y_pixels < resolution)
)
mask[y_pixels[valid], x_pixels[valid]] = True
```
**Reuse For**: Session 4 (particle position validation)

#### Gaussian Kernel Generation
**Needed For**: Session 4 (erosion brush)
**Implementation Required**: Create standalone utility

**Example**:
```python
def gaussian_kernel_2d(size, sigma):
    """Generate 2D Gaussian kernel."""
    ax = np.arange(-size//2 + 1, size//2 + 1)
    xx, yy = np.meshgrid(ax, ax)
    kernel = np.exp(-(xx**2 + yy**2) / (2 * sigma**2))
    return kernel / kernel.sum()  # Normalize
```

### 7.2 Progress Tracking

**Location**: `src/progress_tracker.py`
**Reusable For**: All sessions (show generation progress)
**Usage**:
```python
from src.progress_tracker import ProgressTracker

with ProgressTracker("Simulating erosion", total=num_particles) as progress:
    for i in range(num_particles):
        # ... simulate particle ...
        if i % 1000 == 0:
            progress.update(1000)
```

---

## 8. Module Structure for New System

### 8.1 Recommended Directory Structure

```
src/generation/
├── __init__.py
├── zone_generator.py           # Session 2
├── weighted_terrain.py         # Session 3
├── hydraulic_erosion.py        # Session 4 (NEW - particle-based)
├── ridge_enhancement.py        # Session 5
├── pipeline.py                 # Session 6
├── river_analysis.py           # Session 7
└── utils/
    ├── __init__.py
    ├── smart_normalize.py      # Extracted from tectonic_generator
    ├── gaussian_kernel.py      # New utility
    └── bilinear_interpolation.py  # New utility
```

### 8.2 Import Strategy

**Reuse existing**:
```python
# Noise generation
from src.noise_generator import NoiseGenerator

# Validation
from src.buildability_enforcer import BuildabilityEnforcer

# Analysis
from src.analysis.terrain_analyzer import TerrainAnalyzer

# Progress tracking
from src.progress_tracker import ProgressTracker
```

**New implementations** (Sessions 2-5):
```python
# New generation pipeline
from src.generation.zone_generator import BuildabilityZoneGenerator
from src.generation.weighted_terrain import ZoneWeightedTerrainGenerator
from src.generation.hydraulic_erosion import ParticleBasedErosion
from src.generation.ridge_enhancement import RidgeEnhancer
from src.generation.pipeline import HybridTerrainPipeline
```

---

## 9. What NOT to Reuse (Deprecated Approaches)

### 9.1 Binary Mask System
**Location**: `src/buildability_enforcer.py:44-182`
**Reason**: New system uses CONTINUOUS buildability potential, not binary masks
**Replacement**: Session 2 zone generation with Perlin noise

### 9.2 Gradient Control Map
**Location**: `src/noise_generator.py:373-504`
**Reason**: Causes frequency discontinuities (root cause of 3.4% failure)
**Replacement**: Session 3 amplitude modulation

### 9.3 Multi-Octave Blending
**Anti-Pattern**:
```python
# ❌ DO NOT DO THIS (creates frequency discontinuities)
terrain = (
    0.3 * noise(x, y, octaves=2) +  # Buildable
    0.4 * noise(x, y, octaves=5) +  # Transition
    0.3 * noise(x, y, octaves=7)    # Scenic
)
```

**Correct Approach** (Session 3):
```python
# ✅ Single noise field, amplitude modulation only
base_noise = noise(x, y, octaves=6)  # SAME octaves everywhere
amplitude = lerp(0.3, 1.0, 1 - buildability_potential)
terrain = amplitude * base_noise  # Modulate amplitude, NOT frequency
```

### 9.4 Post-Processing Smoothing (as primary buildability method)
**Location**: `src/buildability_enforcer.py:263-394`
**Reason**: New system generates buildable terrain directly via erosion
**Use Case**: Optional cleanup only (not primary mechanism)

---

## 10. Dependencies to Maintain

### 10.1 Required External Libraries

**Already Available**:
- `numpy`: Array operations
- `scipy`: Gaussian filters, interpolation, distance transforms
- `numba`: JIT compilation (optional but recommended)
- `pyfastnoiselite`: Fast noise generation (optional but recommended)

**No New Dependencies Required** for Sessions 2-5

### 10.2 Version Compatibility

Check existing `requirements.txt` or `pyproject.toml`:
- numpy >= 1.20.0
- scipy >= 1.7.0
- numba >= 0.54.0 (optional)
- pyfastnoiselite >= 1.0.0 (optional)

---

## 11. Testing Infrastructure

### 11.1 Existing Test Patterns

**Location**: `tests/` directory
**Pattern**: pytest-based tests with fixtures

**Reusable Test Patterns**:
```python
import pytest
import numpy as np

def test_zone_generation():
    """Test buildability zone generation."""
    from src.generation.zone_generator import BuildabilityZoneGenerator

    gen = BuildabilityZoneGenerator(resolution=1024, seed=42)
    zones = gen.generate_potential_map(target_coverage=0.70)

    # Validate output
    assert zones.shape == (1024, 1024)
    assert zones.dtype == np.float32
    assert zones.min() >= 0.0
    assert zones.max() <= 1.0

    # Validate coverage
    coverage = np.sum(zones > 0.5) / zones.size
    assert 0.65 <= coverage <= 0.75  # 70% ± 5%
```

### 11.2 Validation Functions to Reuse

**From existing tests**:
- Shape validation
- Range validation ([0, 1] normalized)
- Buildability percentage calculation
- Statistical analysis (mean, std, percentiles)

---

## 12. Performance Benchmarking

### 12.1 Existing Benchmark Pattern

**Example** (from `hydraulic_erosion.py:159-163`):
```python
import time

start_time = time.time()
# ... operation ...
elapsed = time.time() - start_time

print(f"[TIMING] Operation complete in {elapsed:.2f}s")
```

**Reuse For**: All sessions to track performance

### 12.2 Target Performance Metrics

| Session | Component | Target Time (4096×4096) |
|---------|-----------|-------------------------|
| 2 | Zone generation | < 1 second |
| 3 | Weighted terrain | < 10 seconds |
| 4 | Hydraulic erosion | < 5 minutes |
| 5 | Ridge enhancement | < 10 seconds |
| 6 | Full pipeline | < 6 minutes |

---

## Summary: Key Reusable Components

### ✅ **Directly Reusable (No Changes)**:
1. `NoiseGenerator._generate_perlin_fast()` - Fast noise generation
2. `BuildabilityEnforcer.calculate_slopes()` - Slope calculation
3. `BuildabilityEnforcer.calculate_buildability_percentage()` - Validation
4. `TerrainAnalyzer` - Analysis tools
5. `ProgressTracker` - Progress display
6. Numba JIT patterns - Performance optimization
7. GUI parameter control patterns - User interface

### 🔧 **Reusable with Adaptation**:
1. Smart normalization technique (extract from `tectonic_generator.py`)
2. D8 flow directions (adapt for particle movement)
3. Gaussian blur (adapt for erosion brush)
4. Domain warping (optional enhancement)

### ❌ **NOT Reusable (Deprecated)**:
1. Binary mask generation
2. Gradient control map
3. Multi-octave blending
4. Pipe model erosion (needs particle-based replacement)
5. Post-processing as primary buildability mechanism

---

**Document Complete**
**Next**: Create SESSION_2_HANDOFF.md for implementation kickoff
