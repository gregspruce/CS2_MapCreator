"""
Quick test for elevation legend feature
"""

import numpy as np
from src.noise_generator import NoiseGenerator
from src.preview_generator import PreviewGenerator
from PIL import Image

print("Testing elevation legend rendering...")

# Generate small test terrain
print("\n1. Generating test terrain (512x512)...")
noise_gen = NoiseGenerator(seed=42)
terrain = noise_gen.generate_perlin(
    resolution=512,
    scale=100.0,
    octaves=6,
    show_progress=False
)

# Create preview with hillshade and colors
print("2. Creating hillshade preview...")
preview_gen = PreviewGenerator(terrain, height_scale=4096.0)

hillshade = preview_gen.generate_hillshade(azimuth=315, altitude=45)
colored = preview_gen.apply_colormap(colormap='terrain')
blended = preview_gen.blend_hillshade_with_colors(
    hillshade=hillshade,
    colors=colored,
    blend_factor=0.6
)

# Add legend
print("3. Adding elevation legend...")
with_legend = preview_gen.draw_legend_with_labels(
    preview_image=blended,
    colormap='terrain',
    position='right',
    height_scale_meters=4096.0
)

# Save result
output_path = 'output/test_legend_preview.png'
print(f"4. Saving preview to {output_path}...")

import os
os.makedirs('output', exist_ok=True)

img = Image.fromarray(with_legend)
img.save(output_path)

print(f"\n[OK] Legend test complete!")
print(f"Check {output_path} to see the elevation legend.")
print("\nLegend should show:")
print("  - Color gradient bar (green -> brown -> white)")
print("  - Elevation labels (4.1km, 3.1km, 2.0km, 1.0km, 0m)")
print("  - 'Elevation' title at top")
print("  - Semi-transparent white background")
