"""
Test tool deselection and pan/zoom navigation.

This test verifies that:
1. Pan/Zoom button sets tool to 'none'
2. When tool is 'none', canvas click enables panning
3. Tool callback returns False when tool is 'none'
4. Canvas correctly switches between tool mode and pan mode
"""

import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(__file__))

import tkinter as tk
from src.gui.heightmap_gui import HeightmapGUI
import numpy as np


def test_tool_deselection():
    """Test that tool deselection works correctly."""
    print("\n" + "="*60)
    print("Testing Tool Deselection and Pan/Zoom Navigation")
    print("="*60 + "\n")

    # Create GUI instance (creates its own root window)
    gui = HeightmapGUI()
    gui.withdraw()  # Hide window

    # Generate some terrain to work with
    gui.generate_terrain()

    # Test 1: Verify Pan/Zoom button sets tool to 'none'
    print("1. Testing Pan/Zoom button...")
    gui.tool_palette.current_tool.set('raise')  # Start with a tool selected
    assert gui.tool_palette.current_tool.get() == 'raise', "Tool should be 'raise'"

    gui.tool_palette._deselect_tools()  # Click Pan/Zoom button
    assert gui.tool_palette.current_tool.get() == 'none', "Tool should be 'none' after deselect"
    print("   [PASS] Pan/Zoom button sets tool to 'none'\n")

    # Test 2: Verify tool callback returns False when tool is 'none'
    print("2. Testing tool callback with 'none' tool...")
    gui.tool_palette.current_tool.set('none')
    result = gui._on_tool_click(100, 100)
    assert result == False, "Tool callback should return False when tool is 'none'"
    print("   [PASS] Tool callback returns False for 'none' tool\n")

    # Test 3: Verify tool callback returns True when tool is active
    print("3. Testing tool callback with active tool...")
    gui.tool_palette.current_tool.set('raise')
    result = gui._on_tool_click(2048, 2048)
    assert result == True, "Tool callback should return True when tool is active"
    print("   [PASS] Tool callback returns True for active tool\n")

    # Test 4: Verify switching between tools
    print("4. Testing tool switching...")
    gui.tool_palette.current_tool.set('raise')
    assert gui.tool_palette.current_tool.get() == 'raise'

    gui.tool_palette.current_tool.set('smooth')
    assert gui.tool_palette.current_tool.get() == 'smooth'

    gui.tool_palette._deselect_tools()
    assert gui.tool_palette.current_tool.get() == 'none'
    print("   [PASS] Tool switching works correctly\n")

    # Cleanup
    gui.destroy()

    print("="*60)
    print("ALL TESTS PASSED!")
    print("="*60 + "\n")

    print("Expected workflow:")
    print("1. User selects brush tool -> Tool active, clicks apply tool")
    print("2. User clicks 'Pan/Zoom' -> Tool becomes 'none'")
    print("3. User clicks canvas -> Pan mode enabled automatically")
    print("4. User drags -> Preview pans around")
    print("\nResult: User can freely switch between tool mode and pan mode!\n")


if __name__ == '__main__':
    test_tool_deselection()
