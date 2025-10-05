# Ridge and Valley Tools - User Guide

**Version**: 2.4.1 (Unreleased)
**Last Updated**: 2025-10-05
**Status**: Implemented and Tested

---

## Overview

The Ridge and Valley tools allow you to create linear terrain features by clicking and dragging on the heightmap preview. These tools are perfect for:

- Creating mountain ridges
- Carving river valleys
- Adding terrain structure
- Connecting elevated/lowered areas

---

## How to Use

### Ridge Tool

Creates a linear elevation between two points.

**Steps**:
1. Click "Generate Terrain" to create a heightmap (or load existing)
2. Select **Ridge** from the Tool Palette
3. Adjust **Brush Size** (controls ridge width)
4. Adjust **Strength** (controls ridge height)
5. On the preview canvas:
   - **Click** at starting point
   - **Drag** to ending point (yellow dashed line shows preview)
   - **Release** to create ridge

**Result**: Linear elevated ridge from start to end point with Gaussian falloff on sides.

---

### Valley Tool

Creates a linear depression between two points.

**Steps**:
1. Click "Generate Terrain" to create a heightmap (or load existing)
2. Select **Valley** from the Tool Palette
3. Adjust **Brush Size** (controls valley width)
4. Adjust **Strength** (controls valley depth)
5. On the preview canvas:
   - **Click** at starting point
   - **Drag** to ending point (yellow dashed line shows preview)
   - **Release** to create valley

**Result**: Linear carved valley from start to end point with Gaussian falloff on sides.

---

## Visual Feedback

While dragging, you'll see:
- **Yellow dashed line**: Shows where the ridge/valley will be placed
- **Real-time updates**: Line follows your cursor as you drag
- **Status bar**: Shows helpful messages

---

## Parameters

### Brush Size
Controls the **width** of the ridge or valley.

- **Small** (10-50): Narrow features like creeks or small ridges
- **Medium** (50-150): Standard features like valleys or mountain ridges
- **Large** (150-300): Wide features like broad plateaus or major valleys

### Strength
Controls the **intensity** of the feature.

- **Low** (0.1-0.3): Subtle elevation changes
- **Medium** (0.3-0.6): Noticeable features
- **High** (0.6-1.0): Dramatic terrain changes

**Note**: Actual height/depth = strength × 0.3 (scaled for natural-looking results)

---

## Undo/Redo Support

Ridge and valley tools fully support undo/redo:

- **Undo**: Press `Ctrl+Z` or use Edit → Undo
- **Redo**: Press `Ctrl+Y` or use Edit → Redo

Each ridge/valley operation creates a separate command in the history, allowing you to experiment freely.

---

## Tips and Tricks

### Creating Mountain Ranges
1. Use **Ridge** tool with medium-high strength
2. Draw multiple connected ridges
3. Vary the width and height for natural look
4. Use **Smooth** brush tool to blend connections

### Carving River Systems
1. Use **Valley** tool with medium width
2. Start from high elevation, drag to low elevation
3. Create branching tributaries by starting valleys at main valley
4. Lower strength near mouth for gradual transitions

### Combining with Other Tools
- **Hill/Depression**: Add at ridge/valley ends for peaks/lakes
- **Raise/Lower**: Adjust elevation along ridge/valley
- **Smooth**: Blend edges with surrounding terrain
- **Flatten**: Create plateaus along ridges

---

## Technical Details

### Algorithm
Both tools use:
1. **Line rasterization**: Interpolate points along line from start to end
2. **Gaussian falloff**: Perpendicular distance from line determines intensity
3. **Mask composition**: Multiple passes create smooth, continuous features

### Performance
- **Fast**: O(n) where n is line length
- **Resolution independent**: Works equally well on 1024×1024 or 4096×4096
- **Real-time preview**: Preview line updates instantly during drag

---

## Common Issues

### "Tool not yet implemented" message
**Cause**: Terrain hasn't been generated yet
**Solution**: Click "Generate Terrain" first

### Ridge/valley not visible
**Cause**: Strength too low or feature too narrow
**Solution**: Increase Brush Size and Strength parameters

### Line doesn't appear while dragging
**Cause**: Not clicking on the preview canvas
**Solution**: Ensure you're clicking and dragging on the heightmap preview

---

## Files Modified

**Implementation**:
- `src/gui/preview_canvas.py` - Two-point state tracking and preview line rendering
- `src/gui/heightmap_gui.py` - Ridge/valley tool integration with Command pattern

**Backend** (existing):
- `src/features/terrain_editor.py` - Ridge/valley algorithms (lines 211-308)

**Tests**:
- `tests/test_ridge_valley_automated.py` - Backend functionality tests
- `tests/test_ridge_valley_tools.py` - Interactive GUI test

---

## Related Documentation

- **Tool Palette**: See `docs/GUI_USAGE_NOTES.md` for all available tools
- **Keyboard Shortcuts**: See main README.md for full shortcut list
- **Command Pattern**: See source code comments in `src/state_manager.py`

---

## Future Enhancements (Potential)

- **Curved ridges**: Support multiple control points for non-linear features
- **Width variation**: Taper ridge/valley from start to end
- **Elevation matching**: Automatically adjust height based on endpoint elevations
- **Preset styles**: Quick selection for river valleys, mountain ridges, etc.

---

**Status**: Feature complete and ready for use!
**Testing**: Automated tests pass ✓
**Documentation**: Complete ✓
