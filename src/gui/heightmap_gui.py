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
from ..terrain_parameter_mapper import TerrainParameterMapper
from ..buildability_enforcer import BuildabilityEnforcer
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
        self.title("CS2 Heightmap Generator v2.4")
        self.geometry("1280x720")  # Reduced from 800 (more compact layout!)
        self.minsize(1024, 650)    # Fits standard 768px screens

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

        # Worldmap (optional, generated separately)
        self.worldmap = None  # Will be WorldmapGenerator instance when generated
        self.has_worldmap = False

        # Display options
        self.show_legend = True  # Show elevation legend by default
        self.show_water_overlay = False  # Water features overlay (off by default)
        self.water_level = None  # Water level for overlay (set when coastal features added)

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
        view_menu.add_checkbutton(label="Show Elevation Legend", command=self.toggle_legend, variable=tk.BooleanVar(value=True))
        # "Show Water Features" moved to Water tab in parameter panel

        # Tools menu
        tools_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Tools", menu=tools_menu)
        tools_menu.add_command(label="Generate Worldmap", command=self.generate_worldmap)
        tools_menu.add_separator()
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
        ttk.Button(toolbar, text="Generate Terrain", command=self.generate_terrain, width=15).pack(side=tk.LEFT, padx=2)
        ttk.Button(toolbar, text="Generate Worldmap", command=self.generate_worldmap, width=15).pack(side=tk.LEFT, padx=2)

    def _create_main_layout(self):
        """Create the main layout with panels."""
        # Main container (paned window for resizable panels)
        main_paned = ttk.PanedWindow(self, orient=tk.HORIZONTAL)
        main_paned.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # Left panel - Parameters
        self.param_panel = ParameterPanel(main_paned, self)
        main_paned.add(self.param_panel, weight=0)

        # Center panel - Preview canvas with legend
        center_frame = ttk.Frame(main_paned)

        # Create container for preview and legend
        preview_container = ttk.Frame(center_frame)
        preview_container.pack(fill=tk.BOTH, expand=True)

        # Preview canvas (left side of container)
        self.preview = PreviewCanvas(preview_container, size=512)
        self.preview.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.preview.set_heightmap_resolution(self.resolution)
        self.preview.tool_callback = self._on_tool_click

        # Legend panel (right side of container, fixed width - increased for label space)
        self.legend_frame = ttk.Frame(preview_container, width=140, relief=tk.SUNKEN, borderwidth=1)
        self.legend_frame.pack(side=tk.RIGHT, fill=tk.Y, padx=(5, 0))
        self.legend_frame.pack_propagate(False)  # Maintain fixed width

        # Legend title
        legend_title = ttk.Label(self.legend_frame, text="Elevation", font=('Arial', 11, 'bold'))
        legend_title.pack(pady=(10, 5))

        # Legend canvas for color scale - wider to accommodate labels
        self.legend_canvas = tk.Canvas(self.legend_frame, width=120, height=400, bg='white', highlightthickness=0)
        self.legend_canvas.pack(pady=10)

        main_paned.add(center_frame, weight=1)

        # Right panel - Tools
        self.tool_palette = ToolPalette(main_paned, self)
        main_paned.add(self.tool_palette, weight=0)

    def _create_status_bar(self):
        """Create the status bar with generation status indicators."""
        self.status_bar = ttk.Frame(self, relief=tk.SUNKEN, borderwidth=1)
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X)

        self.status_label = ttk.Label(self.status_bar, text="Ready", anchor=tk.W)
        self.status_label.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)

        # Status indicators for what's been generated
        self.worldmap_status = ttk.Label(self.status_bar, text="Worldmap: ✗", foreground='gray')
        self.worldmap_status.pack(side=tk.RIGHT, padx=5)

        ttk.Separator(self.status_bar, orient=tk.VERTICAL).pack(side=tk.RIGHT, fill=tk.Y, padx=2)

        self.playable_status = ttk.Label(self.status_bar, text="Playable: —", foreground='gray')
        self.playable_status.pack(side=tk.RIGHT, padx=5)

        ttk.Separator(self.status_bar, orient=tk.VERTICAL).pack(side=tk.RIGHT, fill=tk.Y, padx=2)

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
        """
        Update the preview canvas with current heightmap.

        Performance optimization:
        - Downsample to 512x512 before preview generation
        - Avoids 3.6s freeze on full 4096x4096 processing
        - Preview quality unchanged (canvas is 512px anyway)
        """
        from PIL import Image
        from scipy import ndimage

        # Downsample heightmap to preview resolution (512x512)
        # This makes preview generation 64x faster!
        preview_size = 512
        if self.heightmap.shape[0] > preview_size:
            # Use zoom for high-quality downsampling
            zoom_factor = preview_size / self.heightmap.shape[0]
            downsampled = ndimage.zoom(self.heightmap, zoom_factor, order=1)
        else:
            downsampled = self.heightmap

        # Generate hillshade preview on downsampled data
        preview_gen = PreviewGenerator(downsampled, height_scale=4096.0)

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
        preview_image = Image.fromarray(blended_array)

        # Add water overlay if enabled and water level is set
        if self.show_water_overlay and self.water_level is not None:
            from PIL import ImageDraw
            import numpy as np

            # Create water mask (areas below water level)
            water_mask = downsampled <= self.water_level

            # Create semi-transparent blue overlay
            overlay = Image.new('RGBA', preview_image.size, (0, 0, 0, 0))
            overlay_pixels = np.array(overlay)

            # Set water areas to semi-transparent blue (RGBA: 30, 144, 255, 128)
            # Using dodger blue with 50% transparency
            overlay_pixels[water_mask] = [30, 144, 255, 128]

            overlay = Image.fromarray(overlay_pixels, 'RGBA')

            # Convert preview to RGBA and composite with overlay
            preview_rgba = preview_image.convert('RGBA')
            preview_image = Image.alpha_composite(preview_rgba, overlay)

        # Update canvas
        self.preview.update_image(preview_image)

        # Update legend panel
        if self.show_legend:
            self.update_legend()

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
        """Export heightmap directly to Cities Skylines 2."""
        # Check if heightmap exists
        if self.heightmap is None or np.all(self.heightmap == 0):
            messagebox.showwarning(
                "No Terrain",
                "Please generate terrain first before exporting."
            )
            return

        # Import CS2 exporter
        from ..cs2_exporter import CS2Exporter
        from tkinter import simpledialog
        import tempfile

        # Ask for map name
        map_name = simpledialog.askstring(
            "Export to CS2",
            "Enter a name for your map:",
            initialvalue="My Custom Map"
        )

        if not map_name:
            return  # User cancelled

        # Export to temporary file first
        self.set_status("Exporting to Cities Skylines 2...")
        self.update_idletasks()

        try:
            # Create temporary files
            with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as tmp_heightmap:
                tmp_heightmap_path = tmp_heightmap.name

            # Save heightmap to temp file
            self.generator.heightmap = self.heightmap.copy()
            self.generator.export_png(tmp_heightmap_path)

            # Save worldmap if it exists
            tmp_worldmap_path = None
            if self.has_worldmap and self.worldmap is not None:
                with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as tmp_worldmap:
                    tmp_worldmap_path = tmp_worldmap.name
                self.worldmap.export_png(tmp_worldmap_path)

            # Export to CS2
            exporter = CS2Exporter()

            # Check if CS2 directory exists
            if exporter.get_cs2_directory() is None:
                if messagebox.askyesno(
                    "CS2 Directory Not Found",
                    "Cities Skylines 2 heightmaps directory not found.\n\n"
                    "Would you like to create it?\n\n"
                    "This is normal if you haven't run CS2 yet or if it's a fresh installation."
                ):
                    exporter.create_cs2_directory()
                else:
                    return

            # Export files
            heightmap_dest, worldmap_dest = exporter.export_to_cs2(
                heightmap_path=tmp_heightmap_path,
                map_name=map_name,
                worldmap_path=tmp_worldmap_path,
                overwrite=True
            )

            # Clean up temporary files
            import os
            os.unlink(tmp_heightmap_path)
            if tmp_worldmap_path:
                os.unlink(tmp_worldmap_path)

            self.set_status("Exported to CS2 successfully")

            # Show success message
            msg = f"Successfully exported to Cities Skylines 2!\n\n"
            msg += f"Map name: {map_name}\n"
            msg += f"Location: {heightmap_dest.parent}\n\n"
            msg += "You can now import this heightmap in CS2's Map Editor."

            messagebox.showinfo("Export Complete", msg)

        except Exception as e:
            messagebox.showerror("Export Error", f"Failed to export to CS2:\n{e}")
            self.set_status("CS2 export failed")

    def undo(self):
        """Undo the last operation."""
        if self.history.can_undo():
            self.history.undo()
            # CRITICAL FIX: Update GUI heightmap from generator after undo
            self.heightmap = self.generator.heightmap.copy()
            self.update_preview()
            self.set_status("Undo successful")
        else:
            self.set_status("Nothing to undo")

    def redo(self):
        """Redo the last undone operation."""
        if self.history.can_redo():
            self.history.redo()
            # CRITICAL FIX: Update GUI heightmap from generator after redo
            self.heightmap = self.generator.heightmap.copy()
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

        Uses the new pipeline (Sessions 2-8) hybrid zoned generation to achieve
        55-65% buildable terrain. Runs in background thread to prevent UI freezing.
        """
        # Get parameters from UI
        pipeline_params = self.param_panel.get_parameters()

        # Generate using pipeline
        self._generate_terrain_pipeline(pipeline_params)


    def _generate_terrain_pipeline(self, intuitive_params):
        """
        New pipeline terrain generation (Sessions 2-8).

        Hybrid zoned generation with hydraulic erosion to achieve 55-65% buildable terrain.
        Runs in background thread to prevent UI freezing (~3-4 minutes).

        Args:
            intuitive_params: Parameter dictionary from parameter panel
        """
        # Create progress dialog (only accepts parent and title)
        progress_dialog = ProgressDialog(
            self,
            title="Generating Terrain (Pipeline)"
        )
        # Initial status message
        progress_dialog.update(0, "Initializing pipeline...")

        def generate_in_background():
            """Run pipeline generation in background thread."""
            try:
                from ..generation.pipeline import TerrainGenerationPipeline

                # Create pipeline with seed
                seed = self.noise_gen.seed if hasattr(self, 'noise_gen') else None
                pipeline = TerrainGenerationPipeline(
                    resolution=self.resolution,
                    map_size_meters=14336.0,
                    seed=seed
                )

                # Extract pipeline parameters
                params = {
                    # Zone Generation (Session 2)
                    'target_coverage': intuitive_params.get('target_coverage', 0.70),
                    'zone_wavelength': intuitive_params.get('zone_wavelength', 6500.0),
                    'zone_octaves': intuitive_params.get('zone_octaves', 2),

                    # Terrain Generation (Session 3)
                    'base_amplitude': intuitive_params.get('base_amplitude', 0.2),
                    'min_amplitude_mult': intuitive_params.get('min_amplitude_mult', 0.3),
                    'max_amplitude_mult': intuitive_params.get('max_amplitude_mult', 1.0),
                    'terrain_wavelength': intuitive_params.get('terrain_wavelength', 1000.0),
                    'terrain_octaves': intuitive_params.get('terrain_octaves', 6),

                    # Ridge Enhancement (Session 5)
                    'ridge_strength': intuitive_params.get('ridge_strength', 0.2),
                    'ridge_octaves': intuitive_params.get('ridge_octaves', 5),
                    'ridge_wavelength': intuitive_params.get('ridge_wavelength', 1500.0),
                    'apply_ridges': intuitive_params.get('apply_ridges', False),  # Fixed: Match pipeline default

                    # Hydraulic Erosion (Session 4)
                    'num_particles': intuitive_params.get('num_particles', 100000),
                    'erosion_rate': intuitive_params.get('pipeline_erosion_rate', 0.5),
                    'deposition_rate': intuitive_params.get('pipeline_deposition_rate', 0.3),
                    'apply_erosion': intuitive_params.get('apply_erosion', False),  # Fixed: Match pipeline default

                    # River Analysis (Session 7)
                    'river_threshold_percentile': intuitive_params.get('river_threshold_percentile', 99.0),
                    'min_river_length': intuitive_params.get('min_river_length', 10),
                    'apply_rivers': intuitive_params.get('apply_rivers', True),

                    # Detail Addition (Session 8)
                    'detail_amplitude': intuitive_params.get('detail_amplitude', 0.02),
                    'detail_wavelength': intuitive_params.get('detail_wavelength', 75.0),
                    'apply_detail': intuitive_params.get('apply_detail', False),  # Fixed: Match pipeline default

                    # Constraint Verification (Session 8)
                    'target_buildable_min': intuitive_params.get('target_buildable_min', 55.0),
                    'target_buildable_max': intuitive_params.get('target_buildable_max', 65.0),
                    'apply_constraint_adjustment': intuitive_params.get('apply_constraint_adjustment', True),

                    # Control
                    'verbose': True  # Enable console output for debugging
                }

                # Update progress: Starting pipeline
                self.after(0, lambda: progress_dialog.update(0, "Stage 1/6: Generating buildability zones..."))

                # Generate terrain with pipeline
                terrain, stats = pipeline.generate(**params)

                # Update UI on main thread
                self.after(0, lambda: self._on_pipeline_complete(terrain, stats, progress_dialog))

            except Exception as e:
                import traceback
                error_details = traceback.format_exc()
                print(f"[PIPELINE ERROR] {error_details}")
                # Handle errors on main thread
                self.after(0, lambda: self._on_generation_error(str(e), progress_dialog))

        # Start background thread
        thread = threading.Thread(target=generate_in_background, daemon=True)
        thread.start()

        # Note: ProgressDialog shows automatically when created (Toplevel window)

    def _on_pipeline_complete(self, terrain: np.ndarray, stats: dict, progress_dialog: ProgressDialog):
        """
        Called when pipeline generation completes (on main thread).

        Args:
            terrain: Generated terrain heightmap
            stats: Pipeline statistics dictionary
            progress_dialog: Progress dialog to close
        """
        progress_dialog.close()

        # Update heightmap
        self.heightmap = terrain
        self.generator.heightmap = terrain.copy()

        # Update preview
        self.set_status("Generating preview...")
        self.update_idletasks()
        self.update_preview()

        # Update status indicators
        self.playable_status.config(text="Playable: ✓", foreground='green')

        # Show results dialog
        from .pipeline_results_dialog import show_results_dialog
        show_results_dialog(self, stats)

        # Update status
        final_buildable = stats.get('final_buildable_pct', 0.0)
        total_time = stats.get('total_pipeline_time', 0.0)
        self.set_status(f"Pipeline complete: {final_buildable:.1f}% buildable in {total_time:.1f}s")

        print(f"[GUI] Pipeline generation complete: {final_buildable:.1f}% buildable")

    def _on_generation_error(self, error_message: str, progress_dialog: ProgressDialog):
        """
        Called when generation fails (on main thread).

        Args:
            error_message: Error message to display
            progress_dialog: Progress dialog to close
        """
        progress_dialog.close()

        # Show error dialog
        messagebox.showerror(
            "Generation Error",
            f"Terrain generation failed:\n\n{error_message}\n\n"
            f"Please check the console for details."
        )

        # Update status
        self.set_status("Generation failed")

        print(f"[GUI] Generation error: {error_message}")

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

    def toggle_legend(self):
        """Toggle elevation legend visibility."""
        self.show_legend = not self.show_legend

        # Show/hide legend frame
        if self.show_legend:
            self.legend_frame.pack(side=tk.RIGHT, fill=tk.Y, padx=(5, 0))
            self.update_legend()
        else:
            self.legend_frame.pack_forget()

        status = "shown" if self.show_legend else "hidden"
        self.set_status(f"Elevation legend {status}")

    def toggle_water_overlay(self):
        """Toggle water features overlay visibility."""
        self.show_water_overlay = not self.show_water_overlay

        # Update preview to show/hide water overlay
        if self.heightmap is not None:
            self.update_preview()

        status = "shown" if self.show_water_overlay else "hidden"
        self.set_status(f"Water overlay {status}")

    def update_legend(self):
        """
        Update the elevation legend with current colormap.

        Draws a vertical color gradient matching the terrain preview
        with elevation labels from 0m to 4096m.
        """
        from PIL import Image, ImageTk, ImageDraw, ImageFont

        # Clear existing canvas
        self.legend_canvas.delete("all")

        # Generate color gradient
        preview_gen = PreviewGenerator(self.heightmap, height_scale=4096.0)
        gradient_height = 400
        gradient_width = 30  # Reduced from 40 to save space for labels

        # Create vertical gradient array
        gradient = np.linspace(1.0, 0.0, gradient_height)[:, np.newaxis]
        gradient = np.repeat(gradient, gradient_width, axis=1)

        # Create temp preview generator for gradient
        temp_gen = PreviewGenerator(gradient, height_scale=4096.0)
        legend_colors = temp_gen.apply_colormap(colormap='terrain', min_height=0.0, max_height=1.0)

        # Convert to PIL Image
        legend_img = Image.fromarray(legend_colors)

        # Convert to PhotoImage for canvas
        self.legend_photo = ImageTk.PhotoImage(legend_img)

        # Draw on canvas - positioned at left edge
        self.legend_canvas.create_image(10, 0, anchor=tk.NW, image=self.legend_photo)

        # Add elevation labels
        try:
            font = ImageFont.truetype("arial.ttf", 10)
        except:
            font = None

        num_labels = 9
        for i in range(num_labels):
            fraction = i / (num_labels - 1)
            elevation_m = 4096.0 * (1.0 - fraction)

            y_pos = int(fraction * gradient_height)

            # Format label
            if elevation_m >= 1000:
                label = f"{elevation_m/1000:.1f}km"
            else:
                label = f"{int(elevation_m)}m"

            # Draw label to right of gradient (gradient ends at x=40, add 5px spacing)
            self.legend_canvas.create_text(
                45, y_pos,
                text=label,
                anchor=tk.W,
                font=('Arial', 9)
            )

    def generate_worldmap(self):
        """
        Generate worldmap from current playable heightmap.

        Worldmap shows terrain beyond the playable area for visual context.
        Only generate after playable area is finalized (performance optimization).
        """
        # Check if playable heightmap exists
        if self.heightmap is None or np.all(self.heightmap == 0):
            messagebox.showwarning(
                "No Playable Area",
                "Please generate the playable area first.\n\n"
                "The worldmap embeds the playable area, so you need to "
                "create that before generating the worldmap."
            )
            return

        # Confirm generation (takes time)
        if not messagebox.askyesno(
            "Generate Worldmap",
            "Generate worldmap from current playable area?\n\n"
            "This will create terrain surrounding the playable area.\n"
            "Generation may take 1-2 minutes."
        ):
            return

        # Create progress dialog (only accepts parent and title)
        progress_dialog = ProgressDialog(
            self,
            title="Generating Worldmap"
        )
        # Initial status message
        progress_dialog.update(0, "Generating worldmap with embedded playable area...\nThis may take 1-2 minutes.")

        def generate_worldmap_in_background():
            """Run worldmap generation in background thread."""
            try:
                from ..worldmap_generator import WorldmapGenerator, create_worldmap_preset

                # Create worldmap with ocean surrounding
                worldmap_gen = create_worldmap_preset(
                    preset='ocean',
                    playable_heightmap=self.heightmap,
                    noise_generator=self.noise_gen
                )

                # Update UI on main thread
                self.after(0, lambda: self._on_worldmap_complete(worldmap_gen, progress_dialog))

            except Exception as e:
                # Handle errors on main thread
                self.after(0, lambda: self._on_generation_error(str(e), progress_dialog))

        # Start background thread
        thread = threading.Thread(target=generate_worldmap_in_background, daemon=True)
        thread.start()

        # Note: ProgressDialog shows automatically when created (Toplevel window)

    def _on_worldmap_complete(self, worldmap_gen, progress_dialog: ProgressDialog):
        """Called when worldmap generation completes."""
        self.worldmap = worldmap_gen
        self.has_worldmap = True
        progress_dialog.close()

        # Update status indicator
        self.worldmap_status.config(text="Worldmap: ✓", foreground='green')
        self.set_status("Worldmap generated successfully")

        messagebox.showinfo(
            "Worldmap Complete",
            "Worldmap generated successfully!\n\n"
            "When you save/export, both the playable area and worldmap will be included."
        )

    def add_rivers(self):
        """Add rivers to the heightmap using D8 flow accumulation algorithm."""
        # Check if heightmap exists
        if self.heightmap is None or np.all(self.heightmap == 0):
            messagebox.showwarning(
                "No Terrain",
                "Please generate terrain first before adding rivers."
            )
            return

        # Import river generator
        from ..features.river_generator import RiverGenerator, AddRiverCommand

        # Ask for parameters
        from tkinter import simpledialog

        num_rivers = simpledialog.askinteger(
            "River Generation",
            "Number of rivers to generate:",
            initialvalue=3,
            minvalue=1,
            maxvalue=20
        )

        if num_rivers is None:
            return  # User cancelled

        # Generate rivers with progress feedback
        progress = ProgressDialog(self, "Generating Rivers")

        try:
            # Step 1: Initialize
            progress.update(0, f"Initializing river generation...")
            command = AddRiverCommand(
                self.generator,
                num_rivers=num_rivers,
                threshold=500,  # Flow accumulation threshold
                description=f"Add {num_rivers} rivers"
            )

            # Step 2: Calculate flow (happens inside execute)
            progress.update(20, "Calculating flow directions...")

            # Step 3: Generate rivers
            progress.update(40, f"Carving {num_rivers} river paths...")
            self.history.execute(command)

            # Step 4: Update heightmap
            progress.update(80, "Updating heightmap...")
            self.heightmap = self.generator.heightmap.copy()

            # Step 5: Update preview
            progress.update(90, "Updating preview...")
            self.update_preview()

            progress.update(100, "Complete!")

            self.set_status(f"Generated {num_rivers} rivers successfully")
            messagebox.showinfo(
                "Rivers Added",
                f"Successfully generated {num_rivers} river(s) using natural flow patterns."
            )

        except Exception as e:
            messagebox.showerror("River Generation Error", f"Failed to generate rivers:\n{e}")
            self.set_status("River generation failed")

        finally:
            progress.close()

    def add_lakes(self):
        """Add lakes to the heightmap using watershed segmentation algorithm."""
        # Check if heightmap exists
        if self.heightmap is None or np.all(self.heightmap == 0):
            messagebox.showwarning(
                "No Terrain",
                "Please generate terrain first before adding lakes."
            )
            return

        # Import lake generator
        from ..features.water_body_generator import WaterBodyGenerator, AddLakeCommand

        # Ask for parameters
        from tkinter import simpledialog

        num_lakes = simpledialog.askinteger(
            "Lake Generation",
            "Number of lakes to generate:",
            initialvalue=5,
            minvalue=1,
            maxvalue=20
        )

        if num_lakes is None:
            return  # User cancelled

        # Generate lakes with progress feedback
        progress = ProgressDialog(self, "Generating Lakes")

        try:
            # Step 1: Initialize
            progress.update(0, f"Initializing lake generation...")
            command = AddLakeCommand(
                self.generator,
                num_lakes=num_lakes,
                min_depth=0.02,  # 2% of height range
                min_size=25,     # Minimum 25 pixels
                description=f"Add {num_lakes} lakes"
            )

            # Step 2: Analyze terrain
            progress.update(20, "Analyzing terrain depressions...")

            # Step 3: Generate lakes
            progress.update(40, f"Creating {num_lakes} lakes...")
            self.history.execute(command)

            # Step 4: Update heightmap
            progress.update(80, "Updating heightmap...")
            self.heightmap = self.generator.heightmap.copy()

            # Auto-detect water level for overlay (if not already set)
            # Set to minimum terrain height + 5% to capture lake surfaces
            if self.water_level is None:
                min_height = float(np.min(self.heightmap))
                height_range = float(np.max(self.heightmap) - min_height)
                self.water_level = min_height + (height_range * 0.05)

            # Step 5: Update preview
            progress.update(90, "Updating preview...")
            self.update_preview()

            progress.update(100, "Complete!")

            self.set_status(f"Generated {num_lakes} lakes successfully")
            messagebox.showinfo(
                "Lakes Added",
                f"Successfully generated {num_lakes} lake(s) in natural depressions."
            )

        except Exception as e:
            messagebox.showerror("Lake Generation Error", f"Failed to generate lakes:\n{e}")
            self.set_status("Lake generation failed")

        finally:
            progress.close()

    def add_coastal(self):
        """Add coastal features (beaches and cliffs) based on slope analysis."""
        # Check if heightmap exists
        if self.heightmap is None or np.all(self.heightmap == 0):
            messagebox.showwarning(
                "No Terrain",
                "Please generate terrain first before adding coastal features."
            )
            return

        # Import coastal generator
        from ..features.coastal_generator import CoastalGenerator, AddCoastalFeaturesCommand

        # Get actual terrain height range for better defaults
        min_height = float(np.min(self.heightmap))
        max_height = float(np.max(self.heightmap))
        height_range = max_height - min_height

        # Calculate a reasonable default water level (20% of actual range above minimum)
        default_water_level = min_height + (height_range * 0.2)

        # Ask for water level
        from tkinter import simpledialog

        # Show dialog with actual height information
        water_level = simpledialog.askfloat(
            "Coastal Features",
            f"Water level:\n\n"
            f"Terrain range: {min_height:.3f} to {max_height:.3f}\n"
            f"Suggested: {default_water_level:.3f} (20% above minimum)\n\n"
            f"Enter water level (0.0-1.0):",
            initialvalue=default_water_level,
            minvalue=0.0,
            maxvalue=1.0
        )

        if water_level is None:
            return  # User cancelled

        # Generate coastal features with progress feedback
        progress = ProgressDialog(self, "Generating Coastal Features")

        try:
            # Step 1: Initialize
            progress.update(0, "Initializing coastal generation...")
            command = AddCoastalFeaturesCommand(
                self.generator,
                water_level=water_level,
                add_beaches=True,
                add_cliffs=True,
                beach_intensity=0.5,
                cliff_intensity=0.5,
                description="Add coastal features"
            )

            # Step 2: Analyze slopes
            progress.update(20, "Analyzing terrain slopes...")

            # Step 3: Generate features
            progress.update(40, "Creating beaches and cliffs...")
            self.history.execute(command)

            # Step 4: Update heightmap
            progress.update(80, "Updating heightmap...")
            self.heightmap = self.generator.heightmap.copy()

            # Store water level for overlay visualization
            self.water_level = water_level

            # Step 5: Update preview
            progress.update(90, "Updating preview...")
            self.update_preview()

            progress.update(100, "Complete!")

            self.set_status("Generated coastal features successfully")
            messagebox.showinfo(
                "Coastal Features Added",
                "Successfully generated beaches and cliffs based on slope analysis."
            )

        except Exception as e:
            messagebox.showerror("Coastal Generation Error", f"Failed to generate coastal features:\n{e}")
            self.set_status("Coastal generation failed")

        finally:
            progress.close()

    def show_analysis(self):
        """Show comprehensive terrain analysis."""
        # Check if heightmap exists
        if self.heightmap is None or np.all(self.heightmap == 0):
            messagebox.showwarning(
                "No Terrain",
                "Please generate terrain first before analyzing."
            )
            return

        # Import terrain analyzer
        from ..analysis.terrain_analyzer import TerrainAnalyzer

        self.set_status("Analyzing terrain...")
        self.update_idletasks()

        try:
            # Create analyzer
            analyzer = TerrainAnalyzer(self.heightmap, height_scale=4096.0, map_size_meters=14336.0)

            # Get statistics
            stats = analyzer.get_statistics()

            # Format analysis results
            analysis_text = "Terrain Analysis Results\n"
            analysis_text += "=" * 50 + "\n\n"

            analysis_text += "Height Distribution:\n"
            analysis_text += f"  Min elevation: {stats['min_height']:.3f} ({stats['min_height']*4096:.1f}m)\n"
            analysis_text += f"  Max elevation: {stats['max_height']:.3f} ({stats['max_height']*4096:.1f}m)\n"
            analysis_text += f"  Mean elevation: {stats['mean_height']:.3f} ({stats['mean_height']*4096:.1f}m)\n"
            analysis_text += f"  Median elevation: {stats['median_height']:.3f} ({stats['median_height']*4096:.1f}m)\n"
            analysis_text += f"  Range: {stats['range_height']:.3f} ({stats['range_height']*4096:.1f}m)\n"
            analysis_text += f"  Std deviation: {stats['std_height']:.3f}\n\n"

            analysis_text += "Quartiles:\n"
            analysis_text += f"  25th percentile: {stats['percentile_25']:.3f} ({stats['percentile_25']*4096:.1f}m)\n"
            analysis_text += f"  50th percentile: {stats['percentile_50']:.3f} ({stats['percentile_50']*4096:.1f}m)\n"
            analysis_text += f"  75th percentile: {stats['percentile_75']:.3f} ({stats['percentile_75']*4096:.1f}m)\n\n"

            analysis_text += "Slope Analysis:\n"
            analysis_text += f"  Mean slope: {stats['mean_slope']:.2f} degrees\n"
            analysis_text += f"  Max slope: {stats['max_slope']:.2f} degrees\n"
            analysis_text += f"  Flat areas (<5°): {stats['flat_percent']:.1f}%\n"
            analysis_text += f"  Steep areas (>45°): {stats['steep_percent']:.1f}%\n\n"

            analysis_text += "Terrain Classification:\n"
            # Classify terrain based on statistics
            if stats['mean_slope'] < 5:
                terrain_type = "Flat Plains"
            elif stats['mean_slope'] < 15:
                terrain_type = "Rolling Hills"
            elif stats['mean_slope'] < 30:
                terrain_type = "Mountains"
            else:
                terrain_type = "Steep Mountains"

            analysis_text += f"  Type: {terrain_type}\n"
            analysis_text += f"  Buildable area: {stats['flat_percent']:.1f}%\n"

            # Show in dialog
            from tkinter import scrolledtext

            # Create analysis window
            analysis_window = tk.Toplevel(self)
            analysis_window.title("Terrain Analysis")
            analysis_window.geometry("600x500")

            # Add text widget with scrollbar
            text_widget = scrolledtext.ScrolledText(
                analysis_window,
                wrap=tk.WORD,
                font=('Courier New', 10)
            )
            text_widget.pack(expand=True, fill=tk.BOTH, padx=10, pady=10)
            text_widget.insert(1.0, analysis_text)
            text_widget.configure(state='disabled')  # Make read-only

            # Add close button
            close_btn = ttk.Button(
                analysis_window,
                text="Close",
                command=analysis_window.destroy
            )
            close_btn.pack(pady=5)

            self.set_status("Analysis complete")

        except Exception as e:
            messagebox.showerror("Analysis Error", f"Failed to analyze terrain:\n{e}")
            self.set_status("Analysis failed")

    def show_3d_preview(self):
        """
        Show 3D preview of heightmap.

        Why separate window:
        - Non-blocking (main GUI stays responsive)
        - Can rotate/zoom independently
        - Can open multiple previews
        - Easy to close when done

        Performance:
        - Downsamples to 256x256 (256x data reduction!)
        - Render time: ~0.5s
        - Smooth 60fps rotation
        - Uses matplotlib (built-in, no extra dependencies)
        """
        # Check if heightmap exists
        if self.heightmap is None or np.all(self.heightmap == 0):
            messagebox.showwarning(
                "No Terrain",
                "Please generate terrain first before showing 3D preview."
            )
            return

        self.set_status("Generating 3D preview...")
        self.update_idletasks()

        try:
            # Import 3D preview module
            from ..preview_3d import generate_3d_preview

            # Get elevation range for display
            min_height = float(np.min(self.heightmap))
            max_height = float(np.max(self.heightmap))
            elevation_range = (min_height * 4096, max_height * 4096)  # Convert to meters

            # Generate 3D preview
            # Uses 256x256 resolution (fast and smooth)
            # Vertical exaggeration 2.0x (makes features visible)
            preview = generate_3d_preview(
                self.heightmap,
                resolution=256,
                vertical_exaggeration=2.0,
                elevation_range=elevation_range
            )

            # Status bar shows usage info instead of popup (prevents focus stealing)
            self.set_status("3D preview: Left-drag=rotate, Right-drag=pan, Scroll=zoom")

            # REMOVED: messagebox.showinfo() that was stealing focus
            # Usage info now shown in status bar instead

        except Exception as e:
            messagebox.showerror("3D Preview Error", f"Failed to generate 3D preview:\n{e}")
            self.set_status("3D preview failed")
            import traceback
            traceback.print_exc()

    def show_docs(self):
        """Show documentation."""
        import webbrowser
        from pathlib import Path

        # Try to open README.md in browser or system viewer
        readme_path = Path(__file__).parent.parent.parent / "README.md"

        if readme_path.exists():
            # Try to open with default application
            try:
                webbrowser.open(readme_path.as_uri())
                self.set_status("Opened documentation")
            except Exception as e:
                messagebox.showinfo(
                    "Documentation",
                    f"Documentation is available at:\n{readme_path}\n\n"
                    f"Key features:\n"
                    f"- Generate 4096x4096 heightmaps for CS2\n"
                    f"- 7 terrain presets (Mountains, Islands, etc.)\n"
                    f"- Water features (Rivers, Lakes, Coastal)\n"
                    f"- Full undo/redo support\n"
                    f"- Direct export to CS2\n\n"
                    f"See README.md for complete documentation."
                )
        else:
            messagebox.showinfo(
                "Documentation",
                "CS2 Heightmap Generator v2.1\n\n"
                "Key Features:\n"
                "- Generate 4096x4096 heightmaps for CS2\n"
                "- Ultra-fast generation (<1 second)\n"
                "- 7 terrain presets\n"
                "- Water features (Rivers, Lakes, Coastal)\n"
                "- Terrain analysis tools\n"
                "- Full undo/redo support\n"
                "- Direct export to CS2\n\n"
                "For complete documentation, see README.md in the project root."
            )

    def _on_tool_click(self, x: int, y: int, **kwargs):
        """
        Handle tool application at clicked position.

        Args:
            x, y: Heightmap coordinates
            **kwargs: Additional args (is_drag_start, is_drag, is_drag_end)

        Returns:
            bool: True if tool was applied, False if tool is 'none'

        Why return value:
        - Canvas needs to know if tool was active
        - If False, canvas enables pan mode automatically
        - Clean separation of concerns
        """
        # Get current tool from tool palette
        current_tool = self.tool_palette.current_tool.get()

        if current_tool == 'none':
            # No tool selected - return False so canvas enables panning
            return False

        # Check if terrain exists
        if self.heightmap is None or np.all(self.heightmap == 0):
            self.set_status("Please generate terrain first")
            return False

        # Import terrain editor commands
        from ..features.terrain_editor import BrushCommand, AddFeatureCommand

        # Ensure generator has current heightmap
        self.generator.heightmap = self.heightmap.copy()

        # Get brush parameters
        brush_params = self.tool_palette.get_brush_parameters()
        radius = brush_params['size']
        strength = brush_params['strength']

        # Handle brush tools
        if current_tool in ['raise', 'lower', 'smooth', 'flatten']:
            # Apply brush tool
            command = BrushCommand(
                self.generator,
                x=x,
                y=y,
                radius=radius,
                strength=strength,
                operation=current_tool,
                description=f"{current_tool.capitalize()} at ({x}, {y})"
            )
            self.history.execute(command)
            self.heightmap = self.generator.heightmap.copy()
            self.update_preview()
            self.set_status(f"Applied {current_tool} tool")
            return True

        # Handle feature tools (single-click placement)
        elif current_tool == 'hill':
            command = AddFeatureCommand(
                self.generator,
                feature_type='hill',
                params={'x': x, 'y': y, 'radius': radius, 'height': strength * 0.3},
                description=f"Add hill at ({x}, {y})"
            )
            self.history.execute(command)
            self.heightmap = self.generator.heightmap.copy()
            self.update_preview()
            self.set_status(f"Added hill at ({x}, {y})")
            return True

        elif current_tool == 'depression':
            command = AddFeatureCommand(
                self.generator,
                feature_type='depression',
                params={'x': x, 'y': y, 'radius': radius, 'depth': strength * 0.3},
                description=f"Add depression at ({x}, {y})"
            )
            self.history.execute(command)
            self.heightmap = self.generator.heightmap.copy()
            self.update_preview()
            self.set_status(f"Added depression at ({x}, {y})")
            return True

        # Handle two-point tools (ridge, valley)
        # These tools require click-drag-release interaction:
        # - is_drag_start=True: Set flag for canvas to track first point
        # - is_drag_end=True + first_point: Execute command with both points
        elif current_tool in ['ridge', 'valley']:
            if kwargs.get('is_drag_start'):
                # First click - tell canvas this is a two-point tool
                self.preview.is_two_point_tool = True
                self.set_status(f"Click and drag to place {current_tool}")
                return True
            elif kwargs.get('is_drag_end') and 'first_point' in kwargs:
                # Release - execute command with both points
                x1, y1 = kwargs['first_point']
                x2, y2 = x, y

                # Determine feature parameters
                if current_tool == 'ridge':
                    feature_type = 'ridge'
                    height = strength * 0.3
                    params = {
                        'x1': x1, 'y1': y1,
                        'x2': x2, 'y2': y2,
                        'width': radius,
                        'height': height
                    }
                    description = f"Add ridge from ({x1}, {y1}) to ({x2}, {y2})"
                else:  # valley
                    feature_type = 'valley'
                    depth = strength * 0.3
                    params = {
                        'x1': x1, 'y1': y1,
                        'x2': x2, 'y2': y2,
                        'width': radius,
                        'depth': depth
                    }
                    description = f"Add valley from ({x1}, {y1}) to ({x2}, {y2})"

                # Execute command
                command = AddFeatureCommand(
                    self.generator,
                    feature_type=feature_type,
                    params=params,
                    description=description
                )
                self.history.execute(command)
                self.heightmap = self.generator.heightmap.copy()
                self.update_preview()
                self.set_status(f"Added {current_tool}")
                return True
            else:
                # Intermediate drag events - ignore for two-point tools
                return True

        # Unknown tool
        return False

    def show_about(self):
        """Show about dialog."""
        messagebox.showinfo(
            "About",
            "CS2 Heightmap Generator v2.1.0\n\n"
            "A professional tool for generating Cities Skylines 2 heightmaps.\n\n"
            "Features:\n"
            "- Ultra-fast terrain generation (<1 second for 4096x4096)\n"
            "- Procedural noise generation with 7 presets\n"
            "- Water features (rivers, lakes, coastal)\n"
            "- Terrain analysis tools\n"
            "- Elevation legend with quantitative heights\n"
            "- Full undo/redo support\n"
            "- Direct export to CS2\n\n"
            "Performance: 60-140x faster than v2.0\n"
            "Developed with Claude Code (Anthropic)"
        )


def main():
    """Entry point for GUI application."""
    app = HeightmapGUI()
    app.mainloop()


if __name__ == "__main__":
    main()
