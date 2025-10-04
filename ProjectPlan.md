# CS2 Heightmap Generator - Comprehensive Implementation Plan

**Version**: 2.0
**Status**: Phase 1 Complete (State Management)
**Last Updated**: 2025-10-04

---

## Executive Summary

This document outlines the complete implementation plan for enhancing the CS2 Heightmap Generator with advanced features including undo/redo, water features (rivers/lakes/coasts), GUI, and performance optimizations.

**Core Philosophy**: Find and implement the ONE optimal solution - no workarounds, no fallbacks, no over-complexity.

---

## Project Phases

### Phase 1: Foundation - State Management [COMPLETE]
**Duration**: Day 1-2
**Status**: COMPLETE - All tests passing

#### Deliverables
- [x] `src/state_manager.py` - Command pattern implementation
- [x] Command classes: SetHeightDataCommand, SmoothCommand, AddCircleCommand, etc.
- [x] CommandHistory with undo/redo stacks
- [x] MacroCommand for composite operations
- [x] Memory tracking and optimization
- [x] `test_state_manager.py` - Comprehensive test suite

#### Key Design Decisions
1. **Command Pattern**: Industry standard for undo/redo (used in Photoshop, Blender, etc.)
2. **Memory Optimization**: Store only changed regions, not full snapshots
3. **Stack-based History**: Undo stack + redo stack (standard behavior)
4. **Macro Support**: Group commands into single undo/redo unit

#### Insights
The Command pattern is the mathematically optimal solution because:
- Encapsulates each operation with its inverse
- Memory efficient (stores only diffs)
- Supports unlimited undo/redo depth
- Enables macro commands (composite operations)

Any other approach (memento pattern, full snapshots, etc.) would be a compromise.

---

### Phase 2: Core Map Features
**Duration**: Week 2 (Days 1-5)
**Status**: PENDING

#### 2.1 River Network Generation
**File**: `src/features/river_generator.py`

**Algorithm**: D8 Flow Accumulation (industry standard in hydrology)

```
1. Calculate slope at each pixel
2. For each pixel, identify steepest descent direction (8 neighbors)
3. Accumulate flow: each pixel receives flow from uphill neighbors
4. Identify river sources (high flow accumulation points)
5. Carve river paths following flow direction
6. Apply width function (wider at low elevations)
7. Smooth river valleys for realistic appearance
```

**Key Methods**:
```python
calculate_flow_accumulation(heightmap) -> flow_map
  # D8 algorithm: O(n) single-pass algorithm

identify_river_sources(flow_map, threshold) -> [(x,y), ...]
  # Find pixels with flow > threshold

carve_river_path(heightmap, source, width_func) -> modified_heightmap
  # Follow flow direction, lower terrain along path

add_river_network(heightmap, num_rivers, params) -> modified_heightmap
  # High-level API: generate complete river system
```

**Why D8 Algorithm**:
- Standard in GIS/hydrology software
- Computationally efficient (O(n))
- Physically accurate (follows gravity)
- No arbitrary/random decisions

#### 2.2 Lake/Depression Detection & Creation
**File**: `src/features/water_body_generator.py`

**Algorithm**: Watershed Segmentation

```
1. Detect local minima (potential lake basins)
2. Apply watershed algorithm to define basin boundaries
3. Calculate fill level (lowest point on basin rim)
4. Level terrain within basin to create flat lake surface
5. Add gradual shore transition for realism
```

**Key Methods**:
```python
detect_depressions(heightmap, min_size) -> [basin_mask, ...]
  # Morphological operations to find basins

fill_basin(heightmap, basin_mask, fill_level) -> modified_heightmap
  # Set all basin pixels to fill_level

create_lake(heightmap, center, size, depth) -> modified_heightmap
  # High-level: dig depression + fill with water

add_shore_transition(heightmap, lake_mask, width) -> modified_heightmap
  # Smooth gradient from land to water
```

**Why Watershed Algorithm**:
- Mathematically defines natural drainage basins
- Handles complex shapes automatically
- Used in all terrain analysis software
- No manual boundary tracing needed

#### 2.3 Coastal Features (Beaches & Cliffs)
**File**: `src/features/coastal_generator.py`

**Algorithm**: Gradient-based Feature Detection

```
1. Define sea level threshold
2. Detect coastline (land/water boundary)
3. Calculate slope at coastline
4. Low slope (<5°) → beach
5. High slope (>30°) → cliff
6. Apply appropriate modifications
```

