# Changelog

All notable changes to the CS2 Heightmap Generator project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).

## [1.0.1] - 2025-10-04

### Fixed
- Replaced `noise` library with `perlin-noise` to avoid C++ compiler requirement
- Updated all noise generation functions to use `perlin-noise` library
- This ensures the tool works without Visual Studio or build tools

### Changed
- `generate_simplex()` now uses OpenSimplex (already was, but clarified in docs)
- All Perlin noise functions now use `perlin-noise` library instead of `noise`

## [1.0.0] - 2025-10-04

### Added
- Initial release of CS2 Heightmap Generator
- Core heightmap generation with 16-bit PNG support
- Multiple procedural noise algorithms:
  - Perlin noise for natural terrain
  - Simplex noise for faster generation
  - OpenSimplex noise alternative
  - Ridged multifractal for mountains
  - Canyon generation algorithm
  - Terraced/mesa terrain generation
- Seven terrain presets:
  - Flat terrain
  - Rolling hills
  - Mountains
  - Islands
  - Canyons
  - Highlands
  - Mesas
- Worldmap generator with four preset modes:
  - Ocean surrounding (island maps)
  - Seamless terrain extension
  - Mountain surroundings
  - Minimal background
- CS2 auto-detection and export system:
  - Automatic directory detection for Windows, macOS, Linux
  - One-click export to CS2
  - Worldmap export support
  - Map management (list, delete)
- Manual terrain design features:
  - Gradient generation
  - Circular hill/depression addition
  - Smoothing operations
  - Height normalization
  - Custom function application
- Four comprehensive examples:
  - Basic usage
  - Preset terrains
  - Worldmap generation
  - Custom terrain design
- Command-line interface (generate_map.py):
  - Interactive mode
  - Batch generation
  - Preset listing
  - System information
- Comprehensive documentation:
  - Detailed README with usage guides
  - Inline code documentation
  - Parameter tuning guide
  - Troubleshooting section

### Technical Details
- Python 3.8+ support
- NumPy-based height data processing
- PIL/Pillow for image handling
- Cross-platform compatibility (Windows, macOS, Linux)
- Efficient 16-bit PNG export
- Normalized internal representation (0.0-1.0)

### Project Structure
```
CS2_Map/
├── src/
│   ├── heightmap_generator.py    # Core functionality
│   ├── noise_generator.py        # Procedural generation
│   ├── worldmap_generator.py     # Worldmap support
│   └── cs2_exporter.py           # CS2 integration
├── examples/                      # Working examples
├── output/                        # Generated files
├── generate_map.py               # CLI tool
├── requirements.txt              # Dependencies
└── README.md                     # Documentation
```

### Dependencies
- Pillow >= 10.0.0
- numpy >= 1.24.0
- scipy >= 1.10.0
- noise >= 1.2.2
- opensimplex >= 0.4.5

---

## Future Enhancements (Planned)

### Potential Features for v2.0
- [ ] Real-world elevation data import (SRTM, ASTER GDEM)
- [ ] GUI interface for visual editing
- [ ] Advanced erosion simulation
- [ ] Texture/biome map generation
- [ ] Batch processing capabilities
- [ ] Heightmap preview visualization
- [ ] Undo/redo for manual edits
- [ ] Import existing CS2 heightmaps for modification
- [ ] Water level visualization
- [ ] Slope analysis tools

### Optimization Ideas
- [ ] Multi-threading for faster generation
- [ ] Tile-based generation for memory efficiency
- [ ] Progress bars for long operations
- [ ] Caching for repeated operations
- [ ] GPU acceleration investigation

### Documentation Improvements
- [ ] Video tutorials
- [ ] Gallery of example terrains
- [ ] Community preset sharing
- [ ] Advanced techniques guide
- [ ] Integration with map modding workflows

---

**Note**: This project follows semantic versioning. Version numbers indicate:
- Major version (1.x.x): Breaking changes
- Minor version (x.1.x): New features, backwards compatible
- Patch version (x.x.1): Bug fixes, small improvements
