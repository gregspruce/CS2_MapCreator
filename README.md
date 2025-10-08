# Cities Skylines 2 Heightmap Generator

**Version 2.4.2 (unreleased)** - A professional Python tool for generating custom heightmaps for Cities Skylines 2. Features evidence-based geological simulation, hydraulic erosion, gradient-based buildability constraints, and advanced user controls.

## Features

### Core Features
- **16-bit Grayscale PNG Export**: CS2-compliant heightmap format
- **Dual Interfaces**: CLI for automation, GUI for visual editing
- **7 Terrain Presets**: Flat, Hills, Mountains, Islands, Canyons, Highlands, Mesas
- **Procedural Generation**: Perlin noise, Simplex noise, ridged multifractal, islands, canyons, mesas
- **Auto-Export to CS2**: Automatically detects and exports to CS2 directory (Windows/macOS/Linux)

### Advanced Features (v2.1.1)
- **⚡ Ultra-Fast Generation**: 4096x4096 terrain in <1 second (60-140x faster than v2.0)
- **Vectorized Processing**: C++/Cython-accelerated noise generation
- **GUI Interface**: Tkinter-based visual editor with instant terrain updates (v2.1.1: preview updates automatically)
- **Elevation Legend**: Dedicated panel showing quantitative height scale - fully visible labels (v2.1.1: layout fixed)
- **State Management**: Full undo/redo support for all operations
- **Water Features**: Fully functional river networks (D8 algorithm), lake generation (watershed), coastal features (v2.1.1: now working)
- **Terrain Analysis**: Comprehensive statistics including slope/aspect/classification (v2.1.1: now accessible via GUI)
- **CS2 Export**: Direct export to Cities Skylines 2 heightmaps directory (v2.1.1: now working)
- **Preview Generation**: Hillshade rendering, multiple colormaps, thumbnail export
- **Preset Management**: Save/load/share custom terrain configurations
- **Worldmap Support**: Extended terrain beyond playable area

### Performance (v2.4.2)
- **Base noise generation**: 5-10 seconds (4096×4096 Perlin/Simplex with domain warping)
- **Full professional pipeline**: 60-75 seconds (with erosion, buildability, all features)
- **Fast mode**: 18-26 seconds (skip erosion for quick iteration)
- **Erosion only**: 40-45 seconds (100 iterations, Numba JIT optimized - 5-8× faster)
- **Coherent structure**: 10-12 seconds (FFT-optimized, 9-14× faster than v2.0)
- **Throughput**: ~19 million pixels/second (noise generation)
- **Scaling**: Near-perfect linear scaling with resolution
- **Setup verification**: Built-in dependency checker ensures optimal performance
- **GUI responsiveness**: Instant preview updates, no manual refresh needed

### NEW in v2.0.0: Hydraulic Erosion & Geological Realism (Stage 1 ✓)
- **⚡ Hydraulic Erosion**: Physically-accurate pipe model with Numba JIT optimization
  - Creates realistic dendritic drainage networks (like real mountains)
  - **Performance**: 1.47s for 50 iterations at 1024×1024 (5-8× faster with Numba)
  - **Performance**: 40-45s for 100 iterations at 4096×4096 (default quality)
  - **Graceful fallback**: Works on all systems (pure NumPy fallback if Numba unavailable)
- **Recursive Domain Warping**: Eliminates grid patterns, adds geological authenticity
- **Ridge Continuity**: Connects mountain ridges while preserving valley detail

### NEW in v2.4.2: Gradient-Based Buildability & Advanced Controls (Stage 2 ✓)
- **Gradient Control Map**: Continuous terrain blending (buildable/moderate/scenic zones)
  - Creates smooth visual transitions (no harsh seams)
  - Achieves 40-50% buildable terrain for CS2 cities (default 40%)
  - Root cause solution (conditional octave generation, not post-processing)
  - Industry-standard approach (World Machine, Gaea use gradient blending)
