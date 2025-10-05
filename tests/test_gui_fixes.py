"""
Quick GUI test to verify v2.1.1 fixes.

Tests:
1. Preview updates automatically after terrain generation
2. Elevation legend fits properly in its container

Usage:
    python test_gui_fixes.py

Then in the GUI:
1. Click a preset button (Mountains, Islands, etc.)
2. Verify preview appears WITHOUT clicking in the window
3. Check elevation legend - labels should be fully visible (not cut off)
"""

import sys
print("\n" + "=" * 70)
print("GUI Fix Verification Test - v2.1.1")
print("=" * 70)
print("\nThis will launch the GUI. Please verify:")
print("  1. After clicking a preset, preview updates AUTOMATICALLY")
print("  2. Elevation legend labels are fully visible (e.g., '3.6km')")
print("\nLaunching GUI...")
print("=" * 70 + "\n")

# Import and run GUI
from src.gui.heightmap_gui import main

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nGUI closed by user.")
        sys.exit(0)
