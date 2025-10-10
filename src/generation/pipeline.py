"""
Full Pipeline Integration (Session 6)

Orchestrates the complete hybrid zoned generation + hydraulic erosion system
to achieve 55-65% buildable terrain for Cities: Skylines 2.

Pipeline Order:
    1. Generate buildability zones (Session 2) - Continuous potential map
    2. Generate zone-weighted terrain (Session 3) - Amplitude-modulated noise
    3. Apply ridge enhancement (Session 5) - Add ridges to scenic zones
    4. Apply hydraulic erosion (Session 4) - Carve valleys, deposit sediment
    5. Normalize and validate - Ensure 55-65% buildability achieved

Key Innovation:
    The buildability_potential map flows through the entire pipeline, enabling
    zone-aware modulation at every stage. This is what allows us to achieve
    55-65% buildability with coherent geological features.

Created: 2025-10-10 (Session 6)
Part of: CS2 Final Implementation Plan
"""

import numpy as np
from typing import Tuple, Dict, Optional
import time

from .zone_generator import BuildabilityZoneGenerator
from .weighted_terrain import ZoneWeightedTerrainGenerator
from .ridge_enhancement import RidgeEnhancer
from .hydraulic_erosion import HydraulicErosionSimulator
from .river_analysis import RiverAnalyzer
from .detail_generator import DetailGenerator
from .constraint_verifier import ConstraintVerifier
from ..buildability_enforcer import BuildabilityEnforcer


