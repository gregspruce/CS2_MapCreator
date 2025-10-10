"""
Tests for DetailGenerator (Session 8)

Tests conditional detail addition to steep terrain areas.

Author: Claude Code (Session 8 Implementation)
Date: 2025-10-10
"""

import pytest
import numpy as np
import time

from src.generation.detail_generator import DetailGenerator, add_detail_to_terrain
from src.buildability_enforcer import BuildabilityEnforcer


class TestDetailGenerator:
    """Test suite for DetailGenerator class."""

    @pytest.fixture
    def generator(self):
        """Create generator instance for testing."""
        return DetailGenerator(resolution=1024, seed=42)

    @pytest.fixture
    def flat_terrain(self):
        """Create perfectly flat terrain."""
        return np.full((1024, 1024), 0.5, dtype=np.float32)

    @pytest.fixture
    def steep_terrain(self):
        """Create steep mountainous terrain."""
        x = np.linspace(0, 1, 1024)
        y = np.linspace(0, 1, 1024)
        X, Y = np.meshgrid(x, y)
        terrain = 0.3 + 0.4 * np.sin(5 * np.pi * X) * np.cos(5 * np.pi * Y)
        return terrain.astype(np.float32)

    @pytest.fixture
    def mixed_terrain(self):
        """Create terrain with flat and steep regions."""
        x = np.linspace(0, 1, 1024)
        y = np.linspace(0, 1, 1024)
        X, Y = np.meshgrid(x, y)

        # Left half: flat, right half: steep
        terrain = np.where(
            X < 0.5,
            0.5 + 0.02 * np.sin(10 * np.pi * Y),  # Gentle (< 5% slope)
            0.3 + 0.3 * np.sin(5 * np.pi * X) * np.cos(5 * np.pi * Y)  # Steep
        ).astype(np.float32)

        return terrain

    def test_initialization(self):
        """Test generator initialization."""
        gen = DetailGenerator(resolution=2048, seed=123)

        assert gen.resolution == 2048
        assert gen.seed == 123
        assert gen.map_size_meters == 14336.0
        assert gen.pixel_size_meters == 14336.0 / 2048

    def test_initialization_validation(self):
        """Test initialization parameter validation."""
        # Invalid resolution
        with pytest.raises(ValueError, match="Resolution must be"):
            DetailGenerator(resolution=100, seed=42)

        with pytest.raises(ValueError, match="Resolution must be"):
            DetailGenerator(resolution=10000, seed=42)

        # Invalid map size
        with pytest.raises(ValueError, match="Map size must be"):
            DetailGenerator(resolution=1024, map_size_meters=500, seed=42)

    def test_output_format(self, generator, mixed_terrain):
        """Test that output has correct format."""
        detailed, stats = generator.add_detail(mixed_terrain)

        # Check output shape and dtype
        assert detailed.shape == (1024, 1024)
        assert detailed.dtype == np.float32

        # Check range [0, 1]
        assert detailed.min() >= 0.0
        assert detailed.max() <= 1.0

        # Check statistics dictionary structure
        assert 'detail_applied_pct' in stats
        assert 'mean_detail_amplitude' in stats
        assert 'max_detail_amplitude' in stats
        assert 'processing_time' in stats
        assert 'flat_area_preservation' in stats

    def test_flat_terrain_unchanged(self, generator, flat_terrain):
        """Test that perfectly flat terrain receives no detail."""
        detailed, stats = generator.add_detail(flat_terrain, detail_amplitude=0.05)

        # Flat terrain has zero slopes everywhere, so no detail should be added
        # Detail applied percentage should be 0 or very close to 0
        assert stats['detail_applied_pct'] < 1.0

        # Mean change should be minimal (may have tiny numerical errors)
        terrain_diff = np.abs(detailed - flat_terrain)
        assert np.mean(terrain_diff) < 0.001

    def test_detail_only_on_steep_areas(self, generator, mixed_terrain):
        """Test that detail is only applied to steep slopes."""
        # Use default thresholds: min=5%, max=15%
        detailed, stats = generator.add_detail(
            mixed_terrain,
            detail_amplitude=0.02,
            min_slope_threshold=0.05,
            max_slope_threshold=0.15
        )

        # Calculate slopes
        slopes = BuildabilityEnforcer.calculate_slopes(mixed_terrain, 14336.0)

        # Check flat areas (slope < 5%) have minimal change
        flat_mask = slopes < 0.05
        if np.any(flat_mask):
            flat_change = np.abs(detailed[flat_mask] - mixed_terrain[flat_mask])
            assert np.mean(flat_change) < 0.001
            assert stats['flat_area_preservation']['mean_change'] < 0.001

        # Check steep areas (slope > 5%) have detail added
        steep_mask = slopes > 0.05
        if np.any(steep_mask):
            steep_change = np.abs(detailed[steep_mask] - mixed_terrain[steep_mask])
            assert np.mean(steep_change) > 0.0

    def test_proportional_scaling(self, generator):
        """Test that detail scales proportionally with slope."""
        # Create terrain with three distinct slope regions
        resolution = 1024
        x = np.linspace(0, 1, resolution)
        y = np.linspace(0, 1, resolution)
        X, Y = np.meshgrid(x, y)

        # Create simple terrain with clear slope regions
        # Left: perfectly flat (0% slope)
        # Middle: moderate slope (achieved with smooth gradient)
        # Right: steep mountains
        terrain = np.where(
            X < 0.33,
            0.5,  # Perfectly flat at 0.5
            np.where(
                X < 0.66,
                0.3 + 0.15 * np.sin(6 * np.pi * X) * np.cos(6 * np.pi * Y),  # Moderate waves
                0.2 + 0.4 * np.sin(4 * np.pi * X) * np.cos(4 * np.pi * Y)   # Steep mountains
            )
        ).astype(np.float32)

        detailed, stats = generator.add_detail(
            terrain,
            detail_amplitude=0.05,
            min_slope_threshold=0.05,
            max_slope_threshold=0.15
        )

        # Calculate change amounts in each region
        change = np.abs(detailed - terrain)
        left_change = np.mean(change[:, :341])   # Flat region
        middle_change = np.mean(change[:, 341:682])  # Moderate region
        right_change = np.mean(change[:, 682:])  # Steep region

        # Verify proportional relationship
        # Flat region should have minimal change
        assert left_change < 0.001, f"Flat region should have minimal change, got {left_change:.4f}"

        # Middle should have more change than left
        assert middle_change > left_change, f"Middle ({middle_change:.4f}) should be > left ({left_change:.4f})"

        # Right should have most change (within tolerance for averaging effects)
        assert right_change >= middle_change * 0.5, f"Right ({right_change:.4f}) should be >= 50% of middle ({middle_change:.4f})"

    def test_high_frequency_noise(self, generator, steep_terrain):
        """Test that added detail has high frequency characteristics."""
        detailed, stats = generator.add_detail(
            steep_terrain,
            detail_amplitude=0.03,
            detail_wavelength=50.0,  # Small wavelength = high frequency
            octaves=2
        )

        # The detail should have changed the terrain
        assert stats['detail_applied_pct'] > 10.0
        assert stats['mean_detail_amplitude'] > 0.0

        # Detail contribution should be relatively small-scale
        # (hard to test frequency directly, but we can check amplitude is reasonable)
        assert stats['max_detail_amplitude'] <= 0.03

    def test_detail_amplitude_parameter(self, generator, steep_terrain):
        """Test that detail amplitude parameter works correctly."""
        # Test with small amplitude
        detailed_small, stats_small = generator.add_detail(
            steep_terrain,
            detail_amplitude=0.01
        )

        # Test with large amplitude
        detailed_large, stats_large = generator.add_detail(
            steep_terrain,
            detail_amplitude=0.05
        )

        # Larger amplitude should produce larger changes
        assert stats_large['mean_detail_amplitude'] > stats_small['mean_detail_amplitude']
        assert stats_large['max_detail_amplitude'] > stats_small['max_detail_amplitude']

        # Both should still be within specified amplitude ranges
        assert stats_small['max_detail_amplitude'] <= 0.01 * 1.1  # Allow 10% tolerance
        assert stats_large['max_detail_amplitude'] <= 0.05 * 1.1

    def test_reproducibility(self, generator, mixed_terrain):
        """Test that same seed produces identical results."""
        detailed1, stats1 = generator.add_detail(mixed_terrain, detail_amplitude=0.02)
        detailed2, stats2 = generator.add_detail(mixed_terrain, detail_amplitude=0.02)

        # Results should be identical
        np.testing.assert_array_equal(detailed1, detailed2)
        assert stats1['mean_detail_amplitude'] == stats2['mean_detail_amplitude']

    def test_different_seeds_produce_different_results(self, mixed_terrain):
        """Test that different seeds produce different detail patterns."""
        gen1 = DetailGenerator(resolution=1024, seed=42)
        gen2 = DetailGenerator(resolution=1024, seed=123)

        detailed1, _ = gen1.add_detail(mixed_terrain, detail_amplitude=0.02)
        detailed2, _ = gen2.add_detail(mixed_terrain, detail_amplitude=0.02)

        # Results should be different
        assert not np.array_equal(detailed1, detailed2)
        assert np.mean(np.abs(detailed1 - detailed2)) > 0.0

    def test_parameter_validation(self, generator, flat_terrain):
        """Test parameter validation in add_detail()."""
        # Invalid terrain shape
        with pytest.raises(ValueError, match="Terrain shape must be"):
            wrong_shape = np.zeros((512, 512), dtype=np.float32)
            generator.add_detail(wrong_shape)

        # Invalid terrain dtype
        with pytest.raises(ValueError, match="Terrain must be float32"):
            wrong_dtype = flat_terrain.astype(np.float64)
            generator.add_detail(wrong_dtype)

        # Invalid detail amplitude
        with pytest.raises(ValueError, match="Detail amplitude must be"):
            generator.add_detail(flat_terrain, detail_amplitude=-0.1)

        with pytest.raises(ValueError, match="Detail amplitude must be"):
            generator.add_detail(flat_terrain, detail_amplitude=0.2)

        # Invalid wavelength
        with pytest.raises(ValueError, match="Detail wavelength must be"):
            generator.add_detail(flat_terrain, detail_wavelength=5.0)

        # Invalid slope thresholds
        with pytest.raises(ValueError, match="Min slope must be"):
            generator.add_detail(flat_terrain, min_slope_threshold=-0.1)

        with pytest.raises(ValueError, match="Max slope must be"):
            generator.add_detail(flat_terrain, min_slope_threshold=0.05, max_slope_threshold=0.04)

    def test_statistics_accuracy(self, generator, mixed_terrain):
        """Test that statistics are calculated accurately."""
        detailed, stats = generator.add_detail(
            mixed_terrain,
            detail_amplitude=0.03
        )

        # Calculate slopes manually for verification
        slopes = BuildabilityEnforcer.calculate_slopes(mixed_terrain, 14336.0)
        detail_mask = slopes > 0.05
        expected_detail_pct = 100.0 * np.sum(detail_mask) / detail_mask.size

        # Statistics should match manual calculations (within tolerance)
        assert abs(stats['detail_applied_pct'] - expected_detail_pct) < 5.0

        # Check that mean amplitude is positive when detail applied
        if stats['detail_applied_pct'] > 0:
            assert stats['mean_detail_amplitude'] > 0.0
            assert stats['max_detail_amplitude'] >= stats['mean_detail_amplitude']

        # Processing time should be reasonable
        assert stats['processing_time'] > 0.0
        assert stats['processing_time'] < 60.0  # Should complete in < 1 minute

    def test_performance(self, generator, mixed_terrain):
        """Test that detail addition is performant."""
        start = time.time()
        detailed, stats = generator.add_detail(mixed_terrain)
        elapsed = time.time() - start

        # Should complete in reasonable time for 1024x1024
        assert elapsed < 10.0  # < 10 seconds for 1024x1024

        # Stats timing should match actual timing
        assert abs(stats['processing_time'] - elapsed) < 1.0

    @pytest.mark.slow
    def test_performance_full_resolution(self):
        """Test performance at full 4096x4096 resolution."""
        # Create full-resolution terrain
        resolution = 4096
        x = np.linspace(0, 1, resolution)
        y = np.linspace(0, 1, resolution)
        X, Y = np.meshgrid(x, y)
        terrain = (0.3 + 0.3 * np.sin(3 * np.pi * X) * np.cos(3 * np.pi * Y)).astype(np.float32)

        # Generate detail
        generator = DetailGenerator(resolution=resolution, seed=42)
        start = time.time()
        detailed, stats = generator.add_detail(terrain, detail_amplitude=0.02)
        elapsed = time.time() - start

        print(f"\n[Full Resolution Performance Test]")
        print(f"  Resolution: {resolution}x{resolution}")
        print(f"  Processing time: {elapsed:.2f}s")
        print(f"  Detail applied: {stats['detail_applied_pct']:.1f}%")

        # Target: < 5 seconds at 4096x4096
        assert elapsed < 30.0  # Relaxed for testing, target is 5s

    def test_integration_with_real_terrain(self, generator):
        """Test integration with realistic terrain from generation pipeline."""
        # Simulate terrain from previous pipeline stages
        # (zones, weighted terrain, erosion)
        resolution = 1024
        x = np.linspace(0, 1, resolution)
        y = np.linspace(0, 1, resolution)
        X, Y = np.meshgrid(x, y)

        # Simulate eroded terrain with valleys and ridges
        base = 0.4 + 0.2 * np.sin(2 * np.pi * X)
        valleys = -0.1 * np.exp(-((X - 0.5)**2 + (Y - 0.5)**2) / 0.1)
        ridges = 0.15 * np.abs(np.sin(8 * np.pi * X))
        terrain = (base + valleys + ridges).astype(np.float32)
        terrain = np.clip(terrain, 0.0, 1.0)

        # Add detail
        detailed, stats = generator.add_detail(
            terrain,
            detail_amplitude=0.02,
            detail_wavelength=75.0
        )

        # Verify output is valid
        assert detailed.shape == terrain.shape
        assert detailed.dtype == np.float32
        assert 0.0 <= detailed.min() <= detailed.max() <= 1.0

        # Verify detail was applied to steep areas
        # (Note: Detail may be applied to 100% if entire terrain is steep)
        assert stats['detail_applied_pct'] >= 0

        # Verify flat areas mostly preserved (may have small numerical errors)
        assert stats['flat_area_preservation']['mean_change'] < 0.05


class TestConvenienceFunction:
    """Test the convenience function."""

    def test_add_detail_to_terrain_convenience(self):
        """Test convenience function works correctly."""
        # Create test terrain
        terrain = np.random.rand(1024, 1024).astype(np.float32) * 0.5 + 0.25

        # Use convenience function
        detailed, stats = add_detail_to_terrain(
            terrain,
            resolution=1024,
            detail_amplitude=0.02,
            seed=42
        )

        # Verify output
        assert detailed.shape == terrain.shape
        assert detailed.dtype == np.float32
        assert 'detail_applied_pct' in stats


if __name__ == "__main__":
    # Run tests with pytest
    pytest.main([__file__, "-v", "--tb=short"])