- **Advanced Tuning Controls**: 5 user-configurable parameters
  - Buildable Octaves (1-4, default: 2) - Lower = smoother
  - Moderate Octaves (3-6, default: 5) - Balance detail/buildability
  - Scenic Octaves (5-9, default: 7) - Higher = more detail
  - Moderate Recursive (0.0-2.0, default: 0.5) - Gentle realism
  - Scenic Recursive (0.0-3.0, default: 1.0) - Strong realism
- **Erosion Parameter Controls**: 4 physics-based parameters
  - Erosion Rate (0.1-0.5, default: 0.2) - Carving strength
  - Deposition Rate (0.01-0.15, default: 0.08) - Sediment smoothing
  - Evaporation Rate (0.005-0.03, default: 0.015) - Water loss control
  - Sediment Capacity (1.0-6.0, default: 3.0) - Max sediment transport
- **Professional defaults**: Erosion enabled (100 iterations), 40% buildability, optimized for playability

**Performance Optimization**: Numba JIT compilation provides 5-8× speedup for erosion simulation with zero code complexity. The system automatically detects Numba availability and falls back to pure NumPy if needed - see [PERFORMANCE.md](PERFORMANCE.md) for details.

## Installation

### Prerequisites

- Python 3.8 or higher
- Cities Skylines 2 (for auto-export feature)

### Quick Setup (Recommended)

**Windows:**
```bash
setup_env.bat
```

**macOS/Linux:**
```bash
chmod +x setup_env.sh
./setup_env.sh
```

This will:
1. Create a virtual environment
2. Install all dependencies (including critical performance library)
3. Set everything up for you

**After setup, verify everything works:**
```bash
python tests/verify_setup.py
```

This checks that all critical dependencies are installed and performance is optimal.

### Manual Setup

If you prefer manual installation:

1. Create a virtual environment:
```bash
# Windows
python -m venv venv
venv\Scripts\activate

# macOS/Linux
python3 -m venv venv
source venv/bin/activate
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

### Activating the Environment

Before using the tool, activate the virtual environment:

**Windows:**
```bash
venv\Scripts\activate
```

**macOS/Linux:**
```bash
source venv/bin/activate
```

## Usage

The CS2 Heightmap Generator offers two interfaces:

### GUI Mode (Recommended for New Users)

Launch the visual interface:

```bash
python gui_main.py
```

**GUI Features:**
- **Live Preview**: Real-time hillshade visualization with terrain colormap (updates automatically!)
- **Elevation Legend**: Dedicated panel showing quantitative heights (0m-4.1km) with fully visible labels
- **Parameter Controls**: 7 terrain presets + adjustable sliders (Scale, Octaves, Persistence, Lacunarity)
- **Fixed Resolution**: 4096x4096 (CS2 requirement - not optional)
- **Zoom & Pan**: Mouse wheel zoom (0.25x-4x), drag to pan
- **Water Features**: Fully functional rivers (D8), lakes (watershed), coastal features (beaches/cliffs)
- **Terrain Analysis**: View comprehensive statistics (height distribution, slope analysis, terrain classification)
- **Menu Bar**: File operations (New, Open, Save, Export to CS2), Edit (Undo/Redo), Tools (Water Features, Analysis)
- **Keyboard Shortcuts**: Ctrl+N (New), Ctrl+S (Save), Ctrl+Z (Undo), Ctrl+Y (Redo)

**Quick Workflow:**
1. Launch GUI: `python gui_main.py` (opens instantly with blank preview)
2. Click a preset (Mountains, Islands, etc.) to generate terrain (<1 second - instant!)
3. **Add water features** via Tools menu:
   - Add Rivers (specify count)
   - Add Lakes (specify count)
   - Add Coastal Features (specify water level)
4. **View Analysis** via Tools → Terrain Analysis (comprehensive statistics)
5. Adjust parameters using sliders (changes update after 500ms)
6. Use File → Export to CS2 to copy directly to Cities Skylines 2 (auto-detects directory)

**Note**: Preview now updates automatically after generation - no clicking required!

### CLI Mode (For Automation)

Generate heightmaps via command line:

```bash
python generate_map.py [preset] [map_name]
```

**Examples:**
```bash
# Generate with preset
python generate_map.py mountains "Alpine Valley"

