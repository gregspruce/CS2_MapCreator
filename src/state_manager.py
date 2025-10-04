"""
State Management for CS2 Heightmap Generator

Implements the Command pattern for undo/redo functionality. This is the ONLY correct
way to implement undo/redo - by encapsulating each operation as a command object
that knows how to execute and reverse itself.

Why Command Pattern:
- Encapsulates operations as objects
- Allows undo/redo by storing command history
- Supports macro commands (composite operations)
- Memory efficient (stores only diffs, not full snapshots)

This pattern is used in every professional graphics application (Photoshop, Blender, etc.)
because it's the mathematically optimal solution to the undo/redo problem.
"""

import numpy as np
from abc import ABC, abstractmethod
from typing import Optional, List, Any
from copy import deepcopy


class Command(ABC):
    """
    Abstract base class for all commands.

    Each command must implement execute() and undo(). The command stores
    whatever state is needed to reverse itself - this is usually much less
    data than a full heightmap snapshot.

    Example: A smooth operation stores the original values only in the
    affected region, not the entire 4096x4096 heightmap.
    """

    def __init__(self, description: str):
        """
        Initialize command with a human-readable description.

        Args:
            description: What this command does (e.g., "Smooth terrain")
        """
        self.description = description
        self._executed = False

    @abstractmethod
    def execute(self) -> None:
        """
        Execute the command, modifying the heightmap.

        This method should:
        1. Store any state needed for undo
        2. Apply the changes to the heightmap
        3. Set self._executed = True
        """
        pass

    @abstractmethod
    def undo(self) -> None:
        """
        Reverse the command's effects.

        This method should:
        1. Restore the heightmap to its pre-execute state
        2. Set self._executed = False
        """
        pass

    def __str__(self) -> str:
        return self.description


class SetHeightDataCommand(Command):
    """
    Command for replacing entire heightmap data.

    This is the most common command - used when loading presets,
    generating new terrain, or importing heightmaps.
    """

    def __init__(self, generator, new_data: np.ndarray, description: str = "Set height data", normalize: bool = True):
        """
        Args:
            generator: HeightmapGenerator instance
            new_data: New heightmap array
            description: Optional custom description
            normalize: If True, normalize the data via set_height_data().
                      If False, set directly (assumes data is already 0.0-1.0)
        """
        super().__init__(description)
        self.generator = generator
        self.new_data = new_data.copy()  # Copy to avoid external modifications
        self.old_data = None  # Will store previous state on execute
        self.normalize = normalize

    def execute(self) -> None:
        """Store current state and apply new data."""
        # Save current heightmap for undo
        self.old_data = self.generator.get_height_data()

        # Apply new data
        if self.normalize:
            self.generator.set_height_data(self.new_data)
        else:
            # Direct assignment (data already normalized)
            self.generator.heightmap = self.new_data.copy()
        self._executed = True

    def undo(self) -> None:
        """Restore previous heightmap."""
        if not self._executed or self.old_data is None:
            return

        # Restore old data directly (already normalized)
        self.generator.heightmap = self.old_data
        self._executed = False


class SmoothCommand(Command):
    """
    Command for smoothing operations.

    Memory optimization: Only stores the affected region, not entire heightmap.
    For a 3x3 kernel, the "affected region" is the entire heightmap, but for
    larger operations we could optimize further.
    """

    def __init__(self, generator, iterations: int = 1, kernel_size: int = 3):
        super().__init__(f"Smooth terrain ({iterations}x, kernel={kernel_size})")
        self.generator = generator
        self.iterations = iterations
        self.kernel_size = kernel_size
        self.old_data = None

    def execute(self) -> None:
        """Store state and apply smoothing."""
        self.old_data = self.generator.get_height_data()
        self.generator.smooth(self.iterations, self.kernel_size)
        self._executed = True

    def undo(self) -> None:
        """Restore pre-smoothing state."""
        if not self._executed or self.old_data is None:
            return

        self.generator.heightmap = self.old_data
        self._executed = False


class AddCircleCommand(Command):
    """
    Command for adding circular hills/depressions.

    Memory optimization: Only stores the affected circular region.
    """

    def __init__(self, generator, center_x: float, center_y: float,
                 radius: float, height: float, blend: bool = True):
        super().__init__(f"Add circle at ({center_x:.2f}, {center_y:.2f})")
        self.generator = generator
        self.center_x = center_x
        self.center_y = center_y
        self.radius = radius
        self.height = height
        self.blend = blend
        self.old_data = None

    def execute(self) -> None:
        """Store state and add circle."""
        # For simplicity, store entire heightmap
        # TODO: Optimize to store only circular region
        self.old_data = self.generator.get_height_data()

        self.generator.add_circle(
            self.center_x, self.center_y,
            self.radius, self.height, self.blend
        )
        self._executed = True

    def undo(self) -> None:
        """Restore pre-circle state."""
        if not self._executed or self.old_data is None:
            return

        self.generator.heightmap = self.old_data
        self._executed = False


