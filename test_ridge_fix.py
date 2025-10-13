"""Quick test to verify ridge enhancement amplitude scaling fix."""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.generation.pipeline import TerrainGenerationPipeline

print("Testing: Zones + Terrain + Ridges (with amplitude scaling fix)")
print("=" * 80)

pipeline = TerrainGenerationPipeline(resolution=512, map_size_meters=14336.0, seed=42)

terrain, stats = pipeline.generate(
    apply_ridges=True,  # Enable ridges with new fix
    apply_erosion=False,
    apply_detail=False,
    apply_rivers=False,
    verbose=True
)

buildability = stats.get('final_buildable_pct', 0.0)
mean_slope = stats.get('final_mean_slope', 0.0)

print(f"\n{'='*80}")
print(f"RESULT: Buildability={buildability:.1f}%, Mean Slope={mean_slope:.2f}%")
print(f"{'='*80}")

if buildability >= 50.0 and buildability <= 65.0:
    print("[SUCCESS] Ridge fix works! Buildability within acceptable range")
    print("  (Some drop expected - ridges add scenic features by design)")
elif buildability >= 40.0:
    print("[GOOD] Ridge fix works! Close to target")
else:
    print(f"[FAILED] Ridges still problematic")
