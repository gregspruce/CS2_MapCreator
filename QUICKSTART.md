# Quick Start Guide

Get up and running with CS2 Heightmap Generator in 5 minutes!

## Step 1: Setup (One-Time)

### Windows
```bash
setup_env.bat
```

### macOS/Linux
```bash
chmod +x setup_env.sh
./setup_env.sh
```

This creates a virtual environment and installs all dependencies.

## Step 2: Activate Virtual Environment

Every time you want to use the tool, activate the environment first:

### Windows
```bash
venv\Scripts\activate
```

### macOS/Linux
```bash
source venv/bin/activate
```

## Step 3: Generate Your First Map

### Interactive Mode (Easiest)
```bash
python generate_map.py
```

Follow the prompts to:
1. Choose a terrain preset
2. Name your map
3. Optionally add a worldmap

### Quick Generation
```bash
python generate_map.py mountains "Alpine Valley"
```

### With Worldmap
```bash
python generate_map.py islands "Tropical Paradise" --worldmap ocean
```

## Common Commands

### List Available Presets
```bash
python generate_map.py --list
```

### Check CS2 Installation
```bash
python generate_map.py --info
```

### Use a Specific Seed (Reproducible)
```bash
python generate_map.py highlands "Scottish Highlands" --seed 42
```

## Available Terrain Presets

| Preset | Description |
|--------|-------------|
| `flat` | Completely flat terrain |
| `rolling_hills` | Gentle rolling hills |
| `mountains` | Dramatic mountain ranges |
| `islands` | Island archipelago |
| `canyon` | Deep canyons and valleys |
| `highlands` | High plateau terrain |
| `mesas` | Flat-topped mesas |

## Worldmap Options

- `ocean` - Surround with water (island map)
- `seamless` - Extend terrain naturally
- `mountains` - Mountainous surroundings
- `minimal` - Simple background

## Where Are My Files?

### Local Files
Generated heightmaps are saved to:
```
CS2_Map/output/
```

### CS2 Installation
If auto-export succeeds, files are copied to:

**Windows:**
```
C:/Users/[username]/AppData/LocalLow/Colossal Order/Cities Skylines II/Heightmaps/
```

**macOS:**
```
~/Library/Application Support/Colossal Order/Cities Skylines II/Heightmaps/
```

**Linux:**
```
~/.local/share/Colossal Order/Cities Skylines II/Heightmaps/
```

## Import Into CS2

1. Launch Cities Skylines 2
2. Open **Map Editor**
3. Go to **Terrain Tools** → **Heightmaps**
4. Click **Import Heightmap**
5. Select your map from the list
6. Done!

## Advanced Usage

### Custom Python Scripts

Create your own script in the project directory:

```python
from src import HeightmapGenerator, create_preset_terrain, quick_export

# Generate terrain
terrain = create_preset_terrain('mountains', resolution=4096, seed=123)

# Create and export
heightmap = HeightmapGenerator(resolution=4096, height_scale=4096)
heightmap.set_height_data(terrain)
heightmap.export_png('output/my_custom_map.png')

# Export to CS2
quick_export('output/my_custom_map.png', 'My Custom Map')
```

### Run Examples

```bash
cd examples
python 01_basic_usage.py
python 02_preset_terrains.py
python 03_with_worldmap.py
python 04_custom_terrain.py
```

## Troubleshooting

### "Python not found"
Install Python 3.8+ from [python.org](https://www.python.org/downloads/)

### "Module not found"
Make sure you've activated the virtual environment:
```bash
# Windows
venv\Scripts\activate

# macOS/Linux
source venv/bin/activate
```

### "CS2 directory not found"
The tool will create the directory automatically. If CS2 hasn't been run yet, the directory won't exist - that's normal!

### Generation is slow
4096x4096 heightmaps take 30-120 seconds to generate. This is normal for high-quality terrain.

### Map doesn't appear in CS2
- Restart CS2 if it was running when you exported
- Check that files are actually in the Heightmaps folder
- Verify the PNG is 16-bit (not 8-bit)

## Tips

1. **Save Your Seeds**: If you like a terrain, note the seed number to recreate it
2. **Test at Lower Resolution**: Use 1024 for quick testing, then 4096 for final
3. **Combine Techniques**: Start with a preset, then customize
4. **Use Worldmaps**: They make maps feel more immersive
5. **Experiment**: Try different presets and parameters

## Next Steps

- Read the full [README.md](README.md) for detailed documentation
- Check [examples/](examples/) for advanced techniques
- Review [CHANGELOG.md](CHANGELOG.md) for version history
- See [TODO.md](TODO.md) for planned features

## Need Help?

- Check the full documentation in README.md
- Review the example scripts in examples/
- All code is heavily commented - read the source!

---

**Happy map making!** 🏔️🗺️
