"""
CS2 Map Terrain Generation Techniques

This module contains terrain generation techniques and algorithms
that enhance the quality, playability, and realism of generated heightmaps.

Modules:
- slope_analysis: Validates terrain slopes and generates quality metrics
- domain_warping: (integrated into noise_generator.py)

Why separate from features/:
- features/ contains user-facing terrain features (rivers, lakes, coastlines)
- techniques/ contains underlying generation algorithms and validators
- This separation provides logical organization and clear responsibilities

Note: Buildability constraints will be implemented in Stage 2 as part of
conditional octave generation during noise creation, not post-processing.
"""

__version__ = "1.0.0"
