"""
Pipeline Results Dialog (Session 9)

Displays comprehensive statistics from the terrain generation pipeline (Sessions 2-8).

Shows:
- Stage timings and performance metrics
- Buildability progression through stages
- Final terrain analysis
- Recommendations for parameter tuning

Why This Design:
- Scrollable text display for long output
- Organized by sections (timings, buildability, analysis)
- Non-blocking dialog (user can close anytime)
- Copy-friendly format for sharing results

Created: 2025-10-10 (Session 9)
Part of: CS2 Final Implementation Plan
"""

import tkinter as tk
from tkinter import ttk, scrolledtext
from typing import Dict


class PipelineResultsDialog(tk.Toplevel):
    """
    Dialog window for displaying pipeline generation results.

    Layout:
    - Title with generation summary
    - Scrollable text area with statistics
    - Close button

    Why scrollable text:
    - Pipeline produces extensive statistics
    - Users may want to review different sections
    - Easy to copy/paste results
    """

    def __init__(self, parent, stats: Dict):
        """
        Initialize results dialog.

        Args:
            parent: Parent window (main GUI)
            stats: Complete statistics dictionary from pipeline.generate()
        """
        super().__init__(parent)
        self.stats = stats

        # Window setup
        self.title("Pipeline Generation Results")
        self.geometry("700x600")
        self.minsize(600, 500)

        # Create widgets
        self._create_widgets()

        # Center on parent
        self.transient(parent)
        self.update_idletasks()
        x = parent.winfo_x() + (parent.winfo_width() - self.winfo_width()) // 2
        y = parent.winfo_y() + (parent.winfo_height() - self.winfo_height()) // 2
        self.geometry(f"+{x}+{y}")

    def _create_widgets(self):
        """Create dialog widgets."""
        # Title frame with summary
        title_frame = ttk.Frame(self, padding=10)
        title_frame.pack(fill=tk.X)

        # Build success/failure status
        final_buildable = self.stats.get('final_buildable_pct', 0.0)
        target_min = self.stats.get('target_buildable_min', 55.0)
        target_max = self.stats.get('target_buildable_max', 65.0)
        target_achieved = self.stats.get('target_achieved', False)

        if target_achieved:
            status_text = f"✓ SUCCESS - {final_buildable:.1f}% Buildable (Target: {target_min:.0f}-{target_max:.0f}%)"
            status_color = 'green4'
        elif final_buildable < target_min:
            status_text = f"⚠ BELOW TARGET - {final_buildable:.1f}% Buildable (Target: {target_min:.0f}-{target_max:.0f}%)"
            status_color = 'orange3'
        else:
            status_text = f"⚠ ABOVE TARGET - {final_buildable:.1f}% Buildable (Target: {target_min:.0f}-{target_max:.0f}%)"
            status_color = 'orange3'

        title_label = ttk.Label(
            title_frame,
            text=status_text,
            font=('Arial', 12, 'bold'),
            foreground=status_color
        )
        title_label.pack(pady=(0, 5))

        # Total time
        total_time = self.stats.get('total_pipeline_time', 0.0)
        time_label = ttk.Label(
            title_frame,
            text=f"Total Generation Time: {total_time:.1f}s ({total_time/60:.1f} min)",
            font=('Arial', 10)
        )
        time_label.pack()

        # Scrollable text area
        text_frame = ttk.Frame(self, padding=10)
        text_frame.pack(fill=tk.BOTH, expand=True)

        self.text_widget = scrolledtext.ScrolledText(
            text_frame,
            wrap=tk.WORD,
            font=('Courier New', 9),
            padx=5,
            pady=5
        )
        self.text_widget.pack(fill=tk.BOTH, expand=True)

        # Populate text with formatted statistics
        self._populate_statistics()

        # Make text read-only
        self.text_widget.configure(state='disabled')

        # Button frame
        button_frame = ttk.Frame(self, padding=10)
        button_frame.pack(fill=tk.X)

        copy_btn = ttk.Button(
            button_frame,
            text="Copy to Clipboard",
            command=self._copy_to_clipboard
        )
        copy_btn.pack(side=tk.LEFT, padx=(0, 5))

        close_btn = ttk.Button(
            button_frame,
            text="Close",
            command=self.destroy
        )
        close_btn.pack(side=tk.RIGHT)

    def _populate_statistics(self):
        """Populate text widget with formatted statistics."""
        self.text_widget.configure(state='normal')

        # Header
        self._write_section("=" * 70)
        self._write_section("TERRAIN GENERATION PIPELINE - DETAILED RESULTS")
        self._write_section("=" * 70)
        self._write("")

        # Metadata
        self._write_section("[PIPELINE METADATA]")
        self._write(f"  Resolution:      {self.stats.get('resolution', 4096)}×{self.stats.get('resolution', 4096)}")
        self._write(f"  Map Size:        {self.stats.get('map_size_meters', 14336.0):.0f}m")
        self._write(f"  Seed:            {self.stats.get('seed', 'N/A')}")
        self._write(f"  Pipeline Version: {self.stats.get('pipeline_version', '1.0')}")
        self._write("")

        # Stage Timings
        self._write_section("[STAGE TIMINGS]")
        self._write(f"  Stage 1 (Zones):           {self.stats.get('stage1_zone_time', 0.0):6.2f}s")
        self._write(f"  Stage 2 (Terrain):         {self.stats.get('stage2_terrain_time', 0.0):6.2f}s")
        self._write(f"  Stage 3 (Ridges):          {self.stats.get('stage3_ridge_time', 0.0):6.2f}s")
        self._write(f"  Stage 4 (Erosion):         {self.stats.get('stage4_erosion_time', 0.0):6.2f}s")
        self._write(f"  Stage 4.5 (Rivers):        {self.stats.get('stage4_5_river_time', 0.0):6.2f}s")
        self._write(f"  Stage 5.5 (Detail+Verify): {self.stats.get('stage5_5_detail_verification_time', 0.0):6.2f}s")
        self._write(f"  Stage 6 (Normalization):   {self.stats.get('stage6_normalization_time', 0.0):6.2f}s")
        self._write(f"  {'-' * 40}")
        total = self.stats.get('total_pipeline_time', 0.0)
        self._write(f"  Total:                     {total:6.2f}s ({total/60:.1f} min)")
        self._write("")

        # Buildability Progression
        self._write_section("[BUILDABILITY PROGRESSION]")
        terrain_stats = self.stats.get('terrain_stats', {})
        erosion_stats = self.stats.get('erosion_stats', {})
        verification = self.stats.get('verification_result', {})

        self._write(f"  After zones:        N/A (potential map only)")
        self._write(f"  After terrain:      {terrain_stats.get('buildable_percent', 0.0):6.1f}%")
        self._write(f"  After ridges:       {terrain_stats.get('buildable_percent', 0.0):6.1f}% (ridges don't change slopes)")
        if not erosion_stats.get('skipped', False):
            self._write(f"  After erosion:      {erosion_stats.get('final_buildable_pct', 0.0):6.1f}%")
        if not verification.get('skipped', False):
            self._write(f"  After verification: {verification.get('final_buildable_pct', 0.0):6.1f}%")
        self._write(f"  Final (normalized): {self.stats.get('final_buildable_pct', 0.0):6.1f}%")
        self._write("")

        # Final Terrain Analysis
        self._write_section("[FINAL TERRAIN ANALYSIS]")
        self._write(f"  Buildable percentage: {self.stats.get('final_buildable_pct', 0.0):.1f}%")
        self._write(f"  Mean slope:           {self.stats.get('final_mean_slope', 0.0):.2f}%")
        self._write(f"  Median slope:         {self.stats.get('final_median_slope', 0.0):.2f}%")
        self._write(f"  90th percentile:      {self.stats.get('final_p90_slope', 0.0):.2f}%")
        self._write(f"  99th percentile:      {self.stats.get('final_p99_slope', 0.0):.2f}%")
        self._write(f"  Height range:         [{self.stats.get('final_min_height', 0.0):.4f}, {self.stats.get('final_max_height', 1.0):.4f}]")
        self._write("")

        # Detail Statistics (if applied)
        detail_stats = self.stats.get('detail_stats', {})
        if not detail_stats.get('skipped', False):
            self._write_section("[DETAIL ADDITION]")
            self._write(f"  Detail applied to:     {detail_stats.get('detail_applied_pct', 0.0):.1f}% of terrain")
            self._write(f"  Mean detail amplitude: {detail_stats.get('mean_detail_amplitude', 0.0):.4f}")
            self._write(f"  Max detail amplitude:  {detail_stats.get('max_detail_amplitude', 0.0):.4f}")
            self._write(f"  Processing time:       {detail_stats.get('processing_time', 0.0):.2f}s")
            self._write("")

        # River Statistics (if applied)
        river_stats = self.stats.get('river_stats', {})
        if not river_stats.get('skipped', False):
            self._write_section("[RIVER ANALYSIS]")
            self._write(f"  Rivers detected:       {river_stats.get('num_rivers', 0)}")
            if river_stats.get('num_rivers', 0) > 0:
                self._write(f"  Total river length:    {river_stats.get('total_river_length_meters', 0.0):.0f}m")
                self._write(f"  Longest river:         {river_stats.get('longest_river_length_meters', 0.0):.0f}m")
                self._write(f"  Mean river length:     {river_stats.get('mean_river_length_meters', 0.0):.0f}m")
            self._write("")

        # Validation Status
        self._write_section("[VALIDATION]")
        target_min = self.stats.get('target_buildable_min', 55.0)
        target_max = self.stats.get('target_buildable_max', 65.0)
        final_buildable = self.stats.get('final_buildable_pct', 0.0)
        target_achieved = self.stats.get('target_achieved', False)

        self._write(f"  Target range:         {target_min:.0f}-{target_max:.0f}% buildable")
        self._write(f"  Achieved:             {final_buildable:.1f}%")

        if target_achieved:
            self._write(f"  Status:               [SUCCESS] Target achieved!")
        elif final_buildable < target_min:
            deficit = target_min - final_buildable
            self._write(f"  Status:               [BELOW TARGET] by {deficit:.1f}%")
            self._write(f"  Suggestion:           Increase target_coverage or num_particles")
        else:
            excess = final_buildable - target_max
            self._write(f"  Status:               [ABOVE TARGET] by {excess:.1f}%")
            self._write(f"  Suggestion:           Decrease target_coverage or reduce erosion")
        self._write("")

        # Parameters Used
        self._write_section("[PARAMETERS USED]")
        params = self.stats.get('parameters', {})
        self._write(f"  Target Coverage:      {params.get('target_coverage', 0.7):.2f}")
        self._write(f"  Zone Wavelength:      {params.get('zone_wavelength', 6500.0):.0f}m")
        self._write(f"  Base Amplitude:       {params.get('base_amplitude', 0.2):.2f}")
        self._write(f"  Erosion Particles:    {params.get('num_particles', 0):,}")
        self._write(f"  Apply Ridges:         {params.get('apply_ridges', True)}")
        self._write(f"  Apply Erosion:        {params.get('apply_erosion', True)}")
        self._write("")

        # Footer
        self._write_section("=" * 70)
        self._write_section("END OF REPORT")
        self._write_section("=" * 70)

        self.text_widget.configure(state='disabled')

    def _write_section(self, text: str):
        """Write a section header."""
        self.text_widget.insert(tk.END, text + "\n")

    def _write(self, text: str):
        """Write a line of text."""
        self.text_widget.insert(tk.END, text + "\n")

    def _copy_to_clipboard(self):
        """Copy all text to clipboard."""
        self.clipboard_clear()
        self.clipboard_append(self.text_widget.get(1.0, tk.END))
        self.title("Pipeline Generation Results (Copied to Clipboard)")
        self.after(2000, lambda: self.title("Pipeline Generation Results"))


def show_results_dialog(parent, stats: Dict):
    """
    Convenience function to show results dialog.

    Args:
        parent: Parent window
        stats: Pipeline statistics dictionary

    Returns:
        PipelineResultsDialog instance
    """
    dialog = PipelineResultsDialog(parent, stats)
    return dialog
