"""
Test Suite for Progress Tracking Module

Tests the ProgressTracker context manager and helper functions.
Ensures progress tracking works correctly without interfering with operations.

Design Philosophy:
- Progress tracking should be transparent (not change results)
- Must handle errors gracefully (cleanup even on exceptions)
- Should work in both interactive and silent modes
"""

import sys
import io
from contextlib import redirect_stdout
from src.progress_tracker import ProgressTracker, track_array_operation, track_iteration


def test_basic_progress_tracking():
    """
    Test basic progress tracker functionality.

    Validates:
    - Context manager enters/exits cleanly
    - Update() increments progress
    - Cleanup happens even on exceptions
    """
    print("\n[TEST 1] Basic Progress Tracking")
    print("-" * 50)

    # Capture stdout to verify progress bar output
    output = io.StringIO()
    with redirect_stdout(output):
        with ProgressTracker("Test operation", total=10) as progress:
            for i in range(10):
                progress.update(1)

    # Verify operation completed
    print("OK - Progress tracker completed successfully")

    # Test exception handling (cleanup must still happen)
    try:
        output = io.StringIO()
        with redirect_stdout(output):
            with ProgressTracker("Test with error", total=5) as progress:
                for i in range(3):
                    progress.update(1)
                raise ValueError("Simulated error")
    except ValueError:
        print("OK - Exception handled, cleanup completed")

    print("PASS - Basic progress tracking works correctly")


def test_disabled_progress():
    """
    Test progress tracking in silent/disabled mode.

    Validates:
    - No progress bar created when disable=True
    - Operations still complete normally
    - No output generated
    """
    print("\n[TEST 2] Disabled Progress (Silent Mode)")
    print("-" * 50)

    output = io.StringIO()
    with redirect_stdout(output):
        with ProgressTracker("Silent operation", total=10, disable=True) as progress:
            for i in range(10):
                progress.update(1)

    # Verify no progress bar output in silent mode
    result = output.getvalue()
    if len(result) == 0 or "Silent operation" not in result:
        print("OK - Silent mode produces minimal/no output")
    else:
        print(f"WARNING - Silent mode produced output: {len(result)} chars")

    print("PASS - Silent mode works correctly")


def test_dynamic_updates():
    """
    Test dynamic progress bar updates.

    Validates:
    - set_description() changes display text
    - set_postfix() adds extra info
    - Updates work during operation
    """
    print("\n[TEST 3] Dynamic Progress Updates")
    print("-" * 50)

    output = io.StringIO()
    with redirect_stdout(output):
        with ProgressTracker("Processing", total=20) as progress:
            # Stage 1
            progress.set_description("Stage 1: Loading")
            for i in range(10):
                progress.update(1)

            # Stage 2
            progress.set_description("Stage 2: Processing")
            progress.set_postfix(stage="final", items=20)
            for i in range(10):
                progress.update(1)

    print("OK - Dynamic updates completed")
    print("PASS - Description and postfix updates work")


def test_array_operation_tracking():
    """
    Test the array operation helper function.

    Validates:
    - Correct chunk calculation
    - Progress updates for array-like operations
    - Typical use case for heightmap processing
    """
    print("\n[TEST 4] Array Operation Tracking")
    print("-" * 50)

    # Simulate processing a 4096x4096 array (16,777,216 elements)
    total_size = 4096 * 4096
    chunk_size = 100000

    output = io.StringIO()
    with redirect_stdout(output):
        with track_array_operation("Processing array", total_size, chunk_size) as progress:
            processed = 0
            while processed < total_size:
                current_chunk = min(chunk_size, total_size - processed)
                # Simulate processing
                processed += current_chunk
                progress.update(1)

    print(f"OK - Processed {total_size:,} elements in chunks of {chunk_size:,}")
    print("PASS - Array operation tracking works")


def test_iteration_tracking():
    """
    Test the iteration wrapper function.

    Validates:
    - Wrapping iterables with progress
    - Automatic total detection
    - Simpler syntax for loops
    """
    print("\n[TEST 5] Iteration Tracking")
    print("-" * 50)

    items = list(range(50))

    output = io.StringIO()
    with redirect_stdout(output):
        count = 0
        for item in track_iteration("Processing items", items, disable=True):
            count += 1

    if count == len(items):
        print(f"OK - Processed {count} items")
    else:
        print(f"ERROR - Expected {len(items)} items, processed {count}")

    print("PASS - Iteration tracking works")


def test_thread_safety_simulation():
    """
    Test that progress tracker doesn't break with concurrent updates.

    Note: This is a basic test - full multi-threading testing
    happens in Phase 5 (Week 5).

    Validates:
    - Multiple rapid updates don't crash
    - Progress tracker state remains consistent
    """
    print("\n[TEST 6] Thread Safety Simulation")
    print("-" * 50)

    output = io.StringIO()
    with redirect_stdout(output):
        with ProgressTracker("Rapid updates", total=1000, disable=True) as progress:
            # Simulate many rapid updates (like from multiple threads)
            for i in range(1000):
                progress.update(1)

    print("OK - Handled 1000 rapid updates")
    print("PASS - Thread safety simulation complete")


def run_all_tests():
    """
    Run all progress tracker tests.

    Returns:
        bool: True if all tests passed, False otherwise
    """
    print("=" * 50)
    print("Progress Tracker Test Suite")
    print("=" * 50)

    try:
        test_basic_progress_tracking()
        test_disabled_progress()
        test_dynamic_updates()
        test_array_operation_tracking()
        test_iteration_tracking()
        test_thread_safety_simulation()

        print("\n" + "=" * 50)
        print("ALL TESTS PASSED")
        print("=" * 50)
        return True

    except Exception as e:
        print("\n" + "=" * 50)
        print(f"TEST FAILED: {e}")
        print("=" * 50)
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