**Key Methods**:
```python
detect_coastline(heightmap, sea_level) -> coastline_mask
  # Find boundary between land and water

calculate_coastal_slope(heightmap, coastline) -> slope_map
  # Gradient magnitude at coast

add_beach(heightmap, coastline, width, slope) -> modified_heightmap
  # Gradual slope from water to land

add_cliffs(heightmap, coastline, height, roughness) -> modified_heightmap
  # Steep vertical faces
```

---

### Phase 3: Quality of Life Features
**Duration**: Week 3 (Days 1-5)
**Status**: PENDING

#### 3.1 Progress Indicators
**File**: `src/progress_tracker.py`

**Implementation**: tqdm library (industry standard)

```python
class ProgressTracker:
    """Context manager for progress tracking"""

    def __init__(self, description, total):
        self.bar = tqdm(desc=description, total=total)

    def update(self, n=1):
        self.bar.update(n)

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.bar.close()

# Usage:
with ProgressTracker("Generating terrain", 4096) as progress:
    for y in range(4096):
        # ... generate row ...
        progress.update()
```

**Why tqdm**:
- Industry standard (used in ML, scientific computing)
- Zero configuration
- Works in terminal and Jupyter
- No wheel reinventing

#### 3.2 Visual Preview Generation
**File**: `src/preview_generator.py`

**Algorithm**: Hillshade Rendering

```
Hillshade = cos(zenith) * cos(slope) + sin(zenith) * sin(slope) * cos(azimuth - aspect)

Where:
- zenith = 90° - altitude
- slope = arctan(gradient_magnitude)
- aspect = arctan2(dy, dx)
- azimuth = light direction (typically 315° = NW)
```

**Key Methods**:
```python
generate_preview(heightmap, size=512, mode='elevation') -> PIL.Image
  # Modes: 'elevation', 'hillshade', 'slope', 'aspect'

generate_hillshade(heightmap, azimuth=315, altitude=45) -> shaded_map
  # Calculate hillshade using standard GIS formula

apply_colormap(data, colormap='terrain') -> RGB_image
  # Convert grayscale to colored visualization
```

**Why Hillshade**:
- Standard in GIS/cartography
- Reveals terrain detail better than flat elevation
- Mathematically simple and fast
- Creates publication-quality visualizations

#### 3.3 Terrain Analysis Tools
**File**: `src/analysis/terrain_analyzer.py`

**Algorithms**: Standard GIS Metrics

```python
calculate_slope(heightmap) -> slope_degrees
  # Gradient magnitude: sqrt(dx² + dy²)
  # Convert to degrees: arctan(gradient) * 180/π

calculate_aspect(heightmap) -> aspect_degrees
  # Direction: arctan2(dy, dx) * 180/π
  # 0° = North, 90° = East, 180° = South, 270° = West

calculate_statistics(heightmap) -> stats_dict
  # Mean, std, min, max, percentiles
  # Slope distribution histogram
  # Buildable area percentage
```

---

### Phase 4: GUI Implementation
**Duration**: Week 4 (Days 1-5)
**Status**: PENDING

**File**: `src/gui/heightmap_gui.py`

**Technology**: Tkinter (Python stdlib - zero external dependencies)

#### GUI Architecture

```
Main Window (1280x800)
├── Menu Bar (File, Edit, View, Tools, Help)
├── Toolbar (Quick actions)
├── Left Panel (300px)
│   ├── Preset Selector (radio buttons)
│   ├── Parameter Sliders
│   └── Manual Tools Palette
├── Center Panel (700px)
│   ├── Preview Canvas (512x512 live preview)
│   └── Status Bar
└── Right Panel (280px)
    ├── History List (undo/redo)
    ├── Statistics Display
    └── Action Buttons
```

#### Key Classes

```python
class HeightmapGUI(tk.Tk):
    """Main application window"""
    def __init__(self):
        # Initialize generator with CommandHistory
        self.generator = HeightmapGenerator()
        self.history = CommandHistory()

        # Create UI components
        self.preview = PreviewCanvas(self, size=512)
        self.params = ParameterPanel(self)
        self.tools = ToolPalette(self)

class PreviewCanvas(tk.Canvas):
    """Live heightmap preview with hillshade"""
    def update_preview(self, heightmap):
        # Generate hillshade
        # Convert to PIL Image
        # Display on canvas

class ParameterPanel(tk.Frame):
    """Sliders for terrain parameters"""
    # Scale, octaves, persistence, etc.
    # Debounced updates (500ms) to avoid lag

class ToolPalette(tk.Frame):
    """Manual editing tools"""
    # Click-to-place: hills, rivers, lakes
    # Brush tools: raise, lower, smooth
```

#### Real-Time Features

