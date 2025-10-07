"""
Test domain warping at different amplitudes to understand the relationship
between amplitude and slope steepness.

Hypothesis: Maybe the issue is that domain_warp_amp should be MUCH smaller,
not 40-80 as suggested in the evidence document.
"""

import numpy as np
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.noise_generator import NoiseGenerator
from src.buildability_enforcer import BuildabilityEnforcer


def test_amplitude(resolution, scale, octaves, persistence, amp, label):
    """Test a specific domain warp amplitude."""
    gen = NoiseGenerator(seed=42)

    heightmap = gen.generate_perlin(
        resolution=resolution,
        scale=scale,
        octaves=octaves,
        persistence=persistence,
        lacunarity=2.0,
        show_progress=False,
        domain_warp_amp=amp,
        recursive_warp=False  # Test WITHOUT recursive first
    )

    stats = BuildabilityEnforcer.analyze_buildability(heightmap)
    print(f"{label:40s}: build={stats['excellent_buildable_pct']:5.1f}%, "
          f"mean={stats['mean_slope']:6.1f}%, p90={stats['p90_slope']:6.1f}%")
    return stats


print("\n" + "="*80)
print("DOMAIN WARP AMPLITUDE TESTING")
print("="*80)
print("\nTesting relationship between domain_warp_amp and terrain slopes")
print("Base config: 1024 resolution, scale=100, octaves=8, persistence=0.5")
print("Testing WITHOUT recursive warping first")
print("="*80)

resolution = 1024
scale = 100
octaves = 8
persistence = 0.5

print("\n[TEST 1] Very small amplitudes (maybe evidence doc is in different units?):")
print("-"*80)
test_amplitude(resolution, scale, octaves, persistence, 0.0, "No warping")
test_amplitude(resolution, scale, octaves, persistence, 1.0, "Amplitude 1.0")
test_amplitude(resolution, scale, octaves, persistence, 5.0, "Amplitude 5.0")
test_amplitude(resolution, scale, octaves, persistence, 10.0, "Amplitude 10.0")
test_amplitude(resolution, scale, octaves, persistence, 20.0, "Amplitude 20.0")

print("\n[TEST 2] Evidence document range (40-80):")
print("-"*80)
test_amplitude(resolution, scale, octaves, persistence, 40.0, "Amplitude 40.0 [evidence min]")
test_amplitude(resolution, scale, octaves, persistence, 60.0, "Amplitude 60.0 [current]")
test_amplitude(resolution, scale, octaves, persistence, 80.0, "Amplitude 80.0 [evidence max]")

print("\n[TEST 3] Testing on SMOOTHER base terrain (octaves=2, persistence=0.3):")
print("-"*80)
octaves_smooth = 2
persistence_smooth = 0.3
test_amplitude(resolution, scale, octaves_smooth, persistence_smooth, 0.0, "Smooth base + No warp")
test_amplitude(resolution, scale, octaves_smooth, persistence_smooth, 5.0, "Smooth base + Amp 5.0")
test_amplitude(resolution, scale, octaves_smooth, persistence_smooth, 10.0, "Smooth base + Amp 10.0")
test_amplitude(resolution, scale, octaves_smooth, persistence_smooth, 20.0, "Smooth base + Amp 20.0")
test_amplitude(resolution, scale, octaves_smooth, persistence_smooth, 40.0, "Smooth base + Amp 40.0")

print("\n[TEST 4] Testing with LARGER scale (maybe amp needs to scale with scale?):")
print("-"*80)
scale_large = 1000
test_amplitude(resolution, scale_large, octaves, persistence, 0.0, "Scale=1000 + No warp")
test_amplitude(resolution, scale_large, octaves, persistence, 5.0, "Scale=1000 + Amp 5.0")
test_amplitude(resolution, scale_large, octaves, persistence, 20.0, "Scale=1000 + Amp 20.0")
test_amplitude(resolution, scale_large, octaves, persistence, 60.0, "Scale=1000 + Amp 60.0")

print("\n" + "="*80)
print("CONCLUSION")
print("="*80)
print("Finding domain_warp_amp values that don't destroy buildability")
print("="*80)
