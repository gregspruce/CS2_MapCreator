# Parameter Reference Guide

**Date**: 2025-10-08
**Purpose**: Complete reference for all terrain generation parameters

---

## 1. Tectonic Structure Parameters (Task 2.1)

### `num_fault_lines` (Integer: 3-7)

**What**: Number of tectonic fault lines to generate
**Default**: 5
**Range**: 3-7
**Effect**: More faults = more complex mountain ranges
**GUI Control**: "Fault Lines" slider

**Values**:
- 3: Simple terrain with single mountain range
- 5: Balanced terrain with moderate complexity (DEFAULT)
- 7: Complex terrain with multiple intersecting ranges

**Location**: `src/tectonic_generator.py::generate_fault_lines()`

---

###max_uplift` (Float: 0.15-0.6)

**What**: Maximum tectonic elevation uplift along fault lines
**Default**: 0.2 **[BEST VALUE FOR 18.5% BUILDABLE]**
**Range**: 0.15-0.6
**Effect**: Controls mountain height and steepness
**GUI Control**: "Mountain Height" slider

**Values**:
- 0.15: Ultra-gentle mountains, very buildable
- 0.2: Gentle mountains, best buildability (18.5%) **[RECOMMENDED]**
- 0.4: Moderate mountains, lower buildability (~10-15%)
- 0.6: Extreme mountains, very low buildability (~5-10%)
- 0.8: Catastrophic (tested), unusable (<3%)

**Physical Meaning**:
- Value in normalized [0, 1] heightmap space
- 0.2 = 819m elevation (0.2 × 4096m)
- 0.6 = 2458m elevation (0.6 × 4096m)

**Critical Finding**: Lower is better for buildability
- max_uplift=0.2 → 18.5% buildable
- max_uplift=0.8 → 0.5% buildable

**Location**: `src/tectonic_generator.py::apply_uplift_profile()`

---

### `falloff_meters` (Float: 300-1000m)

**What**: Distance over which tectonic elevation decays from fault
**Default**: 600m
**Range**: 300-1000m
**Effect**: Controls mountain width and slope steepness
**GUI Control**: "Falloff Distance" slider

**Values**:
- 300m: Narrow, steep mountains
- 600m: Moderate width mountains (DEFAULT)
- 1000m: Wide, gradual mountains

**Mathematical Formula**:
```python
elevation = max_uplift * exp(-distance_field / falloff_meters)
```

**At max_uplift=0.2, falloff=600m**:
- 0m from fault: 0.2 elevation (full uplift)
- 600m from fault: 0.2 × e^-1 = 0.074 elevation (37% of max)
- 1200m from fault: 0.2 × e^-2 = 0.027 elevation (14% of max)
- 1800m from fault: 0.2 × e^-3 = 0.010 elevation (5% of max)

**Location**: `src/tectonic_generator.py::apply_uplift_profile()`

---

## 2. Amplitude Modulation Parameters (Task 2.3)

### `buildable_amplitude` (Float: 0.01-0.2)

**What**: Noise amplitude multiplier in buildable zones
**Default**: 0.05 **[BEST VALUE FOR 18.5% BUILDABLE]**
**Range**: 0.01-0.2
**Effect**: Controls terrain detail/roughness in flat areas
**GUI Control**: "Buildable Zones" slider

**Values**:
- 0.01: Minimal texture (smoothest, highest buildability)
- 0.05: Gentle texture, best buildability (18.5%) **[RECOMMENDED]**
- 0.1: Moderate texture, lower buildability
- 0.2: High texture, very low buildability

**Physical Meaning**:
- Value in normalized [0, 1] heightmap space
- Noise field is [-1, 1], so amplitude is the multiplier
- 0.05 amplitude × max noise 1.0 = ±0.05 variation
- 0.05 × 4096m = ±205m elevation variation
- 205m over 3.5m pixel = 58m/m slope ratio = 5800% slope (unrealistic)
- **This is why even 0.05 creates steep slopes**

**Critical Finding**: Lower is better for buildability
- 0.05 amplitude → 18.5% buildable
- 0.3 amplitude → 0.5% buildable

**Location**: `src/tectonic_generator.py::generate_amplitude_modulated_terrain()`

---

### `scenic_amplitude` (Float: 0.1-1.0)

**What**: Noise amplitude multiplier in scenic (mountain) zones
**Default**: 0.2 **[BEST VALUE FOR 18.5% BUILDABLE]**
**Range**: 0.1-1.0
**Effect**: Controls mountain detail and visual drama
**GUI Control**: "Scenic Zones" slider

**Values**:
- 0.1: Gentle mountains, less visual interest
- 0.2: Moderate mountains, good balance (DEFAULT) **[RECOMMENDED]**
- 0.5: Dramatic mountains, high visual interest
- 1.0: Extreme detail, maximum drama

