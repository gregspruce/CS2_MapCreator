"""
Integration test: Verify brush tools work in GUI without freezing.
"""

import numpy as np
import time
from src.heightmap_generator import HeightmapGenerator
from src.noise_generator import NoiseGenerator
from src.features.terrain_editor import BrushCommand
from src.state_manager import CommandHistory

def simulate_gui_brush_stroke():
    """Simulate what happens when user clicks with brush tool in GUI."""
    print("Simulating GUI brush stroke workflow...")

    # Setup (what GUI does on startup)
    print("\n1. Setup...")
    generator = HeightmapGenerator(resolution=4096)
    history = CommandHistory()
    noise_gen = NoiseGenerator()

    # Generate terrain (what user does first)
    print("2. Generating terrain...")
    start = time.time()
    heightmap = noise_gen.generate_perlin(
        resolution=4096,
        scale=200.0,
        octaves=6,
        persistence=0.5,
        lacunarity=2.0,
        show_progress=False
    )
    generator.heightmap = heightmap
    print(f"   Terrain generated in {time.time()-start:.3f}s")

    # User clicks with brush tool
    print("\n3. User clicks with Raise brush (radius=50, strength=0.5)...")
    start = time.time()

    # Create command
    command = BrushCommand(
        generator,
        x=2048,
        y=2048,
        radius=50,
        strength=0.5,
        operation='raise',
        description="Raise at (2048, 2048)"
    )

    # Execute command
    history.execute(command)
    cmd_time = time.time() - start
    print(f"   Command executed in {cmd_time:.3f}s")

    # Copy heightmap (what GUI does)
    heightmap = generator.heightmap.copy()

    # Update preview (what GUI does) - THIS IS THE CRITICAL PART
    print("\n4. Updating preview (with downsampling fix)...")
    start = time.time()

    # Simulate the NEW update_preview() method
    from scipy import ndimage
    from src.preview_generator import PreviewGenerator

    # Downsample
    preview_size = 512
    zoom_factor = preview_size / heightmap.shape[0]
    downsampled = ndimage.zoom(heightmap, zoom_factor, order=1)

    # Generate preview
    preview_gen = PreviewGenerator(downsampled, height_scale=4096.0)
    hillshade = preview_gen.generate_hillshade(azimuth=315, altitude=45)
    colored = preview_gen.apply_colormap(colormap='terrain')
    blended = preview_gen.blend_hillshade_with_colors(
        hillshade=hillshade,
        colors=colored,
        blend_factor=0.6
    )

    preview_time = time.time() - start
    print(f"   Preview updated in {preview_time:.3f}s")

    # Total time for brush stroke
    total_time = cmd_time + preview_time
    print(f"\n5. Total time for one brush stroke: {total_time:.3f}s")

    # Verdict
    print("\n" + "="*60)
    if total_time < 0.1:
        print("[OK] EXCELLENT: Brush feels instant (<100ms)")
    elif total_time < 0.3:
        print("[OK] GOOD: Brush feels responsive (<300ms)")
    elif total_time < 0.5:
        print("- ACCEPTABLE: Slight delay but usable (<500ms)")
    else:
        print("[X] BAD: GUI will feel frozen (>500ms)")
    print("="*60)

    # Test undo
    print("\n6. Testing undo...")
    start = time.time()
    history.undo()
    undo_time = time.time() - start
    print(f"   Undo completed in {undo_time:.3f}s")

    print("\nIntegration test complete!")

if __name__ == "__main__":
    simulate_gui_brush_stroke()
