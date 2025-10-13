"""
Particle-Based Hydraulic Erosion Simulator (Session 4)

Implements particle-based erosion with zone modulation to achieve
55-65% buildable terrain through sediment deposition in valleys.

Algorithm: Particle lifecycle simulation
- Each water droplet flows downhill following gradient
- Erodes terrain proportional to velocity and slope
- Carries sediment up to capacity
- Deposits when capacity exceeded (creates flat valleys)
- Zone modulation: strong erosion in buildable, gentle in scenic

Key Innovation: Zone-modulated erosion creates buildability
- Buildable zones (P=1.0): erosion_factor = 1.5 (strong deposition → flat valleys)
- Scenic zones (P=0.0): erosion_factor = 0.5 (preserve mountains)

Performance: Numba JIT optimization provides 5-8× speedup
- With Numba: 2-5 minutes for 100k particles at 4096×4096
- Without Numba: 10-30 minutes (fallback)

Created: 2025-10-10 (Session 4)
Part of: CS2 Final Implementation Plan
"""

import numpy as np
from typing import Tuple, Dict, Optional
import time
import warnings

# Try to import Numba for performance optimization
NUMBA_AVAILABLE = False
try:
    from numba import njit, prange
    NUMBA_AVAILABLE = True
    print("[EROSION] Numba JIT compilation available - Fast particle-based erosion enabled")
except ImportError:
    print("[EROSION] Numba not available - using pure NumPy fallback (10-30× slower)")
    warnings.warn("Numba not installed. Erosion will be significantly slower. "
                  "Install with: pip install numba", RuntimeWarning)
    # Create dummy decorator for fallback
    def njit(*args, **kwargs):
        def decorator(func):
            return func
        return decorator
    prange = range


# ============================================================================
# Utility Functions
# ============================================================================

def create_gaussian_kernel(radius: int, sigma: Optional[float] = None) -> np.ndarray:
    """
    Create 2D Gaussian kernel for erosion brush.

    Args:
        radius: Kernel radius in pixels (3-5 typical)
        sigma: Gaussian standard deviation (default: radius / 2)

    Returns:
        Normalized Gaussian kernel, shape (2*radius+1, 2*radius+1)

    Formula: G(x, y) = exp(-(x² + y²) / (2σ²))
    Normalized so sum = 1.0 (preserves erosion amount)
    """
    if sigma is None:
        sigma = radius / 2.0

    size = 2 * radius + 1
    kernel = np.zeros((size, size), dtype=np.float32)

    for dy in range(-radius, radius + 1):
        for dx in range(-radius, radius + 1):
            r_sq = dx*dx + dy*dy
            kernel[dy + radius, dx + radius] = np.exp(-r_sq / (2.0 * sigma**2))

    # Normalize so sum = 1.0
    return kernel / kernel.sum()


@njit(cache=True)
def bilinear_interpolate(array: np.ndarray, x: float, y: float) -> float:
    """
    Bilinear interpolation for sub-pixel sampling (Numba-optimized).

    Args:
        array: 2D array to sample from
        x, y: Continuous coordinates (floats)

    Returns:
        Interpolated value at (x, y)

    Formula:
        h(x,y) = (1-fx)*(1-fy)*h[y0,x0] + fx*(1-fy)*h[y0,x1] +
                 (1-fx)*fy*h[y1,x0] + fx*fy*h[y1,x1]
    Where fx, fy are fractional parts of x, y
    """
    height, width = array.shape

    # Clamp to bounds
    x = max(0.0, min(float(width - 1), x))
    y = max(0.0, min(float(height - 1), y))

    # Integer and fractional parts
    x0 = int(x)
    y0 = int(y)
    x1 = min(x0 + 1, width - 1)
    y1 = min(y0 + 1, height - 1)

    fx = x - x0
    fy = y - y0

    # Bilinear interpolation
    return (
        (1.0 - fx) * (1.0 - fy) * array[y0, x0] +
        fx * (1.0 - fy) * array[y0, x1] +
        (1.0 - fx) * fy * array[y1, x0] +
        fx * fy * array[y1, x1]
    )


