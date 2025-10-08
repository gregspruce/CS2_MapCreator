# CS2 Map Generator - Architecture Documentation

**Version**: 2.4.2 (unreleased) - v2.0.0 Development
**Last Updated**: 2025-10-07
**Status**: Post-merge from feature/terrain-gen-v2-overhaul

---

## Table of Contents

1. [System Overview](#system-overview)
2. [Entry Points](#entry-points)
3. [Core Architecture](#core-architecture)
4. [Module Directory](#module-directory)
5. [Generation Pipeline](#generation-pipeline)
6. [File Status Reference](#file-status-reference)
7. [Import Graph](#import-graph)
8. [Decision Records](#decision-records)

---

## System Overview

The CS2 Map Generator is a professional terrain generation tool for Cities Skylines 2. It uses evidence-based geological simulation to create realistic, playable heightmaps.

**Key Features**:
- Hydraulic erosion simulation (Stage 1 ✓)
- Gradient-based buildability constraints (Stage 2 Task 2.2 ✓)
- Advanced user controls (UI polish ✓)
- 60-75s generation time for professional-quality 4096×4096 terrain

**Technology Stack**:
- Python 3.8+
- NumPy (array operations)
- FastNoiseLite (noise generation)
- Numba (JIT compilation for erosion)
- Tkinter (GUI)
- PIL/Pillow (image export)

---

## Entry Points

### 1. GUI Application (`gui_main.py`)

**Primary user interface** for interactive terrain generation.

```python
# Launch GUI
python gui_main.py
```

**Features**:
- Live preview with hillshade rendering
- Parameter controls (sliders, presets)
- Water features (rivers, lakes, coastal)
- Terrain analysis tools
- Direct CS2 export

**Imports**: `src.gui.HeightmapGUI`

---

### 2. CLI Generator (`generate_map.py`)

**Command-line interface** for batch/scripted generation.

```bash
# Generate with preset
python generate_map.py mountains "Alpine Valley"

# List presets
python generate_map.py --list
```

**Features**:
- Preset-based generation
- Worldmap support
- Auto-export to CS2

**Imports**: `HeightmapGenerator`, `NoiseGenerator`, `WorldmapGenerator`, `CS2Exporter`

---

### 3. Example Scripts (`examples/*.py`)

**Learning resources** demonstrating API usage.

- `01_basic_usage.py` - Simple Perlin generation
- `02_preset_terrains.py` - Using terrain presets
- `03_with_worldmap.py` - Extended worldmap creation
- `04_custom_terrain.py` - Custom parameter tuning

---

## Core Architecture

### Architectural Pattern

**Layered Architecture** with service-oriented design:

```
┌─────────────────────────────────────┐
│   Presentation Layer (GUI/CLI)      │
├─────────────────────────────────────┤
│   Orchestration Layer (Pipeline)    │
├─────────────────────────────────────┤
│   Service Layer (Generators)        │
├─────────────────────────────────────┤
│   Foundation Layer (Core Classes)   │
└─────────────────────────────────────┘
```

### Dependency Flow

**Unidirectional** from top to bottom (no circular dependencies):

```
GUI → Orchestration → Services → Foundation
```

---

## Module Directory

### `/src/` - Core Modules

#### Foundation Classes

| File | Purpose | Status |
|------|---------|--------|
| `heightmap_generator.py` | Base heightmap container (4096×4096) | ✅ ACTIVE |
| `noise_generator.py` | Perlin/Simplex noise with FastNoiseLite | ✅ ACTIVE |
| `cs2_exporter.py` | CS2 directory detection, PNG export | ✅ ACTIVE |
| `worldmap_generator.py` | Extended worldmap beyond playable area | ✅ ACTIVE |

#### Service Classes

| File | Purpose | Status |
|------|---------|--------|
| `coherent_terrain_generator_optimized.py` | FFT-optimized coherent generation (9-14x faster) | ✅ ACTIVE |
| `coherent_terrain_generator_legacy.py` | Legacy coherent generation (slow, benchmarking only) | ⚠️ LEGACY |
| `buildability_enforcer.py` | Slope smoothing for buildability targets | ✅ ACTIVE |
| `terrain_realism.py` | Domain warping, ridge sharpening | ✅ ACTIVE |
| `terrain_parameter_mapper.py` | Intuitive → technical parameter conversion | ✅ ACTIVE |

#### Support Classes

| File | Purpose | Status |
|------|---------|--------|
| `state_manager.py` | Undo/redo (command pattern) | ✅ ACTIVE |
| `preset_manager.py` | Terrain preset storage/loading | ✅ ACTIVE |
| `preview_generator.py` | Hillshade rendering | ✅ ACTIVE |
| `preview_3d.py` | 3D preview generation (optional) | ✅ ACTIVE |
| `progress_tracker.py` | Progress bar for long operations | ✅ ACTIVE |

---

### `/src/features/` - Feature Modules

| File | Purpose | Status |
|------|---------|--------|
| `hydraulic_erosion.py` | Pipe model erosion (Numba JIT) | ✅ ACTIVE |
| `river_generator.py` | D8 flow accumulation, river networks | ✅ ACTIVE |
| `water_body_generator.py` | Lake detection, watershed | ✅ ACTIVE |
| `coastal_generator.py` | Beach/cliff generation | ✅ ACTIVE |
| `terrain_editor.py` | Manual brush editing | ✅ ACTIVE |
| `performance_utils.py` | Downsampling for water features | ✅ ACTIVE |

---

### `/src/gui/` - GUI Components

| File | Purpose | Status |
|------|---------|--------|
| `heightmap_gui.py` | Main Tkinter application window | ✅ ACTIVE |
| `parameter_panel.py` | Terrain parameter controls (sliders) | ✅ ACTIVE |
| `preview_canvas.py` | Live heightmap preview | ✅ ACTIVE |
| `tool_palette.py` | Manual editing tools | ✅ ACTIVE |
| `progress_dialog.py` | Progress bar dialog | ✅ ACTIVE |

---

### `/src/analysis/` - Analysis Tools

| File | Purpose | Status |
|------|---------|--------|
| `terrain_analyzer.py` | Slope/aspect analysis, statistics | ✅ ACTIVE |

---

### `/src/techniques/` - Algorithm Techniques

| File | Purpose | Status |
|------|---------|--------|
| `slope_analysis.py` | Slope analysis and validation | ⚠️ UNCLEAR (not imported) |

**Note**: `slope_analysis.py` may be redundant (overlaps with `buildability_enforcer.py` and `terrain_analyzer.py`). Review needed.

---

## Generation Pipeline

### Full Professional-Quality Pipeline

```
1. PARAMETER SETUP (0s)
   └─> TerrainParameterMapper: Intuitive → Technical conversion

2. NOISE GENERATION (5-10s)
   ├─> NoiseGenerator.generate_buildability_control_map()
   ├─> NoiseGenerator.generate_perlin() [buildable layer: 2 octaves, no warp]
   ├─> NoiseGenerator.generate_perlin() [moderate layer: 5 octaves, warp=0.5]
   └─> NoiseGenerator.generate_perlin() [scenic layer: 7 octaves, warp=1.0]

3. TERRAIN BLENDING (1-2s)
   └─> Quadratic interpolation (buildable/moderate/scenic)

4. COHERENT STRUCTURE (10-12s)
   └─> CoherentTerrainGenerator.make_coherent()
       ├─> FFT-based coherence (ridge continuity)
       └─> Domain warping (removes grid patterns)

5. HYDRAULIC EROSION (40-45s)
   └─> HydraulicErosionSimulator.simulate_erosion()
       ├─> Pipe model algorithm
       ├─> Numba JIT optimization (5-8x speedup)
       └─> 100 iterations (default quality)

6. BUILDABILITY ENFORCEMENT (1-2s)
   └─> BuildabilityEnforcer.enforce_buildability_constraint()
       ├─> Calculate slopes
       ├─> Identify problem areas
       └─> Smart blur (preserves valleys/ridges)

7. EXPORT (1-2s)
   └─> CS2Exporter.export_to_cs2()
       └─> 16-bit PNG to CS2 directory

TOTAL: 60-75 seconds
```

### Fast Mode Pipeline (Skip Erosion)

```
1-3. [Same as above: 5-10s]
4. COHERENT STRUCTURE (10-12s)
6. BUILDABILITY ENFORCEMENT (1-2s)
7. EXPORT (1-2s)

TOTAL: 18-26 seconds
```

---

## File Status Reference

### Active Production Files (33 files)

**Core Generation**:
- heightmap_generator.py
- noise_generator.py
- coherent_terrain_generator_optimized.py
- buildability_enforcer.py
- terrain_realism.py
- terrain_parameter_mapper.py
- cs2_exporter.py
- worldmap_generator.py

**GUI**:
- gui/heightmap_gui.py
- gui/parameter_panel.py
- gui/preview_canvas.py
- gui/tool_palette.py
- gui/progress_dialog.py

**Features**:
- features/hydraulic_erosion.py
- features/river_generator.py
- features/water_body_generator.py
- features/coastal_generator.py
- features/terrain_editor.py
- features/performance_utils.py

**Support**:
- state_manager.py
- preset_manager.py
- preview_generator.py
- preview_3d.py
- progress_tracker.py
- analysis/terrain_analyzer.py

### Legacy/Superseded Files (1 file)

- **coherent_terrain_generator_legacy.py** - Superseded by optimized version ✅ RENAMED 2025-10-07
  - Still used by: test_stage1_quickwin2.py (benchmarking only)
  - Import updated to use explicit `_legacy.py` name

### Removed Files (Cleanup 2025-10-07)

- **techniques/slope_analysis.py** - DELETED ✅
  - Reason: 100% redundant with buildability_enforcer.py
  - Recovery: Available in git history if needed
  - Details: See FILE_REMOVAL_LOG.md

---

## Import Graph

### GUI Application Flow

```
gui_main.py
└─> src.gui.HeightmapGUI
    ├─> HeightmapGenerator (core container)
    ├─> NoiseGenerator (terrain generation)
    ├─> BuildabilityEnforcer (slope smoothing)
    ├─> TerrainParameterMapper (parameter conversion)
    ├─> PresetManager (preset storage)
    ├─> StateManager (undo/redo)
    ├─> PreviewGenerator (hillshade rendering)
    │   └─> TerrainAnalyzer (slope/aspect analysis)
    ├─> ParameterPanel (UI controls)
    ├─> PreviewCanvas (UI preview)
    ├─> ToolPalette (UI tools)
    ├─> ProgressDialog (UI progress)
    └─> Dynamic imports:
        ├─> CoherentTerrainGenerator (optimized version)
        │   └─> HydraulicErosionSimulator
        ├─> TerrainRealism (domain warping, ridges)
        ├─> WorldmapGenerator (optional)
        ├─> RiverGenerator (features)
        │   └─> PerformanceUtils (downsampling)
        ├─> WaterBodyGenerator (features)
        │   └─> PerformanceUtils (downsampling)
        ├─> CoastalGenerator (features)
        │   └─> PerformanceUtils (downsampling)
        ├─> TerrainEditor (manual editing)
        └─> Preview3D (optional 3D view)
```

### CLI Application Flow

```
generate_map.py
├─> HeightmapGenerator
├─> NoiseGenerator
├─> WorldmapGenerator
└─> CS2Exporter
```

### No Circular Dependencies

✅ All dependencies are **unidirectional** (top → down)
✅ No module imports form cycles
✅ Clean separation of concerns

---

## Decision Records

### ADR-001: Gradient Control Map vs Binary

**Date**: 2025-10-07
**Status**: ✅ APPROVED
**Context**: Evidence document specified binary buildability mask (0 or 1)

**Decision**: Implemented gradient control map (0.0-1.0) with 3-layer blending

**Rationale**:
1. Binary approach caused "oscillating wildly" visual problem
2. Hard transitions created visible seams at zone boundaries
3. Gradient provides smooth visual transitions
4. Industry standard (World Machine, Gaea use gradients)
5. Still achieves 45-55% buildable target

**Consequences**:
- ✅ Superior visual quality
- ✅ Better user experience
- ✅ Same buildability targets met
- ⚠️ Slight deviation from evidence spec (justified)

**Related Files**:
- `src/noise_generator.py` (control map generation)
- `src/gui/heightmap_gui.py` (pipeline implementation)
- `tests/test_stage2_buildability.py` (validation)

---

### ADR-002: Coherent Generator Optimization

**Date**: 2025-10-06
**Status**: ✅ APPROVED
**Context**: Original coherent generator took 114s at 4096×4096

**Decision**: Created FFT-optimized version (9-14x speedup)

**Rationale**:
1. Performance bottleneck identified
2. FFT approach mathematically equivalent
3. Massive speedup (114s → 10s)
4. No visual quality loss

**Consequences**:
- ✅ 9-14x performance improvement
- ✅ Same visual output
- ⚠️ Two files with same class name (confusing)

**Recommendation**: Rename legacy version to avoid confusion

**Related Files**:
- `src/coherent_terrain_generator_optimized.py` (new version)
- `src/coherent_terrain_generator.py` (legacy version)

---

### ADR-003: Numba JIT for Erosion

**Date**: 2025-10-06
**Status**: ✅ APPROVED
**Context**: Hydraulic erosion was performance bottleneck

**Decision**: Added Numba JIT compilation with graceful fallback

**Rationale**:
1. Erosion simulation is compute-intensive
2. Numba provides 5-8x speedup with zero code complexity
3. Graceful fallback ensures cross-platform compatibility
4. No dependencies on Numba (optional optimization)

**Consequences**:
- ✅ 5-8x speedup when Numba available
- ✅ Works on all systems (pure NumPy fallback)
- ✅ No user configuration needed

**Related Files**:
- `src/features/hydraulic_erosion.py`

---

### ADR-004: Buildability Post-Processing Removal

**Date**: 2025-10-06
**Status**: ✅ APPROVED
**Context**: Phase 1.2 included destructive post-processing flattening

**Decision**: Removed post-processing, implemented root cause solution

**Rationale**:
1. CLAUDE.md violation (symptom fix, not root cause)
2. Destructive to terrain features
3. Inconsistent results
4. Evidence document specifies conditional generation (root cause)

**Consequences**:
- ✅ CLAUDE.md compliance
- ✅ Better terrain quality
- ✅ Consistent results
- ✅ Root cause solution (conditional octaves)

**Related Files**:
- `src/buildability_enforcer.py` (retained for Priority 6 smart blur only)

---

## Maintenance Notes

### Adding New Features

1. **Create feature module** in appropriate directory:
   - Core generation → `/src/`
   - Water/terrain features → `/src/features/`
   - GUI components → `/src/gui/`
   - Analysis tools → `/src/analysis/`

2. **Update import graph** in this document

3. **Add tests** in `/tests/`

4. **Update CHANGELOG.md** with feature description

5. **Update README.md** if user-facing

### Deprecating Files

1. **Move to `/src/legacy/`** (or rename with `_legacy` suffix)

2. **Update file status** in this document

3. **Update imports** in test files to explicitly use legacy version

4. **Add deprecation notice** in file docstring

5. **Update FILE_REMOVAL_LOG.md** if removing entirely

### Performance Optimization

1. **Profile first** using `cProfile` or `line_profiler`

2. **Optimize proven bottlenecks** only

3. **Consider Numba JIT** for numerical loops

4. **Benchmark before/after** using test suite

5. **Document performance impact** in CHANGELOG.md

---

## Related Documentation

- **README.md** - User guide and installation
- **CHANGELOG.md** - Version history and changes
- **TODO.md** - Task tracking and roadmap
- **enhanced_project_plan.md** - Strategic v2.0 plan
- **docs/analysis/map_gen_enhancement.md** - Evidence-based requirements
- **PERFORMANCE.md** - Performance optimization guide
- **EROSION.md** - Hydraulic erosion algorithm documentation

---

**Last Updated**: 2025-10-07
**Maintained By**: Claude Code
**Review Frequency**: After each significant architectural change
