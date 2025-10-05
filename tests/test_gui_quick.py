"""
Quick GUI test - verify terrain generation works
"""

print("Testing noise generator directly...")

from src.noise_generator import NoiseGenerator
import time

# Create generator
noise_gen = NoiseGenerator(seed=42)

print("\nGenerating 4096x4096 terrain...")
start = time.time()

terrain = noise_gen.generate_perlin(
    resolution=4096,
    scale=150.0,
    octaves=6,
    show_progress=True
)

elapsed = time.time() - start

print(f"\n✓ Generation successful!")
print(f"  Time: {elapsed:.2f}s")
print(f"  Shape: {terrain.shape}")
print(f"  Min: {terrain.min():.4f}, Max: {terrain.max():.4f}")
print("\nIf you see this, the noise generation is working correctly.")
print("The GUI issue is likely a rendering/update problem, not generation.")
