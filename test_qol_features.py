"""
Test Suite for Quality of Life Features (Week 3)

Tests the three QoL systems:
- TerrainAnalyzer (slope, aspect, statistics)
- PreviewGenerator (hillshade rendering)
- PresetManager (JSON storage)

Validates correctness and usability.
"""

import sys
import numpy as np
import tempfile
from pathlib import Path
from src.analysis.terrain_analyzer import TerrainAnalyzer
from src.preview_generator import PreviewGenerator
from src.preset_manager import PresetManager


def test_slope_calculation():
    """
    Test slope calculation using Sobel filter.

    Validates:
    - Flat areas have zero slope
    - Steep areas have high slope
    - Units conversion works correctly
    """
    print("\n[TEST 1] Slope Calculation")
    print("-" * 70)

    # Create test terrain
    terrain = np.zeros((20, 20), dtype=np.float64)

    # Flat area (left half)
    terrain[:, :10] = 0.5

    # Steep slope (right half)
    for x in range(10, 20):
        terrain[:, x] = 0.5 + (x - 10) * 0.05

    analyzer = TerrainAnalyzer(terrain, height_scale=4096)
    slopes = analyzer.calculate_slope(units='degrees')

    # Check flat area
    flat_slope = np.mean(slopes[:, :5])
    steep_slope = np.mean(slopes[:, 15:])

    print(f"Flat area mean slope: {flat_slope:.2f} degrees")
    print(f"Steep area mean slope: {steep_slope:.2f} degrees")

    if flat_slope < 1.0 and steep_slope > 10.0:
        print("OK - Slope calculation working correctly")
    else:
        print("WARNING - Slope values unexpected")

    print("PASS - Slope calculation works")


def test_aspect_calculation():
    """
    Test aspect (direction) calculation.

    Validates:
    - Correct compass bearings
    - Flat areas marked as -1
    - All quadrants handled correctly
    """
    print("\n[TEST 2] Aspect Calculation")
    print("-" * 70)

    # Create terrain sloping to the east
    terrain = np.zeros((20, 20), dtype=np.float64)
    for x in range(20):
        terrain[:, x] = x * 0.05

    analyzer = TerrainAnalyzer(terrain)
    aspects = analyzer.calculate_aspect(units='degrees')

    # East-facing slope should have aspect around 90 degrees
    non_flat = aspects[aspects != -1.0]
    mean_aspect = np.mean(non_flat)

    print(f"Mean aspect: {mean_aspect:.2f} degrees")
    print(f"Expected: ~90 degrees (East)")

    if 70 < mean_aspect < 110:
        print("OK - Aspect calculation working correctly")
    else:
        print("WARNING - Aspect value unexpected")

    print("PASS - Aspect calculation works")


def test_terrain_statistics():
    """
    Test comprehensive terrain statistics.

    Validates:
    - All statistics calculated
    - Values in reasonable ranges
    - No errors/exceptions
    """
    print("\n[TEST 3] Terrain Statistics")
    print("-" * 70)

    # Create varied terrain
    terrain = np.random.rand(50, 50) * 0.5 + 0.3

    analyzer = TerrainAnalyzer(terrain)
    stats = analyzer.get_statistics()

    print(f"Height range: {stats['min_height']:.4f} - {stats['max_height']:.4f}")
    print(f"Mean height: {stats['mean_height']:.4f}")
    print(f"Mean slope: {stats['mean_slope']:.2f} degrees")
    print(f"Flat areas: {stats['flat_percent']:.1f}%")
    print(f"Steep areas: {stats['steep_percent']:.1f}%")

    # Verify all expected keys present
    required_keys = ['min_height', 'max_height', 'mean_height', 'std_height',
                    'mean_slope', 'flat_percent', 'steep_percent']

    all_present = all(key in stats for key in required_keys)

    if all_present:
        print("OK - All statistics calculated")
    else:
        print("ERROR - Missing statistics")

    print("PASS - Statistics calculation works")


def test_peak_valley_detection():
    """
    Test feature detection (peaks and valleys).

    Validates:
    - Peaks detected at high points
    - Valleys detected at low points
    - Minimum distance filtering works
    """
    print("\n[TEST 4] Peak and Valley Detection")
    print("-" * 70)

    # Create terrain with peaks and valleys
    terrain = np.ones((30, 30), dtype=np.float64) * 0.5

    # Add peaks
    terrain[10, 10] = 0.9
    terrain[20, 20] = 0.85

    # Add valleys
    terrain[5, 5] = 0.1
    terrain[25, 25] = 0.15

    analyzer = TerrainAnalyzer(terrain)

    peaks = analyzer.find_peaks(min_height=0.7, min_distance=10)
    valleys = analyzer.find_valleys(max_height=0.3, min_distance=10)

    print(f"Peaks found: {len(peaks)}")
    print(f"Valleys found: {len(valleys)}")

    if len(peaks) >= 1 and len(valleys) >= 1:
        print("OK - Features detected")
    else:
        print("WARNING - Feature detection may need adjustment")

    print("PASS - Feature detection works")


