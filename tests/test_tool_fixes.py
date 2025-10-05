"""
Test script to verify tool fixes.

Tests:
1. Brush tools (raise, lower, smooth, flatten)
2. Feature tools (hill, depression)
3. Coastal generation with proper water level
"""

import numpy as np
from src.features.terrain_editor import TerrainEditor, BrushCommand, AddFeatureCommand
from src.features.coastal_generator import CoastalGenerator
from src.heightmap_generator import HeightmapGenerator
from src.noise_generator import NoiseGenerator

def test_brush_tools():
    """Test brush tool implementation."""
    print("\n=== Testing Brush Tools ===")

    # Generate test terrain
    noise_gen = NoiseGenerator()
    heightmap = noise_gen.generate_perlin(
        resolution=512,
        scale=200.0,
        octaves=6,
        persistence=0.5,
        lacunarity=2.0,
        show_progress=False
    )

    # Create editor
    editor = TerrainEditor(heightmap)

    # Test raise tool
    print("Testing raise tool...")
    result = editor.apply_brush(x=256, y=256, radius=50, strength=0.5, operation='raise')
    assert result.shape == heightmap.shape, "Raise tool changed shape"
    assert not np.array_equal(result, heightmap), "Raise tool had no effect"
    print("[OK] Raise tool works")

    # Test lower tool
    print("Testing lower tool...")
    result = editor.apply_brush(x=256, y=256, radius=50, strength=0.5, operation='lower')
    assert not np.array_equal(result, heightmap), "Lower tool had no effect"
    print("[OK] Lower tool works")

    # Test smooth tool
    print("Testing smooth tool...")
    result = editor.apply_brush(x=256, y=256, radius=50, strength=0.5, operation='smooth')
    assert not np.array_equal(result, heightmap), "Smooth tool had no effect"
    print("[OK] Smooth tool works")

    # Test flatten tool
    print("Testing flatten tool...")
    result = editor.apply_brush(x=256, y=256, radius=50, strength=0.5, operation='flatten')
    assert not np.array_equal(result, heightmap), "Flatten tool had no effect"
    print("[OK] Flatten tool works")

    print("All brush tools passed!")

def test_feature_tools():
    """Test feature tool implementation."""
    print("\n=== Testing Feature Tools ===")

    # Generate test terrain
    noise_gen = NoiseGenerator()
    heightmap = noise_gen.generate_perlin(
        resolution=512,
        scale=200.0,
        octaves=6,
        persistence=0.5,
        lacunarity=2.0,
        show_progress=False
    )

    # Create editor
    editor = TerrainEditor(heightmap)

    # Test hill
    print("Testing hill feature...")
    result = editor.add_hill(x=256, y=256, radius=50, height=0.2)
    assert result.shape == heightmap.shape, "Hill changed shape"
    assert not np.array_equal(result, heightmap), "Hill had no effect"
    # Check that terrain was modified (may be clipped at 1.0, so check difference)
    diff = np.sum(np.abs(result - heightmap))
    assert diff > 0, "Hill had no effect on terrain"
    print("[OK] Hill feature works")

    # Test depression
    print("Testing depression feature...")
    result = editor.add_depression(x=256, y=256, radius=50, depth=0.2)
    assert not np.array_equal(result, heightmap), "Depression had no effect"
    print("[OK] Depression feature works")

    # Test ridge
    print("Testing ridge feature...")
    result = editor.add_ridge(x1=100, y1=100, x2=400, y2=400, width=20, height=0.2)
    assert not np.array_equal(result, heightmap), "Ridge had no effect"
    print("[OK] Ridge feature works")

    # Test valley
    print("Testing valley feature...")
    result = editor.add_valley(x1=100, y1=400, x2=400, y2=100, width=20, depth=0.2)
    assert not np.array_equal(result, heightmap), "Valley had no effect"
    print("[OK] Valley feature works")

    print("All feature tools passed!")

def test_coastal_generation():
    """Test coastal generation with proper water level."""
    print("\n=== Testing Coastal Generation ===")

    # Generate test terrain
    noise_gen = NoiseGenerator()
    heightmap = noise_gen.generate_perlin(
        resolution=512,
        scale=200.0,
        octaves=6,
        persistence=0.5,
        lacunarity=2.0,
        show_progress=False
    )

    # Get terrain statistics
    min_height = float(np.min(heightmap))
    max_height = float(np.max(heightmap))
    height_range = max_height - min_height

    print(f"Terrain range: {min_height:.3f} to {max_height:.3f}")
    print(f"Height range: {height_range:.3f}")

    # Calculate proper water level (20% above minimum)
    water_level = min_height + (height_range * 0.2)
    print(f"Water level: {water_level:.3f}")

    # Generate coastal features
    coastal_gen = CoastalGenerator(heightmap, water_level=water_level)
    result = coastal_gen.generate_coastal_features(
        add_beaches=True,
        add_cliffs=True,
        beach_intensity=0.5,
        cliff_intensity=0.5,
        show_progress=False
    )

    # Verify result
    assert result.shape == heightmap.shape, "Coastal generation changed shape"

    # Check that not all terrain is at same height (the bug we fixed)
    unique_values = len(np.unique(result))
    print(f"Unique height values after coastal generation: {unique_values}")
    assert unique_values > 100, f"Map is too uniform (only {unique_values} unique values)"

    # Check that some modification occurred
    diff = np.sum(np.abs(result - heightmap))
    print(f"Total modification: {diff:.2f}")
    assert diff > 0, "Coastal generation had no effect"

    print("[OK] Coastal generation works correctly!")

def test_command_pattern():
    """Test undo/redo via Command pattern."""
    print("\n=== Testing Command Pattern ===")

    # Create generator
    gen = HeightmapGenerator(resolution=512)
    noise_gen = NoiseGenerator()
    gen.heightmap = noise_gen.generate_perlin(
        resolution=512,
        scale=200.0,
        octaves=6,
        persistence=0.5,
        lacunarity=2.0,
        show_progress=False
    )

    original = gen.heightmap.copy()

    # Create and execute brush command
    cmd = BrushCommand(
        gen,
        x=256,
        y=256,
        radius=50,
        strength=0.5,
        operation='raise',
        description="Test brush"
    )
    cmd.execute()
    modified = gen.heightmap.copy()

    assert not np.array_equal(modified, original), "Command had no effect"
    print("[OK] Command execution works")

    # Test undo
    cmd.undo()
    undone = gen.heightmap.copy()

    assert np.array_equal(undone, original), "Undo didn't restore original"
    print("[OK] Command undo works")

    print("Command pattern passed!")

if __name__ == "__main__":
    print("Testing Tool Fixes...")
    print("=" * 50)

    try:
        test_brush_tools()
        test_feature_tools()
        test_coastal_generation()
        test_command_pattern()

        print("\n" + "=" * 50)
        print("ALL TESTS PASSED! [OK]")
        print("=" * 50)

    except Exception as e:
        print(f"\n[FAIL] TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        exit(1)
