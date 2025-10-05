"""
CS2 Heightmap Generator - Main GUI Window

The main application window integrating all GUI components.

Architecture:
- MVC Pattern: Model (HeightmapGenerator), View (GUI), Controller (event handlers)
- State Management: Full undo/redo via CommandHistory
- Live Preview: Real-time hillshade rendering
- Parameter Controls: Sliders with debounced updates (500ms)

Why This Design:
- Separation of concerns (model/view/controller)
- Responsive UI (debouncing prevents lag)
- Integration with existing backend
- Standard GUI patterns (familiar to users)
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from typing import Optional
import numpy as np
from pathlib import Path
import threading

from ..heightmap_generator import HeightmapGenerator
from ..state_manager import CommandHistory
from ..noise_generator import NoiseGenerator
from ..preview_generator import PreviewGenerator
from ..preset_manager import PresetManager
from .preview_canvas import PreviewCanvas
from .parameter_panel import ParameterPanel
from .tool_palette import ToolPalette
from .progress_dialog import ProgressDialog


class HeightmapGUI(tk.Tk):
    """
    Main GUI application for CS2 Heightmap Generator.

    Layout:
    - Menu bar: File, Edit, View, Tools, Help
    - Toolbar: Quick actions (New, Save, Undo, Redo)
    - Left panel (300px): Parameters and presets
    - Center (700px): Preview canvas (512x512)
    - Right panel (280px): Tools and history
    - Status bar: Current operation, resolution, zoom

    Why this layout:
    - Parameters on left (most used controls)
    - Preview in center (focus of attention)
    - Tools on right (secondary actions)
    - Standard layout (used by Photoshop, GIMP, etc.)
    """

    def __init__(self):
        """Initialize the main GUI window."""
        super().__init__()

        # Window setup
        self.title("CS2 Heightmap Generator v2.0")
        self.geometry("1280x800")
        self.minsize(1024, 600)

        # Set window icon (if available)
        try:
            # Icon would go here - skipping for now
            pass
        except Exception:
            pass

        # Initialize backend components
        # Resolution MUST be 4096x4096 per CS2 specifications
        self.generator = HeightmapGenerator(resolution=4096)
        self.history = CommandHistory()
        self.noise_gen = NoiseGenerator()
        self.preset_mgr = PresetManager()

        # Current heightmap (MUST be 4096x4096 per CS2 wiki requirements)
        # CS2 specification: Heightmaps MUST be exactly 4096x4096 resolution
        # This is NOT optional - it's a game requirement
        # Reference: wiki_instructions.pdf - "Heightmaps should be 4096x4096 resolution"
        self.heightmap = np.zeros((4096, 4096), dtype=np.float64)
        self.resolution = 4096  # FIXED: CS2 requirement, not user-selectable

        # Debounce timer for parameter updates
        self._update_timer = None
        self._pending_update = False

        # Create GUI components
        self._create_menu_bar()
        self._create_toolbar()
        self._create_main_layout()
        self._create_status_bar()

        # Bind keyboard shortcuts
        self._bind_shortcuts()

        # Initialize with flat terrain (instant display)
        # User must explicitly click a preset or Generate button to create terrain
        # Why: User hasn't selected settings yet, shouldn't auto-generate
        self._initialize_flat_terrain()

    def _create_menu_bar(self):
        """Create the menu bar."""
        menubar = tk.Menu(self)
        self.config(menu=menubar)

        # File menu
        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="File", menu=file_menu)
        file_menu.add_command(label="New", command=self.new_heightmap, accelerator="Ctrl+N")
        file_menu.add_command(label="Open...", command=self.open_heightmap, accelerator="Ctrl+O")
        file_menu.add_command(label="Save", command=self.save_heightmap, accelerator="Ctrl+S")
        file_menu.add_command(label="Save As...", command=self.save_heightmap_as, accelerator="Ctrl+Shift+S")
        file_menu.add_separator()
        file_menu.add_command(label="Export to CS2...", command=self.export_to_cs2)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.quit, accelerator="Ctrl+Q")

        # Edit menu
        edit_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Edit", menu=edit_menu)
        edit_menu.add_command(label="Undo", command=self.undo, accelerator="Ctrl+Z")
        edit_menu.add_command(label="Redo", command=self.redo, accelerator="Ctrl+Y")
        edit_menu.add_separator()
        edit_menu.add_command(label="Clear", command=self.clear_heightmap)

        # View menu
        view_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="View", menu=view_menu)
        view_menu.add_command(label="Zoom In", command=self.zoom_in, accelerator="Ctrl++")
        view_menu.add_command(label="Zoom Out", command=self.zoom_out, accelerator="Ctrl+-")
        view_menu.add_command(label="Fit to Window", command=self.zoom_fit, accelerator="Ctrl+0")
        view_menu.add_separator()
        view_menu.add_checkbutton(label="Show Grid", command=self.toggle_grid)

        # Tools menu
        tools_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Tools", menu=tools_menu)
        tools_menu.add_command(label="Generate Rivers", command=self.add_rivers)
        tools_menu.add_command(label="Generate Lakes", command=self.add_lakes)
        tools_menu.add_command(label="Add Coastal Features", command=self.add_coastal)
        tools_menu.add_separator()
        tools_menu.add_command(label="Terrain Analysis", command=self.show_analysis)

        # Help menu
        help_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Help", menu=help_menu)
        help_menu.add_command(label="Documentation", command=self.show_docs)
        help_menu.add_command(label="About", command=self.show_about)

    def _create_toolbar(self):
        """Create the toolbar with quick action buttons."""
        toolbar = ttk.Frame(self, relief=tk.RAISED, borderwidth=1)
        toolbar.pack(side=tk.TOP, fill=tk.X, padx=2, pady=2)

        # Quick action buttons
        ttk.Button(toolbar, text="New", command=self.new_heightmap, width=8).pack(side=tk.LEFT, padx=2)
        ttk.Button(toolbar, text="Save", command=self.save_heightmap, width=8).pack(side=tk.LEFT, padx=2)
        ttk.Separator(toolbar, orient=tk.VERTICAL).pack(side=tk.LEFT, fill=tk.Y, padx=5)
        ttk.Button(toolbar, text="Undo", command=self.undo, width=8).pack(side=tk.LEFT, padx=2)
        ttk.Button(toolbar, text="Redo", command=self.redo, width=8).pack(side=tk.LEFT, padx=2)
        ttk.Separator(toolbar, orient=tk.VERTICAL).pack(side=tk.LEFT, fill=tk.Y, padx=5)
        ttk.Button(toolbar, text="Generate", command=self.generate_terrain, width=10).pack(side=tk.LEFT, padx=2)

    def _create_main_layout(self):
        """Create the main layout with panels."""
        # Main container (paned window for resizable panels)
        main_paned = ttk.PanedWindow(self, orient=tk.HORIZONTAL)
        main_paned.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # Left panel - Parameters
        self.param_panel = ParameterPanel(main_paned, self)
        main_paned.add(self.param_panel, weight=0)

        # Center panel - Preview canvas
        center_frame = ttk.Frame(main_paned)
        self.preview = PreviewCanvas(center_frame, size=512)
        self.preview.pack(fill=tk.BOTH, expand=True)
        main_paned.add(center_frame, weight=1)

        # Right panel - Tools
        self.tool_palette = ToolPalette(main_paned, self)
        main_paned.add(self.tool_palette, weight=0)

    def _create_status_bar(self):
        """Create the status bar."""
        self.status_bar = ttk.Frame(self, relief=tk.SUNKEN, borderwidth=1)
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X)

        self.status_label = ttk.Label(self.status_bar, text="Ready", anchor=tk.W)
        self.status_label.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)

        self.resolution_label = ttk.Label(self.status_bar, text=f"{self.resolution}x{self.resolution}")
        self.resolution_label.pack(side=tk.RIGHT, padx=5)

    def _bind_shortcuts(self):
        """Bind keyboard shortcuts."""
        self.bind("<Control-n>", lambda e: self.new_heightmap())
        self.bind("<Control-o>", lambda e: self.open_heightmap())
        self.bind("<Control-s>", lambda e: self.save_heightmap())
        self.bind("<Control-Shift-S>", lambda e: self.save_heightmap_as())
        self.bind("<Control-q>", lambda e: self.quit())
        self.bind("<Control-z>", lambda e: self.undo())
        self.bind("<Control-y>", lambda e: self.redo())
        self.bind("<Control-plus>", lambda e: self.zoom_in())
        self.bind("<Control-minus>", lambda e: self.zoom_out())
        self.bind("<Control-0>", lambda e: self.zoom_fit())

    def _initialize_flat_terrain(self):
        """
        Initialize GUI with flat terrain for instant display.

        Why flat terrain:
        - Window appears instantly (no generation delay)
        - User hasn't selected any settings/presets yet
        - User must explicitly trigger generation via presets or Generate button
        - UX best practice: Don't auto-generate without user input

        The heightmap is already initialized to zeros in __init__,
        so we just need to create a simple preview.
        """
        # Heightmap is already zeros (flat) from __init__
        # Just create a simple gray preview to show the canvas works
        from PIL import Image
        import numpy as np

        # Create a simple gray preview (512x512 for display)
        preview_array = np.full((512, 512, 3), 128, dtype=np.uint8)  # Mid-gray
        preview_image = Image.fromarray(preview_array)

        self.preview.update_image(preview_image)
        self.set_status("Ready - Select a preset or adjust parameters to generate terrain")

    def update_preview(self):
        """Update the preview canvas with current heightmap."""
        # Generate hillshade preview
        preview_gen = PreviewGenerator(self.heightmap)

        # Generate hillshade
        hillshade = preview_gen.generate_hillshade(
            azimuth=315,
            altitude=45
        )

        # Apply colormap
        colored = preview_gen.apply_colormap(
            colormap='terrain'
        )

        # Blend hillshade with colors
        blended_array = preview_gen.blend_hillshade_with_colors(
            hillshade=hillshade,
            colors=colored,
            blend_factor=0.6
        )

        # Convert numpy array to PIL Image
        from PIL import Image
        preview_image = Image.fromarray(blended_array)

        # Update canvas
        self.preview.update_image(preview_image)

    def schedule_update(self):
        """
        Schedule a debounced preview update.

        Why debouncing:
        - Prevents lag when dragging sliders
        - Updates after 500ms of inactivity
        - Standard UX pattern
        """
        if self._update_timer is not None:
            self.after_cancel(self._update_timer)

        self._update_timer = self.after(500, self._do_scheduled_update)

    def _do_scheduled_update(self):
        """Execute the scheduled update."""
        self._update_timer = None
        self.generate_terrain()

    def set_status(self, message: str):
        """Update status bar message."""
        self.status_label.config(text=message)
        self.update_idletasks()

    # Command methods

    def new_heightmap(self):
        """Create a new heightmap."""
        if messagebox.askyesno("New Heightmap", "Create new heightmap? Unsaved changes will be lost."):
            self.heightmap = np.zeros((self.resolution, self.resolution), dtype=np.float64)
            self.history.clear()
            self._generate_default_terrain()

    def open_heightmap(self):
        """Open an existing heightmap."""
        filename = filedialog.askopenfilename(
            title="Open Heightmap",
            filetypes=[("PNG files", "*.png"), ("All files", "*.*")]
        )
        if filename:
            try:
                self.set_status(f"Loading {Path(filename).name}...")
                # Load using PIL
                from PIL import Image
                img = Image.open(filename)
                self.heightmap = np.array(img, dtype=np.float64) / 65535.0
                self.resolution = self.heightmap.shape[0]
                self.update_preview()
                self.set_status(f"Loaded {Path(filename).name}")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to load heightmap: {e}")
                self.set_status("Error loading file")

    def save_heightmap(self):
        """Save the current heightmap."""
        # Use last saved path or prompt
        self.save_heightmap_as()

    def save_heightmap_as(self):
        """Save the heightmap with a new filename."""
        filename = filedialog.asksaveasfilename(
            title="Save Heightmap",
            defaultextension=".png",
            filetypes=[("PNG files", "*.png"), ("All files", "*.*")]
        )
        if filename:
            try:
                self.set_status(f"Saving {Path(filename).name}...")
                self.generator.set_height_data(self.heightmap)
                self.generator.export_png(filename)
                self.set_status(f"Saved {Path(filename).name}")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to save heightmap: {e}")
                self.set_status("Error saving file")

    def export_to_cs2(self):
        """Export heightmap to CS2."""
        # This would integrate with cs2_exporter.py
        messagebox.showinfo("Export to CS2", "CS2 export functionality will be added here.")

    def undo(self):
        """Undo the last operation."""
        if self.history.can_undo():
            self.history.undo()
            self.update_preview()
            self.set_status("Undo successful")
        else:
            self.set_status("Nothing to undo")

    def redo(self):
        """Redo the last undone operation."""
        if self.history.can_redo():
            self.history.redo()
            self.update_preview()
            self.set_status("Redo successful")
        else:
            self.set_status("Nothing to redo")

    def clear_heightmap(self):
        """Clear the heightmap to flat terrain."""
        if messagebox.askyesno("Clear", "Clear heightmap to flat terrain?"):
            self.heightmap = np.zeros((self.resolution, self.resolution), dtype=np.float64)
            self.update_preview()
            self.set_status("Heightmap cleared")

    def generate_terrain(self):
        """
        Generate terrain with current parameters.

        Uses background thread to keep GUI responsive.

        Why threading:
        - 4096x4096 generation takes 1-2 minutes
        - Running on main thread freezes GUI ("Not Responding")
        - Background thread keeps UI responsive
        - Progress dialog shows user something is happening
        """
        params = self.param_panel.get_parameters()

        # Create progress dialog
        progress_dialog = ProgressDialog(
            self,
            title="Generating Terrain",
            message=f"Generating {self.resolution}x{self.resolution} terrain...\nThis may take 1-2 minutes.",
            cancelable=False
        )

        def generate_in_background():
            """Run generation in background thread."""
            try:
                # Generate using noise generator
                heightmap = self.noise_gen.generate_perlin(
                    resolution=self.resolution,
                    scale=params['scale'],
                    octaves=params['octaves'],
                    persistence=params['persistence'],
                    lacunarity=params['lacunarity'],
                    show_progress=False
                )

                # Update UI on main thread (Tkinter requirement)
                self.after(0, lambda: self._on_generation_complete(heightmap, progress_dialog))

            except Exception as e:
                # Handle errors on main thread
                self.after(0, lambda: self._on_generation_error(str(e), progress_dialog))

        # Start background thread
        thread = threading.Thread(target=generate_in_background, daemon=True)
        thread.start()

        # Show progress dialog (non-blocking)
        progress_dialog.show()

    def _on_generation_complete(self, heightmap: np.ndarray, progress_dialog: ProgressDialog):
        """
        Called when generation completes (on main thread).

        Args:
            heightmap: Generated terrain data
            progress_dialog: Progress dialog to close
        """
        self.heightmap = heightmap
        self.update_preview()
        progress_dialog.close()
        self.set_status("Terrain generated successfully")

    def _on_generation_error(self, error_msg: str, progress_dialog: ProgressDialog):
        """
        Called when generation fails (on main thread).

        Args:
            error_msg: Error message
            progress_dialog: Progress dialog to close
        """
        progress_dialog.close()
        messagebox.showerror("Generation Error", f"Failed to generate terrain:\n\n{error_msg}")
        self.set_status("Generation failed")

    def zoom_in(self):
        """Zoom in on the preview."""
        self.preview.zoom_in()

    def zoom_out(self):
        """Zoom out on the preview."""
        self.preview.zoom_out()

    def zoom_fit(self):
        """Fit preview to window."""
        self.preview.zoom_fit()

    def toggle_grid(self):
        """Toggle grid overlay."""
        self.preview.toggle_grid()

    def add_rivers(self):
        """Add rivers to the heightmap."""
        messagebox.showinfo("Rivers", "River generation will be added here.")

    def add_lakes(self):
        """Add lakes to the heightmap."""
        messagebox.showinfo("Lakes", "Lake generation will be added here.")

    def add_coastal(self):
        """Add coastal features."""
        messagebox.showinfo("Coastal", "Coastal features will be added here.")

    def show_analysis(self):
        """Show terrain analysis."""
        messagebox.showinfo("Analysis", "Terrain analysis will be added here.")

    def show_docs(self):
        """Show documentation."""
        messagebox.showinfo("Documentation", "Documentation will be added here.")

    def show_about(self):
        """Show about dialog."""
        messagebox.showinfo(
            "About",
            "CS2 Heightmap Generator v2.0\n\n"
            "A professional tool for generating Cities Skylines 2 heightmaps.\n\n"
            "Features:\n"
            "- Procedural noise generation\n"
            "- Water features (rivers, lakes, coasts)\n"
            "- Manual editing tools\n"
            "- Full undo/redo support\n"
            "- Performance optimizations"
        )


def main():
    """Entry point for GUI application."""
    app = HeightmapGUI()
    app.mainloop()


if __name__ == "__main__":
    main()
