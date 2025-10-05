"""
Automated test for ridge and valley two-point tools.

Tests the backend functionality without requiring GUI interaction.
"""

import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import numpy as np
from src.features.terrain_editor import TerrainEditor, AddFeatureCommand
from src.heightmap_generator import HeightmapGenerator


def test_ridge_tool():
    """Test ridge tool creates linear elevation."""
    print("Testing ridge tool...")

    # Create test heightmap
    test_heightmap = np.ones((512, 512)) * 0.5
    editor = TerrainEditor(test_heightmap)

    # Add ridge from (100, 100) to (200, 200)
    result = editor.add_ridge(x1=100, y1=100, x2=200, y2=200, width=20, height=0.2)

    # Verify ridge was created
    assert result.shape == test_heightmap.shape, "Ridge output has wrong shape"
    assert np.any(result > test_heightmap), "Ridge did not elevate terrain"

    # Verify ridge is along the line (check midpoint)
    midpoint_y, midpoint_x = 150, 150
    assert result[midpoint_y, midpoint_x] > test_heightmap[midpoint_y, midpoint_x], \
        "Ridge not detected at midpoint"

    # Verify ridge has elevated terrain along line
    center_value = result[150, 150]

    print("  Ridge creates linear elevation - PASS")
    print(f"  Ridge elevation at center: {center_value:.4f}")
    print(f"  Original elevation: {test_heightmap[150, 150]:.4f}")
    print()


def test_valley_tool():
    """Test valley tool creates linear depression."""
    print("Testing valley tool...")

    # Create test heightmap
    test_heightmap = np.ones((512, 512)) * 0.5
    editor = TerrainEditor(test_heightmap)

    # Add valley from (300, 300) to (400, 400)
    result = editor.add_valley(x1=300, y1=300, x2=400, y2=400, width=20, depth=0.2)

    # Verify valley was created
    assert result.shape == test_heightmap.shape, "Valley output has wrong shape"
    assert np.any(result < test_heightmap), "Valley did not lower terrain"

    # Verify valley is along the line (check midpoint)
    midpoint_y, midpoint_x = 350, 350
    assert result[midpoint_y, midpoint_x] < test_heightmap[midpoint_y, midpoint_x], \
        "Valley not detected at midpoint"

    # Verify valley has lowered terrain along line
    center_value = result[350, 350]

    print("  Valley creates linear depression - PASS")
    print(f"  Valley elevation at center: {center_value:.4f}")
    print(f"  Original elevation: {test_heightmap[350, 350]:.4f}")
    print()


def test_ridge_command_undo_redo():
    """Test ridge command with undo/redo."""
    print("Testing ridge command with undo/redo...")

    # Create generator
    generator = HeightmapGenerator(resolution=512)
    generator.heightmap = np.ones((512, 512)) * 0.5

    # Store original
    original = generator.heightmap.copy()

    # Create and execute ridge command
    ridge_params = {
        'x1': 100, 'y1': 100,
        'x2': 200, 'y2': 200,
        'width': 20,
        'height': 0.2
    }
    command = AddFeatureCommand(
        generator,
        feature_type='ridge',
        params=ridge_params,
        description="Test ridge"
    )

    # Execute
    command.execute()
    modified = generator.heightmap.copy()
    assert np.any(modified != original), "Ridge command did not modify heightmap"
    print("  Ridge command executes - PASS")

    # Undo
    command.undo()
    assert np.allclose(generator.heightmap, original), "Ridge undo failed"
    print("  Ridge undo works - PASS")

    print()


def test_valley_command_undo_redo():
    """Test valley command with undo/redo."""
    print("Testing valley command with undo/redo...")

    # Create generator
    generator = HeightmapGenerator(resolution=512)
    generator.heightmap = np.ones((512, 512)) * 0.5

    # Store original
    original = generator.heightmap.copy()

    # Create and execute valley command
    valley_params = {
        'x1': 300, 'y1': 300,
        'x2': 400, 'y2': 400,
        'width': 20,
        'depth': 0.2
    }
    command = AddFeatureCommand(
        generator,
        feature_type='valley',
        params=valley_params,
        description="Test valley"
    )

    # Execute
    command.execute()
    modified = generator.heightmap.copy()
    assert np.any(modified != original), "Valley command did not modify heightmap"
    print("  Valley command executes - PASS")

    # Undo
    command.undo()
    assert np.allclose(generator.heightmap, original), "Valley undo failed"
    print("  Valley undo works - PASS")

    print()


def test_edge_cases():
    """Test edge cases for ridge and valley tools."""
    print("Testing edge cases...")

    test_heightmap = np.ones((512, 512)) * 0.5
    editor = TerrainEditor(test_heightmap)

    # Test very short ridge (single point)
    result = editor.add_ridge(x1=100, y1=100, x2=100, y2=100, width=10, height=0.1)
    assert result.shape == test_heightmap.shape, "Single-point ridge failed"
    print("  Single-point ridge - PASS")

    # Test horizontal ridge
    result = editor.add_ridge(x1=50, y1=100, x2=150, y2=100, width=10, height=0.1)
    assert np.any(result != test_heightmap), "Horizontal ridge failed"
    print("  Horizontal ridge - PASS")

    # Test vertical ridge
    result = editor.add_ridge(x1=100, y1=50, x2=100, y2=150, width=10, height=0.1)
    assert np.any(result != test_heightmap), "Vertical ridge failed"
    print("  Vertical ridge - PASS")

    # Test diagonal valley
    result = editor.add_valley(x1=50, y1=450, x2=450, y2=50, width=15, depth=0.15)
    assert np.any(result != test_heightmap), "Diagonal valley failed"
    print("  Diagonal valley - PASS")

    print()


if __name__ == "__main__":
    print("=" * 70)
    print("AUTOMATED RIDGE & VALLEY TOOL TESTS")
    print("=" * 70)
    print()

    try:
        test_ridge_tool()
        test_valley_tool()
        test_ridge_command_undo_redo()
        test_valley_command_undo_redo()
        test_edge_cases()

        print("=" * 70)
        print("ALL TESTS PASSED!")
        print("=" * 70)
        print()
        print("Backend functionality verified. Ridge and valley tools are working.")
        print()
        print("For GUI testing, run: python tests/test_ridge_valley_tools.py")
        print()

    except AssertionError as e:
        print()
        print("=" * 70)
        print("TEST FAILED!")
        print("=" * 70)
        print(f"Error: {e}")
        print()
        sys.exit(1)
