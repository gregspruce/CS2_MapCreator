# Cities Skylines 2 Heightmap Generator

A comprehensive Python tool for generating custom heightmaps for Cities Skylines 2. Create realistic terrain using procedural noise algorithms, or design custom landscapes with precise control.

## Features

- **16-bit Grayscale PNG Export**: CS2-compliant heightmap format
- **Multiple Terrain Presets**: Rolling hills, mountains, islands, canyons, and more
- **Procedural Generation**: Perlin noise, Simplex noise, ridged multifractal
- **Worldmap Support**: Create extended terrain beyond the playable area
- **Auto-Export to CS2**: Automatically detects and exports to CS2 directory
- **Custom Terrain Design**: Combine techniques for unique landscapes
- **Extensive Documentation**: Detailed comments and examples

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
2. Install all dependencies
3. Set everything up for you

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

## Quick Start

### Generate Your First Heightmap

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

Based on the official Cities Skylines 2 wiki:

- **Resolution**: 4096x4096 pixels (playable area)
- **Format**: 16-bit grayscale PNG or TIFF
- **Height Scale**: Default 4096 meters (customizable)
- **Value Range**: 0 (lowest) to 65535 (highest)
- **Location**: `C:/Users/[username]/AppData/LocalLow/Colossal Order/Cities Skylines II/Heightmaps/`

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
│   ├── heightmap_generator.py    # Core heightmap functionality
│   ├── noise_generator.py        # Procedural terrain generation
│   ├── worldmap_generator.py     # Extended worldmap creation
│   └── cs2_exporter.py           # CS2 integration and export
├── examples/
│   ├── 01_basic_usage.py         # Getting started
│   ├── 02_preset_terrains.py     # Using presets
│   ├── 03_with_worldmap.py       # Heightmap + worldmap
│   └── 04_custom_terrain.py      # Custom design
├── output/                        # Generated heightmaps
├── requirements.txt               # Python dependencies
├── CLAUDE.md                      # Development instructions
└── README.md                      # This file
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

## Performance Notes

- 4096x4096 generation typically takes 30-120 seconds depending on complexity
- Smoothing adds 5-15 seconds per iteration
- Worldmap generation adds 30-60 seconds
- Use SSD storage for faster export

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

**Version**: 1.0
**Last Updated**: 2025-10-04
**Compatible with**: Cities Skylines 2 (all versions)