# List available presets
python generate_map.py --list

# Show system info
python generate_map.py --info
```

## Quick Start (Code)

### Generate Your First Heightmap Programmatically

```python
from src.heightmap_generator import HeightmapGenerator
from src.noise_generator import create_preset_terrain
from src.cs2_exporter import quick_export

# Generate terrain
terrain = create_preset_terrain('mountains', resolution=4096, seed=42)

# Create heightmap
heightmap = HeightmapGenerator(resolution=4096, height_scale=4096)
heightmap.set_height_data(terrain)

# Export locally
heightmap.export_png('output/my_map.png')

# Export to CS2
quick_export('output/my_map.png', 'My Mountain Map')
```

### Run Examples

Check the `examples/` folder for complete working examples:

```bash
cd examples
python 01_basic_usage.py          # Basic terrain generation
python 02_preset_terrains.py      # Different terrain presets
python 03_with_worldmap.py        # Heightmap + worldmap
python 04_custom_terrain.py       # Custom terrain design
```

## CS2 Heightmap Specifications

**CRITICAL**: Based on the official Cities Skylines 2 wiki, these specifications are **MANDATORY**:

- **Resolution**: 4096x4096 pixels (**REQUIRED** - not optional)
- **Format**: 16-bit grayscale PNG or TIFF (**REQUIRED**)
- **Height Scale**: Default 4096 meters (customizable in game)
- **Value Range**: 0 (lowest) to 65535 (highest)
- **Location**: `C:/Users/[username]/AppData/LocalLow/Colossal Order/Cities Skylines II/Heightmaps/`

**WARNING**: Heightmaps with any other resolution will NOT work in Cities Skylines 2. The game requires exactly 4096x4096 pixels.

### Worldmap Specifications

- **Resolution**: 4096x4096 pixels (same as heightmap)
- **Center Area**: 1024x1024 pixels matches the playable heightmap
- **Surrounding**: Shows unplayable terrain for visual context
- **Format**: Same as heightmap (16-bit grayscale PNG)

## Terrain Presets

The tool includes several pre-configured terrain types:

| Preset | Description | Best For |
|--------|-------------|----------|
| `flat` | Completely flat terrain | Testing, custom design base |
| `rolling_hills` | Gentle rolling hills | Suburban development |
| `mountains` | Dramatic mountain ranges | Alpine cities, challenges |
| `islands` | Island archipelago | Coastal cities, bridges |
| `canyon` | Deep valleys and canyons | Desert cities, unique layouts |
| `highlands` | High plateau terrain | Mountain plateaus |
| `mesas` | Flat-topped formations | Southwest-style terrain |

## Advanced Usage

### Custom Terrain Design

```python
from src.heightmap_generator import HeightmapGenerator
from src.noise_generator import NoiseGenerator

# Initialize
heightmap = HeightmapGenerator(resolution=4096, height_scale=5000)

# Create base with gradient
heightmap.create_gradient(start_height=0.3, end_height=0.7, direction='vertical')

# Add a mountain
heightmap.add_circle(center_x=0.5, center_y=0.5, radius=0.2, height=0.3, blend=True)

# Add detail with noise
noise_gen = NoiseGenerator(seed=123)
detail = noise_gen.generate_perlin(resolution=4096, scale=100.0, octaves=4)
combined = heightmap.get_height_data() * 0.8 + detail * 0.2
heightmap.set_height_data(combined)

# Smooth and export
heightmap.smooth(iterations=2)
heightmap.export_png('output/custom.png')
```

### Creating Worldmaps

```python
from src.worldmap_generator import create_worldmap_preset

# Generate playable heightmap first
playable_data = create_preset_terrain('mountains', resolution=4096, seed=999)

heightmap = HeightmapGenerator(resolution=4096)
heightmap.set_height_data(playable_data)
heightmap.export_png('output/map.png')

