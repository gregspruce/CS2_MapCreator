"""
CS2 Terrain Editor Module

Implements brush-based terrain editing and feature placement tools.

Features:
- Brush tools: Raise, Lower, Smooth, Flatten
- Feature tools: Hills, Depressions, Ridges, Valleys
- Undo/redo support via Command pattern
- Real-time preview updates

Why This Design:
- Brush tools use Gaussian falloff for natural blending
- Features use analytical shapes (no noise needed for speed)
- Commands enable undo/redo
- Decoupled from GUI for testability
"""

import numpy as np
from scipy import ndimage
from typing import Tuple, Optional
from ..state_manager import Command


class TerrainEditor:
    """
    Provides terrain editing tools for manual heightmap modification.

    All tools use a brush-based approach with Gaussian falloff
    for smooth, natural-looking modifications.
    """

    def __init__(self, heightmap: np.ndarray):
        """
        Initialize terrain editor.

        Args:
            heightmap: 2D numpy array of elevation values (0.0-1.0)
        """
        self.heightmap = heightmap.copy()
        self.height, self.width = heightmap.shape

    def apply_brush(self,
                   x: int,
                   y: int,
                   radius: int,
                   strength: float,
                   operation: str) -> np.ndarray:
        """
        Apply brush operation at specified location.

        Args:
            x, y: Center position in heightmap coordinates
            radius: Brush size in pixels
            strength: Operation strength (0.0-1.0)
            operation: 'raise', 'lower', 'smooth', or 'flatten'

        Returns:
            Modified heightmap

        Algorithm:
        1. Create Gaussian falloff kernel
        2. Apply operation based on type
        3. Blend with original using strength
        """
        result = self.heightmap.copy()

        # Create brush mask with Gaussian falloff
        brush_mask = self._create_gaussian_brush(radius)

        # Get region to modify
        y_min = max(0, y - radius)
        y_max = min(self.height, y + radius + 1)
        x_min = max(0, x - radius)
        x_max = min(self.width, x + radius + 1)

        # Get brush region (may be clipped at edges)
        brush_y_min = radius - (y - y_min)
        brush_y_max = brush_y_min + (y_max - y_min)
        brush_x_min = radius - (x - x_min)
        brush_x_max = brush_x_min + (x_max - x_min)

        # Extract region
        region = result[y_min:y_max, x_min:x_max]
        mask = brush_mask[brush_y_min:brush_y_max, brush_x_min:brush_x_max]

        # Apply operation
        if operation == 'raise':
            modified = region + (mask * strength * 0.1)  # Scale for reasonable effect
            modified = np.clip(modified, 0.0, 1.0)

        elif operation == 'lower':
            modified = region - (mask * strength * 0.1)
            modified = np.clip(modified, 0.0, 1.0)

        elif operation == 'smooth':
            # Gaussian blur for smoothing
            smoothed = ndimage.gaussian_filter(region, sigma=radius/4)
            # Blend based on mask and strength
            modified = region * (1 - mask * strength) + smoothed * (mask * strength)

        elif operation == 'flatten':
            # Flatten to average height in brush area
            target_height = np.mean(region)
            modified = region * (1 - mask * strength) + target_height * (mask * strength)

        else:
            raise ValueError(f"Unknown operation: {operation}")

        # Write back to result
        result[y_min:y_max, x_min:x_max] = modified

        return result

    def add_hill(self,
                x: int,
                y: int,
                radius: int,
                height: float = 0.2) -> np.ndarray:
        """
        Add a circular hill at specified location.

        Args:
            x, y: Center position
            radius: Hill radius
            height: Hill peak height (0.0-1.0)

        Returns:
            Modified heightmap

        Algorithm:
        - Use Gaussian function for natural hill shape
        - Blend with existing terrain
        """
        result = self.heightmap.copy()

        # Create hill shape (Gaussian)
        hill_mask = self._create_gaussian_brush(radius)

        # Scale to desired height
        hill_shape = hill_mask * height

        # Get region bounds
        y_min = max(0, y - radius)
        y_max = min(self.height, y + radius + 1)
        x_min = max(0, x - radius)
        x_max = min(self.width, x + radius + 1)

        # Get brush region (may be clipped)
        brush_y_min = radius - (y - y_min)
        brush_y_max = brush_y_min + (y_max - y_min)
        brush_x_min = radius - (x - x_min)
        brush_x_max = brush_x_min + (x_max - x_min)

        # Add hill to terrain
        region = result[y_min:y_max, x_min:x_max]
        hill = hill_shape[brush_y_min:brush_y_max, brush_x_min:brush_x_max]

        modified = region + hill
        modified = np.clip(modified, 0.0, 1.0)

        result[y_min:y_max, x_min:x_max] = modified

        return result

    def add_depression(self,
                      x: int,
                      y: int,
                      radius: int,
                      depth: float = 0.2) -> np.ndarray:
        """
        Add a circular depression at specified location.

        Args:
            x, y: Center position
            radius: Depression radius
            depth: Depression depth (0.0-1.0)

        Returns:
            Modified heightmap
        """
        result = self.heightmap.copy()

        # Create depression shape (inverted Gaussian)
        depression_mask = self._create_gaussian_brush(radius)
        depression_shape = depression_mask * depth

        # Get region bounds
        y_min = max(0, y - radius)
        y_max = min(self.height, y + radius + 1)
        x_min = max(0, x - radius)
        x_max = min(self.width, x + radius + 1)

        # Get brush region (may be clipped)
        brush_y_min = radius - (y - y_min)
        brush_y_max = brush_y_min + (y_max - y_min)
        brush_x_min = radius - (x - x_min)
        brush_x_max = brush_x_min + (x_max - x_min)

        # Subtract depression from terrain
        region = result[y_min:y_max, x_min:x_max]
        depression = depression_shape[brush_y_min:brush_y_max, brush_x_min:brush_x_max]

        modified = region - depression
        modified = np.clip(modified, 0.0, 1.0)

        result[y_min:y_max, x_min:x_max] = modified

        return result

    def add_ridge(self,
                 x1: int,
                 y1: int,
                 x2: int,
                 y2: int,
                 width: int,
                 height: float = 0.2) -> np.ndarray:
        """
        Add a linear ridge between two points.

        Args:
            x1, y1: Start position
            x2, y2: End position
            width: Ridge width
            height: Ridge peak height

        Returns:
            Modified heightmap
        """
        result = self.heightmap.copy()

        # Create line mask
        ridge_mask = np.zeros((self.height, self.width), dtype=np.float64)

        # Draw line with width
        length = int(np.sqrt((x2-x1)**2 + (y2-y1)**2))

        for i in range(length + 1):
            t = i / max(length, 1)
            x = int(x1 + t * (x2 - x1))
            y = int(y1 + t * (y2 - y1))

            # Add Gaussian falloff perpendicular to ridge
            for dy in range(-width, width + 1):
                for dx in range(-width, width + 1):
                    nx, ny = x + dx, y + dy
                    if 0 <= nx < self.width and 0 <= ny < self.height:
                        # Distance from ridge line
                        dist = abs(dx)  # Simplified: perpendicular distance
                        if dist < width:
                            # Gaussian falloff
                            falloff = np.exp(-(dist**2) / (2 * (width/2)**2))
                            ridge_mask[ny, nx] = max(ridge_mask[ny, nx], falloff)

        # Apply ridge to terrain
        ridge_shape = ridge_mask * height
        result = result + ridge_shape
        result = np.clip(result, 0.0, 1.0)

        return result

    def add_valley(self,
                  x1: int,
                  y1: int,
                  x2: int,
                  y2: int,
                  width: int,
                  depth: float = 0.2) -> np.ndarray:
        """
        Add a linear valley between two points.

        Args:
            x1, y1: Start position
            x2, y2: End position
            width: Valley width
            depth: Valley depth

        Returns:
            Modified heightmap
        """
        result = self.heightmap.copy()

        # Create line mask (same as ridge)
        valley_mask = np.zeros((self.height, self.width), dtype=np.float64)

        length = int(np.sqrt((x2-x1)**2 + (y2-y1)**2))

        for i in range(length + 1):
            t = i / max(length, 1)
            x = int(x1 + t * (x2 - x1))
            y = int(y1 + t * (y2 - y1))

            # Add Gaussian falloff perpendicular to valley
            for dy in range(-width, width + 1):
                for dx in range(-width, width + 1):
                    nx, ny = x + dx, y + dy
                    if 0 <= nx < self.width and 0 <= ny < self.height:
                        dist = abs(dx)
                        if dist < width:
                            falloff = np.exp(-(dist**2) / (2 * (width/2)**2))
                            valley_mask[ny, nx] = max(valley_mask[ny, nx], falloff)

        # Apply valley to terrain (subtract)
        valley_shape = valley_mask * depth
        result = result - valley_shape
        result = np.clip(result, 0.0, 1.0)

        return result

    def _create_gaussian_brush(self, radius: int) -> np.ndarray:
        """
        Create Gaussian falloff brush kernel.

        Args:
            radius: Brush radius in pixels

        Returns:
            2D array with Gaussian falloff (peak=1.0 at center)

        Why Gaussian:
        - Smooth natural falloff
        - No hard edges
        - Standard in image editing
        """
        size = radius * 2 + 1
        center = radius

        # Create coordinate grid
        y, x = np.ogrid[:size, :size]

        # Calculate distance from center
        distance = np.sqrt((x - center)**2 + (y - center)**2)

        # Gaussian falloff (sigma = radius/2 for nice falloff)
        sigma = radius / 2.0
        brush = np.exp(-(distance**2) / (2 * sigma**2))

        return brush


