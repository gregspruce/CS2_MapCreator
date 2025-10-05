# CS2 Heightmap Generator - Terrain Quality Evaluation Report

**Date:** 2025-10-05
**Evaluated Resolutions:** 512x512, 1024x1024
**Terrain Types Tested:** Flat, Hills, Mountains, Highlands, Islands

---

## Executive Summary

The CS2 Heightmap Generator currently produces **excellent terrain for gameplay** (100% buildable, good elevation variety, natural features), but generates **visually tame terrain** that lacks dramatic geological features like sharp ridges, steep cliffs, and challenging slopes.

**Bottom Line:** Perfect for players who want easy city building. Unsuitable for players who want dramatic mountain scenery.

---

## Detailed Findings

### 1. Buildability Analysis

**Current State:** ALL terrain types are 98-100% buildable

| Terrain Type | Buildable (<5%) | Easy (<2%) | Assessment |
|--------------|-----------------|------------|------------|
| Flat | 100.0% | 100.0% | Completely flat |
| Hills | 100.0% | 100.0% | Gentle rolling hills |
| **Mountains** | **100.0%** | **98.8%** | **Too smooth for mountains!** |
| Highlands | 100.0% | 100.0% | Plateau-like |
| Islands | 100.0% | 100.0% | Very gentle |

**Verdict:** [OK] **Excellent for city building** - players can build anywhere without terrain constraints.

**Problem:** Mountains should be challenging! Real mountainous terrain has 30-50% unbuildable areas.

### 2. Visual Drama Analysis

**Current State:** Maximum slopes are FAR below geological realism

| Terrain Type | Max Slope | Target for Type | Gap |
|--------------|-----------|-----------------|-----|
| Flat | 0.52% | <2% | [OK] Correct |
| Hills | 1.65% | 3-5% | [X] Too smooth |
| **Mountains** | **4.43%** | **8-15%** | **[X] 45% of target!** |
| Highlands | 3.17% | 5-8% | [X] Too smooth |
| Islands | 1.92% | 4-7% | [X] Too smooth |

**Verdict:** [X] **Insufficient visual drama** - terrain lacks sharp ridges, steep peaks, challenging slopes.

### 3. Geological Feature Detection

**Ridge Detection:** Requires slopes >8% in high-elevation areas

**Results:**
- ALL terrain types: **0% ridge coverage**
- Maximum slope achieved: 4.43% (Mountains)
- Ridge threshold: 8.0%
- **Gap: Terrain is 55% too smooth to register ridges**

**What this means:**
- No sharp mountain peaks
- No distinct ridgelines
- No dramatic cliff faces
- No challenging terrain features

### 4. Elevation Variety

**Current State:** Good elevation range, moderate standard deviation

| Terrain Type | Elevation Range | Elevation StdDev | Height Variety | Assessment |
|--------------|-----------------|------------------|----------------|------------|
| Flat | 1.000 | 0.143 | 1.016 | [OK] Correct for flat |
| Hills | 1.000 | 0.158 | Varies | [OK] Good variety |
| Mountains | 1.000 | 0.141 | Varies | [X] Too uniform |
| Highlands | 1.000 | 0.146 | Varies | [OK] Good variety |
| Islands | 1.000 | 0.198 | Varies | [OK] Best variety |

**Verdict:** [OK] **Adequate elevation variety** - terrain uses full 0.0-1.0 range with reasonable distribution.

**Note:** Variety comes from gentle undulations, not dramatic peaks/valleys.

### 5. Root Cause Analysis

**Why is terrain so smooth?**

The previous "too noisy" problem was fixed by:
1. Reducing detail noise weight (0.6 → 0.6)
2. Using aggressive mountain masking (mountain_mask²)
3. Reducing base weight to smooth valleys

**Result:** Created smooth, buildable valleys (GOOD) but also eliminated sharp peaks (BAD).

**Trade-off:** Current settings prioritize buildability over visual drama.

**Diagnostic Results** (from `diagnose_ridges.py`):
- Base noise max slope: 4.02%
- After coherent processing: **0.73%** (82% reduction!)
- After ridge enhancement: 2.30% (helped, but not enough)
- After full pipeline: 1.91%

**Conclusion:** Coherent terrain processing is **too smooth** - it destroys slopes instead of organizing them.

---

## Terrain Type Recommendations

### For Easy City Building (Current Settings)
**Use:** Mountains, Hills, or Highlands
**Benefits:**
- 100% buildable area
- No terrain constraints
- Easy to plan city layout
- Gentle slopes don't block roads

**Drawbacks:**
- Visually boring
- No dramatic landmarks
- No challenging terrain
- Lacks geological realism

### For Dramatic Scenery (NEEDS NEW SETTINGS)
**Would need:**
- Detail weight: 0.6-0.8 (increased)
- Mountain mask: Linear or square (not cubed)
- Ridge enhancement: 0.9-1.0 (maximum)
- Erosion: 0-1 iterations (reduced smoothing)

**Would produce:**
- 60-80% buildable area
- Sharp mountain peaks (8-15% slopes)
- Distinct ridgelines
- Challenging but interesting terrain

**Not currently implemented.**

---

## Comparison to Real-World Terrain

**Real mountainous regions** (e.g., Colorado Rockies, Swiss Alps):
- Buildable valleys: 20-40%
- Moderate slopes: 30-40%
- Steep/unbuildable: 30-50%
- Max slopes: 15-40% (cliffs can be 60-90%)

