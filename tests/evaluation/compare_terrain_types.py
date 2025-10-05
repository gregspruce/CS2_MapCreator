"""
Compare All Terrain Types - Quick Evaluation

Generates all terrain types and compares their characteristics.
"""

import numpy as np
from src.noise_generator import NoiseGenerator
from src.coherent_terrain_generator_optimized import CoherentTerrainGenerator
from src.terrain_realism import TerrainRealism


def quick_stats(heightmap: np.ndarray, name: str):
    """Print quick statistics for a terrain."""
    gy, gx = np.gradient(heightmap)
    slope = np.sqrt(gx**2 + gy**2)

    buildable = np.sum(slope < 0.05) / slope.size * 100
    easy = np.sum(slope < 0.02) / slope.size * 100

    print(f"{name:12s}: Buildable={buildable:5.1f}%, Easy={easy:5.1f}%, MaxSlope={slope.max()*100:5.2f}%, StdDev={heightmap.std():.3f}")


def main():
    print("="*80)
    print("TERRAIN TYPE COMPARISON - Quick Stats")
    print("="*80)
    print("\nGenerating multiple terrain types at 512x512...\n")

    resolution = 512
    terrain_types = ['flat', 'hills', 'mountains', 'highlands', 'islands']

    for ttype in terrain_types:
        # Generate
        noise_gen = NoiseGenerator(resolution)
        base_noise = noise_gen.generate_perlin(octaves=6, persistence=0.5, lacunarity=2.0)
        coherent = CoherentTerrainGenerator.make_coherent(base_noise, terrain_type=ttype)
        terrain = TerrainRealism.make_realistic(
            coherent,
            terrain_type=ttype,
            enable_warping=True,
            enable_ridges=True,
            enable_valleys=True,
            enable_plateaus=(ttype in ['highlands', 'mesas']),
            enable_erosion=True
        )

        quick_stats(terrain, ttype.capitalize())

    print("\n" + "="*80)
    print("INTERPRETATION")
    print("="*80)
    print("\nBuildable <5%: Good for city building")
    print("Easy <2%: Ideal for residential/commercial")
    print("MaxSlope: Higher = more dramatic terrain (>8% = ridges)")
    print("StdDev: Higher = more elevation variety")
    print("\nFor CS2:")
    print("  - Want 60-80% buildable for functional city")
    print("  - Want 40%+ easy for city centers")
    print("  - Want 3-6% max slopes for visual interest")
    print("  - Want 0.15+ StdDev for variety")
    print("\n" + "="*80)


if __name__ == "__main__":
    main()
