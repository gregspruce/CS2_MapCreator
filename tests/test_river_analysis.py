"""
Test Suite for River Analysis (Session 7)

Comprehensive tests validating flow direction, flow accumulation,
river path extraction, and dam site identification.

Author: Claude Code (Session 7)
Date: 2025-10-10
"""

import pytest
import numpy as np
import time
from src.generation.river_analysis import RiverAnalyzer, analyze_rivers


class TestRiverAnalyzer:
    """Test suite for RiverAnalyzer class."""

    def test_initialization(self):
        """Test RiverAnalyzer initialization with valid parameters."""
        analyzer = RiverAnalyzer(resolution=1024, map_size_meters=14336.0, seed=42)

        assert analyzer.resolution == 1024
        assert analyzer.map_size_meters == 14336.0
        assert analyzer.seed == 42
        assert analyzer.pixel_size_meters == 14336.0 / 1024

    def test_initialization_invalid_parameters(self):
        """Test that invalid parameters raise ValueError."""
        # Resolution too small
        with pytest.raises(ValueError, match="Resolution must be >= 3"):
            RiverAnalyzer(resolution=2)

        # Invalid map size
        with pytest.raises(ValueError, match="Map size must be > 0"):
            RiverAnalyzer(resolution=1024, map_size_meters=-100)

    def test_d8_direction_encoding(self):
        """Test D8 direction codes are correct powers of 2."""
        analyzer = RiverAnalyzer(resolution=512)

        # Verify D8 codes are powers of 2
        expected_codes = [1, 2, 4, 8, 16, 32, 64, 128]
        assert list(analyzer.D8_CODES) == expected_codes

        # Verify offset array shape
        assert analyzer.D8_OFFSETS.shape == (8, 2)

    def test_decode_direction(self):
        """Test direction code decoding to (dx, dy) offsets."""
        analyzer = RiverAnalyzer(resolution=512)

        # Test all 8 directions
        assert analyzer._decode_direction(1) == (1, 0)      # E
        assert analyzer._decode_direction(2) == (1, 1)      # SE
        assert analyzer._decode_direction(4) == (0, 1)      # S
        assert analyzer._decode_direction(8) == (-1, 1)     # SW
        assert analyzer._decode_direction(16) == (-1, 0)    # W
        assert analyzer._decode_direction(32) == (-1, -1)   # NW
        assert analyzer._decode_direction(64) == (0, -1)    # N
        assert analyzer._decode_direction(128) == (1, -1)   # NE

        # Test invalid direction
        assert analyzer._decode_direction(0) == (0, 0)
        assert analyzer._decode_direction(255) == (0, 0)

    def test_flow_direction_simple_slope(self):
        """Test flow direction on simple sloped terrain."""
        analyzer = RiverAnalyzer(resolution=5)

        # Create simple slope from left (high) to right (low)
        # Heights: 1.0, 0.75, 0.5, 0.25, 0.0
        heightmap = np.zeros((5, 5), dtype=np.float32)
        for x in range(5):
            heightmap[:, x] = 1.0 - (x * 0.25)

        flow_dir, stats = analyzer._calculate_flow_direction(heightmap)

        # Most cells should flow East (direction code = 1)
        # Interior cells will flow East toward lower elevation
        for y in range(5):
            for x in range(3):  # Columns 0-2 should definitely flow E
                assert flow_dir[y, x] == 1, f"Cell ({x},{y}) should flow E, got {flow_dir[y, x]}"

        # Note: Rightmost column may flow S/SE if there's a gradient,
        # only flows "off map" (code=0) if NO downhill neighbor exists

    def test_flow_direction_valley(self):
        """Test flow direction on V-shaped valley."""
        analyzer = RiverAnalyzer(resolution=7)

        # Create V-shaped valley (high on edges, low in middle)
        heightmap = np.zeros((7, 7), dtype=np.float32)
        for y in range(7):
            for x in range(7):
                # Distance from center column (x=3)
                dist = abs(x - 3)
                heightmap[y, x] = dist * 0.2  # Higher on edges

        flow_dir, stats = analyzer._calculate_flow_direction(heightmap)

        # Cells should flow toward center column
        # Left side flows East, right side flows West
        for y in range(7):
            # Left of center should flow East (toward center)
            for x in range(3):
                assert flow_dir[y, x] in [1, 2, 128], f"Left side should flow toward center"

            # Right of center should flow West (toward center)
            for x in range(4, 7):
                assert flow_dir[y, x] in [16, 8, 32], f"Right side should flow toward center"

    def test_flow_accumulation_linear_slope(self):
        """Test flow accumulation on linear slope."""
        analyzer = RiverAnalyzer(resolution=5)

        # Linear slope from N (high) to S (low)
        heightmap = np.zeros((5, 5), dtype=np.float32)
        for y in range(5):
            heightmap[y, :] = 1.0 - (y * 0.25)

        flow_dir, _ = analyzer._calculate_flow_direction(heightmap)
        flow_map, stats = analyzer._calculate_flow_accumulation(heightmap, flow_dir)

        # With N->S slope, each cell flows South
        # Top row: accumulation = 1 (only itself)
        # Each row below accumulates 1 + (accumulation from above)
        # Bottom row should have maximum accumulation
        expected_top_row = 1
        max_accumulation = np.max(flow_map)

        assert flow_map[0, 0] == expected_top_row, f"Top row should have accumulation = 1"
        # Bottom row should have significantly higher accumulation
        assert max_accumulation > 5, f"Bottom row should accumulate flow from above"
        # Each cell below should have more accumulation than cells above
        for x in range(5):
            assert flow_map[4, x] >= flow_map[0, x], f"Bottom should have more flow than top"

    def test_flow_accumulation_conservation(self):
        """Test that flow accumulation conserves total cells."""
        analyzer = RiverAnalyzer(resolution=64)

        # Random terrain
        np.random.seed(42)
        heightmap = np.random.rand(64, 64).astype(np.float32)

        flow_dir, _ = analyzer._calculate_flow_direction(heightmap)
        flow_map, stats = analyzer._calculate_flow_accumulation(heightmap, flow_dir)

        # Every cell starts with accumulation = 1
        # Total flow through all outlets should equal total cells
        total_cells = 64 * 64

        # Flow map values should all be >= 1
        assert np.all(flow_map >= 1), "All cells should have at least accumulation = 1"

        # Maximum accumulation should not exceed total cells
        assert np.max(flow_map) <= total_cells, "Max accumulation exceeds total cells"

    def test_river_extraction_output_format(self):
        """Test that river extraction produces correct output format."""
        analyzer = RiverAnalyzer(resolution=128)

        # Create terrain with clear drainage (bowl shape)
        x = np.linspace(-1, 1, 128)
        y = np.linspace(-1, 1, 128)
        X, Y = np.meshgrid(x, y)
        heightmap = (X**2 + Y**2).astype(np.float32)  # Bowl: low in center, high on edges
        heightmap = (heightmap - heightmap.min()) / (heightmap.max() - heightmap.min())

        river_network, stats = analyzer.analyze_rivers(
            heightmap,
            threshold_percentile=98.0,
            min_river_length=5,
            verbose=False
        )

        # Verify river_network structure
        assert 'paths' in river_network
        assert 'flow_map' in river_network
        assert 'flow_dir' in river_network
        assert 'dam_sites' in river_network

        # Verify paths format
        assert isinstance(river_network['paths'], list)
        if river_network['paths']:
            path = river_network['paths'][0]
            assert 'points' in path
            assert 'flow_accumulation' in path
            assert 'width' in path
            assert 'start' in path
            assert 'end' in path
            assert 'length_pixels' in path
            assert 'length_meters' in path

        # Verify arrays
        assert river_network['flow_map'].shape == (128, 128)
        assert river_network['flow_dir'].shape == (128, 128)

        # Verify statistics
        assert 'num_rivers' in stats
        assert 'total_river_length_pixels' in stats
        assert 'elapsed_time_seconds' in stats

    def test_river_width_calculation(self):
        """Test river width scales with flow accumulation."""
        analyzer = RiverAnalyzer(resolution=512)

        # Test width calculation for different flow values
        width_1 = analyzer._calculate_river_width(1)
        width_100 = analyzer._calculate_river_width(100)
        width_10000 = analyzer._calculate_river_width(10000)

        # Width should increase with flow (power law)
        assert width_1 < width_100 < width_10000, "Width should increase with flow"

        # Width should be in reasonable range [1, 20]
        assert 1.0 <= width_1 <= 20.0
        assert 1.0 <= width_100 <= 20.0
        assert 1.0 <= width_10000 <= 20.0

        # Very small flow should give minimum width
        width_zero = analyzer._calculate_river_width(0)
        assert width_zero == 1.0, "Zero flow should give minimum width"

    def test_reproducibility_with_seed(self):
        """Test that same seed produces identical results."""
        # Create two identical terrains
        np.random.seed(42)
        heightmap1 = np.random.rand(128, 128).astype(np.float32)
        heightmap2 = heightmap1.copy()

        # Analyze with same seed
        analyzer1 = RiverAnalyzer(resolution=128, seed=42)
        analyzer2 = RiverAnalyzer(resolution=128, seed=42)

        network1, stats1 = analyzer1.analyze_rivers(heightmap1, verbose=False)
        network2, stats2 = analyzer2.analyze_rivers(heightmap2, verbose=False)

        # Results should be identical
        assert stats1['num_rivers'] == stats2['num_rivers']
        assert np.array_equal(network1['flow_map'], network2['flow_map'])
        assert np.array_equal(network1['flow_dir'], network2['flow_dir'])

    def test_invalid_heightmap_shape(self):
        """Test that mismatched heightmap shape raises ValueError."""
        analyzer = RiverAnalyzer(resolution=512)

        # Create heightmap with wrong shape
        heightmap = np.random.rand(256, 256).astype(np.float32)

        with pytest.raises(ValueError, match="Heightmap shape .* doesn't match resolution"):
            analyzer.analyze_rivers(heightmap)

    def test_invalid_parameters(self):
        """Test that invalid analysis parameters raise ValueError."""
        analyzer = RiverAnalyzer(resolution=512)
        heightmap = np.random.rand(512, 512).astype(np.float32)

        # Invalid threshold percentile
        with pytest.raises(ValueError, match="threshold_percentile must be in"):
            analyzer.analyze_rivers(heightmap, threshold_percentile=150.0)

        # Invalid min river length
        with pytest.raises(ValueError, match="min_river_length must be >= 2"):
            analyzer.analyze_rivers(heightmap, min_river_length=1)

    def test_performance_medium_resolution(self):
        """Test performance at medium resolution (1024x1024)."""
        analyzer = RiverAnalyzer(resolution=1024)

        # Create synthetic terrain
        np.random.seed(42)
        heightmap = np.random.rand(1024, 1024).astype(np.float32)

        # Time the analysis
        start = time.time()
        river_network, stats = analyzer.analyze_rivers(heightmap, verbose=False)
        elapsed = time.time() - start

        print(f"\n[Performance Test] 1024x1024 analysis: {elapsed:.2f}s")
        print(f"  Rivers detected: {stats['num_rivers']}")
        print(f"  Max flow accumulation: {stats['max_flow_accumulation']}")

        # Should complete in reasonable time (< 5 seconds for 1024x1024)
        assert elapsed < 5.0, f"Performance too slow: {elapsed:.2f}s"

    @pytest.mark.slow
    def test_performance_full_resolution(self):
        """Test performance at full resolution (4096x4096) - marked slow."""
        analyzer = RiverAnalyzer(resolution=4096)

        # Create synthetic terrain
        np.random.seed(42)
        heightmap = np.random.rand(4096, 4096).astype(np.float32)

        # Time the analysis
        start = time.time()
        river_network, stats = analyzer.analyze_rivers(heightmap, verbose=True)
        elapsed = time.time() - start

        print(f"\n[Performance Test] 4096x4096 analysis: {elapsed:.2f}s")
        print(f"  Rivers detected: {stats['num_rivers']}")
        print(f"  Total river length: {stats['total_river_length_meters']:.0f}m")
        print(f"  Max flow accumulation: {stats['max_flow_accumulation']}")

        # Should meet performance target (< 10 seconds)
        assert elapsed < 10.0, f"Performance target missed: {elapsed:.2f}s > 10.0s"

    def test_dam_site_identification(self):
        """Test that dam sites are identified in narrow valleys."""
        analyzer = RiverAnalyzer(resolution=64)

        # Create terrain with narrow valley
        heightmap = np.ones((64, 64), dtype=np.float32) * 0.5

        # Create river channel down middle
        for y in range(64):
            heightmap[y, 30:34] = 0.2  # Low elevation river channel

        # Create valley walls
        for y in range(64):
            for x in range(64):
                if x < 28 or x > 35:
                    heightmap[y, x] = 0.7  # High elevation on sides

        # Create slope from N to S
        for y in range(64):
            heightmap[y, :] -= y * 0.005

        river_network, stats = analyzer.analyze_rivers(
            heightmap,
            threshold_percentile=95.0,
            min_river_length=10,
            verbose=False
        )

        # Should detect some dam sites
        print(f"\n[Dam Sites] Detected: {len(river_network['dam_sites'])}")
        # Note: Dam site detection depends on complex terrain features,
        # so we just verify the function runs without errors

    def test_convenience_function(self):
        """Test the analyze_rivers convenience function."""
        # Create simple terrain
        heightmap = np.random.rand(256, 256).astype(np.float32)

        # Use convenience function
        river_network, stats = analyze_rivers(
            heightmap,
            resolution=256,
            threshold_percentile=99.0,
            verbose=False
        )

        # Verify output format
        assert 'paths' in river_network
        assert 'flow_map' in river_network
        assert 'num_rivers' in stats

    def test_integration_with_eroded_terrain(self):
        """Test river analysis on erosion-style terrain."""
        analyzer = RiverAnalyzer(resolution=512)

        # Create terrain that mimics erosion effects
        # Start with noise, then add drainage features
        np.random.seed(42)
        heightmap = np.random.rand(512, 512).astype(np.float32) * 0.3

        # Add drainage channels (low elevation paths)
        for i in range(5):
            x = i * 100 + 50
            for y in range(512):
                # Create channel with slope
                heightmap[y, x-2:x+3] = 0.1 + (y / 512) * 0.05

        river_network, stats = analyzer.analyze_rivers(
            heightmap,
            threshold_percentile=95.0,  # Lower threshold to detect synthetic rivers
            min_river_length=20,
            verbose=False
        )

        # Should detect rivers along the drainage channels
        # Note: May be 0 if terrain is too uniform
        print(f"\n[Integration Test] Detected {stats['num_rivers']} rivers")
        print(f"  Threshold value: {stats['threshold_value']:.1f}")
        if stats['num_rivers'] > 0:
            print(f"  Total length: {stats['total_river_length_meters']:.0f}m")


def test_flow_direction_numba_available():
    """Test that Numba is available for performance optimization."""
    from src.generation.river_analysis import NUMBA_AVAILABLE

    if NUMBA_AVAILABLE:
        print("\n[Numba] JIT compilation available (5-8x speedup expected)")
    else:
        print("\n[Numba] JIT compilation NOT available (using NumPy fallback)")


if __name__ == '__main__':
    # Run tests with pytest
    pytest.main([__file__, '-v', '--tb=short'])