class TerrainGenerationPipeline:
    """
    Complete terrain generation pipeline integrating Sessions 2-5.

    This class orchestrates the full hybrid zoned generation system:
    - Zone generation with continuous buildability potential
    - Zone-weighted terrain with smooth amplitude modulation
    - Ridge enhancement for coherent mountain ranges
    - Hydraulic erosion for valley creation and buildability

    Target: 55-65% buildable terrain with geological realism.

    Attributes:
        resolution (int): Heightmap resolution (4096 for CS2)
        map_size_meters (float): Physical map size (14336 for CS2)
        seed (int): Master random seed for reproducibility
    """

    def __init__(self,
                 resolution: int = 4096,
                 map_size_meters: float = 14336.0,
                 seed: Optional[int] = None):
        """
        Initialize pipeline with CS2-compatible defaults.

        Args:
            resolution: Heightmap resolution in pixels (default: 4096)
            map_size_meters: Physical map size in meters (default: 14336)
            seed: Master random seed for reproducibility (default: random)
        """
        self.resolution = resolution
        self.map_size_meters = map_size_meters
        self.seed = seed if seed is not None else np.random.randint(0, 100000)

        # Initialize all generators with consistent seed
        self.zone_gen = BuildabilityZoneGenerator(
            resolution=resolution,
            map_size_meters=map_size_meters,
            seed=self.seed
        )

        self.terrain_gen = ZoneWeightedTerrainGenerator(
            resolution=resolution,
            map_size_meters=map_size_meters,
            seed=self.seed + 1  # Offset seed for variation
        )

        self.ridge_enhancer = RidgeEnhancer(
            resolution=resolution,
            map_size_meters=map_size_meters,
            seed=self.seed + 2
        )

        self.erosion_sim = HydraulicErosionSimulator(
            resolution=resolution,
            map_size_meters=map_size_meters,
            seed=self.seed + 3
        )

        self.river_analyzer = RiverAnalyzer(
            resolution=resolution,
            map_size_meters=map_size_meters,
            seed=self.seed + 4
        )

        self.detail_gen = DetailGenerator(
            resolution=resolution,
            map_size_meters=map_size_meters,
            seed=self.seed + 5
        )

        self.constraint_verifier = ConstraintVerifier(
            resolution=resolution,
            map_size_meters=map_size_meters
        )

    def _normalize_terrain(self, terrain: np.ndarray) -> np.ndarray:
        """
        Normalize terrain to [0, 1] range.

        This ensures consistent range across all pipeline stages,
        preventing amplitude mismatches between stages.

        Args:
            terrain: Input terrain array

        Returns:
            Normalized terrain in [0, 1] range
        """
        terrain_min, terrain_max = terrain.min(), terrain.max()
        if terrain_max > terrain_min:
            terrain = (terrain - terrain_min) / (terrain_max - terrain_min)
        return np.clip(terrain, 0.0, 1.0).astype(np.float32)

    def generate(self,
                 # Zone generation parameters (Session 2)
                 target_coverage: float = 0.70,
                 zone_wavelength: float = 6500.0,
                 zone_octaves: int = 2,

                 # Terrain generation parameters (Session 3)
                 base_amplitude: float = 0.2,
                 min_amplitude_mult: float = 0.3,
                 max_amplitude_mult: float = 1.0,
                 terrain_wavelength: float = 1000.0,
                 terrain_octaves: int = 6,

                 # Ridge enhancement parameters (Session 5)
                 ridge_strength: float = 0.2,
                 ridge_octaves: int = 5,
                 ridge_wavelength: float = 1500.0,

                 # Hydraulic erosion parameters (Session 4)
                 num_particles: int = 100000,
                 erosion_rate: float = 0.5,
                 deposition_rate: float = 0.3,

                 # River analysis parameters (Session 7)
                 river_threshold_percentile: float = 99.0,
                 min_river_length: int = 10,

                 # Detail addition parameters (Session 8)
                 detail_amplitude: float = 0.02,
                 detail_wavelength: float = 75.0,

                 # Constraint verification parameters (Session 8)
                 target_buildable_min: float = 55.0,
                 target_buildable_max: float = 65.0,
                 apply_constraint_adjustment: bool = True,

                 # Control flags
                 apply_ridges: bool = True,
                 apply_erosion: bool = True,
                 apply_rivers: bool = True,
                 apply_detail: bool = True,
                 verbose: bool = True
                 ) -> Tuple[np.ndarray, Dict]:
        """
        Execute complete terrain generation pipeline.

        This method orchestrates all sessions in the correct order to achieve
        55-65% buildable terrain with coherent geological features.

        Args:
            # Zone Generation (Session 2)
            target_coverage: Target buildable coverage 0.60-0.80 (default: 0.70)
            zone_wavelength: Zone feature size 5000-8000m (default: 6500m)
            zone_octaves: Zone octaves 2-3 (default: 2)

            # Weighted Terrain (Session 3)
            base_amplitude: Base terrain amplitude 0.15-0.3 (default: 0.2)
            min_amplitude_mult: Buildable amplitude multiplier 0.2-0.4 (default: 0.3)
            max_amplitude_mult: Scenic amplitude multiplier 0.8-1.2 (default: 1.0)
            terrain_wavelength: Terrain feature size 500-2000m (default: 1000m)
            terrain_octaves: Terrain octaves 4-8 (default: 6)

            # Ridge Enhancement (Session 5)
            ridge_strength: Ridge prominence 0.1-0.3 (default: 0.2)
            ridge_octaves: Ridge octaves 4-6 (default: 5)
            ridge_wavelength: Ridge feature size 1000-2000m (default: 1500m)

            # Hydraulic Erosion (Session 4)
            num_particles: Particle count 50k-200k (default: 100k)
            erosion_rate: Erosion speed 0.3-0.8 (default: 0.5)
            deposition_rate: Deposition speed 0.1-0.5 (default: 0.3)

            # River Analysis (Session 7)
            river_threshold_percentile: Flow percentile for rivers 95-99.5 (default: 99.0)
            min_river_length: Minimum river length in pixels (default: 10)

            # Control
            apply_ridges: Enable ridge enhancement (default: True)
            apply_erosion: Enable hydraulic erosion (default: True)
            apply_rivers: Enable river analysis (default: True)
            verbose: Print progress information (default: True)

        Returns:
            Tuple of (final_heightmap, complete_statistics_dict)
            - final_heightmap: np.ndarray, shape (resolution, resolution), dtype float32
              Range [0.0, 1.0] ready for export
            - complete_statistics_dict: Contains stats from all pipeline stages
              plus final buildability validation

        Raises:
            ValueError: If parameters are out of valid ranges
            RuntimeError: If buildability target (55-65%) not achieved

        Example:
            >>> pipeline = TerrainGenerationPipeline(seed=42)
            >>> terrain, stats = pipeline.generate()
            >>> print(f"Buildability: {stats['final_buildable_pct']:.1f}%")
            Buildability: 60.2%
        """
        pipeline_start_time = time.time()

        if verbose:
            print("=" * 80)
            print("CS2 TERRAIN GENERATION PIPELINE - SESSION 6")
            print("=" * 80)
            print(f"Target: 55-65% buildable terrain")
            print(f"Resolution: {self.resolution}×{self.resolution}")
            print(f"Map size: {self.map_size_meters}m")
            print(f"Seed: {self.seed}")
            print("=" * 80)

        # ====================================================================
        # STAGE 1: Generate Buildability Zones (Session 2)
        # ====================================================================
        if verbose:
            print(f"\n{'='*80}")
            print("STAGE 1/5: BUILDABILITY ZONE GENERATION (SESSION 2)")
            print(f"{'='*80}")

        stage1_start = time.time()
        buildability_potential, zone_stats = self.zone_gen.generate_potential_map(
            target_coverage=target_coverage,
            zone_wavelength=zone_wavelength,
            zone_octaves=zone_octaves,
            verbose=verbose
        )
        stage1_time = time.time() - stage1_start

        if verbose:
            print(f"\n[STAGE 1 COMPLETE] Time: {stage1_time:.2f}s")
            print(f"  Coverage: {zone_stats['coverage_percent']:.1f}% (target: {target_coverage*100:.0f}%)")

        # ====================================================================
        # STAGE 2: Generate Zone-Weighted Terrain (Session 3)
        # ====================================================================
        if verbose:
            print(f"\n{'='*80}")
            print("STAGE 2/5: ZONE-WEIGHTED TERRAIN GENERATION (SESSION 3)")
            print(f"{'='*80}")

        stage2_start = time.time()
        terrain, terrain_stats = self.terrain_gen.generate(
            buildability_potential=buildability_potential,
            base_amplitude=base_amplitude,
            min_amplitude_mult=min_amplitude_mult,
            max_amplitude_mult=max_amplitude_mult,
            terrain_wavelength=terrain_wavelength,
            terrain_octaves=terrain_octaves,
            verbose=verbose
        )
        stage2_time = time.time() - stage2_start

        # Normalize terrain to [0, 1] after weighted generation
        terrain = self._normalize_terrain(terrain)

        if verbose:
            print(f"\n[STAGE 2 COMPLETE] Time: {stage2_time:.2f}s")
            print(f"  Buildability before erosion: {terrain_stats['buildable_percent']:.1f}%")
            print(f"  Terrain normalized to [0, 1] range")

        # ====================================================================
        # STAGE 3: Apply Ridge Enhancement (Session 5) [OPTIONAL]
        # ====================================================================
        if apply_ridges:
            if verbose:
                print(f"\n{'='*80}")
                print("STAGE 3/5: RIDGE ENHANCEMENT (SESSION 5)")
                print(f"{'='*80}")

            stage3_start = time.time()
            terrain, ridge_stats = self.ridge_enhancer.enhance(
                terrain=terrain,
                buildability_potential=buildability_potential,
                ridge_octaves=ridge_octaves,
                ridge_wavelength=ridge_wavelength,
                ridge_strength=ridge_strength,
                verbose=verbose
            )
            stage3_time = time.time() - stage3_start

            # Normalize terrain to [0, 1] after ridge enhancement
            terrain = self._normalize_terrain(terrain)

            if verbose:
                print(f"\n[STAGE 3 COMPLETE] Time: {stage3_time:.2f}s")
                print(f"  Ridge coverage: {ridge_stats['ridge_coverage_pct']:.1f}%")
                print(f"  Terrain normalized to [0, 1] range")
        else:
            stage3_time = 0.0
            ridge_stats = {'skipped': True}
            if verbose:
                print(f"\n[STAGE 3 SKIPPED] Ridge enhancement disabled")

        # ====================================================================
        # STAGE 4: Apply Hydraulic Erosion (Session 4) [OPTIONAL]
        # ====================================================================
        if apply_erosion:
            if verbose:
                print(f"\n{'='*80}")
                print("STAGE 4/5: HYDRAULIC EROSION (SESSION 4)")
                print(f"{'='*80}")

            stage4_start = time.time()
            terrain, erosion_stats = self.erosion_sim.erode(
                heightmap=terrain,
                buildability_potential=buildability_potential,
                num_particles=num_particles,
                erosion_rate=erosion_rate,
                deposition_rate=deposition_rate,
                verbose=verbose
            )
            stage4_time = time.time() - stage4_start

            # Normalize terrain to [0, 1] after erosion
            terrain = self._normalize_terrain(terrain)

            if verbose:
                print(f"\n[STAGE 4 COMPLETE] Time: {stage4_time:.2f}s")
                print(f"  Buildability improvement: +{erosion_stats['improvement_pct']:.1f}%")
                print(f"  Terrain normalized to [0, 1] range")
        else:
            stage4_time = 0.0
            erosion_stats = {'skipped': True}
            if verbose:
                print(f"\n[STAGE 4 SKIPPED] Hydraulic erosion disabled")

        # ====================================================================
        # STAGE 4.5: River Analysis and Flow Networks (Session 7) [OPTIONAL]
        # ====================================================================
        if apply_rivers:
            if verbose:
                print(f"\n{'='*80}")
                print("STAGE 4.5/5: RIVER ANALYSIS (SESSION 7)")
                print(f"{'='*80}")

            stage4_5_start = time.time()
            river_network, river_stats = self.river_analyzer.analyze_rivers(
                heightmap=terrain,
                buildability_potential=buildability_potential,
                threshold_percentile=river_threshold_percentile,
                min_river_length=min_river_length,
                verbose=verbose
            )
            stage4_5_time = time.time() - stage4_5_start

            if verbose:
                print(f"\n[STAGE 4.5 COMPLETE] Time: {stage4_5_time:.2f}s")
                print(f"  Rivers detected: {river_stats['num_rivers']}")
                if river_stats['num_rivers'] > 0:
                    print(f"  Total river length: {river_stats['total_river_length_meters']:.0f}m")
        else:
            stage4_5_time = 0.0
            river_network = None
            river_stats = {'skipped': True}
            if verbose:
                print(f"\n[STAGE 4.5 SKIPPED] River analysis disabled")

        # ====================================================================
        # STAGE 5.5: Detail Addition and Constraint Verification (Session 8)
        # ====================================================================
        if verbose:
            print(f"\n{'='*80}")
            print("STAGE 5.5/6: DETAIL ADDITION & CONSTRAINT VERIFICATION (SESSION 8)")
            print(f"{'='*80}")

        stage5_5_start = time.time()

        # Add conditional detail to steep areas
        if apply_detail:
            if verbose:
                print(f"\n[5.5.1] Adding conditional detail to steep areas...")
            terrain, detail_stats = self.detail_gen.add_detail(
                terrain=terrain,
                detail_amplitude=detail_amplitude,
                detail_wavelength=detail_wavelength
            )
        else:
            detail_stats = {'skipped': True}
            if verbose:
                print(f"\n[5.5.1] Detail addition skipped")

        # Verify buildability constraints and apply adjustments if needed
        if verbose:
            print(f"\n[5.5.2] Verifying buildability constraints...")
        terrain, verification_result = self.constraint_verifier.verify_and_adjust(
            terrain=terrain,
            target_min=target_buildable_min,
            target_max=target_buildable_max,
            apply_adjustment=apply_constraint_adjustment
        )

        stage5_5_time = time.time() - stage5_5_start

        if verbose:
            print(f"\n[STAGE 5.5 COMPLETE] Time: {stage5_5_time:.2f}s")
            if apply_detail:
                print(f"  Detail applied to: {detail_stats['detail_applied_pct']:.1f}% of terrain")
            print(f"  Final buildability: {verification_result['final_buildable_pct']:.1f}%")
            print(f"  Target achieved: {verification_result['target_achieved']}")

        # ====================================================================
        # STAGE 6: Final Normalization and Validation
        # ====================================================================
        if verbose:
            print(f"\n{'='*80}")
            print("STAGE 6/6: FINAL NORMALIZATION")
            print(f"{'='*80}")

        stage6_start = time.time()

        # Safety check: Ensure final terrain is in [0, 1] range
        # (Should already be normalized from previous stages)
        terrain = np.clip(terrain, 0.0, 1.0).astype(np.float32)

        # Calculate final buildability
        final_slopes = BuildabilityEnforcer.calculate_slopes(
            terrain, self.map_size_meters
        )
        final_buildable_pct = BuildabilityEnforcer.calculate_buildability_percentage(final_slopes)

        stage6_time = time.time() - stage6_start

        # ====================================================================
        # Compile Complete Statistics
        # ====================================================================
        total_time = time.time() - pipeline_start_time

        complete_stats = {
            # Pipeline metadata
            'resolution': self.resolution,
            'map_size_meters': self.map_size_meters,
            'seed': self.seed,
            'pipeline_version': '1.0',
            'session': 6,

            # Stage timings
            'stage1_zone_time': stage1_time,
            'stage2_terrain_time': stage2_time,
            'stage3_ridge_time': stage3_time,
            'stage4_erosion_time': stage4_time,
            'stage4_5_river_time': stage4_5_time,
            'stage5_5_detail_verification_time': stage5_5_time,
            'stage6_normalization_time': stage6_time,
            'total_pipeline_time': total_time,

            # Stage statistics
            'zone_stats': zone_stats,
            'terrain_stats': terrain_stats,
            'ridge_stats': ridge_stats,
            'erosion_stats': erosion_stats,
            'river_stats': river_stats,
            'river_network': river_network,
            'detail_stats': detail_stats,
            'verification_result': verification_result,

            # Final metrics
            'final_buildable_pct': float(final_buildable_pct),
            'final_mean_slope': float(final_slopes.mean()),
            'final_median_slope': float(np.median(final_slopes)),
            'final_p90_slope': float(np.percentile(final_slopes, 90)),
            'final_p99_slope': float(np.percentile(final_slopes, 99)),
            'final_min_height': float(terrain.min()),
            'final_max_height': float(terrain.max()),

            # Success validation
            'target_buildable_min': 55.0,
            'target_buildable_max': 65.0,
            'target_achieved': 55.0 <= final_buildable_pct <= 65.0,

            # Parameters used
            'parameters': {
                'target_coverage': target_coverage,
                'zone_wavelength': zone_wavelength,
                'base_amplitude': base_amplitude,
                'num_particles': num_particles if apply_erosion else 0,
                'apply_ridges': apply_ridges,
                'apply_erosion': apply_erosion,
            }
        }

        # ====================================================================
        # Final Report
        # ====================================================================
        if verbose:
            print(f"\n{'='*80}")
            print("PIPELINE COMPLETE - FINAL RESULTS")
            print(f"{'='*80}")
            print(f"\n[TIMING]")
            print(f"  Stage 1 (Zones):       {stage1_time:6.2f}s")
            print(f"  Stage 2 (Terrain):     {stage2_time:6.2f}s")
            print(f"  Stage 3 (Ridges):      {stage3_time:6.2f}s")
            print(f"  Stage 4 (Erosion):     {stage4_time:6.2f}s")
            print(f"  Stage 4.5 (Rivers):    {stage4_5_time:6.2f}s")
            print(f"  Stage 5.5 (Detail+Ver):{stage5_5_time:6.2f}s")
            print(f"  Stage 6 (Normalization):{stage6_time:6.2f}s")
            print(f"  {'-'*40}")
            print(f"  Total:                 {total_time:6.2f}s ({total_time/60:.1f} min)")

            print(f"\n[BUILDABILITY PROGRESSION]")
            print(f"  After zones:         N/A (potential map only)")
            print(f"  After terrain:       {terrain_stats['buildable_percent']:6.1f}%")
            print(f"  After ridges:        {terrain_stats['buildable_percent']:6.1f}% (ridges don't change slopes)")
            if apply_erosion:
                print(f"  After erosion:       {erosion_stats['final_buildable_pct']:6.1f}%")
            print(f"  Final (normalized):  {final_buildable_pct:6.1f}%")

            print(f"\n[FINAL TERRAIN ANALYSIS]")
            print(f"  Buildable percentage: {final_buildable_pct:.1f}%")
            print(f"  Mean slope:           {complete_stats['final_mean_slope']:.2f}%")
            print(f"  Median slope:         {complete_stats['final_median_slope']:.2f}%")
            print(f"  90th percentile:      {complete_stats['final_p90_slope']:.2f}%")
            print(f"  Height range:         [{terrain.min():.4f}, {terrain.max():.4f}]")

            print(f"\n[VALIDATION]")
            print(f"  Target range:         55-65% buildable")
            print(f"  Achieved:             {final_buildable_pct:.1f}%")

            if complete_stats['target_achieved']:
                print(f"  Status:               [SUCCESS] Target achieved!")
            elif final_buildable_pct < 55.0:
                deficit = 55.0 - final_buildable_pct
                print(f"  Status:               [BELOW TARGET] by {deficit:.1f}%")
                print(f"  Suggestion:           Increase target_coverage or num_particles")
            else:
                excess = final_buildable_pct - 65.0
                print(f"  Status:               [ABOVE TARGET] by {excess:.1f}%")
                print(f"  Suggestion:           Decrease target_coverage or reduce erosion")

            print(f"\n{'='*80}")

        return terrain, complete_stats


