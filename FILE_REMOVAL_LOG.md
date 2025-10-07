# File Removal and Reorganization Log

This log tracks all files that have been removed, moved, or reorganized to maintain repository cleanliness per CLAUDE.md guidelines.

---

## 2025-10-05 - Repository Cleanup and Organization

**Reason:** Organize repository per CLAUDE.md guidelines - move test scripts, analysis documents, and results to proper directories.

### Files Moved

#### Test Scripts (Root → tests/evaluation/)
- `test_single_terrain.py` → `tests/evaluation/test_single_terrain.py`
- `test_terrain_quality.py` → `tests/evaluation/test_terrain_quality.py`
- `diagnose_ridges.py` → `tests/evaluation/diagnose_ridges.py`
- `evaluate_for_gameplay.py` → `tests/evaluation/evaluate_for_gameplay.py`
- `compare_terrain_types.py` → `tests/evaluation/compare_terrain_types.py`
- `test_4096_only.py` → `tests/evaluation/test_4096_only.py`
- `test_coherent_optimization.py` → `tests/evaluation/test_coherent_optimization.py`
- `test_coherent_performance.py` → `tests/evaluation/test_coherent_performance.py`
- `test_downsample_quality.py` → `tests/evaluation/test_downsample_quality.py`
- `test_fft_vs_scipy.py` → `tests/evaluation/test_fft_vs_scipy.py`
- `test_water_features_fixes.py` → `tests/evaluation/test_water_features_fixes.py`

#### Analysis Documents (Root → docs/analysis/)
- `TERRAIN_EVALUATION_REPORT.md` → `docs/analysis/2025-10-05_terrain_quality_analysis.md`
- `claude_research_report.md` → `docs/analysis/legacy_erosion_research.md`
- `COHERENT_PERFORMANCE_ANALYSIS.md` → `docs/analysis/2025-10-05_coherent_performance_analysis.md`
- `WATER_FEATURES_BOTTLENECK_ANALYSIS.md` → `docs/analysis/2025-10-05_water_bottleneck_analysis.md`

#### Results Documents (Root → docs/results/)
- `COHERENT_OPTIMIZATION_SUMMARY.md` → `docs/results/2025-10-05_coherent_optimization_results.md`
- `OPTIMIZATION_RESULTS.md` → `docs/results/2025-10-05_optimization_results.md`
- `terrain_analysis/` → `docs/results/2025-10-05_terrain_evaluation/`

#### Fix Reports (Root → docs/fixes/)
- `WATER_FEATURES_BUG_FIXES.md` → `docs/fixes/2025-10-05_water_features_bug_fixes.md`
- `WATER_FEATURES_FIX_REPORT.md` → `docs/fixes/2025-10-05_water_features_fix_report.md`

#### Legacy Files (Root → docs/)
- `docs/TODO.md` → `docs/legacy_TODO_v2.0.md` (superseded by root TODO.md)

### Files Removed (Duplicates)
- `docs/claude_continue.md` (duplicate of root version, root is newer)
- `docs/CHANGELOG.md` (duplicate of root version, root is newer)
- `nul` (temporary file, should not exist)

### Recovery Information

**Commit Hash (before cleanup):** Not yet committed
**Branch:** main
**Date:** 2025-10-05

All moved files can be recovered from git history if needed. No permanent data loss - all files were moved, not deleted (except obvious temp files).

### Directory Structure Created
```
docs/
  analysis/         # Analysis documents with [DATE]_[TOPIC]_analysis.md format
  results/          # Results summaries with [DATE]_[TOPIC]_results.md format
  fixes/            # Fix reports
  features/         # Feature documentation
tests/
  evaluation/       # Test scripts for terrain quality evaluation
```

---

## 2025-10-06 - Repository Cleanup: Buildability Workarounds + Documentation Organization

**Reason:** Remove CLAUDE.md-violating buildability workarounds (symptom fixes, not root cause) and organize documentation per CLAUDE.md structure requirements.

### Files Removed