**Physical Meaning**:
- 0.2 amplitude × max noise 1.0 = ±0.2 variation
- 0.2 × 4096m = ±819m elevation variation
- Creates visually interesting mountains without extreme slopes

**Design Philosophy**:
- Buildable zones: Minimize amplitude (flatten for building)
- Scenic zones: Moderate amplitude (visual interest without chaos)
- **Ratio matters**: scenic/buildable = 0.2/0.05 = 4× more detail in mountains

**Location**: `src/tectonic_generator.py::generate_amplitude_modulated_terrain()`

---

### `noise_octaves` (Integer: 4-8)

**What**: Number of octaves in Perlin noise generation
**Default**: 6 **[SINGLE FREQUENCY FIELD - DO NOT CHANGE]**
**Range**: 4-8 (advanced users only)
**Effect**: Controls terrain detail frequency
**GUI Control**: NOT EXPOSED (advanced parameter)

**Critical Design Decision**: Same octaves everywhere
- Buildable zones: 6 octaves
- Scenic zones: 6 octaves
- **Only amplitude varies, not octaves**
- **This prevents frequency discontinuities** (fatal flaw of gradient system)

**Why 6 Octaves**:
- 1-2 octaves: Too smooth, lacks detail
- 3-4 octaves: Moderate detail, balanced
- 6 octaves: Good detail, not excessive (DEFAULT)
- 8+ octaves: High detail, may create noise

**Location**: `src/tectonic_generator.py::generate_amplitude_modulated_terrain()`

---

## 3. Priority 6 Enforcement Parameters

### `enforcement_iterations` (Integer: 0-20)

**What**: Number of smoothing passes in buildable zones
**Default**: 10
**Range**: 0-20
**Effect**: More iterations = more smoothing = higher buildability (up to limits)
**GUI Control**: "Iterations" slider

**Values**:
- 0: No enforcement (use raw terrain)
- 5: Light smoothing, minimal effect
- 10: Moderate smoothing (DEFAULT)
- 15: Aggressive smoothing
- 20: Maximum smoothing

**Test Results**:
- Test 3: 10 iterations → +0.6% improvement (17.9% → 18.5%)
- Test 6: 20 iterations → -2.8% decline (15.6% → 12.8%)
- **More is NOT always better** (paradoxical decline observed)

**Why Diminishing Returns**:
- Smooths not just slopes, but also terrain features
- Can blur boundaries between zones
- May create unintended artifacts

**Location**: `src/buildability_enforcer.py::enforce_buildability_constraint()`

---

### `enforcement_sigma` (Float: 8-20)

**What**: Gaussian blur radius (strength) for smoothing
**Default**: 12.0
**Range**: 8-20
**Effect**: Larger sigma = stronger smoothing = more aggressive flattening
**GUI Control**: "Strength (sigma)" slider

**Values**:
- 8: Light blur, subtle smoothing
- 12: Moderate blur (DEFAULT)
- 16: Strong blur, aggressive smoothing
- 20: Maximum blur, very aggressive

**Mathematical Meaning**:
- Sigma is the standard deviation of Gaussian kernel
- Larger sigma = wider blur radius = more pixels affected
- sigma=12 means ~99.7% of blur within ±36 pixels (3σ)

**Test Results**:
- Test 3: sigma=12 → 18.5% buildable
- Test 6: sigma=20 → 12.8% buildable (declined)
- **Stronger is NOT always better**

**Location**: `src/buildability_enforcer.py::enforce_buildability_constraint()`

---

### `tolerance` (Float: 1-10%)

**What**: Acceptable deviation from buildability target before stopping
**Default**: 5.0%
**Range**: 1-10%
**Effect**: Tighter tolerance = more iterations = slower convergence
**GUI Control**: NOT EXPOSED (advanced parameter)

**Values**:
- 1%: Very tight, may never converge
- 5%: Balanced (DEFAULT)
- 10%: Loose, fast convergence

**Example**:
- Target: 50% buildable
- Tolerance: 5%
- Accept: 45-55% buildable range
- Stop when: Current buildability within 45-55%

**Location**: `src/buildability_enforcer.py::enforce_buildability_constraint()`

---

## 4. Map Physical Constants

### `map_size_meters` (Float: Fixed at 14336m)

**What**: Physical size of CS2 map in meters
**Value**: 14,336 meters (FIXED BY CS2)
**Effect**: Determines pixel spacing and slope calculations
**GUI Control**: NOT EXPOSED (CS2 requirement)

**Critical Calculations**:
```python
resolution = 4096 pixels
map_size_meters = 14336 meters
pixel_size_meters = map_size_meters / resolution = 3.5 meters/pixel
```