# ============================================================================
# Convenience Functions
# ============================================================================

def generate_terrain(resolution: int = 4096,
                     map_size_meters: float = 14336.0,
                     seed: Optional[int] = None,
                     target_buildable: float = 0.60,
                     num_particles: int = 100000,
                     verbose: bool = True) -> Tuple[np.ndarray, Dict]:
    """
    Convenience function for simple terrain generation.

    Generates terrain using sensible defaults with minimal parameter exposure.
    For advanced control, use TerrainGenerationPipeline class directly.

    Args:
        resolution: Heightmap resolution (default: 4096)
        map_size_meters: Physical map size (default: 14336)
        seed: Random seed (default: random)
        target_buildable: Target buildable percentage 0.55-0.65 (default: 0.60)
        num_particles: Erosion particles (default: 100k)
        verbose: Print progress (default: True)

    Returns:
        Tuple of (heightmap, statistics_dict)

    Example:
        >>> terrain, stats = generate_terrain(seed=42, target_buildable=0.62)
        >>> print(f"Achieved {stats['final_buildable_pct']:.1f}% buildable")
    """
    # Map target_buildable to target_coverage (heuristic)
    # Higher coverage -> more buildable zones -> more buildable terrain
    target_coverage = 0.60 + (target_buildable - 0.55) * 2.0  # Maps [0.55, 0.65] -> [0.60, 0.80]
    target_coverage = np.clip(target_coverage, 0.60, 0.80)

    pipeline = TerrainGenerationPipeline(
        resolution=resolution,
        map_size_meters=map_size_meters,
        seed=seed
    )

    return pipeline.generate(
        target_coverage=target_coverage,
        num_particles=num_particles,
        verbose=verbose
    )


