# TODO - CS2 Heightmap Generator

## Active Development

### High Priority
- [ ] Test all examples with actual CS2 installation
- [ ] Verify 16-bit PNG export compatibility with CS2
- [ ] Test worldmap import in CS2
- [ ] Performance testing with 4096x4096 generation

### Medium Priority
- [ ] Add progress indicators for long operations
- [ ] Create visual preview generation (thumbnail images)
- [ ] Add batch generation script for multiple maps
- [ ] Implement heightmap import/modification workflow
- [ ] Add validation for height scale limits in CS2

### Low Priority
- [ ] Create GUI wrapper using Tkinter
- [ ] Add preset customization save/load
- [ ] Implement undo/redo for manual edits
- [ ] Add terrain analysis tools (slope, aspect)

## Future Enhancements

### Real-World Data Integration
- [ ] SRTM elevation data import
- [ ] ASTER GDEM support
- [ ] Coordinate-based extraction
- [ ] Automatic scaling and cropping

### Advanced Generation
- [ ] Hydraulic erosion simulation
- [ ] Thermal erosion simulation
- [ ] River network generation
- [ ] Lake/depression detection and creation
- [ ] Coastal features (beaches, cliffs)

### Quality of Life
- [ ] Command completion for interactive mode
- [ ] Map preview before export
- [ ] Comparison tool for different seeds
- [ ] Statistics visualization
- [ ] Height profile along lines

### Performance
- [ ] Multi-threading for noise generation
- [ ] Tile-based processing for memory efficiency
- [ ] Caching for repeated operations
- [ ] CUDA/GPU acceleration exploration

### Documentation
- [ ] Video tutorial for beginners
- [ ] Gallery of example terrains with recipes
- [ ] Advanced techniques documentation
- [ ] Community preset repository
- [ ] CS2 modding workflow integration guide

## Bug Tracking

### Known Issues
- None currently reported

### To Investigate
- [ ] Performance with octaves > 6
- [ ] Memory usage with very large operations
- [ ] Cross-platform path handling edge cases

## Completed
- [x] Core heightmap generator
- [x] Noise-based terrain generation
- [x] Worldmap support
- [x] CS2 auto-detection and export
- [x] CLI interface
- [x] Comprehensive examples
- [x] Documentation (README, CHANGELOG)
- [x] Terrain presets

---

**Last Updated**: 2025-10-04
