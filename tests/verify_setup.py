"""
Verify CS2 Heightmap Generator Setup

Checks that all critical dependencies are installed correctly.
Run this after setup to ensure optimal performance.
"""

import sys

print("="*60)
print("CS2 Heightmap Generator - Setup Verification")
print("="*60)

errors = []
warnings = []

# Check Python version
print(f"\nPython version: {sys.version}")
if sys.version_info < (3, 8):
    errors.append("Python 3.8+ required")
else:
    print("[OK] Python version compatible")

# Check critical dependencies
print("\nChecking critical dependencies...")

# NumPy
try:
    import numpy as np
    print(f"[OK] NumPy {np.__version__}")
except ImportError:
    errors.append("NumPy not installed - required for array operations")

# Pillow
try:
    import PIL
    print(f"[OK] Pillow {PIL.__version__}")
except ImportError:
    errors.append("Pillow not installed - required for image export")

# FastNoiseLite (CRITICAL for performance)
try:
    from pyfastnoiselite.pyfastnoiselite import FastNoiseLite, NoiseType, FractalType
    print("[OK] pyfastnoiselite (FastNoiseLite) - FAST path available")
    print("     -> Terrain generation will be FAST (~1 second)")
except ImportError as e:
    errors.append(f"pyfastnoiselite NOT installed: {e}")
    errors.append("     -> Terrain generation will be SLOW (60-120 seconds)")
    errors.append("     -> Install with: pip install pyfastnoiselite")

# Fallback noise libraries (only needed if FastNoiseLite missing)
try:
    import perlin_noise
    print(f"[OK] perlin-noise (fallback)")
except ImportError:
    warnings.append("perlin-noise not installed (fallback only)")

try:
    import opensimplex
    print(f"[OK] opensimplex (fallback)")
except ImportError:
    warnings.append("opensimplex not installed (fallback only)")

# SciPy
try:
    import scipy
    print(f"[OK] scipy {scipy.__version__}")
except ImportError:
    warnings.append("scipy not installed - some features may be unavailable")

# tqdm (progress bars)
try:
    import tqdm
    print(f"[OK] tqdm {tqdm.__version__}")
except ImportError:
    warnings.append("tqdm not installed - no progress bars")

# Tkinter (GUI)
try:
    import tkinter
    print(f"[OK] tkinter (GUI available)")
except ImportError:
    warnings.append("tkinter not installed - GUI unavailable (CLI only)")

# Summary
print("\n" + "="*60)
print("VERIFICATION SUMMARY")
print("="*60)

if errors:
    print("\n[ERRORS] Critical issues found:")
    for err in errors:
        print(f"  - {err}")
    print("\nFix these errors before using the generator!")
    sys.exit(1)

if warnings:
    print("\n[WARNINGS] Optional issues:")
    for warn in warnings:
        print(f"  - {warn}")

if not errors and not warnings:
    print("\n[EXCELLENT] All dependencies installed correctly!")
    print("Terrain generation will be FAST (~1 second for 4096x4096)")

print("\n" + "="*60)
print("Setup verification complete!")
print("="*60)

# Performance test
if not errors:
    print("\nWould you like to run a quick performance test? (y/n): ", end="")
    try:
        response = input().strip().lower()
        if response == 'y':
            print("\nRunning performance test...")
            from src.noise_generator import NoiseGenerator
            import time

            noise_gen = NoiseGenerator(seed=42)
            start = time.time()
            terrain = noise_gen.generate_perlin(
                resolution=2048,
                scale=150.0,
                octaves=6,
                show_progress=False
            )
            elapsed = time.time() - start

            print(f"\n[RESULT] 2048x2048 generation: {elapsed:.2f} seconds")
            if elapsed < 0.5:
                print("[EXCELLENT] Performance is optimal!")
            elif elapsed < 2.0:
                print("[GOOD] Performance is acceptable")
            elif elapsed < 10.0:
                print("[WARNING] Performance is slower than expected")
            else:
                print("[ERROR] Performance is very slow - check if FastNoiseLite is installed")
    except (KeyboardInterrupt, EOFError):
        print("\nSkipping performance test.")