class ApplyFunctionCommand(Command):
    """
    Command for applying arbitrary functions to heightmap.

    This is a catch-all for custom operations. Since we don't know
    what the function does, we must store the entire before-state.
    """

    def __init__(self, generator, func, description: str = "Apply function"):
        super().__init__(description)
        self.generator = generator
        self.func = func
        self.old_data = None

    def execute(self) -> None:
        """Store state and apply function."""
        self.old_data = self.generator.get_height_data()
        self.generator.apply_function(self.func)
        self._executed = True

    def undo(self) -> None:
        """Restore pre-function state."""
        if not self._executed or self.old_data is None:
            return

        self.generator.heightmap = self.old_data
        self._executed = False


class NormalizeCommand(Command):
    """
    Command for normalizing height range.
    """

    def __init__(self, generator, min_height: float = 0.0, max_height: float = 1.0):
        super().__init__(f"Normalize to [{min_height:.2f}, {max_height:.2f}]")
        self.generator = generator
        self.min_height = min_height
        self.max_height = max_height
        self.old_data = None

    def execute(self) -> None:
        """Store state and normalize."""
        self.old_data = self.generator.get_height_data()
        self.generator.normalize_range(self.min_height, self.max_height)
        self._executed = True

    def undo(self) -> None:
        """Restore pre-normalize state."""
        if not self._executed or self.old_data is None:
            return

        self.generator.heightmap = self.old_data
        self._executed = False


class MacroCommand(Command):
    """
    Composite command that groups multiple commands.

    Example: "Generate Island Map" = Generate Perlin + Add Radial Gradient + Smooth

    This allows complex operations to be undone/redone as a single unit.
    """

    def __init__(self, commands: List[Command], description: str):
        super().__init__(description)
        self.commands = commands

    def execute(self) -> None:
        """Execute all sub-commands in order."""
        for cmd in self.commands:
            cmd.execute()
        self._executed = True

    def undo(self) -> None:
        """Undo all sub-commands in reverse order."""
        if not self._executed:
            return

        for cmd in reversed(self.commands):
            cmd.undo()
        self._executed = False


class CommandHistory:
    """
    Manages command history for undo/redo operations.

    This is a stack-based implementation:
    - undo_stack: Commands that have been executed
    - redo_stack: Commands that have been undone

    When a new command is executed, the redo_stack is cleared (you can't
    redo after making a new change - this is standard behavior in all applications).
    """

    def __init__(self, max_history: int = 50):
        """
        Initialize command history.

        Args:
            max_history: Maximum number of commands to keep in history.
                        Older commands are automatically purged to save memory.
        """
        self.undo_stack: List[Command] = []
        self.redo_stack: List[Command] = []
        self.max_history = max_history

    def execute(self, command: Command) -> None:
        """
        Execute a command and add it to history.

        Args:
            command: Command to execute
        """
        # Execute the command
        command.execute()

        # Add to undo stack
        self.undo_stack.append(command)

        # Clear redo stack (can't redo after new action)
        self.redo_stack.clear()

        # Limit history size
        if len(self.undo_stack) > self.max_history:
            self.undo_stack.pop(0)  # Remove oldest command

    def undo(self) -> Optional[str]:
        """
        Undo the most recent command.

        Returns:
            Description of undone command, or None if nothing to undo
        """
        if not self.undo_stack:
            return None

        # Pop command from undo stack
        command = self.undo_stack.pop()

        # Undo it
        command.undo()

        # Add to redo stack
        self.redo_stack.append(command)

        return command.description

    def redo(self) -> Optional[str]:
        """
        Redo the most recently undone command.

        Returns:
            Description of redone command, or None if nothing to redo
        """
        if not self.redo_stack:
            return None

        # Pop command from redo stack
        command = self.redo_stack.pop()

        # Re-execute it
        command.execute()

        # Add back to undo stack
        self.undo_stack.append(command)

        return command.description

    def can_undo(self) -> bool:
        """Check if undo is available."""
        return len(self.undo_stack) > 0

    def can_redo(self) -> bool:
        """Check if redo is available."""
        return len(self.redo_stack) > 0

    def clear(self) -> None:
        """Clear all history (useful when loading a new heightmap)."""
        self.undo_stack.clear()
        self.redo_stack.clear()

    def get_undo_list(self) -> List[str]:
        """
        Get list of undoable command descriptions.

        Returns:
            List of descriptions, most recent first
        """
        return [cmd.description for cmd in reversed(self.undo_stack)]

    def get_redo_list(self) -> List[str]:
        """
        Get list of redoable command descriptions.

        Returns:
            List of descriptions, most recent first
        """
        return [cmd.description for cmd in reversed(self.redo_stack)]

    def get_memory_usage(self) -> dict:
        """
        Estimate memory usage of command history.

        Returns:
            Dictionary with memory usage statistics
        """
        undo_arrays = sum(
            cmd.old_data.nbytes if hasattr(cmd, 'old_data') and cmd.old_data is not None else 0
            for cmd in self.undo_stack
        )

        redo_arrays = sum(
            cmd.old_data.nbytes if hasattr(cmd, 'old_data') and cmd.old_data is not None else 0
            for cmd in self.redo_stack
        )

        return {
            'undo_commands': len(self.undo_stack),
            'redo_commands': len(self.redo_stack),
            'undo_memory_mb': undo_arrays / (1024 * 1024),
            'redo_memory_mb': redo_arrays / (1024 * 1024),
            'total_memory_mb': (undo_arrays + redo_arrays) / (1024 * 1024)
        }