@njit(cache=True)
def calculate_gradient(heightmap: np.ndarray, x: float, y: float) -> Tuple[float, float]:
    """
    Calculate heightmap gradient at position (x, y) using finite differences.

    Args:
        heightmap: Terrain heightmap
        x, y: Position to calculate gradient (continuous coordinates)

    Returns:
        Tuple of (grad_x, grad_y) - gradient pointing downhill

    Uses Sobel-like operator with bilinear interpolation:
        dh/dx ~= (h[x+1] - h[x-1]) / 2
        dh/dy ~= (h[y+1] - h[y-1]) / 2
    Negative for downhill direction
    """
    height, width = heightmap.shape

    # Sample neighboring heights
    h_x_plus = bilinear_interpolate(heightmap, x + 1.0, y)
    h_x_minus = bilinear_interpolate(heightmap, x - 1.0, y)
    h_y_plus = bilinear_interpolate(heightmap, x, y + 1.0)
    h_y_minus = bilinear_interpolate(heightmap, x, y - 1.0)

    # Finite differences (negative for downhill)
    grad_x = -(h_x_plus - h_x_minus) / 2.0
    grad_y = -(h_y_plus - h_y_minus) / 2.0

    return grad_x, grad_y


# ============================================================================
# Numba-Optimized Particle Simulation
# ============================================================================

@njit(cache=True)
def simulate_particle_numba(
    heightmap: np.ndarray,
    buildability_potential: np.ndarray,
    gaussian_kernel: np.ndarray,
    start_x: float,
    start_y: float,
    params: np.ndarray
) -> None:
    """
    Simulate single water particle with erosion/deposition (Numba-optimized).

    Modifies heightmap in-place. This is the core erosion algorithm.

    Args:
        heightmap: Terrain array (modified in-place)
        buildability_potential: Zone map [0,1] from Session 2
        gaussian_kernel: Pre-computed Gaussian brush
        start_x, start_y: Particle spawn position
        params: [inertia, erosion_rate, deposition_rate, evaporation_rate,
                 sediment_capacity, min_slope, max_steps, terrain_scale]

    Particle Lifecycle:
        1. Calculate gradient at current position
        2. Update velocity (gradient descent + inertia)
        3. Calculate sediment capacity (velocity × slope × water)
        4. Erode if capacity > sediment, deposit if capacity < sediment
        5. Apply erosion/deposition with Gaussian brush
        6. Move particle along velocity vector
        7. Evaporate water
        8. Repeat until water depleted or exits map

    Zone Modulation (CRITICAL):
        factor = 0.5 + 1.0 × buildability_potential
        - P=1.0 (buildable): factor=1.5 (strong erosion → flat valleys)
        - P=0.0 (scenic): factor=0.5 (gentle erosion → preserve mountains)

    Terrain Scale:
        Adjusts erosion strength for float32 [0,1] terrain vs 8-bit [0,255].
        Default 10.0 provides gentle, buildability-preserving erosion.
    """
    # Extract parameters
    inertia = params[0]
    erosion_rate = params[1]
    deposition_rate = params[2]
    evaporation_rate = params[3]
    sediment_capacity_coeff = params[4]
    min_slope = params[5]
    max_steps = int(params[6])
    terrain_scale = params[7]  # NEW: Scale factor for [0,1] terrain

    height, width = heightmap.shape
    brush_radius = gaussian_kernel.shape[0] // 2

    # Initialize particle state
    x, y = start_x, start_y
    vx, vy = 0.0, 0.0
    sediment = 0.0
    water = 1.0

    # Particle simulation loop
    for step in range(max_steps):
        # Check termination conditions
        if water < 0.01:
            break
        if x < 0 or x >= width - 1 or y < 0 or y >= height - 1:
            break

        # Calculate gradient (downhill direction)
        grad_x, grad_y = calculate_gradient(heightmap, x, y)
        slope = np.sqrt(grad_x**2 + grad_y**2)

        if slope < min_slope:
            break  # Stuck in local minimum

        # Update velocity with inertia
        vx = inertia * vx + (1.0 - inertia) * grad_x
        vy = inertia * vy + (1.0 - inertia) * grad_y

        # Calculate sediment capacity: C = Ks × slope × |velocity| × water × terrain_scale
        # terrain_scale compensates for float32 [0,1] range vs 8-bit [0,255]
        velocity_mag = np.sqrt(vx**2 + vy**2)
        capacity = sediment_capacity_coeff * slope * velocity_mag * water * terrain_scale

        # Get zone modulation factor
        ix, iy = int(x), int(y)
        ix = max(0, min(width - 1, ix))
        iy = max(0, min(height - 1, iy))
        zone_potential = buildability_potential[iy, ix]
        zone_factor = 0.5 + 1.0 * zone_potential  # [0.5, 1.5] range

        # Erode or deposit
        if sediment < capacity:
            # ERODE - carve terrain
            erode_amount = (capacity - sediment) * erosion_rate * zone_factor
            sediment += erode_amount

            # Apply erosion with Gaussian brush
            for dy in range(-brush_radius, brush_radius + 1):
                for dx in range(-brush_radius, brush_radius + 1):
                    nx, ny = int(x) + dx, int(y) + dy
                    if 0 <= nx < width and 0 <= ny < height:
                        weight = gaussian_kernel[dy + brush_radius, dx + brush_radius]
                        heightmap[ny, nx] -= erode_amount * weight

        else:
            # DEPOSIT - fill valleys (creates flat buildable areas!)
            deposit_amount = (sediment - capacity) * deposition_rate
            sediment -= deposit_amount

            # Apply deposition with Gaussian brush
            for dy in range(-brush_radius, brush_radius + 1):
                for dx in range(-brush_radius, brush_radius + 1):
                    nx, ny = int(x) + dx, int(y) + dy
                    if 0 <= nx < width and 0 <= ny < height:
                        weight = gaussian_kernel[dy + brush_radius, dx + brush_radius]
                        heightmap[ny, nx] += deposit_amount * weight

        # Move particle
        x += vx
        y += vy

        # Evaporate water
        water *= (1.0 - evaporation_rate)


