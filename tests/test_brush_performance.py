"""
Test brush tool performance to diagnose GUI freezing.
"""

import numpy as np
import time
from src.features.terrain_editor import TerrainEditor
from src.noise_generator import NoiseGenerator

def test_brush_on_4096():
    """Test brush tool on full 4096x4096 terrain."""
    print("Testing brush tool on 4096x4096 terrain...")

    # Generate full-size terrain
    print("Generating 4096x4096 terrain...")
    noise_gen = NoiseGenerator()
    heightmap = noise_gen.generate_perlin(
        resolution=4096,
        scale=200.0,
        octaves=6,
        persistence=0.5,
        lacunarity=2.0,
        show_progress=True
    )
    print(f"Terrain generated. Shape: {heightmap.shape}")

    # Create editor
    editor = TerrainEditor(heightmap)

    # Test different radius sizes
    test_cases = [
        (50, 0.5),   # Medium brush
        (100, 0.5),  # Large brush
        (200, 0.5),  # Very large brush
    ]

    for radius, strength in test_cases:
        print(f"\nTesting radius={radius}, strength={strength}")
        print(f"  Brush area: {(2*radius+1)**2} pixels")

        start = time.time()
        result = editor.apply_brush(
            x=2048,
            y=2048,
            radius=radius,
            strength=strength,
            operation='raise'
        )
        elapsed = time.time() - start

        print(f"  Time: {elapsed:.3f}s")

        if elapsed > 1.0:
            print(f"  WARNING: Took longer than 1 second! This will freeze GUI!")

def test_gaussian_creation():
    """Test Gaussian brush creation performance."""
    print("\n\nTesting Gaussian brush creation...")

    editor = TerrainEditor(np.zeros((100, 100)))

    radii = [50, 100, 200, 500]
    for radius in radii:
        start = time.time()
        brush = editor._create_gaussian_brush(radius)
        elapsed = time.time() - start

        print(f"Radius {radius}: {elapsed:.4f}s (array size: {brush.shape})")

        if elapsed > 0.1:
            print(f"  WARNING: Gaussian creation is slow!")

if __name__ == "__main__":
    print("=== Brush Performance Diagnostics ===\n")

    try:
        test_gaussian_creation()
        test_brush_on_4096()

        print("\n\n=== Diagnosis Complete ===")

    except Exception as e:
        print(f"\nERROR: {e}")
        import traceback
        traceback.print_exc()
