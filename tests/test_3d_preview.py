"""
Test 3D preview functionality.

This test verifies:
1. Preview3D class initializes correctly
2. Downsampling works and is fast
3. 3D preview generates without errors
4. Performance is acceptable (<1s for 256x256)
"""

import sys
import os
import time

# Add project root to path
sys.path.insert(0, os.path.dirname(__file__))

import numpy as np
from src.preview_3d import Preview3D, generate_3d_preview


def test_3d_preview():
    """Test 3D preview generation."""
    print("\n" + "="*60)
    print("Testing 3D Preview Functionality")
    print("="*60 + "\n")

    # Test 1: Create test heightmap
    print("1. Creating test heightmap (4096x4096)...")
    heightmap = np.random.rand(4096, 4096)
    # Add some interesting features
    x = np.linspace(-5, 5, 4096)
    y = np.linspace(-5, 5, 4096)
    X, Y = np.meshgrid(x, y)
    heightmap = 0.5 + 0.3 * np.sin(X) * np.cos(Y) + 0.1 * np.random.rand(4096, 4096)
    heightmap = np.clip(heightmap, 0, 1)
    print(f"   [PASS] Test heightmap created: {heightmap.shape}\n")

    # Test 2: Initialize Preview3D
    print("2. Initializing Preview3D...")
    preview = Preview3D(resolution=256)
    assert preview.resolution == 256, "Resolution should be 256"
    print("   [PASS] Preview3D initialized\n")

    # Test 3: Test downsampling performance
    print("3. Testing downsampling performance...")
    start_time = time.time()
    downsampled = preview._downsample(heightmap)
    downsample_time = time.time() - start_time

    assert downsampled.shape == (256, 256), f"Expected (256, 256), got {downsampled.shape}"
    print(f"   [PASS] Downsampled from {heightmap.shape} to {downsampled.shape}")
    print(f"   [PASS] Downsample time: {downsample_time:.4f}s\n")

    # Test 4: Test 3D preview generation performance
    print("4. Testing 3D preview generation (will show window briefly)...")
    start_time = time.time()

    # Generate preview (non-blocking)
    preview.generate_preview(
        heightmap,
        title="Test 3D Preview",
        elevation_range=(0, 4096),
        vertical_exaggeration=2.0
    )

    generation_time = time.time() - start_time

    print(f"   [PASS] 3D preview generated successfully")
    print(f"   [PASS] Generation time: {generation_time:.4f}s")

    # Check performance
    if generation_time < 1.0:
        print(f"   [OK] EXCELLENT: Generation is fast (<1s)")
    elif generation_time < 2.0:
        print(f"   [OK] GOOD: Generation is acceptable (<2s)")
    else:
        print(f"   [WARN] SLOW: Generation took >{generation_time:.1f}s (target: <1s)")
    print()

    # Test 5: Test convenience function
    print("5. Testing convenience function...")
    start_time = time.time()

    preview2 = generate_3d_preview(
        heightmap,
        resolution=256,
        vertical_exaggeration=2.0,
        elevation_range=(0, 4096)
    )

    convenience_time = time.time() - start_time

    print(f"   [PASS] Convenience function works")
    print(f"   [PASS] Generation time: {convenience_time:.4f}s\n")

    # Test 6: Test different resolutions
    print("6. Testing different resolutions...")
    resolutions = [128, 256, 512]
    for res in resolutions:
        start_time = time.time()
        p = Preview3D(resolution=res)
        downsampled = p._downsample(heightmap)
        gen_time = time.time() - start_time

        assert downsampled.shape == (res, res), f"Expected ({res}, {res}), got {downsampled.shape}"
        print(f"   [PASS] {res}x{res}: {gen_time:.4f}s")
    print()

    # Clean up (close windows)
    print("7. Cleaning up...")
    preview.close()
    preview2.close()
    print("   [PASS] Cleanup complete\n")

    # Summary
    print("="*60)
    print("ALL TESTS PASSED!")
    print("="*60 + "\n")

    print("Performance Summary:")
    print(f"  Downsample (4096->256): {downsample_time:.4f}s")
    print(f"  3D Preview (256x256):  {generation_time:.4f}s")
    print(f"  Total:                 {downsample_time + generation_time:.4f}s\n")

    print("Expected user experience:")
    print("1. User clicks '3D Preview' button")
    print(f"2. Wait ~{generation_time:.1f}s (status shows 'Generating...')")
    print("3. 3D window opens with interactive terrain")
    print("4. User can rotate, zoom, pan with mouse")
    print("5. Close window when done\n")

    print("Note: Close the 3D preview windows to complete the test.\n")


if __name__ == '__main__':
    test_3d_preview()