# Create worldmap with ocean surrounding
noise_gen = NoiseGenerator(seed=999)
worldmap = create_worldmap_preset(
    preset='ocean',
    playable_heightmap=heightmap.get_height_data(),
    noise_generator=noise_gen
)

worldmap.export_png('output/map_worldmap.png')
```

### Fine-Tuning Noise Parameters

Understanding noise parameters helps create specific terrain types:

```python
noise_gen = NoiseGenerator(seed=42)

terrain = noise_gen.generate_perlin(
    resolution=4096,
    scale=200.0,        # Larger = smoother terrain (50-500)
    octaves=6,          # More = more detail (1-8)
    persistence=0.5,    # Lower = smoother (0.3-0.7)
    lacunarity=2.0      # Usually keep at 2.0
)
```

**Parameter Guide:**
- **Scale**: Controls wavelength of features
  - 50-100: Rough, detailed terrain
  - 150-250: Realistic rolling terrain
  - 300+: Very smooth, large features
- **Octaves**: Number of detail layers
  - 1-3: Simple, smooth
  - 4-6: Realistic detail
  - 7-8: Very detailed (slower)
- **Persistence**: Detail strength falloff
  - 0.3-0.4: Smooth hills
  - 0.5: Balanced realism
  - 0.6-0.7: Rough mountains

## Project Structure

```
CS2_Map/
├── src/
│   ├── features/                      # Water features, erosion
│   │   ├── hydraulic_erosion.py      # Pipe model erosion (Numba JIT)
│   │   ├── river_generator.py        # D8 flow, river networks
│   │   ├── water_body_generator.py   # Lake detection
│   │   ├── coastal_generator.py      # Beach/cliff generation
│   │   ├── terrain_editor.py         # Manual editing
│   │   └── performance_utils.py      # Downsampling utilities
│   ├── gui/                           # GUI components
│   │   ├── heightmap_gui.py          # Main Tkinter application
│   │   ├── parameter_panel.py        # Control sliders
│   │   ├── preview_canvas.py         # Live preview
│   │   ├── tool_palette.py           # Manual editing tools
│   │   └── progress_dialog.py        # Progress bar
│   ├── analysis/                      # Terrain analysis
│   │   └── terrain_analyzer.py       # Slope/aspect/statistics
│   ├── heightmap_generator.py         # Core heightmap container
│   ├── noise_generator.py             # Perlin/Simplex generation
│   ├── coherent_terrain_generator_optimized.py  # FFT-optimized (9-14x faster)
│   ├── buildability_enforcer.py       # Slope smoothing
│   ├── terrain_realism.py             # Domain warping, ridges
│   ├── terrain_parameter_mapper.py    # Parameter conversion
│   ├── worldmap_generator.py          # Extended worldmap
│   └── cs2_exporter.py                # CS2 integration
├── tests/                             # 22 test files
│   ├── test_stage2_buildability.py   # Buildability validation
│   ├── test_gradient_control_map.py  # Gradient blending tests
│   └── verify_setup.py               # Dependency checker
├── docs/                              # Documentation
│   ├── analysis/                      # Research & analysis
│   │   └── map_gen_enhancement.md    # Evidence-based requirements
│   ├── features/                      # Feature documentation
│   └── fixes/                         # Bug fix documentation
├── examples/                          # Example scripts
│   ├── 01_basic_usage.py             # Getting started
│   ├── 02_preset_terrains.py         # Using presets
│   ├── 03_with_worldmap.py           # Heightmap + worldmap
│   └── 04_custom_terrain.py          # Custom design
├── output/                            # Generated heightmaps
├── requirements.txt                   # Python dependencies
├── ARCHITECTURE.md                    # Architecture documentation
├── CHANGELOG.md                       # Version history
├── TODO.md                            # Task tracking
├── CLAUDE.md                          # Development instructions
└── README.md                          # This file
```

## Importing Into CS2

### Method 1: Automatic Export

```python
from src.cs2_exporter import quick_export

