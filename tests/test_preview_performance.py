"""
Test preview generation performance.
"""

import numpy as np
import time
from src.preview_generator import PreviewGenerator
from src.noise_generator import NoiseGenerator

def test_preview_generation():
    """Test how long update_preview() takes."""
    print("Testing preview generation performance...")

    # Generate terrain
    print("Generating 4096x4096 terrain...")
    noise_gen = NoiseGenerator()
    heightmap = noise_gen.generate_perlin(
        resolution=4096,
        scale=200.0,
        octaves=6,
        persistence=0.5,
        lacunarity=2.0,
        show_progress=False
    )

    # Test preview generation (what GUI does)
    print("\nTesting full preview generation (as GUI does it)...")

    start = time.time()

    # This is what update_preview() does
    preview_gen = PreviewGenerator(heightmap, height_scale=4096.0)

    hillshade = preview_gen.generate_hillshade(azimuth=315, altitude=45)
    t1 = time.time()
    print(f"  Hillshade: {t1-start:.3f}s")

    colored = preview_gen.apply_colormap(colormap='terrain')
    t2 = time.time()
    print(f"  Colormap: {t2-t1:.3f}s")

    blended = preview_gen.blend_hillshade_with_colors(
        hillshade=hillshade,
        colors=colored,
        blend_factor=0.6
    )
    t3 = time.time()
    print(f"  Blending: {t3-t2:.3f}s")

    total = time.time() - start
    print(f"\nTotal preview generation: {total:.3f}s")

    if total > 0.5:
        print("WARNING: Preview generation takes >0.5s - this freezes GUI!")
        print("SOLUTION: Generate preview at lower resolution (e.g., 512x512)")

if __name__ == "__main__":
    test_preview_generation()
