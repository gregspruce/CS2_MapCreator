"""
Test downsampling quality at different factors.
"""

import numpy as np
import time
from scipy.ndimage import gaussian_filter, zoom


def test_downsample_factors(resolution=4096, sigma=1638):
    """Test different downsample factors."""
    print(f"Testing downsample quality: resolution={resolution}, sigma={sigma}")
    print("="*70)

    np.random.seed(42)
    data = np.random.rand(resolution, resolution)

    # Ground truth (slow)
    print("Computing ground truth (scipy)...")
    start = time.time()
    truth = gaussian_filter(data, sigma=sigma)
    time_truth = time.time() - start
    print(f"  Time: {time_truth:.2f}s\n")

    # Test different downsample factors
    for factor in [2, 4, 8]:
        print(f"Downsample factor: {factor}")

        start = time.time()
        # Downsample
        small = zoom(data, 1.0/factor, order=1)
        # Blur
        blurred_small = gaussian_filter(small, sigma=sigma/factor)
        # Upsample
        result = zoom(blurred_small, factor, order=1)
        elapsed = time.time() - start

        # Compare
        mae = np.mean(np.abs(truth - result))

        # Normalize for visual comparison
        truth_norm = (truth - truth.min()) / (truth.max() - truth.min())
        result_norm = (result - result.min()) / (result.max() - result.min())
        mae_norm = np.mean(np.abs(truth_norm - result_norm))

        speedup = time_truth / elapsed

        print(f"  Time: {elapsed:.2f}s ({speedup:.2f}x speedup)")
        print(f"  MAE (raw): {mae:.8f}")
        print(f"  MAE (normalized): {mae_norm:.8f}")
        print()


test_downsample_factors(resolution=4096, sigma=1638)
test_downsample_factors(resolution=4096, sigma=205)
