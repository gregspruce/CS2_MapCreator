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

        # Bind mouse events
        self.bind("<ButtonPress-1>", self._on_pan_start)
        self.bind("<B1-Motion>", self._on_pan_move)
        self.bind("<ButtonRelease-1>", self._on_pan_end)
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

    def _on_pan_start(self, event):
        """Handle pan start (mouse press)."""
        self.pan_start_x = event.x
        self.pan_start_y = event.y
        self.is_panning = True
        self.config(cursor="fleur")  # Move cursor

    def _on_pan_move(self, event):
        """Handle pan move (mouse drag)."""
        if self.is_panning and self.image_id is not None:
            dx = event.x - self.pan_start_x
            dy = event.y - self.pan_start_y
            self.move(self.image_id, dx, dy)
            self.pan_start_x = event.x
            self.pan_start_y = event.y

    def _on_pan_end(self, event):
        """Handle pan end (mouse release)."""
        self.is_panning = False
        self.config(cursor="")

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

        # Scale to heightmap resolution (assuming square heightmap)
        # Note: Parent GUI should provide actual resolution
        resolution = 1024  # Default, should be passed from parent

        hm_x = int(rel_x * resolution)
        hm_y = int(rel_y * resolution)

        return (hm_x, hm_y)