1. **Live Preview** (debounced 500ms)
   - Generate preview in worker thread
   - Update canvas when ready
   - Keep GUI responsive

2. **Click-to-Edit**
   - Click canvas to place features
   - Drag to sculpt terrain
   - All operations go through CommandHistory (undoable)

3. **Parameter Presets**
   - Save/load entire configurations
   - One-click terrain types
   - User custom presets

---

### Phase 5: Preset Management
**Duration**: Day 1-2
**Status**: PENDING

**File**: `src/preset_manager.py`

**Format**: JSON (human-readable, git-friendly)

```json
{
  "version": "1.0",
  "name": "Alpine Valley",
  "description": "Mountain valley with river",
  "terrain": {
    "generator": "perlin",
    "resolution": 4096,
    "height_scale": 5000,
    "seed": 12345,
    "parameters": {
      "scale": 180.0,
      "octaves": 6,
      "persistence": 0.55,
      "lacunarity": 2.1
    }
  },
  "features": [
    {
      "type": "river",
      "source": [0.3, 0.8],
      "width": 10,
      "depth": 50
    },
    {
      "type": "lake",
      "center": [0.5, 0.5],
      "radius": 0.1,
      "depth": 100
    }
  ],
  "post_processing": [
    {
      "operation": "smooth",
      "iterations": 2,
      "kernel_size": 3
    }
  ]
}
```

**Storage**: `~/.cs2_heightmaps/presets/`

**Key Methods**:
```python
save_preset(name, config, filepath)
load_preset(filepath) -> config
list_user_presets() -> [names]
apply_preset(config, generator, history) -> None
```

---

### Phase 6: Performance Optimization
**Duration**: Week 5 (Days 1-5)
**Status**: PENDING

#### 6.1 Multi-Threading for Noise Generation
**File**: Update `src/noise_generator.py`

**Strategy**: Tile-Based Generation

```python
# Split 4096x4096 into 256x256 tiles
num_tiles = 16  # 4096 / 256
tiles = []

with ThreadPoolExecutor(max_workers=cpu_count()) as executor:
    futures = []
    for tile_y in range(num_tiles):
        for tile_x in range(num_tiles):
            future = executor.submit(
                generate_tile,
                tile_x, tile_y, params
            )
            futures.append((tile_x, tile_y, future))

    # Collect results
    for tile_x, tile_y, future in futures:
        tile_data = future.result()
        tiles[(tile_y, tile_x)] = tile_data

# Stitch tiles with overlap blending
heightmap = stitch_tiles(tiles, overlap=4)
```

**Expected Performance**:
- Single-threaded: 60-90 seconds (4096x4096, 6 octaves)
- Multi-threaded (8 cores): 15-25 seconds (3-4x speedup)

**Why Tiling**:
- Noise generation is embarrassingly parallel
- No inter-tile dependencies
- Linear speedup with cores
- Standard approach in procedural generation

#### 6.2 LRU Caching
**File**: `src/cache_manager.py`

**Strategy**: functools.lru_cache + disk cache

```python
# In-memory cache for recent operations
@lru_cache(maxsize=128)
def generate_terrain_cached(preset_name, seed):
    return generate_terrain(preset_name, seed)

# Disk cache for presets
class DiskCache:
    def __init__(self, cache_dir, max_size_mb=1024):
        self.cache_dir = Path(cache_dir)
        self.max_size = max_size_mb * 1024 * 1024

    def get(self, key):
        # Load from disk if exists

    def put(self, key, data):
        # Save to disk, evict old entries if needed
```

**Cache Keys**: `f"{preset}_{seed}_{resolution}"`

---

## File Structure (Final State)

```
CS2_Map/
├── src/
│   ├── heightmap_generator.py       [Existing - No changes]
│   ├── noise_generator.py           [Modified - Add threading]
│   ├── worldmap_generator.py        [Existing - No changes]
│   ├── cs2_exporter.py             [Existing - No changes]
│   │
│   ├── state_manager.py            [NEW - COMPLETE]
│   ├── progress_tracker.py         [NEW - PENDING]
│   ├── preview_generator.py        [NEW - PENDING]
│   ├── preset_manager.py           [NEW - PENDING]
│   ├── cache_manager.py            [NEW - PENDING]
│   │
│   ├── features/
│   │   ├── __init__.py
│   │   ├── river_generator.py      [NEW - PENDING]
│   │   ├── water_body_generator.py [NEW - PENDING]
│   │   └── coastal_generator.py    [NEW - PENDING]
│   │
│   ├── analysis/
│   │   ├── __init__.py
│   │   └── terrain_analyzer.py     [NEW - PENDING]
│   │
│   └── gui/
│       ├── __init__.py
│       ├── heightmap_gui.py        [NEW - PENDING]
│       ├── preview_canvas.py       [NEW - PENDING]
│       ├── parameter_panel.py      [NEW - PENDING]
│       └── tool_palette.py         [NEW - PENDING]
│
├── gui_main.py                     [NEW - PENDING]
├── test_state_manager.py           [NEW - COMPLETE]
├── ProjectPlan.md                  [THIS FILE]
└── requirements.txt                [Modified - Add tqdm]
```