**Why This Matters**:
- Slope calculation REQUIRES pixel spacing
- Bug that was fixed: GUI was missing this division (1170× error)
- Every slope calculation must use: `gradient * height_scale / pixel_size_meters`

**Location**: Used in `src/buildability_enforcer.py` and `src/analysis/terrain_analyzer.py`

---

### `height_scale` (Float: Fixed at 4096m)

**What**: Maximum height of terrain in CS2
**Value**: 4096 meters (CS2 default, customizable in-game)
**Effect**: Converts normalized heightmap [0, 1] to meters [0, 4096m]
**GUI Control**: NOT EXPOSED (CS2 game setting)

**Conversion**:
```python
# Heightmap is normalized [0, 1]
heightmap_normalized = 0.5  # Example value

# Convert to meters
heightmap_meters = heightmap_normalized * 4096 = 2048 meters

# Convert to 16-bit PNG for CS2
png_value = heightmap_normalized * 65535 = 32768 (uint16)
```

**Location**: Used throughout codebase for slope calculations and export

---

## 5. Erosion Parameters (Optional Feature)

### `erosion_enabled` (Boolean: True/False)

**What**: Enable hydraulic erosion simulation
**Default**: False (disabled)
**Effect**: Adds dendritic drainage patterns and valley carving
**GUI Control**: "Enable Erosion" checkbox

**Impact**:
- Time: +40-45s for 100 iterations
- Quality: Adds geological realism
- Buildability: May reduce slightly (creates valleys)

**Location**: `src/features/hydraulic_erosion.py`

---

### `erosion_quality` (String: 'fast'/'balanced'/'maximum')

**What**: Erosion iteration count preset
**Default**: 'balanced' (50 iterations)
**Effect**: More iterations = more erosion effect
**GUI Control**: "Erosion Quality" dropdown

**Values**:
- 'fast': 25 iterations (~12-15s overhead)
- 'balanced': 50 iterations (~40-45s overhead) (DEFAULT)
- 'maximum': 100 iterations (~90-100s overhead)

**Location**: `src/features/hydraulic_erosion.py`

---

### `erosion_rate`, `deposition_rate`, `evaporation_rate`, `sediment_capacity`

**Advanced Parameters** (exposed in GUI for fine-tuning)
- `erosion_rate`: 0.1-0.5 (default: 0.2) - Valley carving strength
- `deposition_rate`: 0.01-0.15 (default: 0.08) - Sediment smoothing
- `evaporation_rate`: 0.005-0.03 (default: 0.015) - Water loss control
- `sediment_capacity`: 1.0-6.0 (default: 3.0) - Max sediment transport

**Location**: `src/features/hydraulic_erosion.py`

---

## 6. Best Parameter Combinations

### Recommended: Maximum Buildability (Test 3)

```python
# Tectonic Structure
num_fault_lines = 5
max_uplift = 0.2              # Gentle mountains
falloff_meters = 600.0        # Moderate falloff

# Amplitude Modulation
buildable_amplitude = 0.05    # Minimal noise in buildable
scenic_amplitude = 0.2        # Moderate visual interest

# Priority 6 Enforcement
enforcement_iterations = 10   # Standard smoothing
enforcement_sigma = 12.0      # Moderate blur
tolerance = 5.0

# Result: 18.5% buildable (best achieved)
```

### Alternative: Ultra-Gentle (Untested)

```python
# Tectonic Structure
num_fault_lines = 3           # Simpler terrain
max_uplift = 0.15             # Very gentle mountains
falloff_meters = 900.0        # Wide, gradual slopes

# Amplitude Modulation
buildable_amplitude = 0.01    # Absolute minimum noise
scenic_amplitude = 0.15       # Gentle mountains

# Priority 6 Enforcement
enforcement_iterations = 15   # More aggressive
enforcement_sigma = 14.0      # Stronger blur

# Expected: 20-25% buildable (hypothesis)
```

### Dramatic Scenic (Lower Buildability)

```python
# Tectonic Structure
num_fault_lines = 7           # Complex mountain ranges
max_uplift = 0.4              # Tall mountains
falloff_meters = 400.0        # Steep slopes

# Amplitude Modulation
buildable_amplitude = 0.1     # More texture everywhere
scenic_amplitude = 0.5        # Dramatic peaks

# Priority 6 Enforcement
enforcement_iterations = 10   # Standard
enforcement_sigma = 12.0      # Moderate

# Expected: 10-15% buildable, very scenic
```

---

## 7. Parameter Interactions

### Critical Interaction: max_uplift × buildable_amplitude

**Observation**: These multiply together in effect on slopes

