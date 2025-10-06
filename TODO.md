# TODO - CS2 Heightmap Generator

**Last Updated**: 2025-10-06
**Current Version**: 2.4.2 (unreleased)
**Status**: Strategic Enhancement Phase - Terrain Generation v2.0 Overhaul

---

## GROUNDBREAKING: Terrain Generation v2.0 Overhaul (Priority: CRITICAL)

**Branch**: `feature/terrain-gen-v2-overhaul`
**Research**: `map_gen_enhancement.md` + `examples/examplemaps/terrain_coherence_analysis.md`
**Goal**: Transform from "procedural noise" to "geological realism" - match professional heightmap quality

**Strategy**: Staged Value Delivery with Adaptive Decision Points
- Stage 1: Foundation (2 weeks) - COMMIT NOW
- Stage 2: Geological Realism (2 weeks) - CONDITIONAL on Stage 1 success
- Stage 3: Professional Polish (2-3 weeks) - CONDITIONAL on Stages 1-2 success

---

### STAGE 1: Foundation - Quick Wins + Hydraulic Erosion (Weeks 1-2) 🔥

**Objective**: Deliver transformative realism improvement in 2 weeks
**Target**: 70-80% improvement in visual quality, generation time <30s

#### Week 1: Quick Wins (3-4 days)
- [ ] **Quick Win 1: Enhanced Domain Warping** (4 hours)
  - File: `src/noise_generator.py`
  - Implement recursive domain warping (Inigo Quilez technique)
  - Apply before all mountain masking
  - Expected impact: Eliminates grid patterns immediately

- [ ] **Quick Win 2: Ridge Continuity Post-Processing** (4 hours)
  - File: `src/coherent_terrain_generator.py`
  - Identify ridge cells (local maxima)
  - Connect nearby ridges using Dijkstra's algorithm
  - Expected impact: +30% feature continuity

#### Week 1-2: Hydraulic Erosion Implementation (7-9 days)
- [ ] **Task 1.1: Algorithm Research & Selection** (Days 1-2)
  - Review pipe model paper: https://inria.hal.science/inria-00402079/document
  - Study reference: https://github.com/dandrino/terrain-erosion-3-ways
  - Choose algorithm: pipe model (quality) vs droplet (speed)
  - Target: 5-10s erosion at 1024x1024
  - Deliverable: Algorithm selection document

- [ ] **Task 1.2: Core Erosion Implementation** (Days 3-7)
  - Create: `src/features/hydraulic_erosion.py`
  - Implement `HydraulicErosionSimulator` class:
    - `__init__`: erosion_rate, deposition_rate, evaporation_rate, sediment_capacity
    - `simulate_erosion()`: Per iteration flow → erode → transport → deposit
    - `fast_erosion_multiresolution()`: Downsample → erode → upsample pattern
  - D8 flow direction calculation (reuse from river_generator.py)
  - Sediment transport: `C = Kc × sin(slope) × velocity`
  - Erosion-deposition logic with progress callback
  - Deliverable: Erosion completes in 5-10s at 1024 res

- [ ] **Task 1.3: Pipeline Integration** (Days 8-10)
  - Modify: `src/coherent_terrain_generator.py`
  - Add erosion step after base terrain, before detail
  - Create erosion presets: fast (skip), balanced (50 iter), maximum (100 iter)
  - Update `generate_heightmap()` to call erosion when enabled
  - Deliverable: Integrated erosion with quality levels

- [ ] **Task 1.4: Testing & Validation** (Days 11-12)
  - Generate test heightmaps with erosion enabled
  - Visual comparison: Check dendritic drainage patterns
  - Performance benchmark: Measure total time (target <30s)
  - Compare with example heightmaps (examples/examplemaps/)
  - CS2 import test: Verify loads and plays correctly
  - Deliverable: Test report with before/after comparison

