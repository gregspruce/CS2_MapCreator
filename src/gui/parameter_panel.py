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

        # Fixed resolution (CS2 requirement)
        self.resolution = 4096

        # Session 9: New Pipeline Parameters (Sessions 2-8)
        self.pipeline_params = {
            # Zone Generation (Session 2)
            'target_coverage': tk.DoubleVar(value=0.72),  # Tuned for 55-65% buildability (with all stages)
            'zone_wavelength': tk.DoubleVar(value=6500.0),  # 5000-8000m
            'zone_octaves': tk.IntVar(value=2),  # 2-3

            # Terrain Generation (Session 3)
            'base_amplitude': tk.DoubleVar(value=0.09),  # Tuned for 55-65% buildability (was 0.18 - too steep)
            'min_amplitude_mult': tk.DoubleVar(value=0.3),  # 0.2-0.4
            'max_amplitude_mult': tk.DoubleVar(value=1.0),  # 0.8-1.2
            'terrain_wavelength': tk.DoubleVar(value=1000.0),  # 500-2000m
            'terrain_octaves': tk.IntVar(value=6),  # 4-8

            # Ridge Enhancement (Session 5)
            'ridge_strength': tk.DoubleVar(value=0.2),  # 0.1-0.3
            'ridge_octaves': tk.IntVar(value=5),  # 4-6
            'ridge_wavelength': tk.DoubleVar(value=1500.0),  # 1000-2000m
            'apply_ridges': tk.BooleanVar(value=True),  # Session 5: Ridge enhancement for coherent mountains

            # Hydraulic Erosion (Session 4)
            'num_particles': tk.IntVar(value=100000),  # 50k-200k
            'pipeline_erosion_rate': tk.DoubleVar(value=0.2),  # 0.1-0.5
            'pipeline_deposition_rate': tk.DoubleVar(value=0.6),  # 0.3-0.8
            'apply_erosion': tk.BooleanVar(value=True),  # Session 4: THE critical component for 55-65% buildability

            # River Analysis (Session 7)
            'river_threshold_percentile': tk.DoubleVar(value=99.0),  # 95-99.5
            'min_river_length': tk.IntVar(value=10),  # 10+
            'apply_rivers': tk.BooleanVar(value=True),

            # Detail Addition (Session 8)
            'detail_amplitude': tk.DoubleVar(value=0.02),  # 0.01-0.05
            'detail_wavelength': tk.DoubleVar(value=75.0),  # 50-150m
            'apply_detail': tk.BooleanVar(value=False),  # Disabled - too large for gentle terrain

            # Constraint Verification (Session 8)
            'target_buildable_min': tk.DoubleVar(value=55.0),  # 55%
            'target_buildable_max': tk.DoubleVar(value=65.0),  # 65%
            'apply_constraint_adjustment': tk.BooleanVar(value=True),
        }

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

        # Tab 1: Pipeline parameters (Sessions 2-8)
        self._create_pipeline_tab()

        # Tab 2: Water features
        self._create_water_tab()

        # Generate button (always visible at bottom)
        generate_btn = ttk.Button(
            self,
            text="Generate Terrain",
            command=self._on_generate,
            style='Accent.TButton'  # Make it prominent
        )
        generate_btn.pack(pady=10, padx=10, fill=tk.X)


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

        # Show Water Features toggle
        water_toggle = ttk.Checkbutton(
            tab,
            text="Show Water Features Overlay",
            command=self.gui.toggle_water_overlay
        )
        water_toggle.pack(anchor=tk.W, pady=5)

        # 3D Preview button
        preview_btn = ttk.Button(
            tab,
            text="3D Preview",
            command=self.gui.show_3d_preview
        )
        preview_btn.pack(fill=tk.X, pady=5)


    def _create_slider_control(self, parent, label_text: str, variable, from_val: float, to_val: float, format_str: str, tooltip_text: str):
        """
        Create a compact slider control with label, slider, value display, and tooltip.

        Args:
            parent: Parent widget
            label_text: Label text (e.g., "Buildable Octaves:")
            variable: Tkinter variable (IntVar or DoubleVar)
            from_val: Minimum value
            to_val: Maximum value
            format_str: Format string for value display (e.g., "{:.0f}" for integers, "{:.1f}" for floats)
            tooltip_text: Help text displayed below the slider

        Why this pattern:
        - Compact layout for advanced controls
        - Label, slider, and value on same line
        - Tooltip provides context without cluttering UI
        - Value updates in real-time
        """
        # Main control frame (label, slider, value on one line)
        control_frame = ttk.Frame(parent)
        control_frame.pack(fill=tk.X, pady=2)

        # Label on the left
        ttk.Label(control_frame, text=label_text, width=20).pack(side=tk.LEFT, padx=(0, 10))

        # Slider in the middle (expands to fill)
        slider = ttk.Scale(control_frame, from_=from_val, to=to_val, variable=variable, orient=tk.HORIZONTAL)
        slider.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 10))

        # Value label on the right
        value_label = ttk.Label(control_frame, text=format_str.format(variable.get()), width=5)
        value_label.pack(side=tk.LEFT)

        # Update label when slider changes
        def update_label(*args):
            value_label.config(text=format_str.format(variable.get()))
        variable.trace_add('write', update_label)

        # Tooltip below (small gray text)
        tooltip = ttk.Label(parent, text=tooltip_text, font=('Arial', 7), foreground='gray50')
        tooltip.pack(anchor=tk.W, pady=(0, 5))

    def _on_generate(self):
        """Handle Generate button click."""
        self.gui.generate_terrain()

    def _create_pipeline_tab(self):
        """Create new pipeline parameters tab (Session 9)."""
        tab = ttk.Frame(self.notebook, padding=10)
        self.notebook.add(tab, text="Terrain")

        # Info section
        info_frame = ttk.LabelFrame(tab, text="New Pipeline (Sessions 2-8)", padding=10)
        info_frame.pack(fill=tk.X, pady=(0, 10))

        info_text = ttk.Label(
            info_frame,
            text="Hybrid zoned generation with hydraulic erosion\nTarget: 55-65% buildable terrain\nGeneration time: 3-4 minutes",
            font=('Arial', 9),
            justify=tk.LEFT,
            foreground='gray30'
        )
        info_text.pack(anchor=tk.W)

        # Create scrollable frame for parameters
        canvas = tk.Canvas(tab, highlightthickness=0)
        scrollbar = ttk.Scrollbar(tab, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)

        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )

        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        # Zone Generation section
        zone_frame = ttk.LabelFrame(scrollable_frame, text="Zone Generation (Session 2)", padding=5)
        zone_frame.pack(fill=tk.X, pady=(0, 5))

        self._create_slider_control(
            zone_frame, "Target Coverage:", self.pipeline_params['target_coverage'],
            0.60, 0.80, "{:.2f}", "Buildable zone coverage (0.70=70% of map)"
        )
        self._create_slider_control(
            zone_frame, "Zone Wavelength (m):", self.pipeline_params['zone_wavelength'],
            5000.0, 8000.0, "{:.0f}", "Zone feature size (6500=large zones)"
        )
        self._create_slider_control(
            zone_frame, "Zone Octaves:", self.pipeline_params['zone_octaves'],
            2, 3, "{:.0f}", "Zone detail level (2=simple, 3=complex)"
        )

        # Terrain Generation section
        terrain_frame = ttk.LabelFrame(scrollable_frame, text="Terrain Generation (Session 3)", padding=5)
        terrain_frame.pack(fill=tk.X, pady=(0, 5))

        self._create_slider_control(
            terrain_frame, "Base Amplitude:", self.pipeline_params['base_amplitude'],
            0.15, 0.3, "{:.2f}", "Overall terrain height (0.2=moderate)"
        )
        self._create_slider_control(
            terrain_frame, "Min Amplitude Mult:", self.pipeline_params['min_amplitude_mult'],
            0.2, 0.4, "{:.2f}", "Buildable zone amplitude (0.3=gentle)"
        )
        self._create_slider_control(
            terrain_frame, "Max Amplitude Mult:", self.pipeline_params['max_amplitude_mult'],
            0.8, 1.2, "{:.2f}", "Scenic zone amplitude (1.0=full)"
        )
        self._create_slider_control(
            terrain_frame, "Terrain Wavelength (m):", self.pipeline_params['terrain_wavelength'],
            500.0, 2000.0, "{:.0f}", "Terrain feature size (1000=moderate)"
        )
        self._create_slider_control(
            terrain_frame, "Terrain Octaves:", self.pipeline_params['terrain_octaves'],
            4, 8, "{:.0f}", "Detail level (6=balanced)"
        )

        # Ridge Enhancement section
        ridge_frame = ttk.LabelFrame(scrollable_frame, text="Ridge Enhancement (Session 5)", padding=5)
        ridge_frame.pack(fill=tk.X, pady=(0, 5))

        ttk.Checkbutton(
            ridge_frame,
            text="Enable Ridge Enhancement",
            variable=self.pipeline_params['apply_ridges']
        ).pack(anchor=tk.W, pady=(0, 5))

        self._create_slider_control(
            ridge_frame, "Ridge Strength:", self.pipeline_params['ridge_strength'],
            0.1, 0.3, "{:.2f}", "Ridge prominence (0.2=moderate)"
        )
        self._create_slider_control(
            ridge_frame, "Ridge Octaves:", self.pipeline_params['ridge_octaves'],
            4, 6, "{:.0f}", "Ridge detail (5=balanced)"
        )
        self._create_slider_control(
            ridge_frame, "Ridge Wavelength (m):", self.pipeline_params['ridge_wavelength'],
            1000.0, 2000.0, "{:.0f}", "Ridge spacing (1500=moderate)"
        )

        # Hydraulic Erosion section
        erosion_frame = ttk.LabelFrame(scrollable_frame, text="Hydraulic Erosion (Session 4)", padding=5)
        erosion_frame.pack(fill=tk.X, pady=(0, 5))

        ttk.Checkbutton(
            erosion_frame,
            text="Enable Hydraulic Erosion",
            variable=self.pipeline_params['apply_erosion']
        ).pack(anchor=tk.W, pady=(0, 5))

        self._create_slider_control(
            erosion_frame, "Particles:", self.pipeline_params['num_particles'],
            50000, 200000, "{:.0f}", "Erosion particles (100k=balanced, higher=slower)"
        )
        self._create_slider_control(
            erosion_frame, "Erosion Rate:", self.pipeline_params['pipeline_erosion_rate'],
            0.1, 0.5, "{:.2f}", "Carving strength (0.2=gentle, favors deposition)"
        )
        self._create_slider_control(
            erosion_frame, "Deposition Rate:", self.pipeline_params['pipeline_deposition_rate'],
            0.3, 0.8, "{:.2f}", "Sediment deposition (0.6=strong, fills valleys)"
        )

        # River Analysis section
        river_frame = ttk.LabelFrame(scrollable_frame, text="River Analysis (Session 7)", padding=5)
        river_frame.pack(fill=tk.X, pady=(0, 5))

        ttk.Checkbutton(
            river_frame,
            text="Enable River Analysis",
            variable=self.pipeline_params['apply_rivers']
        ).pack(anchor=tk.W, pady=(0, 5))

        self._create_slider_control(
            river_frame, "Threshold Percentile:", self.pipeline_params['river_threshold_percentile'],
            95.0, 99.5, "{:.1f}", "Flow accumulation threshold (99.0=major rivers)"
        )
        self._create_slider_control(
            river_frame, "Min River Length:", self.pipeline_params['min_river_length'],
            10, 50, "{:.0f}", "Minimum river length in pixels (10=all)"
        )

        # Detail Addition section
        detail_frame = ttk.LabelFrame(scrollable_frame, text="Detail Addition (Session 8)", padding=5)
        detail_frame.pack(fill=tk.X, pady=(0, 5))

        ttk.Checkbutton(
            detail_frame,
            text="Enable Detail Addition",
            variable=self.pipeline_params['apply_detail']
        ).pack(anchor=tk.W, pady=(0, 5))

        self._create_slider_control(
            detail_frame, "Detail Amplitude:", self.pipeline_params['detail_amplitude'],
            0.01, 0.05, "{:.3f}", "Detail height (0.02=subtle)"
        )
        self._create_slider_control(
            detail_frame, "Detail Wavelength (m):", self.pipeline_params['detail_wavelength'],
            50.0, 150.0, "{:.0f}", "Detail feature size (75=moderate)"
        )

        # Constraint Verification section
        constraint_frame = ttk.LabelFrame(scrollable_frame, text="Buildability Constraints (Session 8)", padding=5)
        constraint_frame.pack(fill=tk.X, pady=(0, 5))

        ttk.Checkbutton(
            constraint_frame,
            text="Enable Auto-Adjustment",
            variable=self.pipeline_params['apply_constraint_adjustment']
        ).pack(anchor=tk.W, pady=(0, 5))

        self._create_slider_control(
            constraint_frame, "Target Min (%):", self.pipeline_params['target_buildable_min'],
            50.0, 60.0, "{:.0f}", "Minimum buildable percentage"
        )
        self._create_slider_control(
            constraint_frame, "Target Max (%):", self.pipeline_params['target_buildable_max'],
            60.0, 70.0, "{:.0f}", "Maximum buildable percentage"
        )

        # Pack canvas and scrollbar
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

    def get_parameters(self) -> Dict:
        """
        Get current pipeline parameter values.

        Returns:
            Dictionary of pipeline parameter values (Sessions 2-8)

        Used by:
        - Main GUI for terrain generation
        """
        params_dict = {}

        # Return only pipeline parameters
        for key, var in self.pipeline_params.items():
            params_dict[key] = var.get()

        return params_dict

    def set_parameters(self, params: Dict):
        """
        Set pipeline parameter values.

        Args:
            params: Dictionary of pipeline parameter values

        Used for:
        - Loading presets
        - Restoring state
        """
        for key, value in params.items():
            if key in self.pipeline_params:
                self.pipeline_params[key].set(value)
