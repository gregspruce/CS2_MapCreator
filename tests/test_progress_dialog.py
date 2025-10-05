"""
Test progress dialog functionality.

Quick visual test to ensure progress dialog displays correctly.
"""

import sys
import os
import time

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

import tkinter as tk
from src.gui.progress_dialog import ProgressDialog


def test_progress_dialog():
    """Test progress dialog with simulated work."""
    print("\n[TEST] Testing Progress Dialog")
    print("A progress window should appear...")

    # Create minimal tkinter root
    root = tk.Tk()
    root.withdraw()  # Hide root window

    # Create progress dialog
    progress = ProgressDialog(root, "Test Progress")

    # Simulate work with progress updates
    steps = [
        (0, "Initializing..."),
        (20, "Loading data..."),
        (40, "Processing..."),
        (60, "Computing results..."),
        (80, "Finalizing..."),
        (100, "Complete!")
    ]

    try:
        for percentage, message in steps:
            progress.update(percentage, message)
            print(f"  [{percentage}%] {message}")
            time.sleep(0.5)  # Simulate work

        print("\n[OK] Progress dialog test complete!")
        print("The dialog should have shown all steps and then closed.\n")

    finally:
        progress.close()
        root.destroy()


if __name__ == '__main__':
    test_progress_dialog()