# Command classes for undo/redo support

class BrushCommand(Command):
    """Command for brush operations (raise, lower, smooth, flatten)."""

    def __init__(self,
                 generator,
                 x: int,
                 y: int,
                 radius: int,
                 strength: float,
                 operation: str,
                 description: str = None):
        """Initialize brush command."""
        desc = description or f"{operation.capitalize()} brush"
        super().__init__(desc)
        self.generator = generator
        self.x = x
        self.y = y
        self.radius = radius
        self.strength = strength
        self.operation = operation
        self.previous_data: Optional[np.ndarray] = None
        self.modified_data: Optional[np.ndarray] = None

    def execute(self) -> None:
        """Execute brush operation."""
        self.previous_data = self.generator.heightmap.copy()

        editor = TerrainEditor(self.generator.heightmap)
        self.modified_data = editor.apply_brush(
            self.x, self.y, self.radius, self.strength, self.operation
        )

        self.generator.heightmap = self.modified_data.copy()
        self._executed = True

    def undo(self) -> None:
        """Undo brush operation."""
        if not self._executed or self.previous_data is None:
            raise RuntimeError("Cannot undo: command not executed")

        self.generator.heightmap = self.previous_data.copy()
        self._executed = False


class AddFeatureCommand(Command):
    """Command for adding terrain features (hills, depressions, etc.)."""

    def __init__(self,
                 generator,
                 feature_type: str,
                 params: dict,
                 description: str = None):
        """
        Initialize feature command.

        Args:
            generator: HeightmapGenerator instance
            feature_type: 'hill', 'depression', 'ridge', or 'valley'
            params: Feature parameters (varies by type)
            description: Human-readable description
        """
        desc = description or f"Add {feature_type}"
        super().__init__(desc)
        self.generator = generator
        self.feature_type = feature_type
        self.params = params
        self.previous_data: Optional[np.ndarray] = None
        self.modified_data: Optional[np.ndarray] = None

    def execute(self) -> None:
        """Execute feature addition."""
        self.previous_data = self.generator.heightmap.copy()

        editor = TerrainEditor(self.generator.heightmap)

        if self.feature_type == 'hill':
            self.modified_data = editor.add_hill(**self.params)
        elif self.feature_type == 'depression':
            self.modified_data = editor.add_depression(**self.params)
        elif self.feature_type == 'ridge':
            self.modified_data = editor.add_ridge(**self.params)
        elif self.feature_type == 'valley':
            self.modified_data = editor.add_valley(**self.params)
        else:
            raise ValueError(f"Unknown feature type: {self.feature_type}")

        self.generator.heightmap = self.modified_data.copy()
        self._executed = True

    def undo(self) -> None:
        """Undo feature addition."""
        if not self._executed or self.previous_data is None:
            raise RuntimeError("Cannot undo: command not executed")

        self.generator.heightmap = self.previous_data.copy()
        self._executed = False
