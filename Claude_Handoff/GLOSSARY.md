# Glossary: Terms, Concepts, and Calculations

**Purpose**: Quick reference for terminology and mathematical concepts in the CS2 Map Generator

---

## A

### Amplitude Modulation
**Definition**: Varying the strength (amplitude) of a signal while keeping its frequency constant.

**In this project**: Single noise field (6 octaves everywhere), amplitude varies by zone:
- Buildable zones: amplitude × 0.05 (gentle)
- Scenic zones: amplitude × 0.2 (moderate detail)

**Why**: Prevents frequency discontinuities that plagued the gradient system.

**See**: Task 2.3, `src/tectonic_generator.py::generate_amplitude_modulated_terrain()`

---

## B

### Binary Mask
**Definition**: Image where each pixel is either 0 or 1 (two states only).

**In this project**: Buildability mask where:
- 1 = buildable zone (valleys, plains)
- 0 = scenic zone (mountains)

**Why Binary**: Enables amplitude modulation approach (can't have "half" octaves).

**Contrast**: Gradient control map used continuous 0.0-1.0 values (failed catastrophically).

**See**: Task 2.2, `src/buildability_enforcer.py::generate_buildability_mask_from_tectonics()`

---

### Buildability
**Definition**: Percentage of terrain with slopes ≤5% (CS2 standard for construction).

**Calculation**:
```python
slopes = calculate_slopes(heightmap)
buildable_mask = slopes <= 5.0
buildable_percentage = (buildable_mask.sum() / slopes.size) * 100.0
```

**Original Target**: 45-55%
**Current Achievement**: 18.5%
**Adjusted Target**: 15-25% (realistic for mountainous terrain)

**See**: Priority 2+6 System

---

### B-Spline
**Definition**: Mathematical curve defined by control points with smooth curvature.

**In this project**: Used to create tectonic fault lines:
- Input: 5-7 control points (random placements)
- Output: Smooth fault line curve
- Properties: C2 continuous (smooth first and second derivatives)

**Why B-Spline**: Creates realistic, geologically plausible fault traces (not jagged lines).

**See**: Task 2.1, `src/tectonic_generator.py::generate_fault_lines()`

---

## C

### Clipping (Normalization)
**Definition**: Constraining values to a range without stretching.

**Formula**:
```python
clipped = np.clip(values, 0.0, 1.0)  # Any value <0 → 0, >1 → 1
```

**Contrast**: Stretching normalization (see below)

**In Smart Normalization**:
- IF range in [-0.1, 1.1]: CLIP (no gradient amplification)
- ELSE: STRETCH (gradient amplification)

**See**: Smart Normalization, `src/tectonic_generator.py` lines 719-742

---

### CS2
**Definition**: Cities: Skylines 2, a city-building simulation game by Colossal Order.

**Heightmap Requirements**:
- Resolution: 4096×4096 pixels (REQUIRED)
- Format: 16-bit grayscale PNG
- Value Range: 0-65535
- Physical Size: 14,336m × 14,336m (default)
- Height Scale: 0-4096m (customizable in-game)
- Buildability: 0-5% slopes

---

## D

### D8 Flow Direction
**Definition**: Algorithm for water flow simulation on heightmaps.

**Method**: Each cell flows to 1 of 8 neighbors (N, NE, E, SE, S, SW, W, NW) based on steepest descent.

**Used In**: River generation, hydraulic erosion

**See**: `src/features/river_generator.py`, `src/features/hydraulic_erosion.py`

---

### Distance Field
**Definition**: Image where each pixel's value is the distance to the nearest "feature" pixel.

**In this project**: Euclidean distance to nearest fault line:
- Calculated using `scipy.ndimage.distance_transform_edt()`
- Units: Meters (converted from pixels)
- Used for: Tectonic uplift falloff, buildability mask

**Example**:
```
Fault:  X . . . .
Result: 0 1 2 3 4  (distance in pixels)
```

**See**: Task 2.1, `src/tectonic_generator.py::calculate_distance_field()`

---

### Domain Warping
**Definition**: Displacing coordinates before sampling noise, creating curved/distorted features.

**Formula**:
```python
warped_x = x + warp_noise_x(x, y) * strength
warped_y = y + warp_noise_y(x, y) * strength
value = base_noise(warped_x, warped_y)
```

**Effect**: Transforms grid-aligned patterns into organic, curved features.

**See**: Stage 1, `src/noise_generator.py::_apply_recursive_domain_warp()`

---

## E

### Exponential Falloff
**Definition**: Rapid decay following exponential function e^(-x).

**Formula**:
```python
elevation = max_uplift * exp(-distance / falloff_meters)
```

**Properties**:
- At distance=0: elevation = max_uplift (full height)
- At distance=falloff_meters: elevation = max_uplift * 0.37 (37% of max)
- At distance=2×falloff_meters: elevation = max_uplift * 0.14 (14% of max)

**Why Exponential**: Natural decay pattern for tectonic forces (not linear, not cliff-like).

**See**: Task 2.1, `src/tectonic_generator.py::apply_uplift_profile()`

---

## F

### FastNoiseLite
**Definition**: C++/Cython noise generation library with vectorized operations.

**Performance**: 60-140× faster than pure Python noise libraries.

**Critical Importance**: Without it, generation takes 60-120s instead of <1s.

**Installation**: `pip install pyfastnoiselite`

**See**: `src/noise_generator.py`

---

### Fault Line
**Definition**: Fracture in Earth's crust where tectonic plates meet/move.

**In this project**: B-spline curves representing geological faults:
- Generate 3-7 random fault lines
- Mountain ranges form along faults (tectonic uplift)
- Distance from faults determines buildability

**See**: Task 2.1, Priority 2

---

### FBM (Fractal Brownian Motion)
**Definition**: Noise algorithm that sums multiple octaves of noise at different frequencies.

**Formula**:
```python
result = 0
amplitude = 1.0
for octave in range(num_octaves):
    result += perlin(x * frequency, y * frequency) * amplitude
    frequency *= lacunarity  # Usually 2.0
    amplitude *= persistence  # Usually 0.5
```

**Parameters**:
- `octaves`: Number of layers (more = more detail)
- `persistence`: Amplitude decay (0.5 = each octave is half strength)
- `lacunarity`: Frequency multiplier (2.0 = each octave is 2× frequency)

**See**: `src/noise_generator.py`

---

### Frequency Discontinuity
**Definition**: Abrupt change in detail/roughness between adjacent regions.

**In Gradient System (FAILED)**:
- Buildable zones: 2 octaves (smooth, low frequency)
- Scenic zones: 7 octaves (detailed, high frequency)
- Boundary: Jarring transition (discontinuity)

**Result**: 6× more jagged terrain, visible "patches"

**Solution**: Single frequency field (same octaves everywhere), vary amplitude only.

**See**: `docs/analysis/BUILDABILITY_FAILURE_ANALYSIS.md`

---

## G

### Gaussian Blur
**Definition**: Smoothing operation using Gaussian (bell curve) kernel.

**Formula**: Convolve image with Gaussian kernel:
```python
G(x,y) = (1 / 2πσ²) * exp(-(x² + y²) / 2σ²)
```

**Parameter sigma (σ)**: Standard deviation, controls blur strength
- Small sigma (8): Light blur, narrow kernel
- Large sigma (20): Strong blur, wide kernel
- 99.7% of blur within ±3σ pixels

**Used In**: Priority 6 enforcement, ridge continuity enhancement

**See**: `src/buildability_enforcer.py`, `scipy.ndimage.gaussian_filter`

---

### Gradient (Image)
**Definition**: Rate of change of pixel values (how quickly height changes).

**Calculation**:
```python
dy, dx = np.gradient(heightmap)  # Sobel-like operators
gradient_magnitude = np.sqrt(dx² + dy²)
```

**High Gradient**: Steep slopes, rapid elevation change
**Low Gradient**: Gentle slopes, gradual elevation change

**Gradient Amplification**: When normalization stretches heightmap, multiplies all gradients.

**See**: Slope Calculation, Smart Normalization

---

### Gradient Control Map (FAILED SYSTEM)
**Definition**: Continuous [0.0-1.0] mask used to blend multiple terrain layers.

**Method**:
```python
terrain = buildable_layer * mask² + moderate_layer * 2*mask*(1-mask) + scenic_layer * (1-mask)²
```

**Why It Failed**:
- Blended 2-octave, 5-octave, 7-octave noise
- Created frequency discontinuities at boundaries
- Result: 3.4% buildable, 6× more jagged than reference

**Replaced By**: Binary mask + amplitude modulation (18.5% buildable)

**See**: `docs/analysis/BUILDABILITY_FAILURE_ANALYSIS.md`

---

## H

### Heightmap
**Definition**: Grayscale image where pixel brightness represents terrain elevation.

**Format**:
- **Internal**: Float64 array, normalized [0.0, 1.0]
- **Export**: 16-bit PNG, range [0, 65535]
- **In CS2**: Height 0-4096m (default, customizable)

**Conversion**:
```python
# Internal → Export
png_value = heightmap_float * 65535

# Export → CS2 meters
meters = (png_value / 65535) * 4096
```

---

### Hydraulic Erosion
**Definition**: Simulation of water erosion carving valleys and depositing sediment.

**Algorithm**: Pipe Model (Mei et al. 2007)
- Virtual pipes between adjacent cells
- Water flows based on pressure differences
- Sediment carried proportional to water velocity
- Deposition when velocity decreases

**Performance**: 40-45s for 100 iterations at 4096×4096 (with Numba JIT)

**See**: Stage 1, `src/features/hydraulic_erosion.py`

---

## M

### Map Size (Meters)
**Definition**: Physical size of terrain in real-world units.

**CS2 Default**: 14,336 meters × 14,336 meters (14.3 km²)

**Pixel Spacing**: map_size / resolution = 14336m / 4096 pixels = **3.5 meters/pixel**

**Critical For**: Slope calculations (missing this division caused 1170× error in GUI)

---

## N

### Normalization
**Definition**: Transforming data to a standard range (typically [0, 1]).

**Stretching Normalization** (can amplify gradients):
```python
normalized = (data - data.min()) / (data.max() - data.min())
```

**Clipping Normalization** (preserves gradients):
```python
normalized = np.clip(data, 0.0, 1.0)
```

**See**: Smart Normalization

---

### Numba
**Definition**: Just-In-Time (JIT) compiler for Python using LLVM.

**Performance**: 5-8× speedup for tight loops (hydraulic erosion).

**Usage**:
```python
from numba import jit

@jit(nopython=True, cache=True)
def fast_function(data):
    # Python code compiled to machine code
```

**See**: `src/features/hydraulic_erosion.py`

---

## O

### Octave (Noise)
**Definition**: Layer of noise at a specific frequency in fractal generation.

**In FBM**:
- Octave 0: Low frequency (large features)
- Octave 1: 2× frequency (medium features)
- Octave 2: 4× frequency (small features)
- ...
- Octave 5: 32× frequency (fine details)

**Total octaves = Total detail level**

**Critical in this project**: SAME octaves everywhere (prevents discontinuities).

**See**: FBM, Frequency Discontinuity

---

## P

### Perlin Noise
**Definition**: Gradient noise algorithm by Ken Perlin (1983), creates smooth random patterns.

**Properties**:
- Continuous (smooth transitions)
- Repeatable (same seed → same pattern)
- Organic looking (not grid-aligned)

**Used For**: Base terrain generation

**See**: `src/noise_generator.py::generate_perlin()`

---

### Pixel Spacing
**Definition**: Real-world distance represented by one pixel.

**Calculation**:
```python
pixel_spacing = map_size_meters / resolution
```

**For CS2**:
```python
pixel_spacing = 14336m / 4096 pixels = 3.5 meters/pixel
```

**Critical Importance**: Required for slope calculations (missing = 1170× error).

**See**: Slope Calculation, Map Size

---

### Priority 2
**Definition**: Project phase for tectonic structure and buildability implementation.

**Tasks**:
- **Task 2.1**: Tectonic fault line generation
- **Task 2.2**: Binary buildability mask
- **Task 2.3**: Amplitude modulated terrain

**Status**: COMPLETE (2025-10-08)

**See**: `docs/analysis/map_gen_enhancement.md`

---

### Priority 6
**Definition**: Project phase for buildability enforcement (smart blur post-processing).

**Method**: Iterative gaussian smoothing in buildable zones only.

**Result**: +0.6% improvement (17.9% → 18.5%) in best case.

**Limitation**: Cannot fix fundamentally steep generation.

**Status**: COMPLETE (2025-10-08)

**See**: `src/buildability_enforcer.py::enforce_buildability_constraint()`

---

## S

### Slope (Terrain)
**Definition**: Steepness of terrain, measured as percentage (rise/run × 100).

**Calculation**:
```python
# Convert to meters
heightmap_meters = heightmap * height_scale  # height_scale = 4096m

# Calculate gradients (Sobel-like)
dy, dx = np.gradient(heightmap_meters)

# Slope ratio = rise / run
slope_ratio = sqrt(dx² + dy²) / pixel_spacing  # pixel_spacing = 3.5m

# Convert to percentage
slope_percentage = slope_ratio * 100
```

**CS2 Standard**: 0-5% slopes are buildable

**Examples**:
- 0% = Perfectly flat
- 5% = 2.86° angle (CS2 buildable limit)
- 27.8% = 15.5° angle (Test 3 mean in buildable zones - too steep)
- 100% = 45° angle (very steep)

**See**: `src/buildability_enforcer.py::calculate_slopes()`

---

### Smart Normalization
**Definition**: Conditional normalization that clips if range is acceptable, stretches only if needed.

**Algorithm**:
```python
if combined_min >= -0.1 and combined_max <= 1.1:
    # Range acceptable, clip (no gradient amplification)
    final_terrain = np.clip(combined, 0.0, 1.0)
else:
    # Range too wide, stretch to [0, 1]
    final_terrain = (combined - combined_min) / (combined_max - combined_min)
```

**Critical Innovation**: Prevents gradient amplification when parameters are low.

**Impact**: 35× improvement (0.5% → 17.9% buildable)

**See**: `src/tectonic_generator.py` lines 719-742

---

### Sobel Operator
**Definition**: Discrete differentiation operator for edge detection/gradient calculation.

**In NumPy**: `np.gradient()` uses centered differences (similar to Sobel)

**Used For**: Calculating terrain slopes (how quickly elevation changes)

**See**: Slope Calculation, Gradient

---

## T

### Tectonic Structure
**Definition**: Geological framework based on tectonic fault lines and uplift.

**In this project**:
1. Generate fault lines (B-spline curves)
2. Calculate distance to faults
3. Apply exponential elevation uplift
4. Result: Mountain ranges along faults, valleys/plains between

**Why**: Geological realism (real mountains follow faults, not random noise).

**See**: Task 2.1, Priority 2

---

### Threshold (Binary Mask)
**Definition**: Value used to separate two categories (buildable vs scenic).

**In Task 2.2**:
- Distance threshold: e.g., 1913m (far from faults = buildable)
- Elevation threshold: e.g., 0.15 (low elevation = buildable)
- Logic: `buildable = (distance > dist_thresh) OR (elevation < elev_thresh)`

**Iterative Adjustment**: Thresholds adjusted until X% of terrain is buildable.

**See**: `src/buildability_enforcer.py::generate_buildability_mask_from_tectonics()`

---

## U

### Uplift (Tectonic)
**Definition**: Elevation of Earth's crust due to tectonic forces.

**In this project**: Exponential elevation falloff from fault lines:
```python
elevation = max_uplift * exp(-distance / falloff_meters)
```

**max_uplift**: Maximum height at fault (0.2 = 819m)
**falloff_meters**: Distance decay rate (600m default)

**Result**: Mountains along faults, gradual descent to valleys.

**See**: Task 2.1, Exponential Falloff

---

## Common Calculations Reference

### Slope Percentage Calculation (CRITICAL)
```python
# CS2 Constants
resolution = 4096 pixels
map_size_meters = 14336.0 meters
height_scale = 4096.0 meters
pixel_spacing = map_size_meters / resolution = 3.5 meters/pixel

# Heightmap (normalized [0, 1])
heightmap = <terrain data>

# Convert to meters
heightmap_meters = heightmap * height_scale  # Now in range [0, 4096m]

# Calculate gradients (elevation change per pixel)
dy, dx = np.gradient(heightmap_meters)  # Units: meters

# Slope ratio (rise over run)
slope_ratio = np.sqrt(dx² + dy²) / pixel_spacing  # Dimensionless (m/m)

# Convert to percentage
slope_percentage = slope_ratio * 100.0  # Units: %

# Buildable mask
buildable = slope_percentage <= 5.0  # CS2 standard
```

**Common Mistake**: Forgetting `/ pixel_spacing` (GUI bug caused 1170× error)

---

### Amplitude to Height Conversion
```python
# Amplitude (normalized space)
amplitude = 0.05

# Noise range (centered around 0)
noise_range = [-1, 1]

# Maximum variation
max_variation = amplitude * 1.0 = 0.05

# In meters
meters_variation = 0.05 * 4096m = 205 meters

# Slope created (if over 3.5m pixel)
slope_ratio = 205m / 3.5m = 58.6 m/m
slope_percentage = 5860%  # (unrealistic, actual is distributed)

# Distributed over 10 pixels (realistic)
slope_ratio = 205m / 35m = 5.86 m/m
slope_percentage = 586%  # Still way above 5% target
```

**This explains why 0.05 amplitude creates 27.8% mean slopes.**

---

### Smart Normalization Threshold Check
```python
# Combined terrain (tectonic + noise)
combined = tectonic_elevation + modulated_noise

# Calculate range
combined_min = combined.min()
combined_max = combined.max()

# Check if within acceptable range
if combined_min >= -0.1 and combined_max <= 1.1:
    # CLIP (no gradient amplification)
    final_terrain = np.clip(combined, 0.0, 1.0)
    print("[SMART NORM] Range acceptable, using clip")
else:
    # STRETCH (gradient amplification)
    combined_range = combined_max - combined_min
    final_terrain = (combined - combined_min) / combined_range
    print(f"[SMART NORM] Range [{combined_min:.3f}, {combined_max:.3f}], stretching")
    print(f"[SMART NORM] Gradient amplification factor: {1.0 / combined_range:.2f}×")
```

---

## Glossary Version

**Version**: 1.0
**Last Updated**: 2025-10-08
**Maintainer**: CS2 Map Generator Project