# ============================================================================
# Main Simulator Class
# ============================================================================

class HydraulicErosionSimulator:
    """
    Particle-based hydraulic erosion simulator with zone modulation.

    This is THE critical component for achieving 55-65% buildable terrain.
    Through sediment deposition in valleys (especially buildable zones),
    particle-based erosion naturally creates flat areas perfect for building.

    Key Features:
    - Particle-based simulation (100k-200k water droplets)
    - Zone-modulated erosion (strong in buildable, gentle in scenic)
    - Gaussian erosion brush (prevents single-pixel artifacts)
    - Numba JIT optimization (5-8× speedup, < 5 min for 100k particles)

    Integration with Sessions 2 & 3:
    - Input: weighted terrain from Session 3, zones from Session 2
    - Output: eroded terrain with 55-65% buildability
    """

    def __init__(self,
                 resolution: int = 4096,
                 map_size_meters: float = 14336.0,
                 seed: Optional[int] = None):
        """
        Initialize erosion simulator.

        Args:
            resolution: Heightmap resolution (4096 for CS2)
            map_size_meters: Physical map size (14336m for CS2)
            seed: Random seed for reproducibility
        """
        self.resolution = resolution
        self.map_size_meters = map_size_meters
        self.seed = seed if seed is not None else np.random.randint(0, 100000)
        self.using_numba = NUMBA_AVAILABLE

        # Pre-compute Gaussian kernel (reused for all particles)
        self.gaussian_kernel = create_gaussian_kernel(radius=3, sigma=1.5)

    def erode(self,
              heightmap: np.ndarray,
              buildability_potential: np.ndarray,
              num_particles: int = 100000,
              inertia: float = 0.1,
              erosion_rate: float = 0.2,
              deposition_rate: float = 0.6,
              evaporation_rate: float = 0.005,
              sediment_capacity: float = 6.0,
              min_slope: float = 0.0005,
              brush_radius: int = 3,
              terrain_scale: float = None,  # Changed: Now auto-calculated if None
              verbose: bool = True) -> Tuple[np.ndarray, Dict]:
        """
        Apply particle-based hydraulic erosion with zone modulation.

        Args:
            heightmap: Input terrain from Session 3, shape (N, N), range [0, 1]
            buildability_potential: Zones from Session 2, shape (N, N), range [0, 1]
            num_particles: Number of particles to simulate (50k-200k)
            inertia: Velocity preservation (0.05-0.3, default 0.1)
            erosion_rate: Terrain carving speed (0.1-0.5, default 0.2)
            deposition_rate: Sediment settling speed (0.3-0.8, default 0.6)
            evaporation_rate: Water loss per step (0.001-0.01, default 0.005)
            sediment_capacity: Max sediment per water (4.0-8.0, default 6.0)
            min_slope: Movement threshold (0.0001-0.001, default 0.0005)
            brush_radius: Erosion spread radius (3-5 pixels, default 3)
            terrain_scale: Amplitude scale for erosion (default: auto-calculated as terrain_amplitude * 0.001)
            verbose: Print progress information

        Returns:
            Tuple of (eroded_heightmap, statistics_dict)
            - eroded_heightmap: Modified terrain, shape (N, N), range [0, 1]
            - statistics_dict: Performance and buildability metrics

        Expected Result:
            Buildability increases from 40-45% (input) to 55-65% (output)
            through sediment deposition in valleys.
        """
        # Validate inputs
        if heightmap.shape != buildability_potential.shape:
            raise ValueError(f"Shape mismatch: heightmap {heightmap.shape} vs "
                           f"buildability {buildability_potential.shape}")

        if heightmap.shape[0] != heightmap.shape[1]:
            raise ValueError(f"Heightmap must be square, got {heightmap.shape}")

        if num_particles < 1000:
            raise ValueError(f"num_particles too small: {num_particles} (min 1000)")

        if not (0.05 <= inertia <= 0.5):
            raise ValueError(f"inertia out of range: {inertia} (valid: 0.05-0.5)")

        # CRITICAL FIX: Auto-calculate terrain_scale based on actual terrain amplitude
        # This ensures erosion strength is proportional to terrain range
        if terrain_scale is None:
            terrain_amplitude = float(heightmap.max() - heightmap.min())
            if terrain_amplitude < 0.001:
                raise ValueError(f"Terrain too flat: amplitude={terrain_amplitude:.6f}")

            # Scale factor: Make erosion proportional to terrain amplitude
            # Multiplier tuned empirically for gentle but noticeable erosion
            # For terrain with amplitude 0.1, use terrain_scale ~0.1
            # For terrain with amplitude 1.0, use terrain_scale ~1.0
            # With amplitude preservation, this creates subtle valley filling
            terrain_scale = terrain_amplitude * 1.0

            if verbose:
                print(f"\n[TERRAIN SCALE AUTO-CALCULATION]")
                print(f"  Terrain amplitude: {terrain_amplitude:.4f}")
                print(f"  Calculated terrain_scale: {terrain_scale:.2f}")
                print(f"  Rationale: Erosion scaled to {(terrain_scale / terrain_amplitude):.1f}x terrain amplitude")

        if verbose:
            impl_type = "Numba JIT" if self.using_numba else "Pure NumPy (SLOW)"
            print(f"\n[SESSION 4: Particle-Based Hydraulic Erosion]")
            print(f"  Implementation: {impl_type}")
            print(f"  Resolution: {heightmap.shape[0]}×{heightmap.shape[1]}")
            print(f"  Particles: {num_particles:,}")
            print(f"  Brush radius: {brush_radius} pixels")
            print(f"  Terrain scale: {terrain_scale:.2f}")
            print(f"  Zone modulation: ENABLED (buildable=1.5×, scenic=0.5×)")

        start_time = time.time()

        # Create working copy
        eroded = heightmap.copy().astype(np.float32)
        zones = buildability_potential.astype(np.float32)

        # Ensure Gaussian kernel matches brush_radius
        if brush_radius != 3:
            self.gaussian_kernel = create_gaussian_kernel(radius=brush_radius, sigma=brush_radius/2)
        kernel = self.gaussian_kernel.astype(np.float32)

        # Calculate initial buildability
        from ..buildability_enforcer import BuildabilityEnforcer
        initial_slopes = BuildabilityEnforcer.calculate_slopes(eroded, self.map_size_meters)
        initial_buildable = BuildabilityEnforcer.calculate_buildability_percentage(initial_slopes)

        if verbose:
            print(f"  Initial buildability: {initial_buildable:.1f}%")
            print(f"  Starting erosion simulation...")

        # Set random seed for reproducibility
        np.random.seed(self.seed)

        # Package parameters for Numba
        params = np.array([
            inertia,
            erosion_rate,
            deposition_rate,
            evaporation_rate,
            sediment_capacity,
            min_slope,
            1000,  # max_steps per particle
            terrain_scale  # NEW: Scale factor for [0,1] terrain
        ], dtype=np.float32)

        # Simulate particles
        height, width = eroded.shape

        if self.using_numba:
            # FAST PATH: Numba-optimized
            self._simulate_particles_numba(
                eroded, zones, kernel, num_particles, params, verbose
            )
        else:
            # FALLBACK: Pure Python (SLOW!)
            if verbose:
                print(f"  WARNING: Running without Numba - this will be SLOW!")
            self._simulate_particles_python(
                eroded, zones, kernel, num_particles, params, verbose
            )

        elapsed = time.time() - start_time

        # CRITICAL FIX: Preserve original amplitude instead of normalizing to [0,1]
        # This prevents slope amplification that destroys buildability
        eroded_min, eroded_max = eroded.min(), eroded.max()
        original_amplitude = heightmap.max() - heightmap.min()

        if eroded_max > eroded_min:
            # Normalize to original amplitude, not [0,1]
            eroded = (eroded - eroded_min) / (eroded_max - eroded_min) * original_amplitude

        if verbose:
            print(f"\n[AMPLITUDE PRESERVATION]")
            print(f"  Original range: [0.000, {original_amplitude:.4f}]")
            print(f"  Eroded range (before norm): [{eroded_min:.4f}, {eroded_max:.4f}]")
            print(f"  Final range (after norm): [0.000, {eroded.max():.4f}]")
            print(f"  Amplification: {eroded.max() / original_amplitude:.2f}x")

        # Calculate final buildability AFTER normalization
        final_slopes = BuildabilityEnforcer.calculate_slopes(eroded, self.map_size_meters)
        final_buildable = BuildabilityEnforcer.calculate_buildability_percentage(final_slopes)

        if verbose:
            print(f"\n[Erosion Complete]")
            print(f"  Time elapsed: {elapsed:.1f}s ({elapsed/60:.1f} min)")
            print(f"  Performance: {num_particles/elapsed:.0f} particles/sec")
            print(f"  Initial buildability: {initial_buildable:.1f}%")
            print(f"  Final buildability: {final_buildable:.1f}%")
            print(f"  Improvement: +{final_buildable - initial_buildable:.1f} percentage points")

            if final_buildable >= 55.0 and final_buildable <= 65.0:
                print(f"  [SUCCESS] Target range achieved (55-65%)")
            else:
                print(f"  [WARNING] Outside target range (got {final_buildable:.1f}%, target 55-65%)")

        # Statistics
        stats = {
            'initial_buildable_pct': float(initial_buildable),
            'final_buildable_pct': float(final_buildable),
            'improvement_pct': float(final_buildable - initial_buildable),
            'num_particles': num_particles,
            'elapsed_seconds': elapsed,
            'particles_per_second': num_particles / elapsed,
            'using_numba': self.using_numba,
            'success': 55.0 <= final_buildable <= 65.0
        }

        return eroded, stats

    def _simulate_particles_numba(self,
                                   eroded: np.ndarray,
                                   zones: np.ndarray,
                                   kernel: np.ndarray,
                                   num_particles: int,
                                   params: np.ndarray,
                                   verbose: bool) -> None:
        """Simulate particles with Numba optimization (FAST)."""
        height, width = eroded.shape

        # Spawn particles at random positions
        spawn_x = np.random.uniform(1, width - 2, num_particles).astype(np.float32)
        spawn_y = np.random.uniform(1, height - 2, num_particles).astype(np.float32)

        # Progress tracking
        progress_interval = max(1, num_particles // 20)  # Report every 5%

        for i in range(num_particles):
            # Simulate particle
            simulate_particle_numba(
                eroded, zones, kernel,
                spawn_x[i], spawn_y[i],
                params
            )

            # Progress update
            if verbose and (i + 1) % progress_interval == 0:
                pct = (i + 1) / num_particles * 100
                print(f"  Progress: {pct:.0f}% ({i+1:,}/{num_particles:,} particles)")

    def _simulate_particles_python(self,
                                    eroded: np.ndarray,
                                    zones: np.ndarray,
                                    kernel: np.ndarray,
                                    num_particles: int,
                                    params: np.ndarray,
                                    verbose: bool) -> None:
        """Simulate particles in pure Python (SLOW fallback)."""
        height, width = eroded.shape

        # Spawn particles
        spawn_x = np.random.uniform(1, width - 2, num_particles).astype(np.float32)
        spawn_y = np.random.uniform(1, height - 2, num_particles).astype(np.float32)

        progress_interval = max(1, num_particles // 20)

        for i in range(num_particles):
            simulate_particle_numba(  # Works without JIT (slower)
                eroded, zones, kernel,
                spawn_x[i], spawn_y[i],
                params
            )

            if verbose and (i + 1) % progress_interval == 0:
                pct = (i + 1) / num_particles * 100
                print(f"  Progress: {pct:.0f}% ({i+1:,}/{num_particles:,} particles) [SLOW MODE]")


# ============================================================================
# Convenience function for pipeline integration
# ============================================================================

def apply_hydraulic_erosion(
    heightmap: np.ndarray,
    buildability_potential: np.ndarray,
    num_particles: int = 100000,
    resolution: int = 4096,
    map_size_meters: float = 14336.0,
    seed: Optional[int] = None,
    verbose: bool = True
) -> Tuple[np.ndarray, Dict]:
    """
    Convenience function to apply hydraulic erosion.

    Args:
        heightmap: Input terrain from Session 3
        buildability_potential: Zones from Session 2
        num_particles: Number of particles (50k-200k)
        resolution: Map resolution
        map_size_meters: Physical size
        seed: Random seed
        verbose: Print progress

    Returns:
        Tuple of (eroded_heightmap, statistics_dict)
    """
    simulator = HydraulicErosionSimulator(
        resolution=resolution,
        map_size_meters=map_size_meters,
        seed=seed
    )

    return simulator.erode(
        heightmap,
        buildability_potential,
        num_particles=num_particles,
        verbose=verbose
    )
