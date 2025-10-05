"""
CS2 Heightmap Generator - Parameter Control Panel

Parameter controls for terrain generation with preset selection.

Features:
- Preset selector (7 terrain types)
- Parameter sliders (scale, octaves, persistence, lacunarity)
- Resolution selector
- Debounced updates (500ms)
- Real-time value display

Why This Design:
- Sliders intuitive for continuous values
- Presets for quick terrain types
- Debouncing prevents UI lag
- Standard pattern (used in audio/video software)
"""

import tkinter as tk
from tkinter import ttk
from typing import Dict, Callable, Optional
from ..terrain_parameter_mapper import (
    TerrainParameterMapper,
    get_preset_parameters,
    get_preset_description
)


class ParameterPanel(ttk.Frame):
    """
    Parameter control panel for terrain generation.

    Layout:
    - Preset selector (radio buttons)
    - Resolution dropdown
    - Parameter sliders:
      * Scale (10-500)
      * Octaves (1-10)
      * Persistence (0.1-0.9)
      * Lacunarity (1.5-3.5)
    - Generate button

    Why these parameters:
    - Scale: Controls feature size (mountains vs hills)
    - Octaves: Detail level (more = more detail)
    - Persistence: Roughness (higher = rougher)
    - Lacunarity: Frequency multiplier (standard: 2.0)

    These are the standard Perlin noise parameters used everywhere.
    """

    def __init__(self, parent, gui):
        """
        Initialize parameter panel.

        Args:
            parent: Parent widget
            gui: Reference to main GUI (for callbacks)
        """
        super().__init__(parent, width=300)
        self.gui = gui

        # Intuitive parameter values (what users actually understand)
        # NOTE: Resolution is FIXED at 4096x4096 per CS2 wiki requirements
        self.params = {
            'preset': tk.StringVar(value='mountains'),
            'resolution': tk.IntVar(value=4096),  # FIXED: CS2 requirement
            'roughness': tk.DoubleVar(value=70.0),  # 0-100: smooth ↔ jagged
            'feature_size': tk.DoubleVar(value=60.0),  # 0-100: small ↔ large
            'detail_level': tk.DoubleVar(value=75.0),  # 0-100: simple ↔ intricate
            'height_variation': tk.DoubleVar(value=85.0)  # 0-100: flat ↔ extreme
        }

        # Advanced mode (technical parameters) - hidden by default
        self.show_advanced = tk.BooleanVar(value=False)

        # Create widgets
        self._create_widgets()

    def _create_widgets(self):
        """Create all parameter control widgets using tabs for compact layout."""
        # Title
        title = ttk.Label(self, text="Terrain Generator", font=('Arial', 12, 'bold'))
        title.pack(pady=(10, 5))

        # Create tabbed interface (saves ~200px vertical space!)
        self.notebook = ttk.Notebook(self)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # Tab 1: Basic terrain parameters
        self._create_basic_tab()

        # Tab 2: Water features
        self._create_water_tab()

        # Tab 3: Advanced options (hidden by default, can be expanded later)
        # self._create_advanced_tab()  # Future: technical parameters

        # Generate button (always visible at bottom)
        generate_btn = ttk.Button(
            self,
            text="Generate Playable Terrain",
            command=self._on_generate,
            style='Accent.TButton'  # Make it prominent
        )
        generate_btn.pack(pady=10, padx=10, fill=tk.X)

    def _create_basic_tab(self):
        """Create basic terrain parameters tab."""
        tab = ttk.Frame(self.notebook, padding=10)
        self.notebook.add(tab, text="Basic")

        # Preset selector (dropdown instead of radio buttons - saves space!)
        preset_frame = ttk.LabelFrame(tab, text="Terrain Preset", padding=10)
        preset_frame.pack(fill=tk.X, pady=(0, 10))

        presets = [
            ('Mountains', 'mountains'),
            ('Hills', 'hills'),
            ('Flat', 'flat'),
            ('Islands', 'islands'),
            ('Canyons', 'canyons'),
            ('Highlands', 'highlands'),
            ('Mesas', 'mesas')
        ]

        # Dropdown instead of 7 radio buttons (saves ~140px!)
        # Map display names to internal values
        self.preset_map = {label: value for label, value in presets}
        self.preset_reverse_map = {value: label for label, value in presets}

        preset_combo = ttk.Combobox(
            preset_frame,
            values=[label for label, _ in presets],
            state='readonly',
            width=20
        )
        # Set initial value
        preset_combo.set(self.preset_reverse_map.get(self.params['preset'].get(), 'Mountains'))
        preset_combo.pack(fill=tk.X)
        preset_combo.bind('<<ComboboxSelected>>', lambda e: self._on_preset_combo_change(preset_combo))

        # Resolution info (compact)
        res_frame = ttk.LabelFrame(tab, text="Resolution", padding=10)
        res_frame.pack(fill=tk.X, pady=(0, 10))
        ttk.Label(
            res_frame,
            text="4096×4096 (CS2 Required)",
            font=('Arial', 9, 'bold')
        ).pack()

        # Parameter sliders (compact layout)
        self._create_parameter_sliders_compact(tab)

    def _create_parameter_sliders_compact(self, parent):
        """Create compact parameter sliders."""
        frame = ttk.LabelFrame(parent, text="Terrain Characteristics", padding=10)
        frame.pack(fill=tk.X, pady=(0, 10))

        # Create sliders in compact format
        self._create_slider(frame, "Roughness:", self.params['roughness'], 0.0, 100.0, 1.0, "smooth ↔ jagged")
        self._create_slider(frame, "Feature Size:", self.params['feature_size'], 0.0, 100.0, 1.0, "small ↔ large")
        self._create_slider(frame, "Detail Level:", self.params['detail_level'], 0.0, 100.0, 1.0, "simple ↔ intricate")
        self._create_slider(frame, "Height Variation:", self.params['height_variation'], 0.0, 100.0, 1.0, "flat ↔ extreme")

    def _create_water_tab(self):
        """Create water features tab."""
        tab = ttk.Frame(self.notebook, padding=10)
        self.notebook.add(tab, text="Water")

        # Info label
        info = ttk.Label(
            tab,
            text="Add water features to terrain\n(Generate terrain first)",
            font=('Arial', 9),
            justify=tk.CENTER,
            foreground='gray30'
        )
        info.pack(pady=(0, 15))

        # Rivers button
        rivers_btn = ttk.Button(
            tab,
            text="Add Rivers",
            command=self.gui.add_rivers
        )
        rivers_btn.pack(fill=tk.X, pady=5)

        # Lakes button
        lakes_btn = ttk.Button(
            tab,
            text="Add Lakes",
            command=self.gui.add_lakes
        )
        lakes_btn.pack(fill=tk.X, pady=5)

        # Coastal features button
        coastal_btn = ttk.Button(
            tab,
            text="Add Coastal Features",
            command=self.gui.add_coastal
        )
        coastal_btn.pack(fill=tk.X, pady=5)

        # Separator
        ttk.Separator(tab, orient=tk.HORIZONTAL).pack(fill=tk.X, pady=15)

        # 3D Preview button
        preview_btn = ttk.Button(
            tab,
            text="3D Preview",
            command=self.gui.show_3d_preview
        )
        preview_btn.pack(fill=tk.X, pady=5)

    def _create_preset_selector(self):
        """Create preset selection radio buttons."""
        frame = ttk.LabelFrame(self, text="Terrain Preset", padding=10)
        frame.pack(fill=tk.X, padx=10, pady=5)

        presets = [
            ('Flat', 'flat'),
            ('Hills', 'hills'),
            ('Mountains', 'mountains'),
            ('Islands', 'islands'),
            ('Canyons', 'canyons'),
            ('Highlands', 'highlands'),
            ('Mesas', 'mesas')
        ]

        for label, value in presets:
            rb = ttk.Radiobutton(
                frame,
                text=label,
                variable=self.params['preset'],
                value=value,
                command=self._on_preset_change
            )
            rb.pack(anchor=tk.W)

    def _create_resolution_display(self):
        """
        Display fixed resolution (not selectable).

        Why fixed:
        - CS2 wiki specifies heightmaps MUST be 4096x4096
        - This is not optional - it's a game requirement
        - 16-bit grayscale PNG format
        - Default height scale: 4096 meters

        Reference: wiki_instructions.pdf, page 1:
        "Heightmaps should be 4096x4096 resolution"
        """
        frame = ttk.LabelFrame(self, text="Resolution (CS2 Requirement)", padding=10)
        frame.pack(fill=tk.X, padx=10, pady=5)

        # Display fixed resolution with explanation
        info_label = ttk.Label(
            frame,
            text="4096 x 4096 pixels\n(Required by Cities Skylines 2)",
            font=('Arial', 10, 'bold'),
            justify=tk.CENTER
        )
        info_label.pack(pady=5)

        # Add informational note
        note_label = ttk.Label(
            frame,
            text="Resolution is fixed per CS2 specifications.\nAll heightmaps must be exactly 4096x4096.",
            font=('Arial', 8),
            justify=tk.CENTER,
            foreground='gray30'
        )
        note_label.pack()

    def _create_parameter_sliders(self):
        """Create intuitive parameter sliders with labels."""
        frame = ttk.LabelFrame(self, text="Terrain Characteristics", padding=10)
        frame.pack(fill=tk.X, padx=10, pady=5)

        # Roughness slider (0-100%)
        self._create_slider(
            frame,
            "Roughness:",
            self.params['roughness'],
            from_=0.0,
            to=100.0,
            resolution=1.0,
            description="smooth ↔ jagged"
        )

        # Feature Size slider (0-100%)
        self._create_slider(
            frame,
            "Feature Size:",
            self.params['feature_size'],
            from_=0.0,
            to=100.0,
            resolution=1.0,
            description="small ↔ large"
        )

        # Detail Level slider (0-100%)
        self._create_slider(
            frame,
            "Detail Level:",
            self.params['detail_level'],
            from_=0.0,
            to=100.0,
            resolution=1.0,
            description="simple ↔ intricate"
        )

        # Height Variation slider (0-100%)
        self._create_slider(
            frame,
            "Height Variation:",
            self.params['height_variation'],
            from_=0.0,
            to=100.0,
            resolution=1.0,
            description="flat ↔ extreme"
        )

    def _create_slider(self, parent, label: str, variable, from_: float, to: float, resolution: float, description: str = ""):
        """
        Create a labeled slider with value display and description.

        Args:
            parent: Parent widget
            label: Slider label
            variable: Tkinter variable
            from_: Minimum value
            to: Maximum value
            resolution: Step size
            description: Optional description text (e.g., "smooth ↔ jagged")

        Why this pattern:
        - Label shows what parameter is
        - Value display shows current value (with % for 0-100 range)
        - Description shows what the range means
        - Slider for intuitive adjustment
        """
        # Container frame
        container = ttk.Frame(parent)
        container.pack(fill=tk.X, pady=8)

        # Label and value
        label_frame = ttk.Frame(container)
        label_frame.pack(fill=tk.X)

        ttk.Label(label_frame, text=label, width=15, anchor=tk.W).pack(side=tk.LEFT)

        # Format value with % for 0-100 ranges
        if from_ == 0.0 and to == 100.0:
            value_text = tk.StringVar()
            value_text.set(f"{variable.get():.0f}%")
            variable.trace_add('write', lambda *args: value_text.set(f"{variable.get():.0f}%"))
            value_label = ttk.Label(label_frame, textvariable=value_text, width=8, anchor=tk.E)
        else:
            value_label = ttk.Label(label_frame, textvariable=variable, width=8, anchor=tk.E)
        value_label.pack(side=tk.RIGHT)

        # Slider
        slider = ttk.Scale(
            container,
            from_=from_,
            to=to,
            variable=variable,
            orient=tk.HORIZONTAL,
            command=lambda v: self._on_parameter_change()
        )
        slider.pack(fill=tk.X)

        # Description (if provided)
        if description:
            desc_label = ttk.Label(
                container,
                text=description,
                font=('Arial', 8, 'italic'),
                foreground='gray40'
            )
            desc_label.pack()

    def _on_preset_combo_change(self, combo):
        """Handle preset combobox selection change."""
        selected_label = combo.get()
        preset_value = self.preset_map.get(selected_label)
        if preset_value:
            self.params['preset'].set(preset_value)
            self._on_preset_change()

    def _on_preset_change(self):
        """Handle preset selection change - updates intuitive parameters."""
        preset = self.params['preset'].get()

        try:
            # Get intuitive parameters for this preset
            params = get_preset_parameters(preset)

            # Update intuitive parameter sliders
            self.params['roughness'].set(params['roughness'])
            self.params['feature_size'].set(params['feature_size'])
            self.params['detail_level'].set(params['detail_level'])
            self.params['height_variation'].set(params['height_variation'])

            # Don't auto-generate - let user click Generate button
            # This gives user control over when generation happens
            self.gui.set_status(f"Preset '{preset}' loaded - Click 'Generate Playable' to apply")

        except KeyError:
            # Unknown preset, ignore
            pass

    # Resolution change handler removed - resolution is now fixed at 4096x4096

    def _on_parameter_change(self):
        """
        Handle parameter slider change.

        Don't auto-generate - just update status.
        User must click 'Generate Playable' to apply changes.
        """
        # Show user that parameters changed (no auto-generation)
        self.gui.set_status("Parameters changed - Click 'Generate Playable' to apply")

    def _on_generate(self):
        """Handle Generate button click."""
        self.gui.generate_terrain()

    def get_parameters(self) -> Dict:
        """
        Get current intuitive parameter values.

        Returns:
            Dictionary of intuitive parameter values

        Used by:
        - Main GUI for terrain generation (converts to technical params)
        - Preset saving/loading
        """
        return {
            'preset': self.params['preset'].get(),
            'resolution': self.params['resolution'].get(),
            'roughness': self.params['roughness'].get(),
            'feature_size': self.params['feature_size'].get(),
            'detail_level': self.params['detail_level'].get(),
            'height_variation': self.params['height_variation'].get()
        }

    def set_parameters(self, params: Dict):
        """
        Set intuitive parameter values.

        Args:
            params: Dictionary of intuitive parameter values

        Used for:
        - Loading presets
        - Restoring state
        """
        if 'preset' in params:
            self.params['preset'].set(params['preset'])
        if 'resolution' in params:
            self.params['resolution'].set(params['resolution'])
        if 'roughness' in params:
            self.params['roughness'].set(params['roughness'])
        if 'feature_size' in params:
            self.params['feature_size'].set(params['feature_size'])
        if 'detail_level' in params:
            self.params['detail_level'].set(params['detail_level'])
        if 'height_variation' in params:
            self.params['height_variation'].set(params['height_variation'])
