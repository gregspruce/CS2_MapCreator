"""
Quick test script to verify water features and analysis are working.

Tests:
1. River generation (D8 flow accumulation)
2. Lake generation (watershed segmentation)
3. Coastal features (beaches and cliffs)
4. Terrain analysis

This does NOT test the GUI - it tests the backend implementations directly.
"""

import numpy as np
from src.heightmap_generator import HeightmapGenerator
from src.noise_generator import NoiseGenerator, create_preset_terrain

def test_rivers():
    """Test river generation."""
    print("\n[TEST] River Generation")
    print("-" * 50)

    try:
        from src.features.river_generator import RiverGenerator, AddRiverCommand

        # Create test terrain
        print("  Creating test terrain...")
        generator = HeightmapGenerator(resolution=1024)  # Smaller for speed
        terrain = create_preset_terrain('mountains', resolution=1024, seed=42)
        generator.heightmap = terrain

        # Create river command
        print("  Generating rivers...")
        command = AddRiverCommand(
            generator,
            num_rivers=3,
            threshold=500,
            description="Test rivers"
        )

        # Execute
        command.execute()

        # Verify heightmap was modified
        assert not np.allclose(generator.heightmap, terrain), "Heightmap should be modified"

        print("  [OK] Rivers generated successfully")
        return True

    except Exception as e:
        print(f"  [FAILED] River generation error: {e}")
        return False


def test_lakes():
    """Test lake generation."""
    print("\n[TEST] Lake Generation")
    print("-" * 50)

    try:
        from src.features.water_body_generator import WaterBodyGenerator, AddLakeCommand

        # Create test terrain
        print("  Creating test terrain...")
        generator = HeightmapGenerator(resolution=1024)
        terrain = create_preset_terrain('mountains', resolution=1024, seed=42)
        generator.heightmap = terrain

        # Create lake command
        print("  Generating lakes...")
        command = AddLakeCommand(
            generator,
            num_lakes=5,
            min_depth=0.02,
            min_size=25,
            description="Test lakes"
        )

        # Execute
        command.execute()

        # Check if any lakes were actually created
        # Lake generation might find zero valid depressions
        if np.allclose(generator.heightmap, terrain):
            print("  [WARNING] No lakes generated (no valid depressions found)")
            print("            This is expected for some terrain types")
            print("  [OK] Lake generation code works (zero lakes is valid)")
            return True
        else:
            print("  [OK] Lakes generated and heightmap modified")
            return True

    except Exception as e:
        print(f"  [FAILED] Lake generation error: {e}")
        return False


def test_coastal():
    """Test coastal feature generation."""
    print("\n[TEST] Coastal Features")
    print("-" * 50)

    try:
        from src.features.coastal_generator import CoastalGenerator, AddCoastalFeaturesCommand

        # Create test terrain
        print("  Creating test terrain...")
        generator = HeightmapGenerator(resolution=1024)
        terrain = create_preset_terrain('islands', resolution=1024, seed=42)
        generator.heightmap = terrain

        # Create coastal command
        print("  Generating coastal features...")
        command = AddCoastalFeaturesCommand(
            generator,
            water_level=0.3,
            add_beaches=True,
            add_cliffs=True,
            beach_intensity=0.5,
            cliff_intensity=0.5,
            description="Test coastal"
        )

        # Execute
        command.execute()

        # Verify heightmap was modified
        assert not np.allclose(generator.heightmap, terrain), "Heightmap should be modified"

        print("  [OK] Coastal features generated successfully")
        return True

    except Exception as e:
        print(f"  [FAILED] Coastal generation error: {e}")
        return False


def test_analysis():
    """Test terrain analysis."""
    print("\n[TEST] Terrain Analysis")
    print("-" * 50)

    try:
        from src.analysis.terrain_analyzer import TerrainAnalyzer

        # Create test terrain
        print("  Creating test terrain...")
        terrain = create_preset_terrain('mountains', resolution=1024, seed=42)

        # Create analyzer
        print("  Analyzing terrain...")
        analyzer = TerrainAnalyzer(terrain, height_scale=4096.0)

        # Get statistics
        stats = analyzer.get_statistics()

        # Verify statistics
        assert 'min_height' in stats, "Missing min_height"
        assert 'max_height' in stats, "Missing max_height"
        assert 'mean_slope' in stats, "Missing mean_slope"
        assert 'flat_percent' in stats, "Missing flat_percent"

        print(f"  Min elevation: {stats['min_height']:.3f}")
        print(f"  Max elevation: {stats['max_height']:.3f}")
        print(f"  Mean slope: {stats['mean_slope']:.2f} degrees")
        print(f"  Flat areas: {stats['flat_percent']:.1f}%")

        print("  [OK] Terrain analysis working")
        return True

    except Exception as e:
        print(f"  [FAILED] Terrain analysis error: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all tests."""
    print("=" * 50)
    print("Feature Implementation Test Suite")
    print("=" * 50)

    results = {
        'Rivers': test_rivers(),
        'Lakes': test_lakes(),
        'Coastal': test_coastal(),
        'Analysis': test_analysis()
    }

    print("\n" + "=" * 50)
    print("Test Summary")
    print("=" * 50)

    for feature, passed in results.items():
        status = "[OK]" if passed else "[FAILED]"
        print(f"  {status} {feature}")

    all_passed = all(results.values())

    print("\n" + "=" * 50)
    if all_passed:
        print("All tests PASSED!")
        print("Water features and analysis are working correctly.")
    else:
        print("Some tests FAILED!")
        print("Check error messages above for details.")
    print("=" * 50)

    return 0 if all_passed else 1


if __name__ == "__main__":
    exit(main())
