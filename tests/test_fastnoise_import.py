"""
Test FastNoiseLite import and availability
"""

print("Testing FastNoiseLite import from GUI context...")

# Simulate how the GUI imports it
try:
    from pyfastnoiselite.pyfastnoiselite import FastNoiseLite, NoiseType, FractalType
    print("[OK] FastNoiseLite imported successfully")
    print(f"  NoiseType.NoiseType_Perlin: {NoiseType.NoiseType_Perlin}")
    print(f"  FractalType.FractalType_FBm: {FractalType.FractalType_FBm}")
    FASTNOISE_AVAILABLE = True
except ImportError as e:
    print(f"[FAIL] FastNoiseLite import failed: {e}")
    FASTNOISE_AVAILABLE = False

print(f"\nFASTNOISE_AVAILABLE = {FASTNOISE_AVAILABLE}")

if FASTNOISE_AVAILABLE:
    print("\nTesting actual noise generation...")
    import numpy as np

    noise = FastNoiseLite(seed=42)
    noise.noise_type = NoiseType.NoiseType_Perlin
    noise.fractal_type = FractalType.FractalType_FBm
    noise.fractal_octaves = 6
    noise.fractal_gain = 0.5
    noise.fractal_lacunarity = 2.0
    noise.frequency = 1.0 / 150.0

    print("Creating coordinate arrays...")
    x_coords = np.arange(100, dtype=np.float32)
    y_coords = np.arange(100, dtype=np.float32)
    xx, yy = np.meshgrid(x_coords, y_coords)
    coords = np.stack([xx.ravel(), yy.ravel()], axis=0)

    print(f"Coords shape: {coords.shape}")
    print("Generating noise...")

    try:
        noise_values = noise.gen_from_coords(coords)
        print(f"[OK] Generation successful! Shape: {noise_values.shape}")
        print(f"  Min: {noise_values.min():.4f}, Max: {noise_values.max():.4f}")
    except Exception as e:
        print(f"[FAIL] Generation failed: {e}")
        import traceback
        traceback.print_exc()
