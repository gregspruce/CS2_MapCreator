# Water Features Performance Bottleneck Analysis

**Date**: 2025-10-05
**Version**: v2.4.0
**Status**: CRITICAL PERFORMANCE ISSUES IDENTIFIED

---

## Executive Summary

Water generation tools (rivers, lakes, coastal) still hang or are unusably slow despite downsampling implementation in v2.4.0.

**Root Cause**: Downsampling exists for rivers but **is never activated by the GUI**. Lakes and coastal generators have **NO downsampling implementation at all** and run O(n²) algorithms on full 4096×4096 data.

---

## Issue 1: River Generator - Downsampling Implemented but NOT USED

### Downsampling Code EXISTS

**File**: `src/features/river_generator.py`
**Lines**: 48-79

```python
def __init__(self, heightmap: np.ndarray, downsample: bool = True, target_size: int = 1024):
    """
    Initialize river generator with a heightmap.

    Args:
        downsample: Enable downsampling for performance (default True)
        target_size: Target resolution for downsampling (default 1024)
    """
    # Downsample if enabled and needed
    if downsample and heightmap.shape[0] > target_size:
        from .performance_utils import downsample_heightmap
        self.heightmap, self.scale_factor = downsample_heightmap(heightmap, target_size)
        self.downsampled = True
        print(f"[RIVER] Using downsampled heightmap for {self.scale_factor:.1f}× speedup")
    else:
        self.heightmap = heightmap.copy()
        self.scale_factor = 1.0
        self.downsampled = False
```

### GUI NEVER Activates Downsampling

**File**: `src/gui/heightmap_gui.py`
**Problem Location 1**: Line 417 (AddRiverCommand)

```python
# This is INSIDE AddRiverCommand.execute()
river_gen = RiverGenerator(self.generator.heightmap)
# ❌ MISSING: downsample=True parameter!
```