#### Test Files (Orphaned from previous iterations)
- `tests/diagnose_buildability_issue.py` (~360 lines, buildability diagnostic workaround)
- `tests/generate_erosion_samples.py`
- `tests/test_16bit_export.py`
- `tests/test_3d_preview.py`
- `tests/test_all_fixes_integration.py`
- `tests/test_brush_gui_integration.py`
- `tests/test_brush_performance.py`
- `tests/test_coherent_and_water_v2.4.py`
- `tests/test_erosion_integration.py`
- `tests/test_fastnoise_import.py`
- `tests/test_features.py`
- `tests/test_gui.py`
- `tests/test_gui_erosion_workflow.py`
- `tests/test_gui_fixes.py`
- `tests/test_gui_quick.py`
- `tests/test_integration.py`
- `tests/test_legend.py`
- `tests/test_manual_generation.py`
- `tests/test_performance.py`
- `tests/test_preview_fix.py`
- `tests/test_preview_performance.py`
- `tests/test_progress_dialog.py`
- `tests/test_progress_tracker.py`
- `tests/test_qol_features.py`
- `tests/test_ridge_valley_automated.py`
- `tests/test_ridge_valley_tools.py`
- `tests/test_state_manager.py`
- `tests/test_tool_deselect.py`
- `tests/test_tool_fixes.py`
- `tests/test_water_features.py`
- `tests/test_water_performance_debug.py`

#### Evaluation Directory (One-off diagnostic scripts)
- `tests/evaluation/` directory with 12 diagnostic scripts (entire directory removed)

#### Source Files (Orphaned/Unused)
- `src/techniques/buildability_system.py` (~420 lines, CLAUDE.md violation - symptom fix)
- `src/realistic_terrain_generator.py` (no active references)
- `src/parallel_generator.py` (only documentation reference, not in active code)
- `src/cache_manager.py` (only self-reference, unused)

**Total Removed:** 47 files (~2,500 lines)

### Files Moved to docs/planning/
- `enhanced_project_plan.md` → `docs/planning/enhanced_project_plan.md`
- `performance_improvement.md` → `docs/planning/performance_improvement.md`

### Files Moved to docs/analysis/
- `claude_research_report.md` → `docs/analysis/claude_research_report.md`
- `map_gen_enhancement.md` → `docs/analysis/map_gen_enhancement.md`
- `terrain_generation_research_20251005.md` → `docs/analysis/terrain_generation_research_20251005.md`
- `examples/examplemaps/terrain_coherence_analysis.md` → `docs/analysis/terrain_coherence_analysis.md`

### Files Moved to docs/fixes/
- `BUG_FIX_domain_warp_type.md` → `docs/fixes/BUG_FIX_domain_warp_type.md`

### Files Modified
- `src/gui/heightmap_gui.py` - Removed buildability post-processing from pipeline
- `src/techniques/__init__.py` - Updated docstring noting buildability is Stage 2 feature
- `CHANGELOG.md` - Added cleanup entry and deprecation notes
- `TODO.md` - Updated with cleanup entry, marked Phase 1.2 as removed
- `claude_continue.md` - Updated with current cleanup state

### Recovery Information

**Commit Hash (before cleanup):** In feature/terrain-gen-v2-overhaul branch
**Branch:** feature/terrain-gen-v2-overhaul
**Date:** 2025-10-06

All files can be recovered from git history if needed. Buildability system removed because it violated CLAUDE.md Code Excellence Standard - attempted to fix buildability AFTER terrain generation (symptom fix) instead of integrating during generation (root cause solution per Stage 2 Task 2.2).

### Directory Structure Enhanced
```
docs/
  planning/         # Strategic plans and roadmaps (NEW)
  analysis/         # Analysis documents with research findings
  results/          # Results summaries
  fixes/            # Fix reports
  features/         # Feature documentation
  review/           # Code reviews
  testing/          # Testing strategies
```

**Retained Essential Tests (6 files):**
- `tests/test_hydraulic_erosion.py`
- `tests/test_stage1_quickwin1.py`
- `tests/test_stage1_quickwin2.py`
- `tests/test_terrain_realism.py`
- `tests/verify_quickwins_integration.py`
- `tests/verify_setup.py`

---

## Notes

- All file movements preserve git history via standard mv/git commands
- Naming convention follows CLAUDE.md: `[DATE]_[TOPIC]_[type].md`
- Test scripts consolidated in tests/evaluation/ for easy discovery
- Analysis and results separated for clarity
- Duplicates removed to avoid confusion about which version is current