**Current "Mountains" terrain:**
- Buildable: 100%
- Moderate slopes: 0%
- Steep/unbuildable: 0%
- Max slopes: 4.43%

**Verdict:** Current "Mountains" resembles **Midwest farmland**, not actual mountains.

---

## Recommendations

### Short-Term (Quick Fixes)

1. **Rename Terrain Types** to match reality:
   - "Mountains" → "Gentle Hills"
   - "Hills" → "Very Gentle Hills"
   - "Flat" → "Plains"

2. **Add Slider: "Terrain Drama"** (0-100%):
   - 0% = Current settings (100% buildable, smooth)
   - 50% = Balanced (70% buildable, some ridges)
   - 100% = Maximum drama (50% buildable, sharp peaks)

3. **Adjust Detail Weight by Drama Level:**
   ```python
   detail_weight = 0.3 + (drama_level * 0.006)  # 0.3-0.9 range
   mountain_mask_power = 3 - (drama_level * 0.02)  # 3.0-1.0 range
   ```

### Long-Term (Better Solution)

1. **Separate Coherence from Smoothing:**
   - Coherence should ORGANIZE noise (create mountain ranges)
   - NOT smooth it (preserve local detail)

2. **Multi-Resolution Detail:**
   - Large-scale: Mountain range placement (current coherent system)
   - Medium-scale: Individual peaks and valleys (needs improvement)
   - Small-scale: Rock outcrops, cliffs (currently missing)

3. **Adaptive Ridge Enhancement:**
   - Detect where ridges should be based on elevation
   - Apply STRONG enhancement only to those areas
   - Keep valleys completely smooth

---

## Gameplay Evaluation (CS2 Specific)

**For Cities Skylines 2**, current terrain is:

### Buildability: [OK] EXCELLENT
- ✓ 100% usable area
- ✓ 98% easy building areas
- ✓ Large contiguous flat regions
- ✓ No terrain blocking roads/zones

### Visual Interest: [X] NEEDS IMPROVEMENT
- ✓ Good elevation range (0.0-1.0)
- ✓ Adequate elevation variety (StdDev 0.14-0.20)
- ✗ No dramatic features (ridges, cliffs)
- ✗ Lacks visual landmarks

### Natural Appearance: [X] NEEDS IMPROVEMENT
- ✓ Coherent geography (mountain zones, valley zones)
- ✓ Smooth geological transitions
- ✗ Too uniform (no sharp peaks)
- ✗ Doesn't resemble real mountains

### Overall CS2 Verdict: [OK] **GOOD for gameplay, POOR for aesthetics**

**Best use case:** Players who prioritize easy city building over scenery.
**Poor use case:** Players who want dramatic mountain cities or challenging terrain.

---

## Testing Methodology

### Test Configurations
- Resolution: 512x512 (fast testing), 1024x1024 (quality check)
- Terrain Types: All 5 types (Flat, Hills, Mountains, Highlands, Islands)
- Iterations: 3-5 per type for consistency check

### Metrics Measured
1. **Buildability:** Percentage of terrain with slope <5%
2. **Easy Building:** Percentage with slope <2%
3. **Max Slope:** Steepest slope achieved
4. **Ridge Coverage:** Percentage meeting ridge criteria (elev >70th percentile, slope >8%)
5. **Elevation StdDev:** Measure of elevation variety
6. **Largest Flat Region:** Largest contiguous buildable area

### Tools Used
- `test_single_terrain.py` - Single terrain analysis
- `diagnose_ridges.py` - Stage-by-stage slope tracking
- `evaluate_for_gameplay.py` - CS2-specific gameplay metrics
- `compare_terrain_types.py` - Cross-type comparison

---

## Conclusion

The CS2 Heightmap Generator is **functioning correctly for its current design goal** (easy city building), but that design goal may not match user expectations for "mountainous" terrain.

**The fundamental question:** Should "Mountains" terrain prioritize:
1. **Gameplay** (easy building, few constraints) - Current design
2. **Realism** (dramatic scenery, challenging terrain) - Needs implementation
3. **Configurable** (user chooses via sliders) - Recommended solution

**Recommendation:** Implement a "Terrain Drama" or "Buildability" slider to let users choose their preferred balance between gameplay ease and visual drama.

**Status:** Currently optimized for buildability at the expense of visual drama.

---

## Appendix: Technical Details

### Current Composition Weights (Mountains)
```python
composed = (
    base_norm * 0.3 +                          # Base (smooth)
    ranges_norm * 0.2 * mountain_mask +       # Ranges (masked)
    detail_norm * 0.6 * (mountain_mask ** 2)  # Detail (heavily masked)
)
```

### Ridge Enhancement Settings (Mountains)
```python
params = {
    'warp': 0.4,      # Domain warping strength
    'ridge': 0.8,     # Ridge sharpening (increased)
    'valley': 0.3,    # Valley carving (reduced)
    'erosion': 1      # Erosion iterations (reduced)
}
```

### Ridge Detection Thresholds
```python
ridge_mask = (heightmap > np.percentile(heightmap, 70)) & (slope > 0.08)
```
- Top 30% elevation
- Slope > 8% (0.08)
- Currently: 0% terrain meets this threshold

---

**Report Generated:** 2025-10-05
**Tool Version:** v2.4 (with coherent terrain optimizations)
**Next Steps:** Implement configurable drama slider or revise mountain terrain composition.