**Problem Location 2**: Lines 852-857 (GUI's add_rivers method)

```python
command = AddRiverCommand(
    self.generator,
    num_rivers=num_rivers,
    threshold=500,
    description=f"Add {num_rivers} rivers"
)
# ❌ AddRiverCommand doesn't accept or pass downsample parameter
```

### Performance Impact

**Without Downsampling** (current behavior):
- `calculate_flow_direction()`: Triple nested loop on 4096×4096
  - Line 99-124: `for y in range(self.height): for x in range(self.width): for dir_idx, (dy, dx) in enumerate(DIRECTIONS):`
  - **134 million iterations** (4096 × 4096 × 8)
  - Estimated time: **30+ minutes**

**With Downsampling** (if activated):
- Same algorithm on 1024×1024
  - **8.4 million iterations** (1024 × 1024 × 8)
  - Estimated time: **~30 seconds**
  - **Speedup: 16×**

---

## Issue 2: Lake Generator - NO DOWNSAMPLING AT ALL

### No Downsampling Implementation

**File**: `src/features/water_body_generator.py`
**Lines**: 36-46

```python
def __init__(self, heightmap: np.ndarray):
    """
    Initialize water body generator with heightmap.

    Note: Heightmap is NOT modified by this class.
    """
    self.heightmap = heightmap.copy()  # ❌ Always copies FULL 4096×4096 (67MB!)
    self.height, self.width = heightmap.shape
    # ❌ NO downsample parameter
    # ❌ NO performance_utils import
    # ❌ NO downsampling logic
```

### Critical Performance Bottlenecks

**Bottleneck 1**: `_estimate_basin_size()` - Lines 145-179
```python
def _estimate_basin_size(self, y: int, x: int, rim_height: float) -> int:
    visited = set()
    to_visit = [(y, x)]
    count = 0

    while to_visit and count < 10000:  # ❌ Flood fill on FULL resolution
        cy, cx = to_visit.pop()
        # ... flood fill logic
        for dy, dx in [(-1,0), (1,0), (0,-1), (0,1)]:
            to_visit.append((cy + dy, cx + dx))
    return count
```
- Called for EVERY depression detected
- Flood fill can visit 10,000 cells PER depression
- On 4096×4096, this is **CATASTROPHICALLY SLOW**

**Bottleneck 2**: `_find_rim_height()` - Lines 117-143
```python
def _find_rim_height(self, y: int, x: int, min_height: float) -> float:
    max_search_radius = min(self.height, self.width) // 4  # ❌ = 1024 on 4096 map!

    for radius in range(1, max_search_radius):  # ❌ Up to 1024 iterations
        for angle in range(0, 360, 15):  # 24 angles per radius
            rad = np.radians(angle)
            dy = int(radius * np.sin(rad))
            dx = int(radius * np.cos(rad))
            # Sample at (y+dy, x+dx)
```
- Called for EVERY depression
- Up to **1024 radius × 24 angles = 24,576 samples** per depression
- On large maps: **EXTREME slowdown**

**Bottleneck 3**: `create_lake()` - Lines 214-248
```python
def create_lake(self, heightmap, center_y, center_x, ...):
    visited = set()
    to_visit = [(center_y, center_x)]

    while to_visit:  # ❌ Unbounded flood fill on FULL resolution
        y, x = to_visit.pop()
        # ... no iteration limit!
        for dy, dx in [(-1,0), (1,0), (0,-1), (0,1), (-1,-1), (-1,1), (1,-1), (1,1)]:
            to_visit.append((y + dy, x + dx))
```
- **NO iteration limit** (unlike `_estimate_basin_size`)
- Can flood fill entire map if rim detection fails
- On 4096×4096: **Potentially 16.7 million iterations**

### GUI Call

**File**: `src/gui/heightmap_gui.py`
**Line**: 336 (inside AddLakeCommand.execute())

```python
water_gen = WaterBodyGenerator(self.generator.heightmap)
# ❌ NO downsampling support in WaterBodyGenerator at all
```

---

## Issue 3: Coastal Generator - NO DOWNSAMPLING AT ALL

### No Downsampling Implementation

**File**: `src/features/coastal_generator.py`
**Lines**: 40-52

```python
def __init__(self, heightmap: np.ndarray, water_level: float = 0.0):
    """
    Initialize coastal generator.

    Note: Heightmap is NOT modified by this class.
    """
    self.heightmap = heightmap.copy()  # ❌ Always copies FULL 4096×4096 (67MB!)
    self.water_level = water_level
    self.height, self.width = heightmap.shape
    # ❌ NO downsample parameter
    # ❌ NO performance_utils import
    # ❌ NO downsampling logic
```

### Critical Performance Bottlenecks

**Bottleneck 1**: `add_beaches()` - Lines 157-174
```python
def add_beaches(self, heightmap, intensity=0.5, width=10):
    # ... detect coastline and slopes (fast, uses ndimage)

    # ❌ DOUBLE NESTED LOOP on FULL heightmap
    for y in range(self.height):        # 4096 iterations
        for x in range(self.width):     # 4096 iterations
            if beach_zone[y, x]:
                distance_from_coast = self._distance_to_coastline(y, x, coastline)
                # ... flatten terrain
```
- **16.7 million iterations** on 4096×4096
- Calls `_distance_to_coastline()` for every beach cell
- Estimated time: **10+ minutes**

**Bottleneck 2**: `add_cliffs()` - Lines 215-233
```python
def add_cliffs(self, heightmap, intensity=0.5, min_height=0.05):
    # ... detect coastline and slopes (fast)

    # ❌ DOUBLE NESTED LOOP on FULL heightmap
    for y in range(self.height):        # 4096 iterations
        for x in range(self.width):     # 4096 iterations
            if is_cliff[y, x]:
                # ... steepen cliffs
                for dy, dx in [(-1,0), (1,0), (0,-1), (0,1)]:
                    # ... modify neighbors
```
- **16.7 million iterations** on 4096×4096
- Additional inner loop for neighbor modification
- Estimated time: **5+ minutes**

**Bottleneck 3**: `_distance_to_coastline()` - Lines 248-262
```python
def _distance_to_coastline(self, y: int, x: int, coastline: np.ndarray) -> float:
    max_search = 20

    for radius in range(max_search):  # Up to 20 radii
        for angle in range(0, 360, 30):  # 12 angles per radius
            rad = np.radians(angle)
            dy = int(radius * np.sin(rad))
            dx = int(radius * np.cos(rad))
            # Sample at (ny, nx)
```
- Called for **EVERY beach cell** (potentially millions on large maps)
- Up to **240 samples per cell** (20 × 12)
- On coastline-heavy maps: **CATASTROPHIC slowdown**

### GUI Call

**File**: `src/gui/heightmap_gui.py`
**Line**: 377 (inside AddCoastalFeaturesCommand.execute())

```python
coastal_gen = CoastalGenerator(self.generator.heightmap, self.water_level)
# ❌ NO downsampling support in CoastalGenerator at all
```

---

## Performance Comparison Table

| Generator | Has Downsampling Code | GUI Activates It | O(n²) Loops on Full Data | Estimated Time (4096²) |
|-----------|----------------------|------------------|-------------------------|------------------------|
| **Rivers** | ✅ YES (lines 48-79) | ❌ NO (line 417) | ❌ NO (but not used) | ~30min (current) |
| **Lakes** | ❌ NO | ❌ N/A | ✅ YES (lines 145-179, 214-248) | ~20-30min |
| **Coastal** | ❌ NO | ❌ N/A | ✅ YES (lines 157-174, 215-233) | ~15-20min |

---

## Evidence: Specific Line Numbers

### Rivers - Downsampling exists but unused
- **Implementation**: `src/features/river_generator.py:48-79`
- **Upsample logic**: `src/features/river_generator.py:365-375`
- **GUI missing flag**: `src/gui/heightmap_gui.py:417, 852-857`
- **Bottleneck if not downsampled**: `src/features/river_generator.py:99-124` (triple loop)

### Lakes - No downsampling
- **Constructor**: `src/features/water_body_generator.py:36-46` (no downsample param)
- **Flood fill 1**: `src/features/water_body_generator.py:145-179` (_estimate_basin_size)
- **Flood fill 2**: `src/features/water_body_generator.py:214-248` (create_lake, unbounded!)
- **Radial search**: `src/features/water_body_generator.py:117-143` (_find_rim_height)
- **GUI call**: `src/gui/heightmap_gui.py:336`

### Coastal - No downsampling
- **Constructor**: `src/features/coastal_generator.py:40-52` (no downsample param)
- **Beach nested loop**: `src/features/coastal_generator.py:157-174` (16.7M iterations)
- **Cliff nested loop**: `src/features/coastal_generator.py:215-233` (16.7M iterations)
- **Distance search**: `src/features/coastal_generator.py:248-262` (240 samples × millions of cells)
- **GUI call**: `src/gui/heightmap_gui.py:377`

---

## Fix Strategy

### Priority 1: Rivers (Quick Fix - 5 minutes)
**File**: `src/features/river_generator.py:417`

Change from:
```python
river_gen = RiverGenerator(self.generator.heightmap)
```

To:
```python
river_gen = RiverGenerator(self.generator.heightmap, downsample=True, target_size=1024)
```

**Expected result**: 30min → 30s (16× speedup)

### Priority 2: Lakes (Implement Pattern - 30 minutes)
**File**: `src/features/water_body_generator.py`

1. Add downsampling to `__init__` (follow river_generator.py:48-79 pattern)
2. Add upsampling to `generate_lakes()` (follow river_generator.py:365-375 pattern)
3. Update GUI call at line 336

**Expected result**: 20min → 30s (40× speedup)

### Priority 3: Coastal (Implement Pattern - 30 minutes)
**File**: `src/features/coastal_generator.py`

1. Add downsampling to `__init__` (follow river_generator.py:48-79 pattern)
2. Add upsampling to `generate_coastal_features()` (follow river_generator.py:365-375 pattern)
3. Update GUI call at line 377

**Expected result**: 15min → 30s (30× speedup)

---

## Testing Plan

After fixes, verify with:
```bash
python tests/test_performance.py  # Should show <60s for all water features
```

Expected timings (4096×4096):
- Rivers: ~30s (was 30min)
- Lakes: ~30s (was 20min)
- Coastal: ~30s (was 15min)

---

## Conclusion

**Why water features still hang**:
1. **Rivers**: Downsampling code exists but GUI never activates it (1-line fix)
2. **Lakes**: NO downsampling + O(n²) flood fills on full resolution (needs implementation)
3. **Coastal**: NO downsampling + O(n²) nested loops on full resolution (needs implementation)

**Impact**: Users experience 15-30 minute freezes even though performance_utils.py exists

**Solution**: 3 straightforward fixes following the existing river_generator.py pattern

---

**Status**: ROOT CAUSE IDENTIFIED
**Priority**: CRITICAL (user-blocking)
**Estimated Fix Time**: 1 hour total
**Estimated Testing Time**: 30 minutes
