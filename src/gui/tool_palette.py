"""
CS2 Heightmap Generator - Tool Palette

Manual editing tools and operation history display.

Features:
- Brush tools (raise, lower, smooth)
- Feature tools (hill, depression)
- Water feature tools (river, lake, coastal)
- History list (undo/redo visualization)
- Quick action buttons

Why This Design:
- Tool-based workflow (standard in image editors)
- Visual history for context
- Quick access to common operations
- Organized by category
"""

import tkinter as tk
from tkinter import ttk
from typing import Optional, List


class ToolPalette(ttk.Frame):
    """
    Tool palette for manual heightmap editing.

    Layout:
    - Brush Tools section
    - Feature Tools section
    - Water Features section
    - History List
    - Quick Actions

    Why this organization:
    - Grouped by purpose (easier to find)
    - Most common tools at top
    - History provides context
    - Standard pattern (Photoshop, GIMP, etc.)
    """

    def __init__(self, parent, gui):
        """
        Initialize tool palette.

        Args:
            parent: Parent widget
            gui: Reference to main GUI (for callbacks)
        """
        super().__init__(parent, width=280)
        self.gui = gui

        # Current tool selection
        self.current_tool = tk.StringVar(value='none')
        self.brush_size = tk.IntVar(value=50)
        self.brush_strength = tk.DoubleVar(value=0.5)

        # Create widgets
        self._create_widgets()

    def _create_widgets(self):
        """Create all tool palette widgets - compact layout."""
        # Title
        title = ttk.Label(self, text="Tools & Actions", font=('Arial', 11, 'bold'))
        title.pack(pady=(8, 3))

        # Navigation mode button (deselect all tools)
        nav_btn = ttk.Button(
            self,
            text="Pan/Zoom Mode",
            command=self._deselect_tools
        )
        nav_btn.pack(fill=tk.X, padx=10, pady=(5, 10))

        # Brush tools section
        self._create_brush_tools()

        # Feature tools section
        self._create_feature_tools()

        # Quick actions (compact)
        self._create_quick_actions()

        # History list (compact)
        self._create_history_list()

    def _create_brush_tools(self):
        """Create brush tool section."""
        frame = ttk.LabelFrame(self, text="Brush Tools", padding=10)
        frame.pack(fill=tk.X, padx=10, pady=5)

        tools = [
            ('Raise', 'raise', 'Raise terrain height'),
            ('Lower', 'lower', 'Lower terrain height'),
            ('Smooth', 'smooth', 'Smooth terrain'),
            ('Flatten', 'flatten', 'Flatten to level')
        ]

        for label, value, tooltip in tools:
            btn = ttk.Button(
                frame,
                text=label,
                command=lambda v=value: self._select_tool(v)
            )
            btn.pack(fill=tk.X, pady=2)

        # Brush size slider
        ttk.Label(frame, text="Brush Size:").pack(anchor=tk.W, pady=(10, 0))
        size_slider = ttk.Scale(
            frame,
            from_=10,
            to=200,
            variable=self.brush_size,
            orient=tk.HORIZONTAL
        )
        size_slider.pack(fill=tk.X)
        ttk.Label(frame, textvariable=self.brush_size).pack(anchor=tk.E)

        # Brush strength slider
        ttk.Label(frame, text="Strength:").pack(anchor=tk.W, pady=(10, 0))
        strength_slider = ttk.Scale(
            frame,
            from_=0.1,
            to=1.0,
            variable=self.brush_strength,
            orient=tk.HORIZONTAL
        )
        strength_slider.pack(fill=tk.X)

        # Label showing current strength value
        strength_label = ttk.Label(frame, text=f"{self.brush_strength.get():.2f}")
        strength_label.pack(anchor=tk.E)

        # Update label when slider changes
        def update_strength_label(val):
            strength_label.config(text=f"{float(val):.2f}")

        strength_slider.config(command=update_strength_label)

    def _create_feature_tools(self):
        """Create feature tool section."""
        frame = ttk.LabelFrame(self, text="Feature Tools", padding=10)
        frame.pack(fill=tk.X, padx=10, pady=5)

        tools = [
            ('Add Hill', 'hill', 'Add circular hill'),
            ('Add Depression', 'depression', 'Add circular depression'),
            ('Add Ridge', 'ridge', 'Add linear ridge'),
            ('Add Valley', 'valley', 'Add linear valley')
        ]

        for label, value, tooltip in tools:
            btn = ttk.Button(
                frame,
                text=label,
                command=lambda v=value: self._select_tool(v)
            )
            btn.pack(fill=tk.X, pady=2)

    # Water tools removed - now in Parameter Panel > Water tab

    def _create_history_list(self):
        """Create compact history list display."""
        frame = ttk.LabelFrame(self, text="History", padding=8)
        frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        # Scrollable listbox (compact)
        scrollbar = ttk.Scrollbar(frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        self.history_listbox = tk.Listbox(
            frame,
            yscrollcommand=scrollbar.set,
            height=5,  # Reduced from 8 to save space
            font=('Arial', 8)  # Smaller font
        )
        self.history_listbox.pack(fill=tk.BOTH, expand=True)
        scrollbar.config(command=self.history_listbox.yview)

        # Bind double-click to jump to history state
        self.history_listbox.bind('<Double-Button-1>', self._on_history_click)

    def _create_quick_actions(self):
        """Create compact quick action buttons."""
        frame = ttk.LabelFrame(self, text="Actions", padding=8)
        frame.pack(fill=tk.X, padx=10, pady=5)

        # Removed 3D Preview (now in Water tab)
        # Keep only non-redundant actions
        actions = [
            ('Analyze Terrain', self.gui.show_analysis),
            ('Export to CS2', self.gui.export_to_cs2)
        ]

        for label, command in actions:
            btn = ttk.Button(frame, text=label, command=command)
            btn.pack(fill=tk.X, pady=2)

    def _deselect_tools(self):
        """
        Deselect all tools and return to pan/zoom mode.

        Sets current_tool to 'none' which enables:
        - Click and drag to pan
        - Mouse wheel to zoom
        - No tool application on click
        """
        self.current_tool.set('none')
        self.gui.set_status("Pan/Zoom mode - Click and drag to move, scroll to zoom")

    def _select_tool(self, tool: str):
        """
        Select a tool for use.

        Args:
            tool: Tool name

        Why this method:
        - Centralizes tool selection logic
        - Can add visual feedback (highlight selected tool)
        - Can setup tool-specific cursor
        """
        self.current_tool.set(tool)
        self.gui.set_status(f"Tool selected: {tool} - Click 'Pan/Zoom' to return to navigation")

        # Note: In full implementation, would:
        # 1. Change cursor on canvas
        # 2. Bind canvas click events to tool action
        # 3. Show tool-specific options
        # 4. Highlight selected tool button

    def _apply_water_feature(self, feature: str):
        """
        Apply water feature to heightmap.

        Args:
            feature: Feature type ('rivers', 'lakes', 'coastal')

        Why separate from _select_tool:
        - Water features are one-time operations, not brush tools
        - Apply immediately, don't require canvas interaction
        - Different workflow pattern
        """
        if feature == 'rivers':
            self.gui.add_rivers()
        elif feature == 'lakes':
            self.gui.add_lakes()
        elif feature == 'coastal':
            self.gui.add_coastal()

    def _update_history(self):
        """
        Update history list display.

        Shows:
        - Command names
        - Timestamp
        - Current position in history (highlighted)

        Why visual history:
        - Provides context for undo/redo
        - Shows what operations were performed
        - Standard in professional software
        """
        self.history_listbox.delete(0, tk.END)

        # Get command history from GUI
        history = self.gui.history

        # Add commands to list
        for i, command in enumerate(history.undo_stack):
            # Format: "1. CommandName"
            self.history_listbox.insert(tk.END, f"{i+1}. {command.__class__.__name__}")

        # Highlight current position
        current_pos = len(history.undo_stack)
        if current_pos > 0:
            self.history_listbox.selection_set(current_pos - 1)
            self.history_listbox.see(current_pos - 1)

    def _on_history_click(self, event):
        """
        Handle history list double-click.

        Allows jumping to specific point in history.

        Why this feature:
        - Non-linear undo (jump to any state)
        - Visual navigation
        - Advanced feature for power users
        """
        selection = self.history_listbox.curselection()
        if selection:
            index = selection[0]
            # Note: Would implement history jumping here
            self.gui.set_status(f"History navigation: Position {index + 1}")

    def _save_preview(self):
        """
        Save current preview image.

        Why separate from save heightmap:
        - Preview is visual representation (hillshade + color)
        - Heightmap is data (16-bit PNG)
        - Different use cases (sharing vs. editing)
        """
        from tkinter import filedialog
        filename = filedialog.asksaveasfilename(
            title="Save Preview Image",
            defaultextension=".png",
            filetypes=[("PNG files", "*.png"), ("JPEG files", "*.jpg")]
        )

        if filename:
            try:
                # Get current preview image
                if self.gui.preview.current_image is not None:
                    self.gui.preview.current_image.save(filename)
                    self.gui.set_status(f"Preview saved: {filename}")
                else:
                    self.gui.set_status("No preview to save")
            except Exception as e:
                from tkinter import messagebox
                messagebox.showerror("Error", f"Failed to save preview: {e}")

    def get_brush_parameters(self) -> dict:
        """
        Get current brush parameters.

        Returns:
            Dictionary with brush size and strength

        Used by:
        - Canvas click handlers
        - Brush tool implementation
        """
        return {
            'size': self.brush_size.get(),
            'strength': self.brush_strength.get()
        }
