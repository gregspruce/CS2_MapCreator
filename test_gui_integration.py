"""
Quick smoke test for GUI integration fixes.

Tests that:
1. GUI can be imported without errors
2. ProgressDialog API is used correctly
3. Pipeline integration is properly set up
"""

import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

def test_imports():
    """Test that all GUI modules can be imported."""
    print("Testing imports...")
    try:
        from src.gui.heightmap_gui import HeightmapGUI
        from src.gui.progress_dialog import ProgressDialog
        from src.gui.pipeline_results_dialog import show_results_dialog
        from src.generation.pipeline import TerrainGenerationPipeline
        print("[OK] All imports successful")
        return True
    except Exception as e:
        print(f"[FAIL] Import failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_progress_dialog_api():
    """Test ProgressDialog API signature."""
    print("\nTesting ProgressDialog API...")
    try:
        from src.gui.progress_dialog import ProgressDialog
        import inspect

        # Get __init__ signature
        sig = inspect.signature(ProgressDialog.__init__)
        params = list(sig.parameters.keys())

        # Should only have: self, parent, title
        expected_params = ['self', 'parent', 'title']

        if params == expected_params:
            print(f"[OK] ProgressDialog API correct: {params}")
            return True
        else:
            print(f"[FAIL] ProgressDialog API mismatch!")
            print(f"  Expected: {expected_params}")
            print(f"  Got: {params}")
            return False
    except Exception as e:
        print(f"[FAIL] ProgressDialog API test failed: {e}")
        return False

def test_gui_has_error_handler():
    """Test that HeightmapGUI has _on_generation_error method."""
    print("\nTesting error handler presence...")
    try:
        from src.gui.heightmap_gui import HeightmapGUI

        if hasattr(HeightmapGUI, '_on_generation_error'):
            print("[OK] _on_generation_error method exists")
            return True
        else:
            print("[FAIL] _on_generation_error method missing!")
            return False
    except Exception as e:
        print(f"[FAIL] Error handler test failed: {e}")
        return False

def test_pipeline_integration():
    """Test that pipeline can be instantiated."""
    print("\nTesting pipeline integration...")
    try:
        from src.generation.pipeline import TerrainGenerationPipeline

        # Try to create pipeline (don't run it, just test init)
        pipeline = TerrainGenerationPipeline(
            resolution=512,  # Small for fast init
            map_size_meters=14336.0,
            seed=42
        )

        print("[OK] Pipeline instantiation successful")
        return True
    except Exception as e:
        print(f"[FAIL] Pipeline instantiation failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Run all smoke tests."""
    print("="*60)
    print("GUI Integration Smoke Tests")
    print("="*60)

    tests = [
        test_imports,
        test_progress_dialog_api,
        test_gui_has_error_handler,
        test_pipeline_integration
    ]

    results = []
    for test in tests:
        try:
            result = test()
            results.append(result)
        except Exception as e:
            print(f"\n[FAIL] Test crashed: {e}")
            import traceback
            traceback.print_exc()
            results.append(False)

    print("\n" + "="*60)
    print(f"Results: {sum(results)}/{len(results)} tests passed")
    print("="*60)

    if all(results):
        print("\n[PASS] All smoke tests PASSED - GUI integration looks good!")
        print("\nNext step: Launch GUI and test terrain generation manually:")
        print("  python src/main.py")
        return 0
    else:
        print("\n[FAIL] Some tests FAILED - fix issues before testing GUI")
        return 1

if __name__ == "__main__":
    sys.exit(main())
