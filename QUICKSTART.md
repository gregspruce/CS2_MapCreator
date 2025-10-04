# Quick Start Guide

Get your first heightmap in 5 minutes!

## Step 1: Setup (One-Time Only)

**Windows:**
```bash
setup_env.bat
```

**macOS/Linux:**
```bash
chmod +x setup_env.sh
./setup_env.sh
```

This creates a virtual environment and installs everything.

## Step 2: Activate Environment

**Every time you use the tool:**

**Windows:**
```bash
venv\Scripts\activate
```

**macOS/Linux:**
```bash
source venv/bin/activate
```

## Step 3: Launch the GUI

**Easiest way - Visual Editor:**

```bash
python gui_main.py
```

That's it! The GUI will open with:
- Live preview of terrain (hillshade visualization)
- 7 preset buttons (Mountains, Islands, Canyons, etc.)
- Parameter sliders (Scale, Octaves, Persistence, Lacunarity)
- File menu to save and export to CS2

**Quick workflow:**
1. Click a preset (e.g., "Mountains")
2. Wait 1-2 minutes for initial generation (4096x4096 = large!)
3. Adjust sliders if desired (changes update after 500ms of inactivity)
4. File > Save to export heightmap PNG
5. File > Export to CS2 to send directly to game

**IMPORTANT**: All heightmaps are generated at **4096x4096 resolution** as required by Cities Skylines 2. This is not optional - the game will reject any other resolution.

## Alternative: CLI Mode

For automation or scripting:

```bash
python generate_map.py mountains "My First Map"
```

This generates a 4096x4096 heightmap and exports to CS2 automatically.

## CS2 Requirements (CRITICAL)

Per the official CS2 wiki:
- **Resolution**: MUST be exactly 4096x4096 pixels
- **Format**: MUST be 16-bit grayscale PNG or TIFF
- **Height Scale**: Default 4096 meters (adjustable in game)

**Any other resolution will NOT work in Cities Skylines 2!**

## Available Terrain Presets

| Preset | Description |
|--------|-------------|
| `flat` | Completely flat terrain |
| `hills` | Gentle rolling hills |
| `mountains` | Dramatic mountain ranges |
| `islands` | Island archipelago |
| `canyons` | Deep canyons and valleys |
| `highlands` | High plateau terrain |
| `mesas` | Flat-topped mesas |

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

## Troubleshooting

### GUI freezes during startup
- Normal! Initial terrain generation (4096x4096) takes 1-2 minutes
- Status bar shows "Generating terrain..."
- Window is responsive once generation completes

### "Python not found"
- Install Python 3.8+ from [python.org](https://www.python.org/downloads/)

### "Module not found"
- Make sure virtual environment is activated:
  - Windows: `venv\Scripts\activate`
  - macOS/Linux: `source venv/bin/activate`

### "CS2 directory not found"
- The tool will create the directory automatically
- If CS2 hasn't been run yet, directory won't exist - that's normal!

### Generation is slow
- 4096x4096 heightmaps take 60-120 seconds to generate
- This is normal for high-quality terrain
- Be patient!

### Map doesn't appear in CS2
- Restart CS2 if it was running when you exported
- Check that files are in the Heightmaps folder
- Verify PNG is 16-bit grayscale (not 8-bit)
- Verify resolution is exactly 4096x4096

## Tips

1. **Be Patient**: 4096x4096 generation takes time (1-2 minutes)
2. **Save Your Seeds**: Note seed numbers to recreate terrains
3. **Use Presets**: Start with a preset, then customize
4. **Experiment**: Try different parameters and see what happens
5. **Remember the Rules**: Always 4096x4096, always 16-bit grayscale

## Next Steps

- Read the full [README.md](README.md) for detailed documentation
- Check [examples/](examples/) for Python scripting examples
- Review [CHANGELOG.md](CHANGELOG.md) for version history
- See [TODO.md](TODO.md) for future features

## Need Help?

- Check the full documentation in README.md
- Review the example scripts in examples/
- All code is heavily commented - read the source!

---

**Happy map making!** 🏔️🗺️
