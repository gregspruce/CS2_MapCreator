# CS2 Heightmap Generator - Water Features Performance Fix

**Date**: 2025-10-05
**Issue**: Water features (rivers, lakes, coastal) hang indefinitely on 4096×4096 heightmaps
**Root Cause**: O(n²) Python loops on 16.7 million cells without downsampling
**Status**: Fix in progress

---

## Problem Analysis

### Issue 1: Hanging/Freezing

**Symptoms**:
- Clicking "Generate Rivers" → GUI freezes
- Clicking "Generate Lakes" → GUI freezes
- Clicking "Add Coastal Features" → GUI freezes
- No progress indication, appears crashed

**Root Cause**:
Water feature algorithms process full 4096×4096 heightmap (16.7M cells) with nested Python loops:

```python
# river_generator.py line 79-100
for y in range(self.height):  # 4096 iterations
    for x in range(self.width):  # 4096 iterations
        for dir_idx, (dy, dx) in enumerate(self.DIRECTIONS):  # 8 iterations
            # ... calculations ...
```

**Computational complexity**:
- River D8 flow: 4096 × 4096 × 8 = **134 million operations** in Python
- Lake detection: Similar + flood fill = **hundreds of millions of operations**
- Estimated time: **10-30 minutes** (appears frozen to user)

### Issue 2: Terrain Realism

**Symptoms**:
- Even when features finish, terrain looks random
- No realistic drainage patterns
- No coherent mountain ranges or valleys
- Maps unusable for actual gameplay

**Root Cause**:
Raw Perlin noise has no geological structure:
- No erosion (ridges, valleys)
- No drainage networks (water flow)
- No continuity (isolated bumps, not ranges)
- Just stacked octaves of noise

Real terrain needs:
- Hydraulic erosion simulation
- Domain warping for structure
- Ridge/billow noise combinations
- Thermal erosion for cliffs

---

## Solution Strategy

### Phase 1: Immediate Performance Fix (This Session)

**Goal**: Make water features responsive (<5s instead of 30min)

**Approach**: Downsample before processing, upsample result

```python
# Pseudocode
def add_rivers_fast(heightmap_4096):
    # 1. Downsample to workable size
    heightmap_1024 = downsample(heightmap_4096, factor=4)

    # 2. Run water feature algorithm on smaller heightmap
    rivers_1024 = generate_rivers(heightmap_1024)

    # 3. Upsample result back to full resolution
    rivers_4096 = upsample(rivers_1024, factor=4)

    # 4. Apply to original heightmap
    return apply_rivers(heightmap_4096, rivers_1024)
```

**Benefits**:
- 4096→1024 = **16× fewer cells** = **16× faster**
- 1024×1024×8 = 8.4M operations (manageable: ~30s)
- Still good quality (1024 resolution plenty for rivers)
- Non-blocking with progress bar

**Trade-offs**:
- Slightly less detailed rivers (acceptable)
- Need careful upsampling (bilinear interpolation)

### Phase 2: Terrain Realism (Next Session)

**Goal**: Generate geologically realistic terrain

**Approaches** (choose one or combine):

1. **Hydraulic Erosion Simulation** (Best quality, slowest)
   - Simulate water flow and sediment transport
   - Creates natural valleys, river networks, alluvial plains
   - Time: ~5-10s for 1024×1024
   - Used by: World Machine, Gaea

2. **Domain Warping** (Fast, good quality)
   - Warp noise coordinates using another noise layer
   - Creates curved mountain ranges, realistic features
   - Time: <1s
   - Used by: Minecraft, No Man's Sky

3. **Ridge/Billow Noise** (Fast, better than Perlin)
   - Ridge noise for mountains (sharp peaks)
   - Billow noise for clouds/hills (rounded)
   - Combine with standard Perlin
   - Time: <1s

4. **Feature-Based Generation** (Most control)
   - Place mountain ranges, valleys, plateaus explicitly
   - Then add detail with noise
   - Erode for realism
   - Time: ~2-5s

**Recommendation**: Start with domain warping + ridge noise (fast, good results), then add optional erosion.

---

## Implementation Plan

### Step 1: Add Downsampling Helper

