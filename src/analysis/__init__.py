"""
CS2 Heightmap Generator - Analysis Module

This module provides terrain analysis tools:
- Slope calculation (steepness)
- Aspect calculation (direction of slope)
- Statistical analysis (height distribution, variance, etc.)

All analysis uses standard GIS methods.
"""

from .terrain_analyzer import TerrainAnalyzer

__all__ = ['TerrainAnalyzer']
