"""
CS2 Heightmap Generator - Progress Dialog

Provides visual feedback during long-running operations.
Prevents GUI from appearing frozen during terrain generation.
"""

import tkinter as tk
from tkinter import ttk


class ProgressDialog:
    """
    Non-blocking progress dialog for long-running operations.

    Shows:
    - Current operation description
    - Progress bar
    - Percentage complete

    Usage:
        progress = ProgressDialog(parent, "Generating Terrain")
        progress.update(0, "Generating base noise...")
        # ... do work ...
        progress.update(33, "Creating mountain ranges...")
        # ... do work ...
        progress.close()
    """

    def __init__(self, parent, title="Processing"):
        """
        Create progress dialog.

        Args:
            parent: Parent tkinter window
            title: Dialog title
        """
        self.parent = parent

        # Create toplevel window
        self.window = tk.Toplevel(parent)
        self.window.title(title)
        self.window.geometry("400x150")
        self.window.resizable(False, False)

        # Center on parent
        self.window.transient(parent)
        self.window.grab_set()

        # Main frame
        frame = ttk.Frame(self.window, padding=20)
        frame.pack(fill=tk.BOTH, expand=True)

        # Status label
        self.status_label = ttk.Label(
            frame,
            text="Starting...",
            font=('Arial', 10)
        )
        self.status_label.pack(pady=(0, 10))

        # Progress bar
        self.progress_bar = ttk.Progressbar(
            frame,
            mode='determinate',
            length=350,
            maximum=100
        )
        self.progress_bar.pack(pady=(0, 5))

        # Percentage label
        self.percentage_label = ttk.Label(
            frame,
            text="0%",
            font=('Arial', 9)
        )
        self.percentage_label.pack(pady=(0, 10))

        # Prevent closing with X button
        self.window.protocol("WM_DELETE_WINDOW", lambda: None)

        # Force window to appear
        self.window.update()

    def update(self, percentage, status_text=None):
        """
        Update progress.

        Args:
            percentage: Progress percentage (0-100)
            status_text: Optional status message to display
        """
        # Update progress bar
        self.progress_bar['value'] = percentage

        # Update percentage label
        self.percentage_label.config(text=f"{int(percentage)}%")

        # Update status text if provided
        if status_text:
            self.status_label.config(text=status_text)

        # Force GUI to update (critical for responsiveness!)
        self.window.update_idletasks()
        self.window.update()

    def close(self):
        """Close the progress dialog."""
        try:
            self.window.grab_release()
            self.window.destroy()
        except:
            pass  # Window may already be destroyed