quick_export(
    heightmap_path='output/my_map.png',
    map_name='My Custom Map',
    worldmap_path='output/my_map_worldmap.png',  # Optional
    overwrite=True
)
```

### Method 2: Manual Import

1. Generate and save your heightmap locally
2. Copy PNG file to: `C:/Users/[username]/AppData/LocalLow/Colossal Order/Cities Skylines II/Heightmaps/`
3. In CS2, open Map Editor
4. Go to Terrain Tools → Heightmaps → Import Heightmap
5. Select your heightmap from the list

## Tips for Great Heightmaps

1. **Height Scale**: Use 3000-5000m for dramatic mountains, 1000-2000m for gentle terrain
2. **Smoothing**: Apply 1-3 smoothing iterations for natural appearance
3. **Combine Techniques**: Layer noise with manual features for best results
4. **Test Iterations**: Use lower resolution (1024) for testing, then generate at 4096
5. **Worldmaps**: Add worldmaps to make your map feel more immersive
6. **Seeds**: Save your seed values to recreate exact terrains later

## Troubleshooting

### CS2 Directory Not Found

The exporter automatically detects CS2's installation. If it fails:

```python
from src.cs2_exporter import CS2Exporter

exporter = CS2Exporter()
exporter.create_cs2_directory()  # Manually create directory
print(exporter.get_info())       # Check status
```

### Heightmap Not Appearing in CS2

- Ensure file is 16-bit PNG (not 8-bit)
- Check resolution is exactly 4096x4096
- Verify filename doesn't contain invalid characters
- Restart CS2 if you added files while it was running

### Generation Taking Too Long

For faster testing:
```python
# Use lower resolution for testing
terrain = create_preset_terrain('mountains', resolution=1024)  # 4x faster

# Reduce octaves
noise_gen.generate_perlin(resolution=4096, octaves=4)  # Instead of 6
```

### Import Errors

```bash
# If noise library fails
pip install noise --force-reinstall

# If PIL/Pillow issues
pip install Pillow --upgrade
```

## Performance Notes (v2.1)

**Actual Performance**:
- 4096x4096 generation: **<1 second** (0.85-0.94s with FastNoiseLite)
- Smoothing: 2-5 seconds per iteration
- Worldmap generation: 1-2 seconds
- Preview rendering: 0.3-0.8 seconds
- **Total workflow**: Real-time interactive (was 2+ minutes in v2.0)

**Critical Dependency**:
- Requires `pyfastnoiselite` for optimal performance
- Without it: Falls back to slow Python (60-120s per generation)
- Run `python verify_setup.py` to check installation

**Hardware Recommendations**:
- CPU: Any modern processor (2+ cores recommended)
- RAM: 4GB minimum, 8GB recommended
- Storage: SSD for faster export (optional)
- GPU: Not required (CPU-based generation)

## Contributing

This is a standalone tool. Feel free to modify and extend for your needs. Key areas for enhancement:

- Real-world elevation data import (SRTM, ASTER)
- GUI interface for visual editing
- Erosion simulation improvements
- Texture/biome map generation
- Batch processing capabilities

## License

This tool is provided as-is for use with Cities Skylines 2. The code is based on standard terrain generation techniques and is free to use and modify.

## Credits

- Terrain generation algorithms: Standard Perlin/Simplex noise implementations
- CS2 heightmap specifications: Cities Skylines 2 Paradox Wiki
- Development: Claude Code (Anthropic)

## References

- [CS2 Map Creation Wiki](https://cs2.paradoxwikis.com/Map_Creation#Heightmaps)
- [Perlin Noise](https://en.wikipedia.org/wiki/Perlin_noise)
- [Fractal Brownian Motion](https://thebookofshaders.com/13/)

---

**Version**: 2.4.2 (unreleased)
**Last Updated**: 2025-10-07
**Compatible with**: Cities Skylines 2 (all versions)
**Key Updates**: Gradient-based buildability, advanced tuning controls, user-configurable erosion parameters, legacy file cleanup
