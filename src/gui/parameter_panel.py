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
            'height_variation': tk.DoubleVar(value=85.0),  # 0-100: flat ↔ extreme
            # Stage 1 Hydraulic Erosion controls
            'erosion_enabled': tk.BooleanVar(value=True),  # DEFAULT: enabled for realistic terrain
            'erosion_quality': tk.StringVar(value='maximum'),  # fast/balanced/maximum - DEFAULT: maximum
            # Erosion physical parameters (tunable)
            'erosion_rate': tk.DoubleVar(value=0.2),           # How aggressively water erodes (0.1-0.5)
            'deposition_rate': tk.DoubleVar(value=0.08),       # How quickly sediment deposits (0.01-0.15)
            'evaporation_rate': tk.DoubleVar(value=0.015),     # Water loss rate (0.005-0.03)
            'sediment_capacity': tk.DoubleVar(value=3.0),      # Max sediment per water unit (1.0-6.0)
            # Stage 2: Priority 2 + Priority 6 Buildability System (NEW IMPLEMENTATION)
            'buildability_enabled': tk.BooleanVar(value=True),  # DEFAULT: enabled
            'buildability_target': tk.DoubleVar(value=50.0),  # Target: 45-55% (currently achieves ~18%)
            # Task 2.1: Tectonic Structure Generation
            'tectonic_enabled': tk.BooleanVar(value=True),  # Use tectonic fault lines for geological realism
            'num_fault_lines': tk.IntVar(value=5),  # Number of fault lines (3-7)
            'max_uplift': tk.DoubleVar(value=0.2),  # Mountain height (0.15-0.6, best: 0.2)
            'falloff_meters': tk.DoubleVar(value=600.0),  # Distance from faults (300-1000m)
            # Task 2.3: Amplitude Modulation (single frequency field)
            'buildable_amplitude': tk.DoubleVar(value=0.05),  # Noise in buildable zones (0.01-0.2, best: 0.05)
            'scenic_amplitude': tk.DoubleVar(value=0.2),  # Noise in scenic zones (0.1-1.0, best: 0.2)
            # Priority 6: Buildability Enforcement (smart blur)
            'enforcement_iterations': tk.IntVar(value=10),  # Smoothing iterations (0-20)
            'enforcement_sigma': tk.DoubleVar(value=12.0)  # Smoothing strength (8-20)
        }

        # Advanced mode (technical parameters) - hidden by default
        self.show_advanced = tk.BooleanVar(value=False)

        # Session 9: Generation Mode Selection (Legacy vs New Pipeline)
        self.generation_mode = tk.StringVar(value='legacy')  # 'legacy' or 'pipeline'

        # Session 9: New Pipeline Parameters (Sessions 2-8)
        self.pipeline_params = {
            # Zone Generation (Session 2)
            'target_coverage': tk.DoubleVar(value=0.70),  # 60-80%
            'zone_wavelength': tk.DoubleVar(value=6500.0),  # 5000-8000m
            'zone_octaves': tk.IntVar(value=2),  # 2-3

            # Terrain Generation (Session 3)
            'base_amplitude': tk.DoubleVar(value=0.2),  # 0.15-0.3
            'min_amplitude_mult': tk.DoubleVar(value=0.3),  # 0.2-0.4
            'max_amplitude_mult': tk.DoubleVar(value=1.0),  # 0.8-1.2
            'terrain_wavelength': tk.DoubleVar(value=1000.0),  # 500-2000m
            'terrain_octaves': tk.IntVar(value=6),  # 4-8

            # Ridge Enhancement (Session 5)
            'ridge_strength': tk.DoubleVar(value=0.2),  # 0.1-0.3
            'ridge_octaves': tk.IntVar(value=5),  # 4-6
            'ridge_wavelength': tk.DoubleVar(value=1500.0),  # 1000-2000m
            'apply_ridges': tk.BooleanVar(value=True),

            # Hydraulic Erosion (Session 4)
            'num_particles': tk.IntVar(value=100000),  # 50k-200k
            'pipeline_erosion_rate': tk.DoubleVar(value=0.5),  # 0.3-0.8
            'pipeline_deposition_rate': tk.DoubleVar(value=0.3),  # 0.1-0.5
            'apply_erosion': tk.BooleanVar(value=True),

            # River Analysis (Session 7)
            'river_threshold_percentile': tk.DoubleVar(value=99.0),  # 95-99.5
            'min_river_length': tk.IntVar(value=10),  # 10+
            'apply_rivers': tk.BooleanVar(value=True),

            # Detail Addition (Session 8)
            'detail_amplitude': tk.DoubleVar(value=0.02),  # 0.01-0.05
            'detail_wavelength': tk.DoubleVar(value=75.0),  # 50-150m
            'apply_detail': tk.BooleanVar(value=True),

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

        # Session 9: Generation Mode Selector
        mode_frame = ttk.LabelFrame(self, text="Generation Mode", padding=10)
        mode_frame.pack(fill=tk.X, padx=5, pady=(0, 5))

        mode_info = ttk.Label(
            mode_frame,
            text="Choose terrain generation system:",
            font=('Arial', 9),
            foreground='gray30'
        )
        mode_info.pack(anchor=tk.W, pady=(0, 5))

        # Radio buttons for mode selection
        legacy_rb = ttk.Radiobutton(
            mode_frame,
            text="Legacy System (v2.4 - Fast, ~1s)",
            variable=self.generation_mode,
            value='legacy',
            command=self._on_mode_change
        )
        legacy_rb.pack(anchor=tk.W, pady=2)

        pipeline_rb = ttk.Radiobutton(
            mode_frame,
            text="New Pipeline (Sessions 2-8 - 55-65% Buildable, ~3-4 min)",
            variable=self.generation_mode,
            value='pipeline',
            command=self._on_mode_change
        )
        pipeline_rb.pack(anchor=tk.W, pady=2)

        # Create tabbed interface (saves ~200px vertical space!)
        self.notebook = ttk.Notebook(self)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # Tab 1: Basic terrain parameters (Legacy mode)
        self._create_basic_tab()

        # Tab 2: Quality & Erosion (Stage 1 features - Legacy mode)
        self._create_quality_tab()

        # Tab 3: New Pipeline parameters (Session 9)
        self._create_pipeline_tab()

        # Tab 4: Water features
        self._create_water_tab()

        # Tab 4: Advanced options (hidden by default, can be expanded later)
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

    def _create_quality_tab(self):
        """Create quality & erosion settings tab (Stage 1 features)."""
        tab = ttk.Frame(self.notebook, padding=10)
        self.notebook.add(tab, text="Quality")

        # Hydraulic Erosion section
        erosion_frame = ttk.LabelFrame(tab, text="Hydraulic Erosion (Stage 1)", padding=10)
        erosion_frame.pack(fill=tk.X, pady=(0, 10))

        # Info label
        info = ttk.Label(
            erosion_frame,
            text="Realistic erosion creates dendritic drainage\npatterns and carved valleys.",
            font=('Arial', 9),
            justify=tk.LEFT,
            foreground='gray30'
        )
        info.pack(pady=(0, 10), anchor=tk.W)

        # Enable erosion checkbox
        erosion_check = ttk.Checkbutton(
            erosion_frame,
            text="Enable Hydraulic Erosion",
            variable=self.params['erosion_enabled'],
            command=self._on_erosion_toggle
        )
        erosion_check.pack(anchor=tk.W, pady=(0, 10))

        # Quality preset dropdown
        quality_frame = ttk.Frame(erosion_frame)
        quality_frame.pack(fill=tk.X, pady=(0, 5))

        ttk.Label(quality_frame, text="Quality Preset:").pack(side=tk.LEFT, padx=(0, 10))

        quality_combo = ttk.Combobox(
            quality_frame,
            textvariable=self.params['erosion_quality'],
            values=['fast', 'balanced', 'maximum'],
            state='readonly',
            width=12
        )
        quality_combo.pack(side=tk.LEFT)

        # Performance hints
        self.erosion_hint_label = ttk.Label(
            erosion_frame,
            text="",
            font=('Arial', 8),
            foreground='gray50'
        )
        self.erosion_hint_label.pack(anchor=tk.W, pady=(5, 0))

        # Bind quality change to update hints
        quality_combo.bind('<<ComboboxSelected>>', lambda e: self._update_erosion_hints())

        # Initial hint update
        self._update_erosion_hints()

        # JIT compilation status (if Numba available)
        try:
            from src.features.hydraulic_erosion import NUMBA_AVAILABLE
            if NUMBA_AVAILABLE:
                jit_label = ttk.Label(
                    erosion_frame,
                    text="✓ Numba JIT acceleration enabled",
                    font=('Arial', 8, 'bold'),
                    foreground='green4'
                )
                jit_label.pack(anchor=tk.W, pady=(10, 0))
            else:
                jit_label = ttk.Label(
                    erosion_frame,
                    text="⚠ Numba not available (slower performance)",
                    font=('Arial', 8),
                    foreground='orange3'
                )
                jit_label.pack(anchor=tk.W, pady=(10, 0))
        except ImportError:
            pass

        # Advanced erosion parameters (collapsible)
        erosion_advanced_frame = ttk.LabelFrame(erosion_frame, text="Advanced Erosion Parameters", padding=5)
        erosion_advanced_frame.pack(fill=tk.X, pady=(10, 0))

        # Erosion Rate
        self._create_slider_control(
            erosion_advanced_frame, "Erosion Rate:", self.params['erosion_rate'],
            0.1, 0.5, "{:.2f}", "Carving strength (0.2=gentle, 0.3=standard, 0.4=aggressive)"
        )

        # Deposition Rate
        self._create_slider_control(
            erosion_advanced_frame, "Deposition Rate:", self.params['deposition_rate'],
            0.01, 0.15, "{:.3f}", "Sediment smoothing (0.05=minimal, 0.08=balanced, 0.12=heavy)"
        )

        # Evaporation Rate
        self._create_slider_control(
            erosion_advanced_frame, "Evaporation Rate:", self.params['evaporation_rate'],
            0.005, 0.03, "{:.3f}", "Water loss control (0.01=low, 0.015=moderate, 0.025=high)"
        )

        # Sediment Capacity
        self._create_slider_control(
            erosion_advanced_frame, "Sediment Capacity:", self.params['sediment_capacity'],
            1.0, 6.0, "{:.1f}", "Max sediment transport (2.0=limited, 3.0=balanced, 5.0=heavy)"
        )

        # Explanation
        explanation_erosion = ttk.Label(
            erosion_advanced_frame,
            text="Fine-tune erosion behavior. Lower values = gentler, higher = more dramatic.\nDefaults are calibrated for buildable terrain.",
            font=('Arial', 7),
            foreground='gray50',
            justify=tk.LEFT
        )
        explanation_erosion.pack(anchor=tk.W, pady=(5, 0))

        # Buildability System (Priority 2 + Priority 6)
        buildability_frame = ttk.LabelFrame(tab, text="Buildability System (Priority 2 + 6)", padding=10)
        buildability_frame.pack(fill=tk.X, pady=(10, 0))

        # Info label
        info_build = ttk.Label(
            buildability_frame,
            text="Tectonic structure + amplitude modulation + smart blur\nCurrently achieves ~18% buildable (target: 45-55%)",
            font=('Arial', 9),
            justify=tk.LEFT,
            foreground='orange3'
        )
        info_build.pack(pady=(0, 10), anchor=tk.W)

        # Enable buildability checkbox
        buildability_check = ttk.Checkbutton(
            buildability_frame,
            text="Enable Buildability System",
            variable=self.params['buildability_enabled']
        )
        buildability_check.pack(anchor=tk.W, pady=(0, 10))

        # Tectonic Structure section
        tectonic_frame = ttk.LabelFrame(buildability_frame, text="Tectonic Structure (Task 2.1)", padding=5)
        tectonic_frame.pack(fill=tk.X, pady=(0, 10))

        # Number of fault lines
        self._create_slider_control(
            tectonic_frame, "Fault Lines:", self.params['num_fault_lines'],
            3, 7, "{:.0f}", "Geological features (3=simple, 7=complex)"
        )

        # Max uplift
        self._create_slider_control(
            tectonic_frame, "Mountain Height:", self.params['max_uplift'],
            0.15, 0.6, "{:.2f}", "Tectonic uplift (0.2=gentle, 0.6=extreme) [best: 0.2]"
        )

        # Falloff distance
        self._create_slider_control(
            tectonic_frame, "Falloff Distance (m):", self.params['falloff_meters'],
            300.0, 1000.0, "{:.0f}", "Mountain slope distance (600=moderate)"
        )

        # Amplitude Modulation section
        amplitude_frame = ttk.LabelFrame(buildability_frame, text="Noise Detail (Task 2.3)", padding=5)
        amplitude_frame.pack(fill=tk.X, pady=(0, 10))

        # Buildable amplitude
        self._create_slider_control(
            amplitude_frame, "Buildable Zones:", self.params['buildable_amplitude'],
            0.01, 0.2, "{:.3f}", "Texture detail in flat areas (0.05=gentle) [best: 0.05]"
        )

        # Scenic amplitude
        self._create_slider_control(
            amplitude_frame, "Scenic Zones:", self.params['scenic_amplitude'],
            0.1, 1.0, "{:.2f}", "Detail in mountains (0.2=moderate, 1.0=extreme) [best: 0.2]"
        )

        # Priority 6 Enforcement section
        enforcement_frame = ttk.LabelFrame(buildability_frame, text="Slope Smoothing (Priority 6)", padding=5)
        enforcement_frame.pack(fill=tk.X, pady=(0, 10))

        # Enforcement iterations
        self._create_slider_control(
            enforcement_frame, "Iterations:", self.params['enforcement_iterations'],
            0, 20, "{:.0f}", "Smoothing passes (10=moderate, 20=aggressive)"
        )

        # Enforcement sigma
        self._create_slider_control(
            enforcement_frame, "Strength (sigma):", self.params['enforcement_sigma'],
            8.0, 20.0, "{:.1f}", "Blur radius in pixels (12=moderate, 20=strong)"
        )

        # Status note
        status_note = ttk.Label(
            buildability_frame,
            text="Note: System uses single frequency field to avoid discontinuities.\nCurrent best parameters achieve 18.5% buildable terrain.",
            font=('Arial', 8),
            foreground='gray50',
            justify=tk.LEFT
        )
        status_note.pack(anchor=tk.W, pady=(5, 0))

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

    def _on_erosion_toggle(self):
        """Handle erosion checkbox toggle."""
        enabled = self.params['erosion_enabled'].get()
        if enabled:
            self.gui.set_status("Erosion enabled - Generation will take slightly longer")
        else:
            self.gui.set_status("Erosion disabled")
        self._update_erosion_hints()

    def _update_erosion_hints(self):
        """Update erosion performance hints based on selected quality."""
        if not hasattr(self, 'erosion_hint_label'):
            return

        quality = self.params['erosion_quality'].get()
        enabled = self.params['erosion_enabled'].get()

        if not enabled:
            self.erosion_hint_label.config(text="Erosion disabled")
            return

        # Quality-specific hints (based on 4096×4096 resolution)
        hints = {
            'fast': '25 iterations (~3-4s overhead)',
            'balanced': '50 iterations (~5-7s overhead)',
            'maximum': '100 iterations (~12-15s overhead)'
        }

        hint_text = hints.get(quality, '')
        self.erosion_hint_label.config(text=hint_text)

    def _create_pipeline_tab(self):
        """Create new pipeline parameters tab (Session 9)."""
        tab = ttk.Frame(self.notebook, padding=10)
        self.notebook.add(tab, text="Pipeline")

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
            0.3, 0.8, "{:.2f}", "Carving strength (0.5=moderate)"
        )
        self._create_slider_control(
            erosion_frame, "Deposition Rate:", self.pipeline_params['pipeline_deposition_rate'],
            0.1, 0.5, "{:.2f}", "Sediment deposition (0.3=moderate)"
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

    def _on_mode_change(self):
        """Handle generation mode change."""
        mode = self.generation_mode.get()
        if mode == 'legacy':
            self.gui.set_status("Legacy system selected - Fast generation (~1s)")
        else:
            self.gui.set_status("New pipeline selected - 55-65% buildable (~3-4 min)")

    def get_parameters(self) -> Dict:
        """
        Get current intuitive parameter values.

        Returns:
            Dictionary of intuitive parameter values

        Used by:
        - Main GUI for terrain generation (converts to technical params)
        - Preset saving/loading
        """
        params_dict = {
            # Generation mode (Session 9)
            'generation_mode': self.generation_mode.get(),

            # Legacy parameters
            'preset': self.params['preset'].get(),
            'resolution': self.params['resolution'].get(),
            'roughness': self.params['roughness'].get(),
            'feature_size': self.params['feature_size'].get(),
            'detail_level': self.params['detail_level'].get(),
            'height_variation': self.params['height_variation'].get(),
            # Stage 1 erosion parameters
            'erosion_enabled': self.params['erosion_enabled'].get(),
            'erosion_quality': self.params['erosion_quality'].get(),
            'erosion_rate': self.params['erosion_rate'].get(),
            'deposition_rate': self.params['deposition_rate'].get(),
            'evaporation_rate': self.params['evaporation_rate'].get(),
            'sediment_capacity': self.params['sediment_capacity'].get(),
            # Stage 2 buildability parameters
            'buildability_enabled': self.params['buildability_enabled'].get(),
            'buildability_target': self.params['buildability_target'].get(),
            # Priority 2 + Priority 6 System Parameters
            'tectonic_enabled': self.params['tectonic_enabled'].get(),
            'num_fault_lines': self.params['num_fault_lines'].get(),
            'max_uplift': self.params['max_uplift'].get(),
            'falloff_meters': self.params['falloff_meters'].get(),
            'buildable_amplitude': self.params['buildable_amplitude'].get(),
            'scenic_amplitude': self.params['scenic_amplitude'].get(),
            'enforcement_iterations': self.params['enforcement_iterations'].get(),
            'enforcement_sigma': self.params['enforcement_sigma'].get()
        }

        # Add new pipeline parameters (Session 9)
        for key, var in self.pipeline_params.items():
            params_dict[key] = var.get()

        return params_dict

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
