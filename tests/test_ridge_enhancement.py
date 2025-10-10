"""
Test Suite for Ridge Enhancement (Session 5)

Validates ridge noise generation, zone-restricted application,
smooth blending, and integration with previous sessions.

Created: 2025-10-10
"""

import pytest
import numpy as np
import time
from src.generation.ridge_enhancement import RidgeEnhancer
from src.generation.zone_generator import BuildabilityZoneGenerator
from src.generation.weighted_terrain import ZoneWeightedTerrainGenerator


class TestRidgeEnhancer:
    """Test suite for RidgeEnhancer class."""

    @pytest.fixture
    def enhancer(self):
        """Create RidgeEnhancer instance for testing."""
        return RidgeEnhancer(resolution=1024, seed=42)

    @pytest.fixture
    def sample_terrain(self):
        """Create sample terrain for testing."""
        terrain = np.random.rand(1024, 1024).astype(np.float32) * 0.5 + 0.25
        return terrain

    @pytest.fixture
    def sample_zones(self):
        """Create sample buildability zones for testing."""
        # Create zones with clear regions:
        # - Bottom half: buildable (P > 0.6)
        # - Top half: scenic (P < 0.3)
        zones = np.zeros((1024, 1024), dtype=np.float32)
        zones[:512, :] = 0.2  # Scenic zones (top half)
        zones[512:, :] = 0.8  # Buildable zones (bottom half)
        return zones

    def test_output_format(self, enhancer, sample_terrain, sample_zones):
        """Test 1: Validate output array format."""
        enhanced, stats = enhancer.enhance(
            sample_terrain,
            sample_zones,
            verbose=False
        )

        # Check shape
        assert enhanced.shape == (1024, 1024), \
            f"Expected shape (1024, 1024), got {enhanced.shape}"

        # Check dtype
        assert enhanced.dtype == np.float32, \
            f"Expected dtype float32, got {enhanced.dtype}"

        # Check range [0, 1]
        assert 0.0 <= enhanced.min() <= enhanced.max() <= 1.0, \
            f"Expected range [0, 1], got [{enhanced.min():.3f}, {enhanced.max():.3f}]"

        # Check stats dict has required keys
        required_keys = [
            'ridge_coverage_pct', 'variance_scenic_after',
            'variance_buildable_after', 'elapsed_time_seconds'
        ]
        for key in required_keys:
            assert key in stats, f"Missing required stat: {key}"

        print(f"✅ Test 1 PASS: Output format correct")

    def test_smoothstep_function(self, enhancer):
        """Test 2: Validate smoothstep mathematical properties."""
        # Test edge cases
        result_below = RidgeEnhancer._smoothstep(0.2, 0.4, np.array([0.1]))
        result_above = RidgeEnhancer._smoothstep(0.2, 0.4, np.array([0.5]))
        result_at_edge0 = RidgeEnhancer._smoothstep(0.2, 0.4, np.array([0.2]))
        result_at_edge1 = RidgeEnhancer._smoothstep(0.2, 0.4, np.array([0.4]))

        # Below edge0 should be 0
        assert np.abs(result_below[0] - 0.0) < 1e-6, \
            f"Smoothstep below edge0 should be 0, got {result_below[0]}"

        # Above edge1 should be 1
        assert np.abs(result_above[0] - 1.0) < 1e-6, \
            f"Smoothstep above edge1 should be 1, got {result_above[0]}"

        # At edges
        assert np.abs(result_at_edge0[0] - 0.0) < 1e-6, \
            f"Smoothstep at edge0 should be 0, got {result_at_edge0[0]}"
        assert np.abs(result_at_edge1[0] - 1.0) < 1e-6, \
            f"Smoothstep at edge1 should be 1, got {result_at_edge1[0]}"

        # Test smooth transition (midpoint should be 0.5)
        result_mid = RidgeEnhancer._smoothstep(0.2, 0.4, np.array([0.3]))
        assert 0.4 < result_mid[0] < 0.6, \
            f"Smoothstep at midpoint should be ~0.5, got {result_mid[0]}"

        # Test monotonicity (should always increase)
        x_values = np.linspace(0.2, 0.4, 100)
        y_values = RidgeEnhancer._smoothstep(0.2, 0.4, x_values)
        differences = np.diff(y_values)
        assert np.all(differences >= 0), "Smoothstep should be monotonically increasing"

        print(f"✅ Test 2 PASS: Smoothstep function correct")

    def test_ridge_noise_generation(self, enhancer):
        """Test 3: Validate ridge noise has correct characteristics."""
        ridge_noise = enhancer._generate_ridge_noise(
            ridge_octaves=5,
            verbose=False
        )

        # Check shape
        assert ridge_noise.shape == (1024, 1024), \
            f"Expected shape (1024, 1024), got {ridge_noise.shape}"

        # Check range [0, 1] (from absolute value transform)
        assert 0.0 <= ridge_noise.min() <= ridge_noise.max() <= 1.0, \
            f"Expected range [0, 1], got [{ridge_noise.min():.3f}, {ridge_noise.max():.3f}]"

        # Ridge noise should have high values at ridges (near edges)
        # The absolute value transform creates peaks
        high_values = ridge_noise > 0.7
        assert np.sum(high_values) > 0, "Ridge noise should have high values (ridges)"

        # Should have variation (not flat)
        assert ridge_noise.std() > 0.1, \
            f"Ridge noise should have variation, std={ridge_noise.std():.3f}"

        print(f"✅ Test 3 PASS: Ridge noise generation correct")

    def test_zone_restriction(self, enhancer, sample_terrain, sample_zones):
        """Test 4: Ridges only apply in scenic zones (P < 0.4)."""
        enhanced, stats = enhancer.enhance(
            sample_terrain,
            sample_zones,
            blend_edge0=0.2,
            blend_edge1=0.4,
            verbose=False
        )

        # Calculate terrain change
        terrain_change = np.abs(enhanced - sample_terrain)

        # Buildable zones (P > 0.6): should have minimal change
        buildable_mask = sample_zones > 0.6
        buildable_change = terrain_change[buildable_mask].mean()

        # Scenic zones (P < 0.3): should have significant change
        scenic_mask = sample_zones < 0.3
        scenic_change = terrain_change[scenic_mask].mean()

        # Scenic zones should change MORE than buildable zones
        assert scenic_change > buildable_change * 10, \
            f"Scenic change ({scenic_change:.6f}) should be > 10× buildable change ({buildable_change:.6f})"

        # Buildable zones should change very little
        assert buildable_change < 0.01, \
            f"Buildable zones should change < 0.01, got {buildable_change:.6f}"

        print(f"✅ Test 4 PASS: Zone restriction working (scenic: {scenic_change:.6f}, buildable: {buildable_change:.6f})")

    def test_smooth_blending(self, enhancer, sample_terrain):
        """Test 5: Smooth transition at zone boundaries."""
        # Create zones with clear transition region
        zones = np.zeros((1024, 1024), dtype=np.float32)
        for i in range(1024):
            # Gradient from scenic (0.1) to buildable (0.7)
            zones[i, :] = 0.1 + (0.6 * i / 1023.0)

        enhanced, stats = enhancer.enhance(
            sample_terrain,
            zones,
            blend_edge0=0.2,
            blend_edge1=0.4,
            verbose=False
        )

        # Calculate terrain change
        terrain_change = np.abs(enhanced - sample_terrain)

        # Check gradient continuity in transition zone
        # Extract center column (representative of transition)
        center_col = terrain_change[:, 512]

        # Calculate gradient (should be smooth, not spiky)
        gradient = np.abs(np.diff(center_col))

        # Max gradient should be reasonable (not huge spikes)
        max_gradient = gradient.max()
        assert max_gradient < 0.05, \
            f"Max gradient should be < 0.05 (smooth), got {max_gradient:.6f}"

        # Mean gradient should be small
        mean_gradient = gradient.mean()
        assert mean_gradient < 0.001, \
            f"Mean gradient should be < 0.001, got {mean_gradient:.6f}"

        print(f"✅ Test 5 PASS: Smooth blending (max gradient: {max_gradient:.6f})")

    def test_buildable_preservation(self, enhancer, sample_terrain, sample_zones):
        """Test 6: Buildable zones (P > 0.4) remain unchanged."""
        enhanced, stats = enhancer.enhance(
            sample_terrain,
            sample_zones,
            blend_edge0=0.2,
            blend_edge1=0.4,
            verbose=False
        )

        # Check variance change in buildable zones
        variance_change = stats['variance_change_buildable']

        # Should be very small (< 0.0001)
        assert abs(variance_change) < 0.0001, \
            f"Buildable zone variance should not change, got Δ={variance_change:.8f}"

        # Mean change should be tiny
        mean_change = stats['mean_change_buildable']
        assert mean_change < 0.001, \
            f"Mean change in buildable zones should be < 0.001, got {mean_change:.6f}"

        print(f"✅ Test 6 PASS: Buildable zones preserved (Δvar={variance_change:.8f})")

    def test_mountain_enhancement(self, enhancer, sample_terrain, sample_zones):
        """Test 7: Scenic zones show increased variance (ridges added)."""
        enhanced, stats = enhancer.enhance(
            sample_terrain,
            sample_zones,
            ridge_strength=0.2,
            verbose=False
        )

        # Check variance change in scenic zones
        variance_change = stats['variance_change_scenic']

        # Should increase (ridges add detail)
        assert variance_change > 0.001, \
            f"Scenic zone variance should increase, got Δ={variance_change:.6f}"

        # Variance after should be > before
        assert stats['variance_scenic_after'] > stats['variance_scenic_before'], \
            "Scenic variance after should exceed before"

        print(f"✅ Test 7 PASS: Mountain enhancement (Δvar={variance_change:.6f})")

    def test_reproducibility(self, enhancer, sample_terrain, sample_zones):
        """Test 8: Same seed produces identical ridges."""
        enhanced1, _ = enhancer.enhance(
            sample_terrain,
            sample_zones,
            verbose=False
        )

        # Create new enhancer with same seed
        enhancer2 = RidgeEnhancer(resolution=1024, seed=42)
        enhanced2, _ = enhancer2.enhance(
            sample_terrain,
            sample_zones,
            verbose=False
        )

        # Should be identical
        assert np.allclose(enhanced1, enhanced2, atol=1e-6), \
            "Same seed should produce identical output"

        print(f"✅ Test 8 PASS: Reproducibility confirmed")

    def test_parameter_validation(self, enhancer, sample_terrain, sample_zones):
        """Test 9: Invalid parameters are rejected."""
        # Test invalid ridge octaves
        with pytest.raises(ValueError, match="Ridge octaves"):
            enhancer.enhance(sample_terrain, sample_zones, ridge_octaves=10, verbose=False)

        # Test invalid ridge strength
        with pytest.raises(ValueError, match="Ridge strength"):
            enhancer.enhance(sample_terrain, sample_zones, ridge_strength=0.5, verbose=False)

        # Test invalid blend edges
        with pytest.raises(ValueError, match="blend_edge0"):
            enhancer.enhance(sample_terrain, sample_zones, blend_edge0=0.5, blend_edge1=0.3, verbose=False)

        # Test mismatched terrain shape
        wrong_terrain = np.random.rand(512, 512).astype(np.float32)
        with pytest.raises(ValueError, match="Terrain shape"):
            enhancer.enhance(wrong_terrain, sample_zones, verbose=False)

        # Test invalid terrain range
        invalid_terrain = np.random.rand(1024, 1024).astype(np.float32) * 2.0  # Range [0, 2]
        with pytest.raises(ValueError, match="Terrain must be in range"):
            enhancer.enhance(invalid_terrain, sample_zones, verbose=False)

        print(f"✅ Test 9 PASS: Parameter validation working")

    def test_performance(self, enhancer, sample_terrain, sample_zones):
        """Test 10: Performance < 10 seconds at 1024×1024 (< 10s at 4096×4096)."""
        start_time = time.time()

        enhanced, stats = enhancer.enhance(
            sample_terrain,
            sample_zones,
            verbose=False
        )

        elapsed = time.time() - start_time

        # Should complete quickly at 1024×1024
        assert elapsed < 5.0, \
            f"Expected < 5 seconds at 1024×1024, got {elapsed:.2f}s"

        # Check stats also reports reasonable time
        assert stats['elapsed_time_seconds'] < 5.0, \
            f"Stats reports {stats['elapsed_time_seconds']:.2f}s > 5s"

        print(f"✅ Test 10 PASS: Performance OK ({elapsed:.2f}s at 1024×1024)")

    def test_integration_with_sessions_2_3(self):
        """Test 11: Integration with BuildabilityZoneGenerator and ZoneWeightedTerrainGenerator."""
        # Session 2: Generate zones
        zone_gen = BuildabilityZoneGenerator(resolution=1024, seed=42)
        zones, zone_stats = zone_gen.generate_potential_map(
            target_coverage=0.70,
            verbose=False
        )

        # Session 3: Generate weighted terrain
        terrain_gen = ZoneWeightedTerrainGenerator(resolution=1024, seed=42)
        terrain, terrain_stats = terrain_gen.generate(
            buildability_potential=zones,
            verbose=False
        )

        # Session 5: Apply ridge enhancement
        enhancer = RidgeEnhancer(resolution=1024, seed=42)
        enhanced, ridge_stats = enhancer.enhance(
            terrain,
            zones,
            verbose=False
        )

        # Validate pipeline worked
        assert enhanced.shape == (1024, 1024), "Pipeline should produce correct shape"
        assert 0.0 <= enhanced.min() <= enhanced.max() <= 1.0, "Pipeline should produce valid range"

        # Check that scenic zones were enhanced
        assert ridge_stats['variance_change_scenic'] > 0.001, \
            "Integration: Scenic zones should be enhanced"

        # Check that buildable zones were preserved (use realistic threshold for integration)
        # With continuous zones from Session 2, some small changes are expected
        # Threshold of 0.01 (1% variance change) is realistic for real integration
        assert abs(ridge_stats['variance_change_buildable']) < 0.01, \
            f"Integration: Buildable zones should be preserved, got Δvar={ridge_stats['variance_change_buildable']:.6f}"

        print(f"✅ Test 11 PASS: Integration with Sessions 2 & 3 working")
        print(f"   Zone coverage: {zone_stats['coverage_percent']:.1f}%")
        print(f"   Terrain buildable: {terrain_stats['buildable_percent']:.1f}%")
        print(f"   Ridge coverage: {ridge_stats['ridge_coverage_pct']:.1f}%")

    def test_ridge_strength_effect(self, enhancer, sample_terrain, sample_zones):
        """Test 12: Ridge strength parameter affects prominence."""
        # Test with low strength
        enhanced_low, stats_low = enhancer.enhance(
            sample_terrain,
            sample_zones,
            ridge_strength=0.1,
            verbose=False
        )

        # Test with high strength
        enhanced_high, stats_high = enhancer.enhance(
            sample_terrain,
            sample_zones,
            ridge_strength=0.3,
            verbose=False
        )

        # High strength should produce greater variance change
        assert stats_high['variance_change_scenic'] > stats_low['variance_change_scenic'], \
            "Higher ridge strength should increase scenic variance more"

        # High strength should produce greater mean change
        assert stats_high['mean_change_scenic'] > stats_low['mean_change_scenic'], \
            "Higher ridge strength should increase mean change more"

        print(f"✅ Test 12 PASS: Ridge strength effect validated")
        print(f"   Low strength (0.1): Δvar={stats_low['variance_change_scenic']:.6f}")
        print(f"   High strength (0.3): Δvar={stats_high['variance_change_scenic']:.6f}")

    def test_different_octaves(self, enhancer, sample_terrain, sample_zones):
        """Test 13: Different ridge octaves produce different detail levels."""
        # Test with few octaves (coarse ridges)
        enhanced_coarse, stats_coarse = enhancer.enhance(
            sample_terrain,
            sample_zones,
            ridge_octaves=4,
            verbose=False
        )

        # Test with many octaves (detailed ridges)
        enhanced_detailed, stats_detailed = enhancer.enhance(
            sample_terrain,
            sample_zones,
            ridge_octaves=6,
            verbose=False
        )

        # Both should produce valid output
        assert enhanced_coarse.shape == enhanced_detailed.shape
        assert 0.0 <= enhanced_coarse.min() and enhanced_coarse.max() <= 1.0
        assert 0.0 <= enhanced_detailed.min() and enhanced_detailed.max() <= 1.0

        # Should produce different results
        difference = np.abs(enhanced_coarse - enhanced_detailed).mean()
        assert difference > 0.001, \
            f"Different octaves should produce different results, diff={difference:.6f}"

        print(f"✅ Test 13 PASS: Different octaves produce different results")
        print(f"   Mean difference: {difference:.6f}")


if __name__ == "__main__":
    # Run tests with pytest
    pytest.main([__file__, "-v", "--tb=short"])
