"""
CS2 Heightmap Generator - GUI Module

Tkinter-based graphical user interface for heightmap generation and editing.

Components:
- heightmap_gui.py: Main application window
- preview_canvas.py: Live preview with hillshade rendering
- parameter_panel.py: Terrain parameter controls
- tool_palette.py: Manual editing tools

Why Tkinter:
- Python standard library (zero external dependencies)
- Cross-platform (Windows, macOS, Linux)
- Sufficient for our needs (no complex animations)
- Easy deployment (no extra setup)
"""

from .heightmap_gui import HeightmapGUI

__all__ = ['HeightmapGUI']
