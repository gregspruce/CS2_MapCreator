"""
Test Terrain Quality - Compare Generated vs Example

This script generates terrain with current system and compares against
the user-provided example to identify spikes, jaggedness, and quality issues.
"""

import numpy as np
from PIL import Image
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from src.noise_generator import NoiseGenerator
from src.buildability_enforcer import BuildabilityEnforcer

def analyze_gradients(heightmap, name="Heightmap"):
    """Analyze local elevation changes (spikes/jaggedness indicator)"""
    # Calculate gradients (elevation change between adjacent pixels)
    dy, dx = np.gradient(heightmap)
    gradient_magnitude = np.sqrt(dx**2 + dy**2)

    # Statistics
    print(f"\n=== {name} Analysis ===")
    print(f"Shape: {heightmap.shape}")
    print(f"Range: {heightmap.min():.1f} to {heightmap.max():.1f}")
    print(f"Mean: {heightmap.mean():.1f}")
    print(f"Std: {heightmap.std():.1f}")

    print(f"\n--- Gradient Analysis (elevation change) ---")
    print(f"Mean gradient: {gradient_magnitude.mean():.6f}")
    print(f"Std gradient: {gradient_magnitude.std():.6f}")
    print(f"Max gradient: {gradient_magnitude.max():.6f}")
    print(f"90th percentile: {np.percentile(gradient_magnitude, 90):.6f}")
    print(f"99th percentile: {np.percentile(gradient_magnitude, 99):.6f}")

    # Spike detection: areas with >10× mean gradient
    spike_threshold = gradient_magnitude.mean() * 10
    spikes = gradient_magnitude > spike_threshold
    spike_count = np.sum(spikes)
    spike_pct = (spike_count / gradient_magnitude.size) * 100
    print(f"\n--- Spike Detection (>10× mean gradient) ---")
    print(f"Spike threshold: {spike_threshold:.6f}")
    print(f"Spike pixels: {spike_count:,} ({spike_pct:.2f}%)")

    # Slope analysis (CS2 buildability)
    slopes = BuildabilityEnforcer.calculate_slopes(heightmap, map_size_meters=14336.0)
    buildable_pct = (np.sum(slopes <= 5.0) / slopes.size) * 100

    print(f"\n--- CS2 Buildability ---")
    print(f"Buildable (0-5% slope): {buildable_pct:.1f}%")
    print(f"Mean slope: {slopes.mean():.2f}%")
    print(f"Max slope: {slopes.max():.2f}%")

    return gradient_magnitude, slopes

def main():
    print("=" * 70)
    print("TERRAIN QUALITY COMPARISON")
    print("=" * 70)

    # 1. Load example heightmap
    print("\n[1/3] Loading example heightmap (user-created, known-good)...")
    example_img = Image.open('examples/examplemaps/example_height.png')
    example_data = np.array(example_img, dtype=np.float64)

    # Normalize to 0-1 for comparison
    example_norm = (example_data - example_data.min()) / (example_data.max() - example_data.min())

    example_grad, example_slopes = analyze_gradients(example_norm, "EXAMPLE (User-Created)")

    # 2. Generate terrain with buildability ENABLED (current system)
    print("\n[2/3] Generating terrain with buildability constraints...")
    noise_gen = NoiseGenerator(seed=42)

    # Generate gradient control map
    print("  - Generating gradient control map...")
    control_map = noise_gen.generate_buildability_control_map(
        resolution=4096,
        target_percent=70.0,  # 70% for 50% final
        seed=42,
        smoothing_radius=40
    )
    control_map = (control_map - control_map.min()) / (control_map.max() - control_map.min())

    # Generate 3 layers
    print("  - Generating buildable layer (octaves=2)...")
    layer_buildable = noise_gen.generate_perlin(
        resolution=4096,
        scale=500 * (4096 / 512),
        octaves=2,
        persistence=0.3,
        lacunarity=2.0,
        show_progress=False,
        domain_warp_amp=0.0,
        recursive_warp=False
    )

    print("  - Generating moderate layer (octaves=5)...")
    layer_moderate = noise_gen.generate_perlin(
        resolution=4096,
        scale=200,
        octaves=5,
        persistence=0.4,
        lacunarity=2.0,
        show_progress=False,
        domain_warp_amp=60.0,
        recursive_warp=True,
        recursive_warp_strength=0.5
    )

    print("  - Generating scenic layer (octaves=7)...")
    layer_scenic = noise_gen.generate_perlin(
        resolution=4096,
        scale=100,
        octaves=7,
        persistence=0.5,
        lacunarity=2.0,
        show_progress=False,
        domain_warp_amp=60.0,
        recursive_warp=True,
        recursive_warp_strength=1.0
    )

    # Blend with gradient control map
    print("  - Blending layers with gradient control...")
    control_squared = control_map ** 2
    control_inv = 1.0 - control_map
    control_inv_squared = control_inv ** 2

    generated = (layer_buildable * control_squared +
                layer_moderate * 2 * control_map * control_inv +
                layer_scenic * control_inv_squared)

    # Normalize
    generated = (generated - generated.min()) / (generated.max() - generated.min())

    # Apply buildability enforcement
    print("  - Applying buildability enforcement...")
    control_mask = (control_map >= 0.5).astype(np.float64)
    generated, stats = BuildabilityEnforcer.enforce_buildability_constraint(
        heightmap=generated,
        buildable_mask=control_mask,
        target_pct=50.0,
        max_iterations=20,
        sigma=64.0,
        tolerance=5.0,
        verbose=False
    )

    generated_grad, generated_slopes = analyze_gradients(generated, "GENERATED (Current System)")

    # 3. Comparison
    print("\n[3/3] COMPARISON ANALYSIS")
    print("=" * 70)

    grad_ratio = generated_grad.mean() / example_grad.mean()
    spike_ratio = generated_grad.max() / example_grad.max()

    print(f"\nGradient Comparison:")
    print(f"  Mean gradient ratio (generated/example): {grad_ratio:.2f}×")
    print(f"  Max gradient ratio (generated/example): {spike_ratio:.2f}×")

    if grad_ratio > 1.5:
        print(f"  WARNING: Generated terrain has {grad_ratio:.1f}x more elevation changes")
    if spike_ratio > 2.0:
        print(f"  WARNING: Generated terrain has {spike_ratio:.1f}x larger spikes")

    # Save comparison visualizations
    print("\n[SAVING] Exporting visualizations...")
    output_dir = Path('output')
    output_dir.mkdir(exist_ok=True)

    # Save generated terrain
    generated_img = Image.fromarray((generated * 65535).astype(np.uint16))
    generated_img.save(output_dir / 'test_generated_buildability.png')
    print(f"  - Saved: output/test_generated_buildability.png")

    # Save gradient magnitude maps for visual comparison
    example_grad_vis = (example_grad / example_grad.max() * 255).astype(np.uint8)
    generated_grad_vis = (generated_grad / generated_grad.max() * 255).astype(np.uint8)

    Image.fromarray(example_grad_vis).save(output_dir / 'test_example_gradients.png')
    Image.fromarray(generated_grad_vis).save(output_dir / 'test_generated_gradients.png')
    print(f"  - Saved: output/test_example_gradients.png")
    print(f"  - Saved: output/test_generated_gradients.png")

    print("\n" + "=" * 70)
    print("ANALYSIS COMPLETE")
    print("=" * 70)
    print("\nReview the gradient visualization images to see spikes/jaggedness.")
    print("Brighter areas = larger elevation changes (potential spikes/holes)")

if __name__ == "__main__":
    main()
