"""
Quick test for state_manager.py

This verifies the undo/redo functionality works correctly.
Run: python test_state_manager.py
"""

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent / 'src'))

import numpy as np
from heightmap_generator import HeightmapGenerator
from state_manager import (
    CommandHistory,
    SetHeightDataCommand,
    SmoothCommand,
    AddCircleCommand,
    MacroCommand
)


def test_basic_undo_redo():
    """Test basic undo/redo operations."""
    print("Testing basic undo/redo...")

    # Create generator and history
    gen = HeightmapGenerator(resolution=256, height_scale=1000)
    history = CommandHistory()

    # Initial state: flat at 0.5
    initial_data = np.full((256, 256), 0.5)
    cmd1 = SetHeightDataCommand(gen, initial_data, "Set flat terrain", normalize=False)
    history.execute(cmd1)

    result = gen.get_height_data()
    print(f"  Expected: 0.5, Got min={result.min():.3f}, max={result.max():.3f}, mean={result.mean():.3f}")
    assert np.allclose(result, 0.5), f"Initial data not set correctly"
    print("OK Initial state set")

    # Add a hill
    cmd2 = AddCircleCommand(gen, 0.5, 0.5, 0.2, 0.3)
    history.execute(cmd2)

    after_hill = gen.get_height_data()
    assert not np.allclose(after_hill, 0.5), "Hill not added"
    print("OK Hill added")

    # Undo hill
    history.undo()
    assert np.allclose(gen.get_height_data(), 0.5), "Undo failed"
    print("OK Undo successful")

    # Redo hill
    history.redo()
    assert np.allclose(gen.get_height_data(), after_hill), "Redo failed"
    print("OK Redo successful")

    print("OK Basic undo/redo tests passed!\n")


def test_smooth_undo():
    """Test that smoothing can be undone."""
    print("Testing smooth undo...")

    gen = HeightmapGenerator(resolution=256)
    history = CommandHistory()

    # Create rough terrain
    rough_data = np.random.rand(256, 256)
    cmd1 = SetHeightDataCommand(gen, rough_data, "Random terrain")
    history.execute(cmd1)

    before_smooth = gen.get_height_data().copy()

    # Smooth it
    cmd2 = SmoothCommand(gen, iterations=3, kernel_size=5)
    history.execute(cmd2)

    after_smooth = gen.get_height_data()
    assert not np.allclose(before_smooth, after_smooth), "Smoothing had no effect"
    print("OK Smoothing applied")

    # Undo smooth
    history.undo()
    assert np.allclose(gen.get_height_data(), before_smooth), "Smooth undo failed"
    print("OK Smooth undone successfully\n")


def test_macro_command():
    """Test that macro commands work."""
    print("Testing macro commands...")

    gen = HeightmapGenerator(resolution=256)
    history = CommandHistory()

    # Create a macro: Set flat + Add 3 hills
    commands = [
        SetHeightDataCommand(gen, np.full((256, 256), 0.5), "Flat", normalize=False),
        AddCircleCommand(gen, 0.3, 0.3, 0.1, 0.2),
        AddCircleCommand(gen, 0.7, 0.3, 0.1, 0.2),
        AddCircleCommand(gen, 0.5, 0.7, 0.1, 0.2),
    ]

    macro = MacroCommand(commands, "Create 3-hill terrain")
    history.execute(macro)

    after_macro = gen.get_height_data()
    print("OK Macro executed")

    # Undo entire macro in one go
    history.undo()
    assert history.can_undo() == False, "Should have no more undo history"
    print("OK Macro undone as single operation")

    # Redo entire macro
    history.redo()
    assert np.allclose(gen.get_height_data(), after_macro), "Macro redo failed"
    print("OK Macro redone successfully\n")


def test_memory_tracking():
    """Test memory usage tracking."""
    print("Testing memory tracking...")

    gen = HeightmapGenerator(resolution=1024)  # Larger for memory test
    history = CommandHistory()

    # Execute several commands
    for i in range(5):
        data = np.random.rand(1024, 1024)
        cmd = SetHeightDataCommand(gen, data, f"Terrain {i+1}")
        history.execute(cmd)

    # Check memory usage
    mem = history.get_memory_usage()
    print(f"  Commands in history: {mem['undo_commands']}")
    print(f"  Memory used: {mem['total_memory_mb']:.2f} MB")

    assert mem['undo_commands'] == 5, "Wrong command count"
    assert mem['total_memory_mb'] > 0, "No memory tracked"
    print("OK Memory tracking works\n")


if __name__ == "__main__":
    print("=" * 50)
    print("State Manager Test Suite")
    print("=" * 50)
    print()

    try:
        test_basic_undo_redo()
        test_smooth_undo()
        test_macro_command()
        test_memory_tracking()

        print("=" * 50)
        print("OK ALL TESTS PASSED!")
        print("=" * 50)

    except AssertionError as e:
        print(f"\nX TEST FAILED: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\nX ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
