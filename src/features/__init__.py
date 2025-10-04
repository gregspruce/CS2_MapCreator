"""
CS2 Heightmap Generator - Features Module

This module contains advanced terrain features that operate on heightmaps:
- River generation (D8 flow accumulation)
- Lake/water body detection (watershed segmentation)
- Coastal features (beaches, cliffs)

All features use the Command pattern for undo/redo support.
"""

from .river_generator import RiverGenerator, AddRiverCommand
from .water_body_generator import WaterBodyGenerator, AddLakeCommand
from .coastal_generator import CoastalGenerator, AddCoastalFeaturesCommand

__all__ = [
    'RiverGenerator',
    'AddRiverCommand',
    'WaterBodyGenerator',
    'AddLakeCommand',
    'CoastalGenerator',
    'AddCoastalFeaturesCommand',
]