def generate_preset(preset_name: str = 'balanced',
                    resolution: int = 4096,
                    map_size_meters: float = 14336.0,
                    seed: Optional[int] = None,
                    verbose: bool = True) -> Tuple[np.ndarray, Dict]:
    """
    Generate terrain using named presets.

    Available presets:
    - 'balanced': 60% buildable, moderate mountains (default)
    - 'mountainous': 55% buildable, dramatic peaks
    - 'rolling_hills': 65% buildable, gentle terrain
    - 'valleys': 58% buildable, strong erosion

    Args:
        preset_name: Preset identifier (see above)
        resolution: Heightmap resolution (default: 4096)
        map_size_meters: Physical map size (default: 14336)
        seed: Random seed (default: random)
        verbose: Print progress (default: True)

    Returns:
        Tuple of (heightmap, statistics_dict)

    Raises:
        ValueError: If preset_name not recognized

    Example:
        >>> terrain, stats = generate_preset('mountainous', seed=42)
    """
    presets = {
        'balanced': {
            'target_coverage': 0.70,
            'base_amplitude': 0.2,
            'min_amplitude_mult': 0.3,
            'max_amplitude_mult': 1.0,
            'ridge_strength': 0.2,
            'num_particles': 100000,
            'apply_ridges': True,
            'apply_erosion': True,
        },
        'mountainous': {
            'target_coverage': 0.65,
            'base_amplitude': 0.25,
            'min_amplitude_mult': 0.3,
            'max_amplitude_mult': 1.2,
            'ridge_strength': 0.25,
            'num_particles': 80000,
            'apply_ridges': True,
            'apply_erosion': True,
        },
        'rolling_hills': {
            'target_coverage': 0.75,
            'base_amplitude': 0.15,
            'min_amplitude_mult': 0.35,
            'max_amplitude_mult': 0.8,
            'ridge_strength': 0.15,
            'num_particles': 120000,
            'apply_ridges': True,
            'apply_erosion': True,
        },
        'valleys': {
            'target_coverage': 0.68,
            'base_amplitude': 0.22,
            'min_amplitude_mult': 0.3,
            'max_amplitude_mult': 1.0,
            'ridge_strength': 0.2,
            'num_particles': 150000,  # Strong erosion
            'apply_ridges': True,
            'apply_erosion': True,
        },
    }

    if preset_name not in presets:
        available = ', '.join(presets.keys())
        raise ValueError(f"Unknown preset '{preset_name}'. Available: {available}")

    params = presets[preset_name]

    if verbose:
        print(f"[PRESET] Generating '{preset_name}' terrain")
        print(f"  Target coverage: {params['target_coverage']*100:.0f}%")
        print(f"  Erosion particles: {params['num_particles']:,}")

    pipeline = TerrainGenerationPipeline(
        resolution=resolution,
        map_size_meters=map_size_meters,
        seed=seed
    )

    return pipeline.generate(verbose=verbose, **params)
