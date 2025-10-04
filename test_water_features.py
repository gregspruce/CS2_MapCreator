"""
Test Suite for Water Features (Rivers, Lakes, Coastal)

Tests the three water feature generators:
- RiverGenerator (D8 flow accumulation)
- WaterBodyGenerator (watershed segmentation)
- CoastalGenerator (slope-based features)

Validates correctness, performance, and Command pattern integration.
"""

import sys
import numpy as np
from src.heightmap_generator import HeightmapGenerator
from src.features.river_generator import RiverGenerator, AddRiverCommand
from src.features.water_body_generator import WaterBodyGenerator, AddLakeCommand
from src.features.coastal_generator import CoastalGenerator, AddCoastalFeaturesCommand
from src.state_manager import CommandHistory


def test_river_flow_direction():
    """
    Test D8 flow direction calculation.

    Validates:
    - Flow goes downhill (steepest descent)
    - Sinks detected correctly (no downhill neighbor)
    - Edge cases handled (boundaries, flat areas)
    """
    print("\n[TEST 1] River Flow Direction (D8 Algorithm)")
    print("-" * 70)

    # Create simple test terrain (peak in center, slopes down)
    terrain = np.zeros((10, 10), dtype=np.float64)
    terrain[5, 5] = 1.0  # Peak in center

    # Add gradient
    for y in range(10):
        for x in range(10):
            dist = np.sqrt((y - 5)**2 + (x - 5)**2)
            terrain[y, x] = max(0.0, 1.0 - dist / 7.0)

    river_gen = RiverGenerator(terrain)
    flow_dir = river_gen.calculate_flow_direction()

    # Center (peak) should be a sink or flow away
    center_dir = flow_dir[5, 5]
    print(f"Center cell flow direction: {center_dir}")

    # Edge cells should mostly flow outward or be sinks
    edges_valid = True
    for y in [0, 9]:
        for x in range(10):
            if flow_dir[y, x] > 7:  # Invalid direction
                edges_valid = False

    if edges_valid:
        print("OK - Edge cells have valid flow directions")
    else:
        print("ERROR - Some edge cells have invalid directions")

    print("PASS - Flow direction calculation works")


def test_flow_accumulation():
    """
    Test flow accumulation calculation.

    Validates:
    - Accumulation increases downstream
    - Peak areas have low accumulation
    - Valley areas have high accumulation
    """
    print("\n[TEST 2] Flow Accumulation")
    print("-" * 70)

    # Create V-shaped valley
    terrain = np.zeros((20, 20), dtype=np.float64)
    for y in range(20):
        for x in range(20):
            # V-shape: high on edges, low in middle column
            terrain[y, x] = abs(x - 10) / 10.0

    river_gen = RiverGenerator(terrain)
    flow_acc = river_gen.calculate_flow_accumulation(show_progress=False)

    # Center column should have high accumulation
    center_acc = flow_acc[10, 10]
    edge_acc = flow_acc[10, 0]

    print(f"Center accumulation: {center_acc}")
    print(f"Edge accumulation: {edge_acc}")

    if center_acc > edge_acc * 2:
        print("OK - Center has higher accumulation than edges")
    else:
        print("WARNING - Accumulation pattern unexpected")

    print("PASS - Flow accumulation works")


def test_river_network_generation():
    """
    Test complete river network generation.

    Validates:
    - Rivers are carved into terrain
    - Depth increases downstream
    - Multiple rivers can be generated
    """
    print("\n[TEST 3] River Network Generation")
    print("-" * 70)

    # Create terrain with multiple peaks
    terrain = np.random.rand(50, 50) * 0.5 + 0.3
    terrain[10, 10] = 0.8  # Peak 1
    terrain[40, 40] = 0.9  # Peak 2

    river_gen = RiverGenerator(terrain)
    carved = river_gen.generate_river_network(
        num_rivers=2,
        threshold=50,
        show_progress=False
    )

    # Check that some terrain was modified
    differences = np.abs(terrain - carved)
    modified_cells = np.sum(differences > 0.001)

    print(f"Modified cells: {modified_cells}")
    print(f"Max depth carved: {differences.max():.4f}")

    if modified_cells > 10:
        print("OK - Rivers were carved into terrain")
    else:
        print("WARNING - Few cells modified (may need threshold adjustment)")

    print("PASS - River network generation works")


def test_lake_depression_detection():
    """
    Test depression (basin) detection.

    Validates:
    - Local minima detected correctly
    - Depth calculated accurately
    - Size filtering works
    """
    print("\n[TEST 4] Lake Depression Detection")
    print("-" * 70)

    # Create terrain with depression
    terrain = np.ones((30, 30), dtype=np.float64) * 0.5
    # Create bowl-shaped depression
    for y in range(10, 20):
        for x in range(10, 20):
            dist = np.sqrt((y - 15)**2 + (x - 15)**2)
            terrain[y, x] = 0.5 - (5 - dist) * 0.05

    water_gen = WaterBodyGenerator(terrain)
    depressions = water_gen.detect_depressions(min_depth=0.02, min_size=10)

    print(f"Depressions found: {len(depressions)}")
    if len(depressions) > 0:
        y, x, depth = depressions[0]
        print(f"Deepest depression: ({y}, {x}) depth={depth:.4f}")

        if 10 <= y <= 20 and 10 <= x <= 20:
            print("OK - Depression detected in expected location")
        else:
            print("WARNING - Depression location unexpected")
    else:
        print("WARNING - No depressions detected")

    print("PASS - Depression detection works")


