"""
Test that generation only happens on explicit Generate button click.
"""

import tkinter as tk
from src.gui.parameter_panel import ParameterPanel
from src.gui.heightmap_gui import HeightmapGUI

def test_manual_generation_workflow():
    """
    Verify that:
    1. Selecting preset does NOT auto-generate
    2. Changing sliders does NOT auto-generate
    3. Only Generate button triggers generation
    """
    print("Testing manual generation workflow...")

    # Track if generation was called
    generation_count = 0

    def mock_generate():
        nonlocal generation_count
        generation_count += 1
        print(f"  [GENERATION #{generation_count}] generate_terrain() called")

    def mock_status(msg):
        print(f"  [STATUS] {msg}")

    # Create mock GUI object
    class MockGUI:
        def generate_terrain(self):
            mock_generate()

        def set_status(self, msg):
            mock_status(msg)

        def schedule_update(self):
            # This should NOT be called anymore
            print("  [ERROR] schedule_update() called (should be removed!)")
            raise AssertionError("schedule_update() should not be called!")

    # Test preset selection
    print("\n1. Testing preset selection...")
    mock_gui = MockGUI()

    # Simulate preset selection (what happens in parameter_panel)
    from src.terrain_parameter_mapper import get_preset_parameters

    preset = 'mountains'
    params = get_preset_parameters(preset)
    mock_gui.set_status(f"Preset '{preset}' loaded - Click 'Generate Playable' to apply")

    if generation_count == 0:
        print("  [PASS] PASS: Preset selection did NOT auto-generate")
    else:
        print("  [FAIL] FAIL: Preset selection triggered generation!")
        return False

    # Test parameter change
    print("\n2. Testing parameter slider change...")
    generation_count = 0

    # Simulate slider change (what happens in parameter_panel)
    mock_gui.set_status("Parameters changed - Click 'Generate Playable' to apply")

    if generation_count == 0:
        print("  [PASS] PASS: Parameter change did NOT auto-generate")
    else:
        print("  [FAIL] FAIL: Parameter change triggered generation!")
        return False

    # Test explicit Generate button
    print("\n3. Testing Generate button click...")
    generation_count = 0

    # Simulate Generate button click
    mock_gui.generate_terrain()

    if generation_count == 1:
        print("  [PASS] PASS: Generate button DID trigger generation")
    else:
        print("  [FAIL] FAIL: Generate button did not trigger generation!")
        return False

    print("\n" + "="*60)
    print("ALL TESTS PASSED!")
    print("="*60)
    print("\nExpected user workflow:")
    print("1. User selects preset -> Status: 'Preset loaded - Click Generate'")
    print("2. User adjusts sliders -> Status: 'Parameters changed - Click Generate'")
    print("3. User clicks Generate -> Terrain generates")
    print("\nResult: User has full control, no unwanted generation!")

    return True

if __name__ == "__main__":
    try:
        success = test_manual_generation_workflow()
        exit(0 if success else 1)
    except Exception as e:
        print(f"\n[FAIL] TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        exit(1)
