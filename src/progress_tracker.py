"""
CS2 Progress Tracking Module

This module provides progress tracking for expensive operations using tqdm.
Progress bars give visual feedback during generation, which can take 30-120 seconds
for full 4096x4096 heightmaps.

Design Pattern: Context Manager
- Ensures cleanup even if errors occur
- Automatic start/stop of progress tracking
- Thread-safe for future multi-threading support
"""

from tqdm import tqdm
from typing import Optional, Any
import sys


class ProgressTracker:
    """
    Context manager for tracking progress of long-running operations.

    Usage:
        with ProgressTracker("Generating terrain", total=100) as progress:
            for i in range(100):
                # ... do work ...
                progress.update(1)

    Why Context Manager Pattern:
    - Guarantees cleanup (progress bar closes even on exceptions)
    - Clean, readable code (with statement)
    - Standard Python pattern for resource management
    """

    def __init__(self,
                 description: str,
                 total: Optional[int] = None,
                 unit: str = "it",
                 disable: bool = False):
        """
        Initialize progress tracker.

        Args:
            description: What operation is being tracked
            total: Total number of iterations (None for unknown)
            unit: Unit name for progress (default: "it" for iterations)
            disable: If True, no progress bar shown (for batch/silent mode)

        Why 'disable' parameter:
        - Allows silent mode for scripting/automation
        - Avoids progress bar clutter in logs
        - Can be controlled by --quiet CLI flag
        """
        self.description = description
        self.total = total
        self.unit = unit
        self.disable = disable
        self.pbar: Optional[tqdm] = None

    def __enter__(self) -> 'ProgressTracker':
        """
        Enter context manager - create and start progress bar.

        Why tqdm parameters used:
        - desc: Shows what's happening
        - total: Enables percentage display
        - unit: Clarifies what's being counted
        - ncols: Fixes width for consistent display
        - file: sys.stdout ensures visibility in all terminals
        """
        if not self.disable:
            self.pbar = tqdm(
                desc=self.description,
                total=self.total,
                unit=self.unit,
                ncols=80,
                file=sys.stdout
            )
        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """
        Exit context manager - close progress bar.

        Args:
            exc_type, exc_val, exc_tb: Exception info (if any occurred)

        Why this matters:
        - Progress bar MUST be closed to clear terminal properly
        - Unclosed bars can corrupt terminal output
        - Even if operation fails, cleanup still happens
        """
        if self.pbar is not None:
            self.pbar.close()

    def update(self, n: int = 1) -> None:
        """
        Update progress by n steps.

        Args:
            n: Number of steps completed (default: 1)

        Thread Safety Note:
        - tqdm is thread-safe by default
        - Safe to call from multiple threads (for Phase 5 multi-threading)
        """
        if self.pbar is not None:
            self.pbar.update(n)

    def set_description(self, desc: str) -> None:
        """
        Change the description while progress bar is running.

        Args:
            desc: New description

        Use Case:
        - Multi-stage operations (e.g., "Loading... Generating... Saving...")
        - Informative feedback during long operations
        """
        if self.pbar is not None:
            self.pbar.set_description(desc)

    def set_postfix(self, **kwargs) -> None:
        """
        Add additional info to progress bar (shown at end of line).

        Args:
            **kwargs: Key-value pairs to display (e.g., loss=0.5, epoch=3)

        Use Case:
        - Show current statistics (memory usage, peak height, etc.)
        - Dynamic info without changing main description
        """
        if self.pbar is not None:
            self.pbar.set_postfix(**kwargs)


def track_array_operation(description: str,
                         total_size: int,
                         chunk_size: int = 1000,
                         disable: bool = False) -> ProgressTracker:
    """
    Create progress tracker for array operations.

    Args:
        description: Operation description
        total_size: Total array size
        chunk_size: Size of each processing chunk
        disable: Disable progress display

    Returns:
        Configured ProgressTracker

    Why this helper exists:
    - Array operations are common (noise generation, smoothing, etc.)
    - Calculates correct 'total' from size and chunk_size
    - Consistent progress tracking across codebase

    Example:
        with track_array_operation("Smoothing", heightmap.size, chunk_size=1000) as progress:
            for chunk in process_chunks(heightmap):
                process(chunk)
                progress.update(len(chunk))
    """
    total_chunks = (total_size + chunk_size - 1) // chunk_size  # Ceiling division
    return ProgressTracker(description, total=total_chunks, unit="chunks", disable=disable)


def track_iteration(description: str,
                   iterable,
                   total: Optional[int] = None,
                   disable: bool = False):
    """
    Wrap an iterable with progress tracking.

    Args:
        description: Operation description
        iterable: Iterable to track
        total: Total items (if not available from iterable)
        disable: Disable progress display

    Returns:
        tqdm-wrapped iterable

    Why this is useful:
    - Simplest way to add progress to loops
    - No manual update() calls needed
    - Automatically detects total from len(iterable) if possible

    Example:
        for item in track_iteration("Processing items", items):
            process(item)
    """
    if disable:
        return iterable

    # Try to get length from iterable
    if total is None:
        try:
            total = len(iterable)
        except TypeError:
            pass  # iterable has no length, use None (unknown total)

    return tqdm(
        iterable,
        desc=description,
        total=total,
        ncols=80,
        file=sys.stdout
    )
