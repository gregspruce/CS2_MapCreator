# User Feedback: Extreme Slope Spikes in Tectonic Structure

**Date**: 2025-10-08
**Reporter**: User
**Issue**: Current tectonic terrain has extreme slope spikes
**Status**: ⚠️ NOTED - Monitoring through Tasks 2.2 & 2.3

---

## User Observation

> "the current terrain is an improvement, but we still have spikes of extreme slope"

**Context**:
- Height scale: 0-4096m (1 meter resolution)
- X,Y scale: 4096×4096 pixels = 14,336m × 14,336m
- Pixel resolution: 3.5m per pixel

**Interpretation**:
The tectonic base structure (Task 2.1) alone may be creating slopes that are too steep, resulting in unbuildable spikes.

---

## Potential Causes

1. **Exponential Falloff Too Steep**
   - Current: falloff_meters = 600m
   - At 600m: elevation drops to 36.8% of peak
   - This creates ~45° slopes near faults
   - May need gentler falloff (800m-1200m)

2. **Max Uplift Too High**
   - Current: max_uplift = 0.8 → 3,277m peaks
   - From fault (0m) to 600m away: 3,277m elevation change
   - Gradient: 3,277m / 600m = 5.46 (546% slope!)
   - This is EXTREME - far beyond CS2's buildability threshold

3. **Missing Smoothing**
   - Tectonic structure is raw exponential decay
   - No erosion or smoothing applied yet
   - Tasks 2.2 and 2.3 will add smoothing layers

---

## Expected Resolution Path

**Task 2.2: Binary Buildability Mask**
- Will identify where slopes are too steep
- Areas near faults will be marked "scenic" (unbuildable)
- Only gentle areas will be marked "buildable"
- Target: 45-55% buildable terrain

**Task 2.3: Conditional Noise with Amplitude Modulation**
- Buildable areas: Low amplitude (0.3) → gentle terrain
- Scenic areas: Full amplitude (1.0) → detailed but steep
- Same octaves everywhere → no frequency discontinuities

**Expected Outcome**:
- Buildable zones will have gentle slopes (no spikes)
- Scenic zones can have extreme slopes (acceptable, not for building)
- Overall terrain: 45-55% buildable, rest is dramatic scenery

---

## Validation Criteria (After Task 2.3)

Must measure on COMPLETE system (Tasks 2.1 + 2.2 + 2.3):

1. **Buildable Area Slopes**
   - Measure: Mean/Max slope in buildable zones ONLY
   - Target: Mean <5%, Max <10% in buildable areas
   - Current issue: Measuring ALL terrain (includes mountains)

2. **Buildable Percentage**
   - Target: 45-55% of terrain at 0-5% slopes
   - Previous failure: 3.4% (gradient system)
   - Must pass: >40% buildable

3. **Spike Count in Buildable Zones**
   - Measure: Extreme gradients (>10%) in buildable-marked areas
   - Target: <1% of buildable zone has spikes
   - This is the KEY metric for this user feedback

---

## Action Plan

✅ **NOTED**: User feedback recorded
✅ **PROCEEDING**: Implement Task 2.2 (as requested)
⏸️ **MONITORING**: Will re-evaluate after Task 2.3 complete
🔧 **IF NEEDED**: Parameter tuning (falloff_meters, max_uplift, amplitude ratios)

**Hypothesis**: The slope spikes will be contained to "scenic" zones (non-buildable) after Tasks 2.2 and 2.3, making them acceptable.

**If hypothesis FALSE**: Adjust tectonic parameters or add gaussian smoothing to buildable zones.

---

**Reporter**: User
**Recorded By**: Claude Code
**Next Milestone**: Task 2.3 complete → Full system validation