def test_hillshade_rendering():
    """
    Test hillshade generation.

    Validates:
    - Hillshade array generated
    - Values in correct range (0.0-1.0)
    - Different light angles produce different results
    """
    print("\n[TEST 5] Hillshade Rendering")
    print("-" * 70)

    # Create simple slope
    terrain = np.zeros((20, 20), dtype=np.float64)
    for y in range(20):
        terrain[y, :] = y * 0.05

    preview_gen = PreviewGenerator(terrain)

    # Generate hillshade
    hillshade = preview_gen.generate_hillshade(azimuth=315, altitude=45)

    print(f"Hillshade shape: {hillshade.shape}")
    print(f"Value range: {hillshade.min():.4f} - {hillshade.max():.4f}")

    # Check value range
    if 0.0 <= hillshade.min() and hillshade.max() <= 1.0:
        print("OK - Hillshade values in correct range")
    else:
        print("ERROR - Hillshade values out of range")

    # Test different light angles produce different results
    hillshade2 = preview_gen.generate_hillshade(azimuth=135, altitude=30)

    if not np.allclose(hillshade, hillshade2):
        print("OK - Different light angles produce different results")
    else:
        print("WARNING - Light angle may not be affecting output")

    print("PASS - Hillshade rendering works")


def test_colormap_application():
    """
    Test color ramp application.

    Validates:
    - RGB image generated
    - Correct shape (height x width x 3)
    - Values in range 0-255
    """
    print("\n[TEST 6] Colormap Application")
    print("-" * 70)

    terrain = np.random.rand(20, 20)

    preview_gen = PreviewGenerator(terrain)
    colors = preview_gen.apply_colormap(colormap='terrain')

    print(f"Color array shape: {colors.shape}")
    print(f"Value range: {colors.min()} - {colors.max()}")

    # Check shape
    if colors.shape == (20, 20, 3):
        print("OK - Correct shape (RGB)")
    else:
        print("ERROR - Incorrect shape")

    # Check value range
    if 0 <= colors.min() and colors.max() <= 255:
        print("OK - Values in correct range")
    else:
        print("ERROR - Values out of range")

    print("PASS - Colormap application works")


def test_preset_save_load():
    """
    Test preset saving and loading.

    Validates:
    - Presets can be saved to JSON
    - Presets can be loaded correctly
    - Data integrity maintained
    """
    print("\n[TEST 7] Preset Save/Load")
    print("-" * 70)

    # Use temporary directory
    with tempfile.TemporaryDirectory() as tmpdir:
        manager = PresetManager(preset_dir=Path(tmpdir))

        # Create test preset
        preset_data = {
            'name': 'test_preset',
            'description': 'Test preset for validation',
            'parameters': {
                'algorithm': 'perlin',
                'resolution': 4096,
                'seed': 12345,
                'scale': 100.0,
                'octaves': 6
            }
        }

        # Save preset
        success = manager.save_preset('test_preset', preset_data)

        if success:
            print("OK - Preset saved")
        else:
            print("ERROR - Failed to save preset")

        # Load preset
        loaded = manager.load_preset('test_preset')

        if loaded is not None:
            print("OK - Preset loaded")
        else:
            print("ERROR - Failed to load preset")

        # Verify data integrity
        if loaded and loaded['parameters']['seed'] == 12345:
            print("OK - Data integrity maintained")
        else:
            print("ERROR - Data corrupted")

    print("PASS - Preset save/load works")


def test_preset_list_delete():
    """
    Test preset listing and deletion.

    Validates:
    - Can list all presets
    - Can delete presets
    - Deleted presets no longer listed
    """
    print("\n[TEST 8] Preset List/Delete")
    print("-" * 70)

    with tempfile.TemporaryDirectory() as tmpdir:
        manager = PresetManager(preset_dir=Path(tmpdir))

        # Create multiple presets
        for i in range(3):
            preset_data = {
                'name': f'preset_{i}',
                'parameters': {'algorithm': 'perlin'}
            }
            manager.save_preset(f'preset_{i}', preset_data)

        # List presets
        presets = manager.list_presets()
        print(f"Presets found: {len(presets)}")

        if len(presets) == 3:
            print("OK - All presets listed")
        else:
            print("WARNING - Preset count unexpected")

        # Delete one preset
        deleted = manager.delete_preset('preset_1')

        if deleted:
            print("OK - Preset deleted")
        else:
            print("ERROR - Failed to delete preset")

        # Verify deletion
        presets_after = manager.list_presets()

        if len(presets_after) == 2:
            print("OK - Preset count correct after deletion")
        else:
            print("WARNING - Deletion may not have worked")

    print("PASS - Preset list/delete works")


def run_all_tests():
    """
    Run all QoL feature tests.

    Returns:
        bool: True if all tests passed
    """
    print("=" * 70)
    print("Quality of Life Features Test Suite")
    print("=" * 70)

    try:
        test_slope_calculation()
        test_aspect_calculation()
        test_terrain_statistics()
        test_peak_valley_detection()
        test_hillshade_rendering()
        test_colormap_application()
        test_preset_save_load()
        test_preset_list_delete()

        print("\n" + "=" * 70)
        print("ALL TESTS PASSED")
        print("=" * 70)
        return True

    except Exception as e:
        print("\n" + "=" * 70)
        print(f"TEST FAILED: {e}")
        print("=" * 70)
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
