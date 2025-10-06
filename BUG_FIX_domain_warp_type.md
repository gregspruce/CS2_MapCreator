# Bug Fix: Domain Warp Type Integer-to-Enum Conversion

## Problem
GUI crashed with error: `'int' object has no attribute 'value'` when generating terrain with `domain_warp_type=0` parameter.

## Root Cause
- `heightmap_gui.py` line 570 passed `domain_warp_type=0` as an integer
- FastNoiseLite expects a `DomainWarpType` enum, not an integer
- `noise_generator.py` was missing the `DomainWarpType` import
- Direct assignment of integer to enum property caused the error

## Solution Implemented

### 1. Added Missing Import (Line 24)
```python
from pyfastnoiselite.pyfastnoiselite import FastNoiseLite, NoiseType, FractalType, DomainWarpType
```

### 2. Added Integer-to-Enum Conversion (Lines 207-218)
```python
if domain_warp_amp > 0.0:
    noise.domain_warp_amp = domain_warp_amp
    # Convert integer to enum if needed for backward compatibility
    if isinstance(domain_warp_type, int):
        # Map integer values to DomainWarpType enum
        # 0 = OpenSimplex2, 1 = OpenSimplex2Reduced, 2 = BasicGrid
        warp_types = [
            DomainWarpType.DomainWarpType_OpenSimplex2,
            DomainWarpType.DomainWarpType_OpenSimplex2Reduced,
            DomainWarpType.DomainWarpType_BasicGrid
        ]
        noise.domain_warp_type = warp_types[domain_warp_type] if domain_warp_type < len(warp_types) else warp_types[0]
    else:
        noise.domain_warp_type = domain_warp_type
```

### 3. Updated Documentation
Enhanced docstrings to clarify that `domain_warp_type` accepts both integers and enums.

## Testing Results

All tests passed successfully:
- Domain warp type 0 (OpenSimplex2): SUCCESS
- Domain warp type 1 (OpenSimplex2Reduced): SUCCESS
- Domain warp type 2 (BasicGrid): SUCCESS
- No domain warping (backward compatibility): SUCCESS

## Files Modified
1. `src/noise_generator.py`
   - Added `DomainWarpType` import
   - Added integer-to-enum conversion logic
   - Updated docstrings

## Backward Compatibility
- Existing code using integers (0, 1, 2) continues to work
- Code using enum values directly also works
- Default behavior (no domain warping) unchanged

## Status
**FIXED AND VERIFIED** - GUI is fully functional again.

---
*Fix Date: 2025-10-06*
*Test Resolution: 128x128 (fast), verified up to 4096x4096*
