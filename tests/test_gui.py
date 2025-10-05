"""
GUI Test Suite for CS2 Heightmap Generator

Basic tests to verify GUI components work correctly.

Note: GUI testing is limited - these tests verify component creation
and basic functionality without requiring full UI interaction.

For full testing, use manual testing checklist:
1. Launch GUI (python gui_main.py)
2. Generate terrain with different presets
3. Adjust parameters and verify preview updates
4. Test zoom/pan on preview
5. Test undo/redo (once operations are wired up)
6. Test save/load functionality
"""

import sys
import numpy as np


def test_gui_imports():
    """
    Test that all GUI modules import correctly.

    Validates:
    - All GUI files present
    - No import errors
    - Dependencies available (Tkinter, PIL, etc.)
    """
    print("\n[TEST 1] GUI Module Imports")
    print("-" * 70)

    try:
        from src.gui import HeightmapGUI
        print("OK - HeightmapGUI imported")
    except ImportError as e:
        print(f"ERROR - Failed to import HeightmapGUI: {e}")
        return False

    try:
        from src.gui.preview_canvas import PreviewCanvas
        print("OK - PreviewCanvas imported")
    except ImportError as e:
        print(f"ERROR - Failed to import PreviewCanvas: {e}")
        return False

    try:
        from src.gui.parameter_panel import ParameterPanel
        print("OK - ParameterPanel imported")
    except ImportError as e:
        print(f"ERROR - Failed to import ParameterPanel: {e}")
        return False

    try:
        from src.gui.tool_palette import ToolPalette
        print("OK - ToolPalette imported")
    except ImportError as e:
        print(f"ERROR - Failed to import ToolPalette: {e}")
        return False

    print("PASS - All GUI modules import successfully")
    return True


def test_gui_dependencies():
    """
    Test that required GUI dependencies are available.

    Dependencies:
    - Tkinter (Python stdlib)
    - PIL (Pillow)
    - NumPy
    """
    print("\n[TEST 2] GUI Dependencies")
    print("-" * 70)

    # Test Tkinter
    try:
        import tkinter as tk
        print("OK - Tkinter available")
    except ImportError:
        print("ERROR - Tkinter not available (Python stdlib issue)")
        return False

    # Test PIL
    try:
        from PIL import Image, ImageTk
        print("OK - PIL (Pillow) available")
    except ImportError:
        print("ERROR - PIL not available (pip install Pillow)")
        return False

    # Test NumPy
    try:
        import numpy
        print("OK - NumPy available")
    except ImportError:
        print("ERROR - NumPy not available (pip install numpy)")
        return False

    print("PASS - All GUI dependencies available")
    return True


def test_backend_integration():
    """
    Test that GUI can access backend components.

    Validates:
    - HeightmapGenerator
    - NoiseGenerator
    - PreviewGenerator
    - PresetManager
    - CommandHistory
    """
    print("\n[TEST 3] Backend Integration")
    print("-" * 70)

    try:
        from src.heightmap_generator import HeightmapGenerator
        gen = HeightmapGenerator(resolution=512)
        print("OK - HeightmapGenerator accessible")
    except Exception as e:
        print(f"ERROR - HeightmapGenerator failed: {e}")
        return False

    try:
        from src.noise_generator import NoiseGenerator
        noise_gen = NoiseGenerator()
        print("OK - NoiseGenerator accessible")
    except Exception as e:
        print(f"ERROR - NoiseGenerator failed: {e}")
        return False

    try:
        from src.preview_generator import PreviewGenerator
        heightmap = np.random.rand(256, 256)
        preview_gen = PreviewGenerator(heightmap)
        print("OK - PreviewGenerator accessible")
    except Exception as e:
        print(f"ERROR - PreviewGenerator failed: {e}")
        return False

    try:
        from src.preset_manager import PresetManager
        preset_mgr = PresetManager()
        print("OK - PresetManager accessible")
    except Exception as e:
        print(f"ERROR - PresetManager failed: {e}")
        return False

    try:
        from src.state_manager import CommandHistory
        history = CommandHistory()
        print("OK - CommandHistory accessible")
    except Exception as e:
        print(f"ERROR - CommandHistory failed: {e}")
        return False

    print("PASS - All backend components accessible")
    return True


def test_gui_creation():
    """
    Test that GUI window can be created (without displaying).

    Note: Creates window but doesn't call mainloop(),
    so it won't actually display.
    """
    print("\n[TEST 4] GUI Window Creation")
    print("-" * 70)

    try:
        from src.gui import HeightmapGUI
        import tkinter as tk

        # Create GUI instance (but don't run mainloop)
        app = HeightmapGUI()

        # Verify components exist
        assert hasattr(app, 'preview'), "Missing preview canvas"
        assert hasattr(app, 'param_panel'), "Missing parameter panel"
        assert hasattr(app, 'tool_palette'), "Missing tool palette"
        assert hasattr(app, 'heightmap'), "Missing heightmap data"

        print("OK - GUI window created successfully")
        print("OK - All components initialized")

        # Destroy window
        app.destroy()

        print("PASS - GUI window creation successful")
        return True

    except Exception as e:
        print(f"ERROR - GUI window creation failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_preview_generation():
    """
    Test that preview images can be generated.

    Validates:
    - Preview generation works
    - Hillshade rendering works
    - PIL image creation works
    """
    print("\n[TEST 5] Preview Image Generation")
    print("-" * 70)

    try:
        from src.preview_generator import PreviewGenerator
        from PIL import Image
        import numpy as np

        # Create test heightmap
        heightmap = np.random.rand(512, 512)

        # Generate preview
        preview_gen = PreviewGenerator(heightmap)

        # Generate hillshade
        hillshade = preview_gen.generate_hillshade(
            azimuth=315,
            altitude=45
        )

        # Apply colormap
        colored = preview_gen.apply_colormap(colormap='terrain')

        # Blend
        blended_array = preview_gen.blend_hillshade_with_colors(
            hillshade=hillshade,
            colors=colored,
            blend_factor=0.6
        )

        # Convert to PIL Image
        preview_image = Image.fromarray(blended_array)

        # Verify it's a PIL Image
        assert isinstance(preview_image, Image.Image), "Preview is not a PIL Image"
        assert preview_image.size == (512, 512), "Preview has wrong size"

        print("OK - Preview generated successfully")
        print(f"OK - Preview size: {preview_image.size}")
        print(f"OK - Preview mode: {preview_image.mode}")

        print("PASS - Preview generation successful")
        return True

    except Exception as e:
        print(f"ERROR - Preview generation failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def run_all_tests():
    """
    Run all GUI tests.

    Returns:
        bool: True if all tests passed
    """
    print("=" * 70)
    print("GUI Test Suite")
    print("=" * 70)

    tests = [
        test_gui_imports,
        test_gui_dependencies,
        test_backend_integration,
        test_gui_creation,
        test_preview_generation
    ]

    results = []
    for test in tests:
        try:
            result = test()
            results.append(result)
        except Exception as e:
            print(f"\nERROR - Test crashed: {e}")
            import traceback
            traceback.print_exc()
            results.append(False)

    print("\n" + "=" * 70)
    if all(results):
        print("ALL GUI TESTS PASSED")
        print("=" * 70)
        return True
    else:
        print(f"SOME GUI TESTS FAILED ({sum(results)}/{len(results)} passed)")
        print("=" * 70)
        return False


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
