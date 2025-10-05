"""
Test to understand FFT vs scipy gaussian filter differences.
"""

import numpy as np
from scipy.ndimage import gaussian_filter
from src.coherent_terrain_generator_optimized import CoherentTerrainGenerator


def compare_methods(resolution=1024, sigma=400):
    """Compare FFT and scipy gaussian filtering."""
    print(f"Resolution: {resolution}, Sigma: {sigma}")

    np.random.seed(42)
    data = np.random.rand(resolution, resolution)

    # Scipy method
    result_scipy = gaussian_filter(data, sigma=sigma)

    # FFT method
    result_fft = CoherentTerrainGenerator._fft_gaussian_filter(data, sigma)

    # Normalize both
    scipy_norm = (result_scipy - result_scipy.min()) / (result_scipy.max() - result_scipy.min())
    fft_norm = (result_fft - result_fft.min()) / (result_fft.max() - result_fft.min())

    # Compare
    mae_raw = np.mean(np.abs(result_scipy - result_fft))
    mae_norm = np.mean(np.abs(scipy_norm - fft_norm))

    print(f"MAE (raw): {mae_raw:.8f}")
    print(f"MAE (normalized): {mae_norm:.8f}")
    print(f"Scipy range: [{result_scipy.min():.6f}, {result_scipy.max():.6f}]")
    print(f"FFT range: [{result_fft.min():.6f}, {result_fft.max():.6f}]")

    # Check different statistics
    print(f"Scipy mean: {result_scipy.mean():.6f}, std: {result_scipy.std():.6f}")
    print(f"FFT mean: {result_fft.mean():.6f}, std: {result_fft.std():.6f}")


# Test at different resolutions and sigmas
print("="*70)
print("FFT vs Scipy Gaussian Filter Comparison")
print("="*70)

print("\nTest 1: Medium sigma, medium resolution")
compare_methods(resolution=1024, sigma=400)

print("\nTest 2: Large sigma, large resolution (4096 base_scale)")
compare_methods(resolution=4096, sigma=1638)

print("\nTest 3: Medium sigma, large resolution (4096 mask)")
compare_methods(resolution=4096, sigma=205)