---

## Dependencies

### Current
```txt
Pillow>=10.0.0
numpy>=1.24.0
scipy>=1.10.0
perlin-noise>=1.12
opensimplex>=0.4.5
```

### To Add
```txt
tqdm>=4.65.0  # Progress bars
```

**Note**: Tkinter is in Python stdlib - no external dependency needed

---

## Testing Strategy

### Unit Tests
- Each module has `test_*.py`
- Mock HeightmapGenerator for isolated testing
- Parametrized tests for different scenarios

### Integration Tests
- Full pipeline: preset → features → export
- GUI automation (if feasible)
- Performance benchmarks

### Manual QA
- Import into CS2 and visual inspection
- User acceptance testing

---

## Success Criteria

### Functional
- [x] Undo/redo works for all operations
- [ ] Rivers follow realistic flow patterns
- [ ] Lakes have natural basins
- [ ] Beaches/cliffs at appropriate slopes
- [ ] GUI is responsive and intuitive
- [ ] Presets save/load correctly

### Performance
- [ ] 4096x4096 generation in <30 seconds (multi-threaded)
- [ ] GUI preview updates in <200ms
- [ ] Undo/redo is instant (<10ms)

### Quality
- [ ] Code follows CLAUDE.md guidelines
- [ ] Comprehensive inline documentation
- [ ] All tests passing
- [ ] No unicode in output (CLAUDE.md compliant)

---

## Development Order (Optimal Path)

### Week 1: Foundation [COMPLETE]
1. [x] Day 1-2: state_manager.py + tests
2. [ ] Day 3: progress_tracker.py
3. [ ] Day 4-5: Integration and testing

### Week 2: Core Features
4. [ ] Day 1-2: river_generator.py
5. [ ] Day 3: water_body_generator.py
6. [ ] Day 4: coastal_generator.py
7. [ ] Day 5: Testing

### Week 3: Analysis & Preview
8. [ ] Day 1: terrain_analyzer.py
9. [ ] Day 2-3: preview_generator.py
10. [ ] Day 4: preset_manager.py
11. [ ] Day 5: Integration

### Week 4: GUI
12. [ ] Day 1-2: heightmap_gui.py skeleton
13. [ ] Day 3: preview_canvas.py
14. [ ] Day 4: parameter_panel.py + tool_palette.py
15. [ ] Day 5: Polish and integration

### Week 5: Performance
16. [ ] Day 1-2: Multi-threading in noise_generator.py
17. [ ] Day 3: cache_manager.py
18. [ ] Day 4-5: Benchmarking and optimization

---

## Why This Is The Optimal Solution

### 1. No Over-Complexity
- Standard patterns (Command, MVC, Observer)
- Each module has ONE clear purpose
- No dependency injection frameworks
- No excessive abstractions

### 2. No Workarounds
- D8 flow (not random rivers)
- Watershed segmentation (not circular holes)
- Command pattern (not memento/snapshots)
- Proper threading (not async hacks)

### 3. No Fallbacks
- One correct implementation per feature
- If broken, fix it (don't add alternatives)
- Fail fast with clear errors

### 4. Maintainable
- Independent modules (testable in isolation)
- Clear separation of concerns
- Centralized state management
- Comprehensive documentation

### 5. Extensible
- New features = new file in features/
- New presets = JSON file
- New tools = button in GUI

### 6. CLAUDE.md Compliant
- Comments explain WHY, not WHAT
- Logical organization
- No redundancy
- Proper error handling
- No unicode in code/output

---

## This Is The Only Solution Any Expert Would Arrive At

An expert recognizes:
1. **Command pattern** is standard for undo/redo
2. **D8 flow** is standard for river generation
3. **Watershed** is standard for basin detection
4. **Tkinter** is obvious (stdlib, cross-platform)
5. **Tiling** is standard for parallel generation
6. **Hillshade** is standard for terrain visualization

Any other approach would be a workaround or compromise.

---

**Document Version**: 2.0
**Last Updated**: 2025-10-04
**Status**: Phase 1 Complete, Phase 2-6 Pending
