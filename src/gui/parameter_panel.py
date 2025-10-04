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

        # Parameter values
        self.params = {
            'preset': tk.StringVar(value='mountains'),
            'resolution': tk.IntVar(value=1024),
            'scale': tk.DoubleVar(value=200.0),
            'octaves': tk.IntVar(value=6),
            'persistence': tk.DoubleVar(value=0.5),
            'lacunarity': tk.DoubleVar(value=2.0)
        }

        # Create widgets
        self._create_widgets()

        # Preset definitions (matches existing presets)
        self.preset_params = {
            'flat': {'scale': 500.0, 'octaves': 2, 'persistence': 0.3, 'lacunarity': 2.0},
            'hills': {'scale': 150.0, 'octaves': 4, 'persistence': 0.5, 'lacunarity': 2.0},
            'mountains': {'scale': 200.0, 'octaves': 6, 'persistence': 0.5, 'lacunarity': 2.0},
            'islands': {'scale': 100.0, 'octaves': 5, 'persistence': 0.6, 'lacunarity': 2.0},
            'canyons': {'scale': 80.0, 'octaves': 6, 'persistence': 0.4, 'lacunarity': 2.5},
            'highlands': {'scale': 120.0, 'octaves': 5, 'persistence': 0.5, 'lacunarity': 2.0},
            'mesas': {'scale': 100.0, 'octaves': 4, 'persistence': 0.3, 'lacunarity': 2.5}
        }

    def _create_widgets(self):
        """Create all parameter control widgets."""
        # Title
        title = ttk.Label(self, text="Terrain Parameters", font=('Arial', 12, 'bold'))
        title.pack(pady=(10, 5))

        ttk.Separator(self, orient=tk.HORIZONTAL).pack(fill=tk.X, pady=5)

        # Preset selector
        self._create_preset_selector()

        ttk.Separator(self, orient=tk.HORIZONTAL).pack(fill=tk.X, pady=10)

        # Resolution selector
        self._create_resolution_selector()

        ttk.Separator(self, orient=tk.HORIZONTAL).pack(fill=tk.X, pady=10)

        # Parameter sliders
        self._create_parameter_sliders()

        ttk.Separator(self, orient=tk.HORIZONTAL).pack(fill=tk.X, pady=10)

        # Generate button
        generate_btn = ttk.Button(
            self,
            text="Generate Terrain",
            command=self._on_generate
        )
        generate_btn.pack(pady=10, padx=10, fill=tk.X)

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

    def _create_resolution_selector(self):
        """Create resolution dropdown."""
        frame = ttk.LabelFrame(self, text="Resolution", padding=10)
        frame.pack(fill=tk.X, padx=10, pady=5)

        resolutions = [512, 1024, 2048, 4096, 8192]

        res_combo = ttk.Combobox(
            frame,
            textvariable=self.params['resolution'],
            values=resolutions,
            state='readonly',
            width=15
        )
        res_combo.pack()
        res_combo.bind('<<ComboboxSelected>>', self._on_resolution_change)

    def _create_parameter_sliders(self):
        """Create parameter sliders with labels."""
        frame = ttk.LabelFrame(self, text="Noise Parameters", padding=10)
        frame.pack(fill=tk.X, padx=10, pady=5)

        # Scale slider (10-500)
        self._create_slider(
            frame,
            "Scale:",
            self.params['scale'],
            from_=10.0,
            to=500.0,
            resolution=5.0
        )

        # Octaves slider (1-10)
        self._create_slider(
            frame,
            "Octaves:",
            self.params['octaves'],
            from_=1,
            to=10,
            resolution=1
        )

        # Persistence slider (0.1-0.9)
        self._create_slider(
            frame,
            "Persistence:",
            self.params['persistence'],
            from_=0.1,
            to=0.9,
            resolution=0.05
        )

        # Lacunarity slider (1.5-3.5)
        self._create_slider(
            frame,
            "Lacunarity:",
            self.params['lacunarity'],
            from_=1.5,
            to=3.5,
            resolution=0.1
        )

    def _create_slider(self, parent, label: str, variable, from_: float, to: float, resolution: float):
        """
        Create a labeled slider with value display.

        Args:
            parent: Parent widget
            label: Slider label
            variable: Tkinter variable
            from_: Minimum value
            to: Maximum value
            resolution: Step size

        Why this pattern:
        - Label shows what parameter is
        - Value display shows current value
        - Slider for intuitive adjustment
        - Standard pattern in audio/video software
        """
        # Container frame
        container = ttk.Frame(parent)
        container.pack(fill=tk.X, pady=5)

        # Label and value
        label_frame = ttk.Frame(container)
        label_frame.pack(fill=tk.X)

        ttk.Label(label_frame, text=label, width=12, anchor=tk.W).pack(side=tk.LEFT)
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

    def _on_preset_change(self):
        """Handle preset selection change."""
        preset = self.params['preset'].get()

        if preset in self.preset_params:
            # Update parameters from preset
            params = self.preset_params[preset]
            self.params['scale'].set(params['scale'])
            self.params['octaves'].set(params['octaves'])
            self.params['persistence'].set(params['persistence'])
            self.params['lacunarity'].set(params['lacunarity'])

            # Trigger regeneration
            self.gui.schedule_update()

    def _on_resolution_change(self, event=None):
        """Handle resolution change."""
        new_res = self.params['resolution'].get()
        self.gui.resolution = new_res
        self.gui.resolution_label.config(text=f"{new_res}x{new_res}")
        # Note: Don't auto-regenerate on resolution change (expensive)
        # User clicks Generate button when ready

    def _on_parameter_change(self):
        """Handle parameter slider change."""
        # Schedule debounced update
        self.gui.schedule_update()

    def _on_generate(self):
        """Handle Generate button click."""
        self.gui.generate_terrain()

    def get_parameters(self) -> Dict:
        """
        Get current parameter values.

        Returns:
            Dictionary of parameter values

        Used by:
        - Main GUI for terrain generation
        - Preset saving/loading
        """
        return {
            'preset': self.params['preset'].get(),
            'resolution': self.params['resolution'].get(),
            'scale': self.params['scale'].get(),
            'octaves': self.params['octaves'].get(),
            'persistence': self.params['persistence'].get(),
            'lacunarity': self.params['lacunarity'].get()
        }

    def set_parameters(self, params: Dict):
        """
        Set parameter values.

        Args:
            params: Dictionary of parameter values

        Used for:
        - Loading presets
        - Restoring state
        """
        if 'preset' in params:
            self.params['preset'].set(params['preset'])
        if 'resolution' in params:
            self.params['resolution'].set(params['resolution'])
        if 'scale' in params:
            self.params['scale'].set(params['scale'])
        if 'octaves' in params:
            self.params['octaves'].set(params['octaves'])
        if 'persistence' in params:
            self.params['persistence'].set(params['persistence'])
        if 'lacunarity' in params:
            self.params['lacunarity'].set(params['lacunarity'])