#### Week 2: Documentation & Release Prep (2-3 days)
- [ ] **Update README.md**: Add "Hydraulic Erosion" section with parameters
- [ ] **Update CHANGELOG.md**: Create v2.0.0 section documenting erosion
- [ ] **Create EROSION.md**: Algorithm deep-dive, parameters, theory
- [ ] **Update examples/**: Add erosion-enabled sample heightmaps
- [ ] **GUI integration**: Add erosion controls with tooltips

**Stage 1 Success Criteria**:
- [x] Dendritic drainage patterns visible in generated terrain
- [x] Visual comparison matches example heightmap quality (>4.0/5.0 rating)
- [x] Generation time <30s in balanced mode
- [x] CS2 import successful with playable terrain
- [x] User feedback: "This looks like real geography, not noise"

**Decision Point After Stage 1**:
- If success criteria met → Ship v2.0.0, gather user feedback, decide on Stage 2
- If not met → Adjust erosion parameters, iterate until criteria met

---

### STAGE 2: Geological Realism - Tectonics + Rivers (Weeks 3-4) 🌍

**Objective**: Add geological foundation and dam-suitable valleys
**Conditional**: Proceed only if Stage 1 achieves success criteria

#### Week 3: Tectonic Structure (5-6 days)
- [ ] **Task 2.1: Fault Line Generation**
  - Create: `src/tectonic_generator.py`
  - Implement `TectonicStructureGenerator`:
    - `generate_fault_lines()`: Bezier curves across map
    - `generate_tectonic_uplift()`: Distance-based elevation from faults
  - Bezier curve generation for realistic patterns
  - Distance field calculation with exponential falloff
  - Fault interaction logic (higher at intersections)

- [ ] **Task 2.2: Buildability Constraint Integration**
  - Modify: `src/coherent_terrain_generator.py`
  - Use tectonic structure as base for generation
  - Implement buildability control map (45-55% flat terrain)
  - Octave modulation: buildable zones (1-2 octaves), scenic zones (1-8 octaves)
  - Domain warping with strength 40-80

#### Week 3-4: River Network Improvements (4-5 days)
- [ ] **Task 3.1: Hierarchical River Generation**
  - Modify: `src/features/river_generator.py`
  - Implement `HierarchicalRiverGenerator`:
    - `generate_from_outlets()`: Grow network upstream from coast
    - `calculate_flow_accumulation()`: D8 algorithm (already exists)
    - Horton-Strahler stream ordering
  - Replace random placement with flow-accumulation-based

- [ ] **Task 3.2: Dam-Suitable Valley Generation**
  - Implement `create_dam_suitable_valley()`:
    - Narrow constriction: 300-400m width (85-115 pixels)
    - Elevated sides: 300-400m higher than riverbed
    - Height drop: 50-100m over 500-1000m distance
    - Water source at high elevation (90th percentile)
  - Identify suitable dam locations (narrow river points)
  - Parameter: `num_dam_valleys` for control

#### Week 4: Integration & Testing (2-3 days)
- [ ] Update presets to use tectonic + erosion pipeline
- [ ] Test buildability validation (45-55% target)
- [ ] Visual validation: Linear continuous mountain ranges
- [ ] CS2 gameplay test: Dam placement works
- [ ] Documentation updates for v2.1.0

**Stage 2 Success Criteria**:
- [x] Mountain ranges are linear and geologically justified
- [x] 45-55% buildable terrain maintained
- [x] At least 2-3 dam-suitable valleys per map
- [x] Visual comparison still >4.0/5.0 rating

---

### STAGE 3: Professional Polish - Pipeline + Validation (Weeks 5-7) ✨

**Objective**: Create unified architecture and professional-grade output
**Conditional**: Proceed only if Stages 1-2 successful

#### Week 5: Unified Pipeline Architecture (4-5 days)
- [ ] **Task 4.1: Pipeline Design & Implementation**
  - Create: `src/terrain_pipeline.py`
  - Implement `UnifiedTerrainPipeline`:
    - Phase 1: Continental structure (512x512)
    - Phase 2: Regional features (1024x1024)
    - Phase 3: Hydraulic erosion (1024x1024)
    - Phase 4: Detail addition (4096x4096)
    - Phase 5: Coastal features (4096x4096)
  - Create `TerrainContext` for data sharing between phases
  - Quality level controls: fast / balanced / maximum

#### Week 5-6: Coastal Integration + Validation (6-8 days)
- [ ] **Task 5.1: Drainage-Aware Coastal Generation**
  - Modify: `src/features/coastal_generator.py`
  - Implement `IntegratedCoastalGenerator`:
    - Fjords: deep valleys meeting ocean
    - Natural harbors: river outlets at coast
    - Headlands: ridges extending into water
  - Use erosion flow accumulation data

- [ ] **Task 6.1: Buildability Validation System**
  - Create: `src/validation/buildability_validator.py`
  - Implement `BuildabilityValidator`:
    - `calculate_slopes()`: Slope percentage per cell
    - `analyze_buildability()`: Statistics and problem areas
    - `enforce_buildability_constraint()`: Targeted smoothing
  - Smart Blur: strength depends on elevation difference
  - Iterative refinement until 45-55% met

#### Week 7: Final Testing & Documentation (5-7 days)
- [ ] Complete pipeline integration testing
- [ ] Performance benchmarks: fast (<12s), balanced (<30s), maximum (<60s)
- [ ] Regression tests: existing presets still work
- [ ] Community validation: Share on Reddit/forums
- [ ] Complete documentation: ADVANCED_USAGE.md, TROUBLESHOOTING.md
- [ ] Create professional example heightmaps
- [ ] Update all presets for new pipeline
- [ ] Release v2.2.0

**Stage 3 Success Criteria**:
- [x] All quality modes within performance targets
- [x] Natural harbors visible in coastlines
- [x] Buildability guaranteed at 45-55%
- [x] Community feedback: "Best heightmap generator for CS2"

---

## Immediate (Current Sprint - Priority: HIGH)

### Phase 1 Follow-up (CRITICAL)
- [ ] **Implement comprehensive test suite**
  - Follow testing strategy in `docs/testing/phase1_testing_strategy.md`
  - ~60 tests across unit, integration, performance, and QA categories
  - Target: 85%+ code coverage for Phase 1 modules
  - Estimated: 44 hours over 1-2 weeks
  - Files: `tests/test_buildability.py`, `tests/test_slope_analysis.py`, etc.

- [ ] **Address remaining code review issues**
  - Review `docs/review/phase1_code_review_python_expert.md` for remaining issues
  - Add input validation to all Phase 1 modules (MEDIUM priority)
  - Estimated: 6-8 hours for production quality
  - Target: Raise code quality from 8.5/10 to 9.5/10

### Testing & Verification
- [ ] **Test water features end-to-end**
  - Generate terrain, add rivers (verify D8 flow)
  - Add lakes (verify watershed segmentation works)
  - Add coastal features (verify beaches and cliffs)
  - Test undo/redo for all water features
  - Verify performance (rivers may take 10-15s for large terrains)

- [ ] **Test GUI thoroughly**
  - Generate multiple terrains with different presets
  - Verify preview updates automatically (no click needed)
  - Verify elevation legend labels fully visible
  - Test terrain analysis (Tools → Terrain Analysis)
  - Test CS2 export (File → Export to CS2)

- [ ] **Verify setup script completeness**
  - Test `setup_env.bat` includes pyfastnoiselite installation
  - Test `verify_setup.py` catches missing dependencies
  - Confirm all features work on fresh install

### Documentation
- [x] Update README.md with v2.1.1 features ✅
- [x] Update CHANGELOG.md with v2.1.1 release notes ✅
- [x] Update CHANGELOG.md with Phase 1 implementation ✅
- [x] Update claude_continue.md for session continuity ✅
- [x] Update TODO.md (this file) ✅
- [x] Create FEATURE_FIX_SUMMARY.md ✅
- [x] Create GUI_FIXES_v2.1.1.md ✅

---

## Short-term (1-2 weeks - Priority: MEDIUM)

### Performance Enhancements

- [ ] **Add Numba JIT compilation for post-processing**
  - Target: smoothing, erosion, hillshade operations
  - Expected: Additional 5-20x speedup on these operations
  - Effort: 2-4 hours
  - Files: `src/heightmap_generator.py`, `src/preview_generator.py`

- [ ] **Implement preview downsampling**
  - Generate 512x512 for GUI preview (instant updates)
  - Generate full 4096x4096 only on save/export
  - Expected: Preview updates in 0.05s instead of 0.9s
  - Effort: 3-5 hours
  - Files: `src/gui/heightmap_gui.py`, `src/preview_generator.py`

---

## Medium-term (1-2 months - Priority: LOW-MEDIUM)

### Advanced Optimizations

- [ ] **GPU acceleration with CuPy**
  - For NVIDIA GPU users
  - Expected: 50-500x speedup on compatible hardware
  - Fallback to CPU for non-NVIDIA systems
  - Effort: 1-2 days
  - Files: `src/noise_generator.py`, `requirements.txt`

- [ ] **Elevation legend customization**
  - Add colormap selector (terrain/elevation/grayscale)
  - Add position selector (left/right/top/bottom)
  - Add size options (small/medium/large)
  - Effort: 4-6 hours
  - Files: `src/gui/heightmap_gui.py`

- [ ] **Parallel worldmap generation**
  - Generate heightmap and worldmap simultaneously
  - Expected: 50% reduction in total workflow time
  - Effort: 1 day
  - Files: `src/worldmap_generator.py`, `src/gui/heightmap_gui.py`

---

## Long-term (3-6 months - Priority: LOW)

### Major Features

- [ ] **WebGL preview rendering**
  - Hardware-accelerated 3D visualization
  - Real-time lighting and shading
  - Interactive camera controls
  - Effort: 1-2 weeks
  - New files: `src/webgl_preview.py` or external viewer

- [ ] **Real-time terrain editing**
  - Brush tools for manual sculpting
  - Live preview updates (<100ms)
  - Undo/redo integration
  - Effort: 2-3 weeks
  - Files: Major refactor of `src/gui/heightmap_gui.py`

- [ ] **Real-world elevation data import**
  - SRTM, ASTER, and other DEM formats
  - Automatic conversion to CS2 format
  - Coordinate system transformations
  - Effort: 1-2 weeks
  - New files: `src/dem_importer.py`

---

## Completed (Phase 1 - 2025-10-05)

### Phase 1: Playable Foundation Implementation
- [x] ✅ **Phase 1.1**: Domain Warping Enhancement (20 min actual, 2-4 hrs estimated)
  - Added `domain_warp_amp` and `domain_warp_type` parameters to noise_generator.py
  - Leveraged FastNoiseLite's built-in domain warp support
  - Eliminates grid-aligned patterns, creates organic terrain

- [x] ✅ **Phase 1.2**: Buildability Constraint System (~350 lines)
  - Created `src/techniques/buildability_system.py`
  - Deterministic buildability control (guarantees 45-55% buildable)
  - Control map generation + morphological smoothing + detail modulation

- [x] ✅ **Phase 1.3**: Slope Validation & Analytics (~300 lines)
  - Created `src/techniques/slope_analysis.py` (SlopeAnalyzer class)
  - NumPy gradient-based slope calculation
  - Distribution analysis and JSON export for QA

- [x] ✅ **Phase 1.4**: Targeted Gaussian Smoothing (~250 lines)
  - Added TargetedSmoothing class to slope_analysis.py
  - Iterative smoothing until buildability target met
  - Preserves detail in flat and scenic areas

- [x] ✅ **Phase 1.5**: 16-bit Export Verification (~235 lines)
  - Created `tests/test_16bit_export.py`
  - All tests passing (conversion, roundtrip, integration)
  - Verified PIL 'I;16' mode preserves precision

- [x] ✅ **Code Quality Fixes**:
  - Fixed HIGH severity: Global random state pollution (use np.random.Generator)
  - Fixed MEDIUM severity: Unicode symbols (use [PASS]/[FAIL] per CLAUDE.md)
  - Python-expert review: 8.5/10 production-ready rating

- [x] ✅ **Expert Reviews**:
  - Python-expert code review: `docs/review/phase1_code_review_python_expert.md`
  - Testing-expert strategy: `docs/testing/phase1_testing_strategy.md`

- [x] ✅ **Documentation**:
  - Updated CHANGELOG.md with comprehensive Phase 1 details
  - Updated TODO.md with Phase 1 tasks and follow-up work
  - Created enhanced_project_plan.md (1000+ lines strategic plan)
  - All files include WHY-focused documentation per CLAUDE.md

**Phase 1 Performance**: 5-15s total pipeline for 4096×4096, 550-700 MB memory

## Completed (v2.1.1 - 2025-10-05)

- [x] ✅ Connected water features to GUI (rivers, lakes, coastal)
- [x] ✅ Connected terrain analysis to GUI (comprehensive statistics)
- [x] ✅ Connected CS2 export to GUI (direct export to CS2 directory)
- [x] ✅ Fixed preview not updating automatically (added GUI redraw calls)
- [x] ✅ Fixed elevation legend text overflow (increased canvas width)
- [x] ✅ Created test_features.py (backend verification - all passing)
- [x] ✅ Updated all documentation for v2.1.1 release

## Completed (v2.1.0 - 2025-10-05)

- [x] ✅ Vectorized noise generation (60-140x speedup)
- [x] ✅ Fixed pyfastnoiselite missing from venv
- [x] ✅ Created verify_setup.py dependency checker
- [x] ✅ Added elevation legend GUI panel
- [x] ✅ Removed GUI threading (not needed for <1s operations)
- [x] ✅ Created comprehensive benchmark suite (test_performance.py)
- [x] ✅ Fixed FractalType enum typo (FBM → FBm)

---

## Notes for Future Development

### Performance Baseline (v2.1.0)
- 4096x4096 Perlin generation: 0.85-0.94s
- 4096x4096 OpenSimplex2: 1.43s
- Throughput: ~19M pixels/second
- Any optimization should be benchmarked against these values

### Critical Dependencies
- **pyfastnoiselite**: REQUIRED for fast generation (verify with `verify_setup.py`)
- **NumPy**: Already optimized with vectorization
- **Pillow**: Fast enough for preview generation

### Code Quality Standards
- Follow CLAUDE.md principles (root cause fixes, no fallbacks)
- Maintain comprehensive documentation
- Update CHANGELOG.md with every significant change
- Test thoroughly before marking as complete

### User Experience Priorities
1. **Performance**: Keep generation <1s (user expects instant results)
2. **Clarity**: GUI should be self-explanatory
3. **Reliability**: No crashes, clear error messages
4. **Flexibility**: Presets for beginners, parameters for experts

---

**Next Session Start**: Run `python verify_setup.py` and `python gui_main.py` to verify everything works. Read `claude_continue.md` for full context.