**Example**:
- max_uplift=0.2, buildable_amp=0.05:
  - Tectonic base: 0.2 (819m)
  - Noise adds: ±0.05 (±205m)
  - Combined: 0.15-0.25 range
  - If normalized: 0.0-1.0 (stretched 1.67×)
  - **But smart norm clips instead → no amplification**

- max_uplift=0.8, buildable_amp=0.3:
  - Tectonic base: 0.8 (3277m)
  - Noise adds: ±0.3 (±1229m)
  - Combined: 0.5-1.1 range
  - Normalized: 0.0-1.0 (stretched 1.67×)
  - **Gradient amplification → catastrophic failure**

**Lesson**: Keep BOTH low for buildability

---

### Critical Interaction: Smart Normalization Threshold

**When Clipping Happens**:
```python
if combined_min >= -0.1 and combined_max <= 1.1:
    # CLIP (no gradient amplification)
    final_terrain = np.clip(combined, 0.0, 1.0)
else:
    # STRETCH (gradient amplification)
    final_terrain = (combined - combined_min) / combined_range
```

**How to Stay Within Threshold**:
- Keep max_uplift ≤ 0.2
- Keep buildable_amplitude ≤ 0.05
- Keep scenic_amplitude ≤ 0.2
- Result: combined typically in [-0.05, 0.4] range
- Falls within [-0.1, 1.1] → clipping → no amplification

**Why This Matters**:
- Test 1-2: Exceeded threshold → stretched → 0.5% buildable (FAIL)
- Test 3: Within threshold → clipped → 17.9% buildable (SUCCESS)
- **35× difference from this alone**

---

## 8. Common Pitfalls

### Pitfall 1: "More iterations will fix it"

**Wrong**: Increasing enforcement_iterations from 10 → 20
**Result**: May DECLINE buildability (Test 6: 15.6% → 12.8%)
**Why**: Over-smoothing blurs zone boundaries and features

**Right**: Keep iterations moderate (10), focus on amplitude parameters

---

### Pitfall 2: "Stronger blur will flatten terrain"

**Wrong**: Increasing enforcement_sigma from 12 → 20
**Result**: May DECLINE buildability (Test 6: 15.6% → 12.8%)
**Why**: Blur affects entire terrain, not just slopes

**Right**: Use moderate sigma (12), accept Priority 6 limits

---

### Pitfall 3: "I can use higher amplitudes and fix with Priority 6"

**Wrong**: buildable_amplitude=0.3 + aggressive Priority 6
**Result**: 0.5% buildable even with enforcement (Test 1-2)
**Why**: Priority 6 cannot fix fundamentally steep generation

**Right**: Use LOW amplitudes from the start (0.05)

---

### Pitfall 4: "Normalization doesn't matter"

**Wrong**: Ignoring normalized range of combined terrain
**Result**: Catastrophic gradient amplification if stretched
**Why**: Stretching [0, 0.4] → [0, 1] multiplies all slopes by 2.5×

**Right**: Keep parameters within [-0.1, 1.1] range to trigger clipping

---

## 9. Parameter Validation Rules

### Required Invariants

```python
# Tectonic
assert 3 <= num_fault_lines <= 7
assert 0.15 <= max_uplift <= 0.6
assert 300 <= falloff_meters <= 1000

# Amplitude
assert 0.01 <= buildable_amplitude <= 0.2
assert 0.1 <= scenic_amplitude <= 1.0
assert buildable_amplitude < scenic_amplitude  # Buildable must be less detailed

# Enforcement
assert 0 <= enforcement_iterations <= 20
assert 8.0 <= enforcement_sigma <= 20.0
assert 1.0 <= tolerance <= 10.0

# Physical Constants (CS2 requirements)
assert map_size_meters == 14336.0
assert resolution == 4096
assert height_scale == 4096.0
```

### Recommended Relationships

```python
# For maximum buildability:
max_uplift <= 0.2
buildable_amplitude <= 0.05
scenic_amplitude <= 0.2

# Scenic/buildable ratio should be > 2×
scenic_amplitude / buildable_amplitude >= 2.0

# Combined range should stay within smart norm threshold
max_uplift + scenic_amplitude <= 1.1  # Approximate upper bound
```

---

## Conclusion

Parameters are **highly interdependent**. The current best combination (Test 3) was discovered through systematic testing, not intuition.

**Key Learnings**:
1. **Lower is better** for buildability (uplift, amplitudes)
2. **Smart normalization** is critical (keep within [-0.1, 1.1])
3. **Priority 6 has limits** (cannot fix steep generation)
4. **More smoothing ≠ better** (diminishing/negative returns)

**For Deep Research**: Explore if alternative parameter combinations can achieve 25-30% buildable without redesign.

---

**Document Version**: 1.0
**Last Updated**: 2025-10-08
**Maintainer**: CS2 Map Generator Project