Create `src/features/performance_utils.py`:

```python
def downsample_for_features(heightmap: np.ndarray, target_size: int = 1024) -> tuple:
    """
    Downsample heightmap for feature generation.

    Returns:
        (downsampled_heightmap, scale_factor)
    """
    current_size = heightmap.shape[0]
    if current_size <= target_size:
        return heightmap, 1.0

    scale_factor = target_size / current_size
    downsampled = ndimage.zoom(heightmap, scale_factor, order=1)

    return downsampled, current_size / target_size

def upsample_rivers(river_mask: np.ndarray, target_size: int) -> np.ndarray:
    """Upsample river mask back to full resolution."""
    scale_factor = target_size / river_mask.shape[0]
    upsampled = ndimage.zoom(river_mask, scale_factor, order=0)  # Nearest neighbor
    return upsampled > 0.5
```

### Step 2: Modify Water Feature Generators

Update `river_generator.py`, `water_body_generator.py`, `coastal_generator.py`:

```python
class RiverGenerator:
    def __init__(self, heightmap: np.ndarray, downsample: bool = True):
        if downsample and heightmap.shape[0] > 1024:
            self.heightmap, self.scale_factor = downsample_for_features(heightmap)
            self.original_size = heightmap.shape[0]
        else:
            self.heightmap = heightmap
            self.scale_factor = 1.0
            self.original_size = heightmap.shape[0]
```

### Step 3: Update GUI Calls

Modify `heightmap_gui.py`:

```python
def add_rivers(self):
    # ... existing validation ...

    # Create generator with downsampling enabled
    generator = RiverGenerator(self.heightmap, downsample=True)

    # Show progress
    progress = ProgressDialog(self, "Generating Rivers")
    progress.update(0, "Calculating flow directions...")

    # Generate (now fast!)
    command = generator.generate_rivers(num_rivers)

    # Execute and update
    self.history.execute(command)
    self.update_preview()

    progress.close()
```

### Step 4: Add Progress Feedback

```python
# In river_generator.py
def calculate_flow_direction(self, progress_callback=None):
    flow_dir = np.full((self.height, self.width), -1, dtype=np.int8)

    total_cells = self.height * self.width
    for i, y in enumerate(range(self.height)):
        if progress_callback and i % 100 == 0:
            progress_callback(i / self.height * 100)

        for x in range(self.width):
            # ... existing logic ...

    return flow_dir
```

---

## Expected Performance

### Before Fix (Current)

| Feature | Resolution | Time | Status |
|---------|-----------|------|---------|
| Rivers | 4096×4096 | 15-30min | Hangs/freezes |
| Lakes | 4096×4096 | 10-20min | Hangs/freezes |
| Coastal | 4096×4096 | 5-10min | Hangs/freezes |

### After Fix (Downsampled)

| Feature | Resolution | Time | Status |
|---------|-----------|------|---------|
| Rivers | 1024×1024 | 20-40s | Responsive with progress |
| Lakes | 1024×1024 | 10-20s | Responsive with progress |
| Coastal | 1024×1024 | 5-10s | Responsive with progress |

### With Optimization (Future)

| Feature | Resolution | Time | Status |
|---------|-----------|------|---------|
| Rivers (vectorized) | 1024×1024 | 2-5s | Fast |
| Lakes (vectorized) | 1024×1024 | 1-3s | Fast |
| Coastal (vectorized) | 1024×1024 | 1-2s | Fast |

---

## Testing Plan

1. **Test downsampling quality**:
   - Generate 4096×4096 terrain
   - Downsample to 1024×1024
   - Compare visual quality
   - Verify rivers still look realistic

2. **Test performance**:
   - Time river generation (should be <60s)
   - Time lake generation (should be <30s)
   - Verify no freezing/hanging

3. **Test upsampling**:
   - Generate rivers on 1024×1024
   - Upsample to 4096×4096
   - Verify rivers align with terrain
   - Check for artifacts

---

## Next Steps

1. Implement downsampling helpers
2. Update water feature generators
3. Add progress feedback
4. Test all features
5. Document new performance
6. Plan terrain realism improvements

---

**Status**: Analysis complete, ready to implement fix
