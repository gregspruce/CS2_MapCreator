"""Quick pipeline test with small resolution to verify normalization fix."""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.generation.pipeline import TerrainGenerationPipeline

print("="*70)
print("QUICK PIPELINE TEST - NORMALIZATION FIX VERIFICATION")
print("="*70)
print("\nTesting with 512x512 resolution for fast verification...")
print("Expected: ~55-65% buildable, reasonable slopes (not 600%!)\n")

# Create small pipeline
pipeline = TerrainGenerationPipeline(
    resolution=512,
    map_size_meters=14336.0,
    seed=42
)

# Run pipeline
terrain, stats = pipeline.generate(verbose=True)

# Validate results
print("\n" + "="*70)
print("VALIDATION")
print("="*70)

buildable_pct = stats['final_buildable_pct']
mean_slope = stats['final_mean_slope']
target_achieved = stats['target_achieved']

print(f"Final buildability: {buildable_pct:.1f}%")
print(f"Mean slope: {mean_slope:.2f}%")
print(f"Target achieved (55-65%): {target_achieved}")

# Check for the bug symptoms
if mean_slope > 100.0:
    print("\n[FAIL] Mean slope > 100% - normalization bug still present!")
    sys.exit(1)
elif buildable_pct < 1.0:
    print("\n[FAIL] Buildability < 1% - pipeline still broken!")
    sys.exit(1)
elif 50.0 <= buildable_pct <= 70.0:
    print("\n[PASS] Pipeline is working! Buildability in acceptable range.")
    print("Ready to test full 4096x4096 resolution.")
    sys.exit(0)
else:
    print(f"\n[WARN] Buildability {buildable_pct:.1f}% outside 50-70% range")
    print("Pipeline working but may need parameter tuning.")
    sys.exit(0)
