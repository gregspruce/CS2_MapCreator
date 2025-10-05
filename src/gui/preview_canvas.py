"""
CS2 Heightmap Generator - Preview Canvas

Live preview canvas with hillshade rendering and zoom/pan controls.

Features:
- Real-time hillshade visualization
- Zoom in/out/fit
- Pan with mouse drag
- Grid overlay (optional)
- Smooth rendering using PIL

Why This Design:
- Canvas widget optimal for image display
- PIL for efficient image conversion
- Zoom/pan standard in image editors
- Grid helps with positioning
"""

import tkinter as tk
from tkinter import ttk
from PIL import Image, ImageTk
import numpy as np
from typing import Optional


class PreviewCanvas(tk.Canvas):
    """
    Canvas widget for displaying heightmap previews.

    Features:
    - Hillshade rendering
    - Zoom (0.25x to 4x)
    - Pan with mouse
    - Grid overlay
    - Smooth updates

    Why Canvas:
    - Built-in zoom/pan support
    - Efficient image rendering
    - Standard Tkinter widget
    - No external dependencies
    """

    def __init__(self, parent, size: int = 512):
        """
        Initialize preview canvas.

        Args:
            parent: Parent widget
            size: Canvas size in pixels (default: 512x512)

        Why 512x512:
        - Good balance of detail and performance
        - Fits well in 1280x800 window
        - Fast rendering (< 100ms typical)
        """
        super().__init__(
            parent,
            width=size,
            height=size,
            bg='gray20',
            highlightthickness=1,
            highlightbackground='gray30'
        )

        self.canvas_size = size
        self.zoom_level = 1.0
        self.zoom_min = 0.25
        self.zoom_max = 4.0

        # Current image
        self.current_image: Optional[Image.Image] = None
        self.photo_image: Optional[ImageTk.PhotoImage] = None
        self.image_id: Optional[int] = None

        # Grid overlay
        self.show_grid_overlay = False
        self.grid_lines = []

        # Pan state
        self.pan_start_x = 0
        self.pan_start_y = 0
        self.is_panning = False

        # Two-point tool state (for ridge/valley)
        self.first_point = None  # (x, y) in heightmap coordinates
        self.preview_line_id = None  # Canvas line ID for visual feedback
        self.is_two_point_tool = False

        # Tool callback (set by parent GUI)
        self.tool_callback = None

        # Bind mouse events
        self.bind("<ButtonPress-1>", self._on_mouse_press)
        self.bind("<B1-Motion>", self._on_mouse_drag)
        self.bind("<ButtonRelease-1>", self._on_mouse_release)
        self.bind("<MouseWheel>", self._on_mouse_wheel)  # Windows
        self.bind("<Button-4>", lambda e: self._on_mouse_wheel_unix(e, 1))  # Linux scroll up
        self.bind("<Button-5>", lambda e: self._on_mouse_wheel_unix(e, -1))  # Linux scroll down

    def update_image(self, image: Image.Image):
        """
        Update the displayed image.

        Args:
            image: PIL Image to display

        Why PIL Image:
        - Industry standard for image handling
        - Efficient resizing (Lanczos filter)
        - Easy Tkinter integration
        - Already used in preview_generator.py
        """
        self.current_image = image

        # Resize to canvas size with current zoom
        display_size = int(self.canvas_size * self.zoom_level)
        resized = image.resize((display_size, display_size), Image.Resampling.LANCZOS)

        # Convert to PhotoImage
        self.photo_image = ImageTk.PhotoImage(resized)

        # Update canvas
        if self.image_id is None:
            self.image_id = self.create_image(
                self.canvas_size // 2,
                self.canvas_size // 2,
                image=self.photo_image
            )
        else:
            self.itemconfig(self.image_id, image=self.photo_image)

        # Update grid if enabled
        if self.show_grid_overlay:
            self._draw_grid()

    def zoom_in(self):
        """Zoom in by 1.5x."""
        new_zoom = min(self.zoom_level * 1.5, self.zoom_max)
        if new_zoom != self.zoom_level:
            self.zoom_level = new_zoom
            self._refresh_display()

    def zoom_out(self):
        """Zoom out by 1.5x."""
        new_zoom = max(self.zoom_level / 1.5, self.zoom_min)
        if new_zoom != self.zoom_level:
            self.zoom_level = new_zoom
            self._refresh_display()

    def zoom_fit(self):
        """Reset zoom to fit canvas."""
        self.zoom_level = 1.0
        self._refresh_display()

    def toggle_grid(self):
        """Toggle grid overlay."""
        self.show_grid_overlay = not self.show_grid_overlay
        if self.show_grid_overlay:
            self._draw_grid()
        else:
            self._clear_grid()

    def _refresh_display(self):
        """Refresh the display after zoom change."""
        if self.current_image is not None:
            self.update_image(self.current_image)

    def _draw_grid(self):
        """Draw grid overlay (8x8 grid)."""
        self._clear_grid()

        # Grid parameters
        grid_size = 8
        cell_size = self.canvas_size // grid_size
        color = 'cyan'
        width = 1

        # Draw vertical lines
        for i in range(grid_size + 1):
            x = i * cell_size
            line_id = self.create_line(
                x, 0, x, self.canvas_size,
                fill=color, width=width, dash=(2, 2)
            )
            self.grid_lines.append(line_id)

        # Draw horizontal lines
        for i in range(grid_size + 1):
            y = i * cell_size
            line_id = self.create_line(
                0, y, self.canvas_size, y,
                fill=color, width=width, dash=(2, 2)
            )
            self.grid_lines.append(line_id)

    def _clear_grid(self):
        """Clear grid overlay."""
        for line_id in self.grid_lines:
            self.delete(line_id)
        self.grid_lines = []

    def _on_mouse_press(self, event):
        """
        Handle mouse press - either pan or tool application.

        Priority:
        1. Ctrl+drag → Always pan (override tool)
        2. Tool selected → Apply tool
        3. No tool ('none') → Pan normally

        Two-point tool behavior:
        - First click stores start point
        - Drag shows preview line
        - Release executes command with both points

        Why this design:
        - Simple priority-based logic
        - Tool callback returns False if tool is 'none'
        - Two-point tools get special handling
        - Enables panning automatically when no tool active
        """
        # Ctrl key always forces pan mode
        if event.state & 0x4:  # 0x4 = Ctrl key
            self.pan_start_x = event.x
            self.pan_start_y = event.y
            self.is_panning = True
            self.config(cursor="fleur")
            return

        # Try to apply tool if callback exists
        tool_was_applied = False
        if self.tool_callback is not None:
            hm_x, hm_y = self.get_clicked_position(event)
            # Callback returns True if tool was applied, False if tool is 'none'
            # For two-point tools, callback sets is_two_point_tool flag
            tool_was_applied = self.tool_callback(hm_x, hm_y, is_drag_start=True)

            # If this is a two-point tool, store first point and canvas coordinates
            if self.is_two_point_tool:
                self.first_point = (hm_x, hm_y)
                self.first_canvas_point = (event.x, event.y)

        # If no tool was applied (or no callback), enable pan mode
        if not tool_was_applied:
            self.pan_start_x = event.x
            self.pan_start_y = event.y
            self.is_panning = True
            self.config(cursor="fleur")

    def _on_mouse_drag(self, event):
        """
        Handle mouse drag - either pan, two-point preview, or continuous tool application.

        For two-point tools (ridge/valley):
        - Draw preview line from first point to current cursor position
        - Update line as mouse moves
        """
        if self.is_panning and self.image_id is not None:
            # Pan mode
            dx = event.x - self.pan_start_x
            dy = event.y - self.pan_start_y
            self.move(self.image_id, dx, dy)
            self.pan_start_x = event.x
            self.pan_start_y = event.y
        elif self.is_two_point_tool and self.first_point is not None:
            # Two-point tool mode - show preview line
            self._update_preview_line(event.x, event.y)
        elif self.tool_callback is not None:
            # Regular tool drag mode (brush tools)
            hm_x, hm_y = self.get_clicked_position(event)
            self.tool_callback(hm_x, hm_y, is_drag=True)

    def _on_mouse_release(self, event):
        """
        Handle mouse release.

        For two-point tools:
        - Execute command with both points
        - Clear preview line
        - Reset state
        """
        if self.is_panning:
            self.is_panning = False
            self.config(cursor="")
        elif self.is_two_point_tool and self.first_point is not None:
            # Two-point tool - execute with both points
            hm_x, hm_y = self.get_clicked_position(event)

            # Clear preview line
            self._clear_preview_line()

            # Execute command with both points
            if self.tool_callback is not None:
                self.tool_callback(hm_x, hm_y, is_drag_end=True, first_point=self.first_point)

            # Reset two-point state
            self.first_point = None
            self.is_two_point_tool = False
        elif self.tool_callback is not None:
            # Regular tool release
            hm_x, hm_y = self.get_clicked_position(event)
            self.tool_callback(hm_x, hm_y, is_drag_end=True)

    def _on_mouse_wheel(self, event):
        """Handle mouse wheel zoom (Windows/macOS)."""
        if event.delta > 0:
            self.zoom_in()
        else:
            self.zoom_out()

    def _on_mouse_wheel_unix(self, event, direction):
        """Handle mouse wheel zoom (Linux)."""
        if direction > 0:
            self.zoom_in()
        else:
            self.zoom_out()

    def set_heightmap_resolution(self, resolution: int):
        """
        Set the heightmap resolution for coordinate conversion.

        Args:
            resolution: Heightmap size (for square heightmaps)
        """
        self.heightmap_resolution = resolution

    def get_clicked_position(self, event) -> tuple[int, int]:
        """
        Convert canvas click position to heightmap coordinates.

        Args:
            event: Mouse event

        Returns:
            (x, y) in heightmap coordinates (0-resolution)

        Why this method:
        - Tools need heightmap coordinates, not canvas pixels
        - Accounts for zoom and pan
        - Standard coordinate transformation
        """
        # Get image coordinates
        canvas_x = self.canvasx(event.x)
        canvas_y = self.canvasy(event.y)

        # Get image bounds
        if self.image_id is None:
            return (0, 0)

        bbox = self.bbox(self.image_id)
        if bbox is None:
            return (0, 0)

        x1, y1, x2, y2 = bbox
        img_width = x2 - x1
        img_height = y2 - y1

        # Convert to relative coordinates (0.0-1.0)
        rel_x = (canvas_x - x1) / img_width if img_width > 0 else 0.0
        rel_y = (canvas_y - y1) / img_height if img_height > 0 else 0.0

        # Clamp to valid range
        rel_x = max(0.0, min(1.0, rel_x))
        rel_y = max(0.0, min(1.0, rel_y))

        # Scale to heightmap resolution (use stored resolution)
        resolution = getattr(self, 'heightmap_resolution', 4096)

        hm_x = int(rel_x * resolution)
        hm_y = int(rel_y * resolution)

        return (hm_x, hm_y)

    def _update_preview_line(self, x2: int, y2: int):
        """
        Update or create preview line for two-point tools.

        Args:
            x2, y2: Current mouse position (canvas coordinates)

        Why this method:
        - Visual feedback shows user where ridge/valley will be placed
        - Line updates in real-time as mouse moves
        - Uses bright color (yellow) for visibility
        """
        if not hasattr(self, 'first_canvas_point') or self.first_canvas_point is None:
            return

        x1, y1 = self.first_canvas_point

        # Delete old preview line if exists
        if self.preview_line_id is not None:
            self.delete(self.preview_line_id)

        # Draw new preview line
        self.preview_line_id = self.create_line(
            x1, y1, x2, y2,
            fill='yellow',
            width=2,
            dash=(4, 4)  # Dashed line for preview effect
        )

    def _clear_preview_line(self):
        """
        Clear the preview line after two-point tool is executed.

        Why this method:
        - Clean up visual feedback after command execution
        - Prevents line from persisting on canvas
        """
        if self.preview_line_id is not None:
            self.delete(self.preview_line_id)
            self.preview_line_id = None
