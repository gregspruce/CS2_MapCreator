"""Quick test to verify detail amplitude scaling fix."""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.generation.pipeline import TerrainGenerationPipeline

print("Testing: Zones + Terrain + Detail (with amplitude scaling fix)")
print("=" * 80)

pipeline = TerrainGenerationPipeline(resolution=512, map_size_meters=14336.0, seed=42)

terrain, stats = pipeline.generate(
    apply_ridges=False,
    apply_erosion=False,
    apply_detail=True,  # Enable detail with new fix
    apply_rivers=False,
    verbose=True
)

buildability = stats.get('final_buildable_pct', 0.0)
mean_slope = stats.get('final_mean_slope', 0.0)

print(f"\n{'='*80}")
print(f"RESULT: Buildability={buildability:.1f}%, Mean Slope={mean_slope:.2f}%")
print(f"{'='*80}")

if buildability >= 55.0 and buildability <= 65.0:
    print("[SUCCESS] Detail fix works! Buildability within target")
elif buildability >= 50.0:
    print("[GOOD] Detail fix works! Close to target")
else:
    print(f"[FAILED] Detail still breaks terrain")
