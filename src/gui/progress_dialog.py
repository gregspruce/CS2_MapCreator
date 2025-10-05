"""
CS2 Heightmap Generator - Progress Dialog

Modal progress dialog for long-running operations.

Features:
- Indeterminate progress bar (for operations without known duration)
- Status message display
- Cancel button (optional)
- Modal window (blocks parent interaction)

Why This Design:
- Standard pattern for long operations
- Keeps user informed
- Allows cancellation if needed
- Non-blocking (parent window stays responsive)
"""

import tkinter as tk
from tkinter import ttk
from typing import Optional, Callable


class ProgressDialog(tk.Toplevel):
    """
    Modal progress dialog for long-running operations.

    Usage:
        dialog = ProgressDialog(parent, "Generating terrain...")
        dialog.show()
        # ... do work in background thread ...
        dialog.close()
    """

    def __init__(self, parent, title: str = "Processing",
                 message: str = "Please wait...",
                 cancelable: bool = False,
                 on_cancel: Optional[Callable] = None):
        """
        Initialize progress dialog.

        Args:
            parent: Parent window
            title: Dialog title
            message: Status message to display
            cancelable: Whether to show cancel button
            on_cancel: Callback function when cancel is clicked
        """
        super().__init__(parent)

        self.parent = parent
        self.cancelled = False
        self.on_cancel = on_cancel

        # Configure window
        self.title(title)
        self.geometry("400x150")
        self.resizable(False, False)

        # Center on parent
        self.transient(parent)
        self.grab_set()  # Make modal

        # Create widgets
        self._create_widgets(message, cancelable)

        # Center on screen
        self.update_idletasks()
        x = parent.winfo_x() + (parent.winfo_width() // 2) - (self.winfo_width() // 2)
        y = parent.winfo_y() + (parent.winfo_height() // 2) - (self.winfo_height() // 2)
        self.geometry(f"+{x}+{y}")

    def _create_widgets(self, message: str, cancelable: bool):
        """Create dialog widgets."""
        # Message label
        self.message_label = ttk.Label(
            self,
            text=message,
            font=('Arial', 10),
            wraplength=350
        )
        self.message_label.pack(pady=20, padx=20)

        # Progress bar (indeterminate mode)
        self.progress = ttk.Progressbar(
            self,
            mode='indeterminate',
            length=350
        )
        self.progress.pack(pady=10, padx=20)
        self.progress.start(10)  # Start animation

        # Cancel button (if enabled)
        if cancelable:
            self.cancel_btn = ttk.Button(
                self,
                text="Cancel",
                command=self._on_cancel
            )
            self.cancel_btn.pack(pady=10)

    def _on_cancel(self):
        """Handle cancel button click."""
        self.cancelled = True
        if self.on_cancel:
            self.on_cancel()
        self.close()

    def update_message(self, message: str):
        """Update the status message."""
        self.message_label.config(text=message)
        self.update_idletasks()

    def close(self):
        """Close the dialog."""
        try:
            self.progress.stop()
            self.grab_release()
            self.destroy()
        except Exception:
            pass  # Ignore errors during cleanup

    def show(self):
        """Show the dialog (non-blocking)."""
        self.update_idletasks()
