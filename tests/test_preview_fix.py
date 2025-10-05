"""
Test the downsampled preview performance fix.
"""

import numpy as np
import time
from scipy import ndimage
from src.preview_generator import PreviewGenerator
from src.noise_generator import NoiseGenerator

def test_downsampled_preview():
    """Test preview generation with downsampling."""
    print("Testing downsampled preview generation...")

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

    # Test ORIGINAL method (slow)
    print("\n1. ORIGINAL method (full 4096x4096):")
    start = time.time()
    preview_gen = PreviewGenerator(heightmap, height_scale=4096.0)
    hillshade = preview_gen.generate_hillshade(azimuth=315, altitude=45)
    colored = preview_gen.apply_colormap(colormap='terrain')
    blended = preview_gen.blend_hillshade_with_colors(
        hillshade=hillshade,
        colors=colored,
        blend_factor=0.6
    )
    original_time = time.time() - start
    print(f"   Time: {original_time:.3f}s")

    # Test NEW method (downsampled - fast)
    print("\n2. NEW method (downsampled to 512x512):")
    start = time.time()

    # Downsample
    preview_size = 512
    zoom_factor = preview_size / heightmap.shape[0]
    downsampled = ndimage.zoom(heightmap, zoom_factor, order=1)
    t1 = time.time()
    print(f"   Downsampling: {t1-start:.3f}s")

    # Generate preview on downsampled
    preview_gen = PreviewGenerator(downsampled, height_scale=4096.0)
    hillshade = preview_gen.generate_hillshade(azimuth=315, altitude=45)
    colored = preview_gen.apply_colormap(colormap='terrain')
    blended = preview_gen.blend_hillshade_with_colors(
        hillshade=hillshade,
        colors=colored,
        blend_factor=0.6
    )
    new_time = time.time() - start
    print(f"   Total: {new_time:.3f}s")

    # Results
    print("\n" + "="*50)
    print("RESULTS:")
    print(f"  Original: {original_time:.3f}s")
    print(f"  New:      {new_time:.3f}s")
    print(f"  Speedup:  {original_time/new_time:.1f}x faster")
    print(f"  Freeze:   {'YES - unusable!' if new_time > 0.5 else 'NO - smooth!'}")
    print("="*50)

if __name__ == "__main__":
    test_downsampled_preview()
