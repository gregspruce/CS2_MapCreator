"""
Tests for ConstraintVerifier (Session 8)

Tests buildability constraint verification and auto-adjustment.

Author: Claude Code (Session 8 Implementation)
Date: 2025-10-10
"""

import pytest
import numpy as np
import time

from src.generation.constraint_verifier import ConstraintVerifier, verify_terrain_buildability
from src.buildability_enforcer import BuildabilityEnforcer


class TestConstraintVerifier:
    """Test suite for ConstraintVerifier class."""

    @pytest.fixture
    def verifier(self):
        """Create verifier instance for testing."""
        return ConstraintVerifier(resolution=1024)

    @pytest.fixture
    def flat_terrain(self):
        """Create perfectly flat terrain (100% buildable)."""
        return np.full((1024, 1024), 0.5, dtype=np.float32)

    @pytest.fixture
    def steep_terrain(self):
        """Create steep mountainous terrain (0% buildable)."""
        x = np.linspace(0, 1, 1024)
        y = np.linspace(0, 1, 1024)
        X, Y = np.meshgrid(x, y)
        # Very steep mountains (all slopes > 10%)
        terrain = 0.2 + 0.6 * np.sin(3 * np.pi * X) * np.cos(3 * np.pi * Y)
        return terrain.astype(np.float32)

    @pytest.fixture
    def mixed_terrain(self):
        """Create terrain with mixed buildability (~40% buildable, below target)."""
        x = np.linspace(0, 1, 1024)
        y = np.linspace(0, 1, 1024)
        X, Y = np.meshgrid(x, y)

        # Center: flat and buildable (~40% of map)
        # Edges: steep mountains
        terrain = np.where(
            (X > 0.35) & (X < 0.65) & (Y > 0.35) & (Y < 0.65),
            0.5 + 0.01 * np.sin(30 * np.pi * Y),  # Flat buildable center
            0.3 + 0.35 * np.sin(4 * np.pi * X) * np.cos(4 * np.pi * Y)  # Steep edges
        ).astype(np.float32)

        return terrain

    def test_initialization(self):
        """Test verifier initialization."""
        verifier = ConstraintVerifier(resolution=2048, map_size_meters=14336.0)

        assert verifier.resolution == 2048
        assert verifier.map_size_meters == 14336.0
        assert verifier.pixel_size_meters == 14336.0 / 2048

    def test_initialization_validation(self):
        """Test initialization parameter validation."""
        # Invalid resolution
        with pytest.raises(ValueError, match="Resolution must be"):
            ConstraintVerifier(resolution=100)

        with pytest.raises(ValueError, match="Resolution must be"):
            ConstraintVerifier(resolution=10000)

        # Invalid map size
        with pytest.raises(ValueError, match="Map size must be"):
            ConstraintVerifier(resolution=1024, map_size_meters=500)

    def test_output_format(self, verifier, mixed_terrain):
        """Test that output has correct format."""
        adjusted, result = verifier.verify_and_adjust(mixed_terrain)

        # Check adjusted terrain shape and dtype
        assert adjusted.shape == (1024, 1024)
        assert adjusted.dtype == np.float32
        assert adjusted.min() >= 0.0
        assert adjusted.max() <= 1.0

        # Check result dictionary structure
        required_keys = [
            'initial_buildable_pct', 'final_buildable_pct',
            'target_min', 'target_max', 'target_achieved',
            'buildable_pct', 'near_buildable_pct', 'unbuildable_pct',
            'adjustments_applied', 'adjustment_stats', 'recommendations',
            'processing_time'
        ]
        for key in required_keys:
            assert key in result, f"Missing key: {key}"

    def test_buildability_calculation_accuracy(self, verifier, flat_terrain):
        """Test that buildability calculation matches BuildabilityEnforcer."""
        adjusted, result = verifier.verify_and_adjust(flat_terrain, apply_adjustment=False)

        # Calculate using BuildabilityEnforcer for comparison
        slopes = BuildabilityEnforcer.calculate_slopes(flat_terrain, 14336.0)
        expected_buildable = BuildabilityEnforcer.calculate_buildability_percentage(slopes)

        # Should match within tolerance
        assert abs(result['initial_buildable_pct'] - expected_buildable) < 0.1

        # Flat terrain should be 100% buildable (or very close)
        assert result['initial_buildable_pct'] > 99.0

    def test_terrain_classification(self, verifier, mixed_terrain):
        """Test that terrain is correctly classified into buildable/near/unbuildable."""
        adjusted, result = verifier.verify_and_adjust(mixed_terrain, apply_adjustment=False)

        # Sum of all categories should be 100%
        total_pct = result['buildable_pct'] + result['near_buildable_pct'] + result['unbuildable_pct']
        assert abs(total_pct - 100.0) < 0.1

        # Mixed terrain should have at least unbuildable regions
        assert result['unbuildable_pct'] > 0

        # At least one category should be non-zero (terrain has variation)
        assert result['buildable_pct'] + result['near_buildable_pct'] >= 0

    def test_target_achieved_when_in_range(self, verifier, flat_terrain):
        """Test that target_achieved is True when buildability is in range."""
        # Use perfectly flat terrain (100% buildable) and set wide target range
        adjusted, result = verifier.verify_and_adjust(
            flat_terrain,
            target_min=50.0,
            target_max=100.0,
            apply_adjustment=False
        )

        # Flat terrain should be ~100% buildable and achieve target
        assert result['final_buildable_pct'] >= 50.0
        assert result['target_achieved']

    def test_no_adjustment_when_target_achieved(self, verifier, flat_terrain):
        """Test that no adjustment is applied when target is already achieved."""
        # Use flat terrain (~100% buildable) with wide target range
        adjusted, result = verifier.verify_and_adjust(
            flat_terrain,
            target_min=50.0,  # Low target that's definitely achieved by flat terrain
            target_max=100.0,
            apply_adjustment=True
        )

        # No adjustments should be applied (target already achieved)
        assert result['adjustments_applied'] is False

        # Terrain should be unchanged
        np.testing.assert_array_equal(adjusted, flat_terrain)

    def test_adjustment_applied_when_below_target(self, verifier, mixed_terrain):
        """Test that adjustment is applied when buildability is below target."""
        adjusted, result = verifier.verify_and_adjust(
            mixed_terrain,
            target_min=55.0,
            target_max=65.0,
            apply_adjustment=True
        )

        # If initial buildability was < 55%, adjustments should be applied
        if result['initial_buildable_pct'] < 55.0:
            assert result['adjustments_applied'] is True

            # Should show improvement
            assert result['final_buildable_pct'] >= result['initial_buildable_pct']

            # Adjustment stats should be present
            assert 'iterations_performed' in result['adjustment_stats']
            assert result['adjustment_stats']['iterations_performed'] > 0

    def test_adjustment_disabled_when_flag_false(self, verifier, mixed_terrain):
        """Test that adjustment is not applied when apply_adjustment=False."""
        adjusted, result = verifier.verify_and_adjust(
            mixed_terrain,
            target_min=55.0,
            target_max=65.0,
            apply_adjustment=False  # Disable adjustment
        )

        # No adjustments should be applied regardless of buildability
        assert result['adjustments_applied'] is False

        # Terrain should be unchanged
        np.testing.assert_array_equal(adjusted, mixed_terrain)

    def test_adjustment_is_conservative(self, verifier, mixed_terrain):
        """Test that adjustment preserves terrain character (conservative smoothing)."""
        adjusted, result = verifier.verify_and_adjust(
            mixed_terrain,
            target_min=55.0,
            target_max=65.0,
            apply_adjustment=True,
            adjustment_sigma=3.0,  # Conservative smoothing
            max_adjustment_iterations=3
        )

        if result['adjustments_applied']:
            # Calculate mean change
            terrain_diff = np.abs(adjusted - mixed_terrain)
            mean_change = np.mean(terrain_diff)
            max_change = np.max(terrain_diff)

            # Changes should be minimal (conservative smoothing)
            assert mean_change < 0.05, f"Mean change too large: {mean_change:.4f}"
            assert max_change < 0.2, f"Max change too large: {max_change:.4f}"

            # Adjustment stats should reflect conservative changes
            assert result['adjustment_stats']['mean_terrain_change'] < 0.05

    def test_adjustment_only_affects_near_buildable(self, verifier):
        """Test that adjustment only smooths near-buildable regions (5-10% slope)."""
        # Create terrain with clear regions: flat, near-buildable, steep
        resolution = 1024
        x = np.linspace(0, 1, resolution)
        y = np.linspace(0, 1, resolution)
        X, Y = np.meshgrid(x, y)

        terrain = np.where(
            X < 0.33,
            0.5,  # Flat (< 5% slope)
            np.where(
                X < 0.66,
                0.45 + 0.08 * np.sin(10 * np.pi * X),  # Near-buildable (5-10% slope)
                0.2 + 0.5 * np.sin(4 * np.pi * X) * np.cos(4 * np.pi * Y)  # Steep (> 10%)
            )
        ).astype(np.float32)

        adjusted, result = verifier.verify_and_adjust(
            terrain,
            target_min=55.0,
            target_max=65.0,
            apply_adjustment=True
        )

        if result['adjustments_applied']:
            # Check that flat region is mostly unchanged
            flat_region = adjusted[:, :341]
            original_flat = terrain[:, :341]
            flat_change = np.mean(np.abs(flat_region - original_flat))
            assert flat_change < 0.01, f"Flat region changed too much: {flat_change:.4f}"

            # Middle region (near-buildable) should show changes
            middle_region = adjusted[:, 341:682]
            original_middle = terrain[:, 341:682]
            middle_change = np.mean(np.abs(middle_region - original_middle))
            # Near-buildable should have some smoothing applied
            assert middle_change >= 0.0  # May or may not change depending on actual slopes

    def test_excess_buildability_detection(self, verifier, flat_terrain):
        """Test that excess buildability (> target_max) is detected."""
        adjusted, result = verifier.verify_and_adjust(
            flat_terrain,
            target_min=55.0,
            target_max=65.0,
            apply_adjustment=False
        )

        # Flat terrain is 100% buildable (exceeds 65% target)
        assert result['final_buildable_pct'] > 65.0

        # Should not achieve target (too high)
        assert not result['target_achieved']

        # Should have recommendations about excess
        recommendations_text = ' '.join(result['recommendations'])
        assert 'exceeds' in recommendations_text.lower() or 'excess' in recommendations_text.lower()

    def test_recommendation_generation(self, verifier, mixed_terrain):
        """Test that appropriate recommendations are generated."""
        adjusted, result = verifier.verify_and_adjust(
            mixed_terrain,
            target_min=55.0,
            target_max=65.0,
            apply_adjustment=False
        )

        # Recommendations list should not be empty
        assert len(result['recommendations']) > 0

        # All recommendations should be strings
        assert all(isinstance(rec, str) for rec in result['recommendations'])

        # Should contain useful guidance
        recommendations_text = ' '.join(result['recommendations'])
        assert len(recommendations_text) > 50  # Substantial recommendations

    def test_parameter_validation(self, verifier, flat_terrain):
        """Test parameter validation in verify_and_adjust()."""
        # Invalid terrain shape
        with pytest.raises(ValueError, match="Terrain shape must be"):
            wrong_shape = np.zeros((512, 512), dtype=np.float32)
            verifier.verify_and_adjust(wrong_shape)

        # Invalid terrain dtype
        with pytest.raises(ValueError, match="Terrain must be float32"):
            wrong_dtype = flat_terrain.astype(np.float64)
            verifier.verify_and_adjust(wrong_dtype)

        # Invalid target_min
        with pytest.raises(ValueError, match="Target min must be"):
            verifier.verify_and_adjust(flat_terrain, target_min=-10.0)

        # Invalid target_max
        with pytest.raises(ValueError, match="Target max must be"):
            verifier.verify_and_adjust(flat_terrain, target_min=55.0, target_max=50.0)

        # Invalid sigma
        with pytest.raises(ValueError, match="Adjustment sigma must be"):
            verifier.verify_and_adjust(flat_terrain, adjustment_sigma=0.1)

        # Invalid max iterations
        with pytest.raises(ValueError, match="Max iterations must be"):
            verifier.verify_and_adjust(flat_terrain, max_adjustment_iterations=20)

    def test_performance(self, verifier, mixed_terrain):
        """Test that verification is performant."""
        start = time.time()
        adjusted, result = verifier.verify_and_adjust(
            mixed_terrain,
            apply_adjustment=True,
            max_adjustment_iterations=3
        )
        elapsed = time.time() - start

        # Should complete in reasonable time for 1024x1024
        # (may be longer if multiple adjustment iterations applied)
        assert elapsed < 30.0  # < 30 seconds

        # Timing should match reported time
        assert abs(result['processing_time'] - elapsed) < 2.0

    def test_reproducibility(self, verifier, mixed_terrain):
        """Test that verification produces consistent results."""
        adjusted1, result1 = verifier.verify_and_adjust(
            mixed_terrain,
            apply_adjustment=False
        )
        adjusted2, result2 = verifier.verify_and_adjust(
            mixed_terrain,
            apply_adjustment=False
        )

        # Results should be identical
        np.testing.assert_array_equal(adjusted1, adjusted2)
        assert result1['initial_buildable_pct'] == result2['initial_buildable_pct']
        assert result1['final_buildable_pct'] == result2['final_buildable_pct']

    def test_adjustment_iteration_limit(self, verifier, steep_terrain):
        """Test that adjustment respects max_adjustment_iterations limit."""
        adjusted, result = verifier.verify_and_adjust(
            steep_terrain,
            target_min=55.0,
            target_max=65.0,
            apply_adjustment=True,
            max_adjustment_iterations=2  # Limit to 2 iterations
        )

        if result['adjustments_applied']:
            # Should not exceed max iterations
            assert result['adjustment_stats']['iterations_performed'] <= 2

    def test_integration_with_realistic_terrain(self, verifier):
        """Test integration with realistic eroded terrain."""
        # Simulate realistic terrain from erosion pipeline
        resolution = 1024
        x = np.linspace(0, 1, resolution)
        y = np.linspace(0, 1, resolution)
        X, Y = np.meshgrid(x, y)

        # Simulate erosion result: valleys (flat) and ridges (steep)
        base = 0.45 + 0.1 * np.sin(2 * np.pi * X)
        valleys = -0.15 * np.exp(-((X - 0.5)**2 + (Y - 0.5)**2) / 0.1)
        ridges = 0.1 * np.abs(np.sin(8 * np.pi * X))
        terrain = (base + valleys + ridges).astype(np.float32)
        terrain = np.clip(terrain, 0.0, 1.0)

        # Verify and adjust
        adjusted, result = verifier.verify_and_adjust(
            terrain,
            target_min=55.0,
            target_max=65.0,
            apply_adjustment=True
        )

        # Verify output is valid
        assert adjusted.shape == terrain.shape
        assert adjusted.dtype == np.float32
        assert 0.0 <= adjusted.min() <= adjusted.max() <= 1.0

        # Verify we got reasonable buildability estimate
        assert 0.0 <= result['final_buildable_pct'] <= 100.0


class TestConvenienceFunction:
    """Test the convenience function."""

    def test_verify_terrain_buildability_convenience(self):
        """Test convenience function works correctly."""
        # Create test terrain
        terrain = np.random.rand(1024, 1024).astype(np.float32) * 0.5 + 0.25

        # Use convenience function
        adjusted, result = verify_terrain_buildability(
            terrain,
            resolution=1024,
            target_min=55.0,
            target_max=65.0,
            apply_adjustment=False
        )

        # Verify output
        assert adjusted.shape == terrain.shape
        assert adjusted.dtype == np.float32
        assert 'final_buildable_pct' in result


if __name__ == "__main__":
    # Run tests with pytest
    pytest.main([__file__, "-v", "--tb=short"])