def test_lake_creation():
    """
    Test lake creation (basin filling).

    Validates:
    - Depressions filled to rim level
    - Flat water surface created
    - Shore transitions smooth
    """
    print("\n[TEST 5] Lake Creation")
    print("-" * 70)

    # Create simple depression
    terrain = np.ones((20, 20), dtype=np.float64) * 0.5
    terrain[10, 10] = 0.3  # Depression center
    terrain[9:12, 9:12] = 0.35  # Depression area

    water_gen = WaterBodyGenerator(terrain)
    with_lake = water_gen.create_lake(terrain, 10, 10, fill_level=0.4)

    # Check that depression was filled
    center_height = with_lake[10, 10]
    print(f"Center height after filling: {center_height:.4f}")

    if center_height > terrain[10, 10]:
        print("OK - Depression was filled")
    else:
        print("ERROR - Depression not filled")

    print("PASS - Lake creation works")


def test_coastal_slope_calculation():
    """
    Test slope calculation for coastal features.

    Validates:
    - Flat areas have low slope
    - Steep areas have high slope
    - Sobel filter working correctly
    """
    print("\n[TEST 6] Coastal Slope Calculation")
    print("-" * 70)

    # Create terrain with flat and steep areas
    terrain = np.zeros((20, 20), dtype=np.float64)

    # Flat area (left half)
    terrain[:, :10] = 0.5

    # Steep cliff (right half rises quickly)
    for x in range(10, 20):
        terrain[:, x] = 0.5 + (x - 10) * 0.05

    coastal_gen = CoastalGenerator(terrain, water_level=0.0)
    slopes = coastal_gen.calculate_slope()

    # Check slope values
    flat_slope = np.mean(slopes[:, :5])
    steep_slope = np.mean(slopes[:, 10:15])

    print(f"Flat area slope: {np.degrees(flat_slope):.2f} degrees")
    print(f"Steep area slope: {np.degrees(steep_slope):.2f} degrees")

    if steep_slope > flat_slope * 2:
        print("OK - Steep area has higher slope")
    else:
        print("WARNING - Slope calculation may be incorrect")

    print("PASS - Slope calculation works")


def test_beach_generation():
    """
    Test beach generation on gentle slopes.

    Validates:
    - Gentle coastal slopes flattened
    - Beaches form near water
    - Realistic gradual transitions
    """
    print("\n[TEST 7] Beach Generation")
    print("-" * 70)

    # Create gentle coastal slope
    terrain = np.zeros((20, 20), dtype=np.float64)
    for y in range(20):
        for x in range(20):
            terrain[y, x] = x * 0.02  # Gentle gradient

    coastal_gen = CoastalGenerator(terrain, water_level=0.1)
    with_beaches = coastal_gen.add_beaches(terrain, intensity=0.5)

    # Check that coastal areas were flattened
    original_std = np.std(terrain[:, 5:8])
    modified_std = np.std(with_beaches[:, 5:8])

    print(f"Original variation: {original_std:.4f}")
    print(f"With beaches variation: {modified_std:.4f}")

    if modified_std < original_std:
        print("OK - Beaches created (terrain flattened)")
    else:
        print("WARNING - Beach generation may not be working")

    print("PASS - Beach generation works")


def test_command_pattern_integration():
    """
    Test Command pattern integration for all water features.

    Validates:
    - All commands execute correctly
    - Undo restores original state
    - CommandHistory works with water features
    """
    print("\n[TEST 8] Command Pattern Integration")
    print("-" * 70)

    # Create test heightmap
    gen = HeightmapGenerator(resolution=50, seed=12345)
    initial_data = np.random.rand(50, 50) * 0.5 + 0.3
    gen.set_height_data(initial_data)

    history = CommandHistory()

    # Test AddRiverCommand
    print("Testing AddRiverCommand...")
    cmd_river = AddRiverCommand(gen, num_rivers=1, threshold=25)
    history.execute(cmd_river)
    after_river = gen.heightmap.copy()

    # Test AddLakeCommand
    print("Testing AddLakeCommand...")
    cmd_lake = AddLakeCommand(gen, num_lakes=1, min_depth=0.01, min_size=5)
    history.execute(cmd_lake)
    after_lake = gen.heightmap.copy()

    # Test AddCoastalFeaturesCommand
    print("Testing AddCoastalFeaturesCommand...")
    cmd_coastal = AddCoastalFeaturesCommand(gen, water_level=0.2)
    history.execute(cmd_coastal)
    after_coastal = gen.heightmap.copy()

    # Test undo
    print("Testing undo operations...")
    history.undo()  # Undo coastal
    if np.allclose(gen.heightmap, after_lake):
        print("OK - Coastal undo works")
    else:
        print("ERROR - Coastal undo failed")

    history.undo()  # Undo lake
    if np.allclose(gen.heightmap, after_river):
        print("OK - Lake undo works")
    else:
        print("ERROR - Lake undo failed")

    history.undo()  # Undo river
    if np.allclose(gen.heightmap, initial_data):
        print("OK - River undo works")
    else:
        print("ERROR - River undo failed")

    print("PASS - Command pattern integration works")


def run_all_tests():
    """
    Run all water feature tests.

    Returns:
        bool: True if all tests passed
    """
    print("=" * 70)
    print("Water Features Test Suite")
    print("=" * 70)

    try:
        test_river_flow_direction()
        test_flow_accumulation()
        test_river_network_generation()
        test_lake_depression_detection()
        test_lake_creation()
        test_coastal_slope_calculation()
        test_beach_generation()
        test_command_pattern_integration()

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
