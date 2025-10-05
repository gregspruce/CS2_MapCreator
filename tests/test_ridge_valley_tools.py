"""
Test script for ridge and valley two-point click-drag tools.

This script verifies:
1. Ridge tool creates linear ridge between two points
2. Valley tool creates linear valley between two points
3. Visual preview line appears during drag
4. Undo/redo works correctly with two-point tools

Usage:
    python tests/test_ridge_valley_tools.py

Expected behavior:
- GUI launches with default terrain
- Select ridge tool, click-drag-release to create ridge
- Select valley tool, click-drag-release to create valley
- Yellow dashed preview line shows during drag
- Tools integrate cleanly with undo/redo system
"""

import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import tkinter as tk
from tkinter import messagebox
import numpy as np

from src.gui.heightmap_gui import HeightmapGUI


def test_ridge_valley_tools():
    """
    Launch GUI for manual testing of ridge and valley tools.

    Instructions for manual testing:
    1. Click "Generate Terrain" to create initial heightmap
    2. Select "Ridge" tool from tool palette
    3. Click on preview canvas, drag to another point, release
       - Should see yellow dashed preview line during drag
       - Should see ridge appear after release
    4. Select "Valley" tool
    5. Click and drag to create valley
    6. Test undo/redo (Ctrl+Z, Ctrl+Y)
    7. Test with different brush sizes and strengths
    """
    print("=" * 70)
    print("RIDGE & VALLEY TOOL TEST")
    print("=" * 70)
    print()
    print("This test launches the GUI for manual verification.")
    print()
    print("Testing steps:")
    print("1. Generate terrain first (click 'Generate Terrain')")
    print("2. Select 'Ridge' tool from tool palette")
    print("3. On the preview canvas:")
    print("   - Click at start point")
    print("   - Drag to end point (yellow dashed line shows preview)")
    print("   - Release to create ridge")
    print("4. Select 'Valley' tool and repeat")
    print("5. Test undo/redo (Ctrl+Z / Ctrl+Y)")
    print("6. Try different brush sizes and strengths")
    print()
    print("Expected behavior:")
    print("- Yellow dashed preview line during drag")
    print("- Ridge elevates terrain along line")
    print("- Valley carves terrain along line")
    print("- Undo/redo works correctly")
    print("- Status bar shows helpful messages")
    print()
    print("=" * 70)
    print()

    # Launch GUI
    app = HeightmapGUI()
    app.mainloop()


def verify_terrain_editor_methods():
    """
    Verify that TerrainEditor has the required methods.

    This is a programmatic sanity check before manual testing.
    """
    print("Verifying TerrainEditor implementation...")

    from src.features.terrain_editor import TerrainEditor

    # Create test heightmap
    test_heightmap = np.random.random((1024, 1024)) * 0.5
    editor = TerrainEditor(test_heightmap)

    # Check ridge method exists
    assert hasattr(editor, 'add_ridge'), "TerrainEditor missing add_ridge method"
    print("  add_ridge method exists")

    # Check valley method exists
    assert hasattr(editor, 'add_valley'), "TerrainEditor missing add_valley method"
    print("  add_valley method exists")

    # Test ridge creation (small test)
    result = editor.add_ridge(x1=100, y1=100, x2=200, y2=200, width=20, height=0.2)
    assert result.shape == test_heightmap.shape, "Ridge output has wrong shape"
    assert np.any(result != test_heightmap), "Ridge did not modify heightmap"
    print("  add_ridge produces valid output")

    # Test valley creation
    result = editor.add_valley(x1=300, y1=300, x2=400, y2=400, width=20, depth=0.2)
    assert result.shape == test_heightmap.shape, "Valley output has wrong shape"
    assert np.any(result != test_heightmap), "Valley did not modify heightmap"
    print("  add_valley produces valid output")

    print("  All TerrainEditor methods verified!")
    print()


def verify_command_integration():
    """
    Verify that AddFeatureCommand works with ridge/valley.
    """
    print("Verifying Command integration...")

    from src.features.terrain_editor import AddFeatureCommand
    from src.heightmap_generator import HeightmapGenerator

    # Create test generator
    generator = HeightmapGenerator(resolution=512)
    generator.heightmap = np.random.random((512, 512)) * 0.5

    # Test ridge command
    ridge_params = {'x1': 100, 'y1': 100, 'x2': 200, 'y2': 200, 'width': 20, 'height': 0.2}
    ridge_cmd = AddFeatureCommand(
        generator,
        feature_type='ridge',
        params=ridge_params,
        description="Test ridge"
    )

    original = generator.heightmap.copy()
    ridge_cmd.execute()
    assert np.any(generator.heightmap != original), "Ridge command did not modify heightmap"
    print("  Ridge command executes successfully")

    ridge_cmd.undo()
    assert np.allclose(generator.heightmap, original), "Ridge undo failed"
    print("  Ridge undo works correctly")

    # Test valley command
    valley_params = {'x1': 300, 'y1': 300, 'x2': 400, 'y2': 400, 'width': 20, 'depth': 0.2}
    valley_cmd = AddFeatureCommand(
        generator,
        feature_type='valley',
        params=valley_params,
        description="Test valley"
    )

    original = generator.heightmap.copy()
    valley_cmd.execute()
    assert np.any(generator.heightmap != original), "Valley command did not modify heightmap"
    print("  Valley command executes successfully")

    valley_cmd.undo()
    assert np.allclose(generator.heightmap, original), "Valley undo failed"
    print("  Valley undo works correctly")

    print("  All command integration verified!")
    print()


if __name__ == "__main__":
    print("Starting ridge/valley tool tests...")
    print()

    # Run programmatic checks first
    verify_terrain_editor_methods()
    verify_command_integration()

    # Launch GUI for manual testing
    print("Launching GUI for manual testing...")
    print("(Close the GUI window to exit)")
    print()

    test_ridge_valley_tools()

    print()
    print("Test complete!")
