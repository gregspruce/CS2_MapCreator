"""
CS2 Heightmap Generator

A comprehensive Python library for generating Cities Skylines 2 compatible heightmaps.

Main modules:
- heightmap_generator: Core heightmap functionality
- noise_generator: Procedural terrain generation
- worldmap_generator: Extended worldmap creation
- cs2_exporter: CS2 integration and export
"""

__version__ = '1.0.0'
__author__ = 'Claude Code'

from .heightmap_generator import HeightmapGenerator
from .noise_generator import NoiseGenerator, create_preset_terrain
from .worldmap_generator import WorldmapGenerator, create_worldmap_preset
from .cs2_exporter import CS2Exporter, quick_export, print_system_info

__all__ = [
    'HeightmapGenerator',
    'NoiseGenerator',
    'create_preset_terrain',
    'WorldmapGenerator',
    'create_worldmap_preset',
    'CS2Exporter',
    'quick_export',
    'print_system_info',
]
