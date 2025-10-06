# Enhancing Cities Skylines 2 Heightmap Generation: Research Report

## Executive Summary

Your heightmap generator faces a clear challenge: **eliminating obvious procedural noise patterns while creating realistic, buildable terrain for Cities Skylines 2**. Research reveals three critical insights. First, modern terrain generation has moved far beyond basic Perlin noise—hydraulic erosion simulation remains the gold standard for realism, eliminating uniform "bumpy" patterns through natural water flow and sediment transport. Second, Cities Skylines 2 is significantly more sensitive to terrain slopes than its predecessor, with buildings creating "ugly terrain steps" even on gentle slopes—**you'll need 45-55% of terrain at 0-5% slopes for playable maps**. Third, the most effective approach combines domain-warped noise for base terrain, GPU-accelerated erosion simulation, and constraint-based generation that guarantees buildable flat areas before adding visual detail to unbuildable zones.

The following sections provide specific algorithms, implementation resources, and CS2-specific considerations to transform your generator from producing unusable "evenly-distributed bumps" into creating geographically plausible, gameplay-ready terrain with interesting water features.

---

## Hydraulic erosion transforms uniform noise into realistic terrain

**The most impactful improvement you can make** is implementing hydraulic erosion simulation. This single technique eliminates the "obvious procedural noise" problem by simulating how water carves valleys, creates drainage networks, and deposits sediment—natural processes that override uniform noise patterns.

The pipe model algorithm by Xing Mei et al. (2007) offers the best balance of realism and performance. The simulation tracks five data layers per heightmap cell: terrain height, water height, suspended sediment, outflow flux in four directions, and velocity. Each iteration executes five steps: water increment (rainfall/sources), flow simulation using virtual pipes between cells, erosion-deposition based on sediment transport capacity, sediment transportation via semi-Lagrangian advection, and water evaporation. The critical formula for sediment transport capacity is **C(x,y) = Kc × sin(α) × |velocity|** where Kc is the sediment capacity constant and α is the local tilt angle. Areas with steeper slopes and faster water movement erode more aggressively, while flat areas accumulate deposits.

This algorithm is GPU-parallelizable and runs at interactive rates—the original paper demonstrates **7 GPU passes generating realistic erosion in under a second** for typical heightmaps. You can find the full academic paper at https://inria.hal.science/inria-00402079/document. For implementation, the UnityTerrainErosionGPU repository (https://github.com/bshishov/UnityTerrainErosionGPU) provides C# compute shaders implementing this exact pipe model with real-time parameter adjustment.

For Python development, the terrain-erosion-3-ways repository by dandrino (https://github.com/dandrino/terrain-erosion-3-ways) implements three distinct erosion approaches with detailed explanations. The particle-based "droplet" method offers a faster alternative: **spawning 50,000-100,000 water particles that trace downhill paths, each picking up sediment proportional to velocity and depositing when slowing**. While less precise than grid-based pipe models, this approach generates a 512×512 island with realistic erosion features in under 0.5 seconds. Job Talle's implementation at https://jobtalle.com/simulating_hydraulic_erosion.html provides clear pseudocode.

The visual difference is dramatic. Pure Perlin noise creates uniformly distributed bumps across the entire heightmap—exactly your current problem. After hydraulic erosion, you get dendritic valley networks, smooth river-carved terrain, sediment deposits in lowlands, and natural drainage patterns that look like real geography. The erosion process concentrates detail in valleys where it matters for realism while smoothing ridges and creating natural plateaus—perfect for buildable city areas.

### Thermal erosion smooths slopes and prevents unrealistic cliffs

Complement hydraulic erosion with thermal erosion to eliminate overly steep slopes. The algorithm is conceptually simple: material exceeding the **angle of repose (talus angle, typically 30-35°)** slides downhill. For each cell, check all eight neighbors. If the height difference exceeds the maximum stable angle, transfer material: `transfer = settling_rate × (height_diff - max_stable_angle) / 2`. Remove the transfer amount from the higher cell and add it to the lower cell.

The implementation from Axel Paris at https://aparis69.github.io/public_html/posts/terrain_erosion.html runs efficiently on GPU with atomic operations to handle race conditions. Running 1000 iterations on a 1024×1024 grid takes approximately 100ms on modern GPUs. This creates scree fields at cliff bases, smooths steep slopes, and forms talus cones—all features that make terrain look naturally weathered rather than procedurally generated.

**Combining hydraulic and thermal erosion in sequence produces the most realistic results**: thermal erosion first to establish stable slopes, then hydraulic erosion to carve valleys and drainage networks, then a final light thermal pass to smooth any artifacts. This multi-pass approach is used by professional tools like World Machine and Gaea.

---

## Domain warping eliminates grid-aligned procedural patterns

Even with erosion simulation, your base noise function matters. **Domain warping breaks up the regular, grid-aligned patterns that make procedural terrain obviously artificial**. Rather than sampling noise directly at each coordinate (x, y), you first generate offset fields using separate noise functions, then sample the primary noise at the warped coordinates.

Inigo Quilez's foundational technique (https://www.iquilezles.org/www/articles/warp/warp.htm) uses this formula:

```
q = [fbm(x, y), fbm(x+5.2, y+1.3)]
r = [fbm(x + 4*q[0], y + 4*q[1]), fbm(x + 4*q[0] + 1.7, y + 4*q[1] + 9.2)]
pattern(x, y) = fbm(x + 4*r[0], y + 4*r[1])
```

The strength factor controls intensity: **values of 40-80 produce pronounced warping that resembles tectonic deformation**, creating meandering valleys and ridgelines that eliminate the uniform appearance of straight fBm. The 3DWorld project demonstrated that domain warping combined with ridged simplex noise creates "endless, varied landscapes" with deep ravines and high peaks—No Man's Sky famously uses this as their "uber noise."

The computational cost is moderate: you're evaluating noise functions multiple times per pixel, but modern vectorized implementations handle this easily. The perlin-numpy library (https://github.com/pvigier/perlin-numpy) provides fast NumPy-vectorized domain warping that processes 4096×4096 heightmaps in seconds on CPU. For C#, FastNoiseLite (https://github.com/Auburn/FastNoiseLite) includes built-in domain warping support with adjustable strength and frequency.

Apply domain warping before erosion simulation. The warping eliminates obvious grid patterns in your base terrain, then erosion simulation adds realistic geological features. This two-stage approach—warped noise followed by physics-based erosion—produces terrain that looks natural at every scale and angle.

---

## Multi-scale generation balances large features with playable flat areas

**Your generator needs different noise frequencies for different purposes**: large-scale features (mountains, valleys, plains) should determine buildability, while small-scale detail adds visual interest only in unbuildable areas. The key is modulating octave amplitudes based on a buildability mask.

Fractal Brownian Motion (fBm) combines multiple noise octaves. Standard parameters are 6-9 octaves, lacunarity of 2.0 (doubling frequency each octave), and persistence of 0.5 (halving amplitude each octave). For Cities Skylines 2's requirements, you should **use only octaves 1-2 with reduced persistence (0.3) in designated buildable zones, but apply full octaves 1-9 with normal persistence (0.5-0.6) in scenic/unbuildable areas**.

Generate a control map first using large-scale Perlin noise (octaves 1-2, frequency 0.001 for a 4096×4096 map). Threshold this to create binary buildable/unbuildable zones—aim for 45-55% buildable to meet CS2's slope constraints. Apply morphological operations (dilation/erosion) to smooth boundaries between zones. Then generate your main heightmap with octave counts and amplitudes modulated by this control map:

```python
for octave in range(octaves):
    freq = base_freq * (lacunarity ** octave)
    amp = base_amp * (persistence ** octave)
    
    if octave > 2 and buildable_mask[x, y]:
        amp *= 0.1  # Reduce high-frequency detail in buildable areas
    
    height += noise(x * freq, y * freq) * amp
```

This approach guarantees flat buildable areas while allowing mountains, cliffs, and valleys for visual interest. The technique is described in detail at https://www.redblobgames.com/maps/terrain-from-noise/ with interactive demonstrations.

The constraint-based approach ensures buildability before adding detail. Academic research by Guérin et al. (2016) on "Sparse Representation of Terrains for Procedural Modeling" (https://hal.science/hal-01258986) demonstrates representing terrain as linear combinations of feature atoms—mountains, valleys, ridges—from a dictionary. You can designate flat "plateau" atoms for buildable areas and mountain/valley atoms for scenic regions, then blend them. This gives precise artistic control while maintaining procedural variety.

---

## River networks require hierarchical generation, not random placement

**Realistic rivers follow watershed physics and hierarchical branching patterns**, not random meandering paths. The Horton-Strahler ordering method creates proper dendritic river systems. Start with river mouths at coastlines or lake edges, then grow the network upstream using priority queues and noise-directed expansion. Leaf tributaries have order 1; when two streams of equal order merge, the downstream segment increases by one order.

The algorithm from Genevaux et al. (SIGGRAPH 2013, https://hal.science/hal-01339224/document) uses Voronoi cell decomposition with noise-controlled growth direction. It runs at 1-3 million triangles per second in JavaScript implementations. Rivers assign thickness based on Strahler numbers—higher order means thicker, more prominent rivers. This creates natural-looking dendritic patterns where small streams converge into major rivers.

For dam-suitable rivers in Cities Skylines 2, you need specific characteristics identified by the community: **both banks significantly elevated (300-400m width valleys), high water sources at mountain elevations, steep elevation gradients along the river path for strong flow, and height differentials of 50-100+ meters between upstream and downstream**. The Rosgen river classification system categorizes rivers by slope and proximity: Type A rivers (mountain streams, steep slopes) work best for dams, while Type C/E rivers (meandering lowland rivers) work for shipping but not hydroelectric power.

The drainage basin growing algorithm from Red Blob Games (https://www.redblobgames.com/x/1723-procedural-river-growing/) implements this efficiently: use Voronoi decomposition, apply noise to control growth direction, ensure downhill-only flow by elevation constraints, and grow from ocean/lake outlets upstream. This guarantees rivers flow physically correctly—always downhill, always to lowest points, no uphill flow errors.

Nick McDonald's Procedural Hydrology system (https://nickmcd.me/2020/04/15/procedural-hydrology/, code at https://github.com/weigert/SimpleHydrology) extends particle-based erosion with stream and pool maps. Water particles that stop moving trigger flood-fill algorithms to create lakes at natural elevation levels. Lakes automatically find drainage points where water exits to continue downstream. This creates cascading lake systems and realistic waterfalls at elevation discontinuities—perfect for dam placement locations.

### Flow accumulation and watershed delineation

Implement the D8 algorithm for flow direction: water flows to the steepest of eight neighboring cells. While simple, it effectively delineates watersheds and calculates drainage area. For each cell, calculate the slope to all eight neighbors: `slope = (height[cell] - height[neighbor]) / distance`. Water flows to the neighbor with maximum slope. The D-Infinity algorithm improves this by dividing flow between two downslope neighbors proportionally, better handling divergent and convergent flow.

Flow accumulation identifies river locations. Start with all cells having accumulation value 1 (the cell itself). Traverse cells from highest to lowest elevation, adding each cell's accumulation to its downslope neighbor. **High accumulation values (10,000+) indicate river locations**; moderate values (100-1,000) suggest streams; low values are hillslopes. This data-driven approach places rivers where physics dictates they should form.

The fast flow accumulation algorithm by Zhou et al. (2018, https://link.springer.com/article/10.1007/s11707-018-0725-9) identifies source cells, interior cells, and intersection cells for efficient traversal. GPU-accelerated FastFlow by Jain et al. (2024, https://onlinelibrary.wiley.com/doi/10.1111/cgf.15243) achieves **34-52× speedup for depression routing on 1024² terrain**, enabling interactive control during generation.

---

## Coastlines need sinuosity detection for natural harbors

Coastlines generated from simple noise thresholds look artificial with straight edges. **Apply multiple techniques to create natural-looking coastlines with bays, harbors, and shipping-friendly features**.

The Voronoi-based island generation by Amit Patel (http://www-cs-students.stanford.edu/~amitp/game-programming/polygon-map-generation/) uses Poisson disc sampling for point distribution, creates Voronoi diagrams, applies noise to polygon edges for organic coastlines, and uses elevation + moisture to determine land/water boundaries. The noisy edge algorithm subdivides coastline quadrilaterals recursively with random offsets, creating fractal coastal detail.

For harbor and bay detection, use the sinuosity method: walk along the coastline and find pairs of points where straight-line distance is much less than coastline distance. Calculate the sinuosity ratio; high values indicate deep bays suitable for harbors. For wide shallow bays, use different distance thresholds. The technique from Dragons Abound (https://gamedev.stackexchange.com/questions/169723/) provides specific implementation guidance.

Multi-scale noise layering enhances coastlines. Apply 6+ octaves of Simplex noise at frequencies 1x, 2x, 4x, 16x, 32x, 64x, but **apply high-frequency detail specifically at the coastline (where elevation ≈ 0)** using formulas like: `e_coast = e + α·(1-e⁴)·(n₄ + n₅/2 + n₆/4)`. This creates detailed, interesting coastlines without adding noise to inland areas.

For shipping in Cities Skylines 2, ensure coastlines have sufficient water depth (below threshold) adjacent to land, gradual depth transitions rather than immediate drop-offs, and protected bays or harbors where sinuosity is high. Community feedback indicates shipping routes need **approach channels at least 8-10 cells wide with consistent depth**.

---

## Cities Skylines 2 demands unprecedented attention to buildable slopes

**This is the most critical finding for your CS2 heightmap generator**: Cities Skylines 2 has severe problems with sloped terrain that CS1 handled gracefully. The community consistently reports that buildings create "ugly steep terrain steps" even on gentle slopes, terrain morphs dramatically and unpredictably when building, and medium-density residential buildings plus larger structures (colleges, high schools) struggle with any slope. One player summarized: "CS1 was more tolerant of terrain slopes and coped much better with automatic flattening... CS2 needs to be flat or players spend hours manually flattening."

Real-world gradient standards provide target values. For plain/rolling areas: 3.3% ruling gradient, 5.0% limiting gradient, 6.7% exceptional gradient. For mountainous areas: 5.0% ruling, 6.0% limiting, 7.0% exceptional. **Your generator should target 0-5% slopes for primary buildable areas, 5-10% for secondary buildable areas (with awareness users will still face issues), and reserve 10%+ slopes for visual interest and unbuildable scenic zones**.

Calculate buildable percentage after generation. Use slope calculation: `slope = arctan(sqrt(dh_dx² + dh_dy²)) × 100%` where dh_dx and dh_dy are height differences to adjacent cells. Count what percentage of your heightmap falls in 0-5% and 5-10% ranges. If you don't achieve 45-55% in the 0-5% range, apply additional smoothing passes to buildable zones.

Gaussian blur with sigma values of 5-10 pixels effectively smooths terrain while maintaining large-scale features. The Smart Blur variant from GIMP/Photoshop preserves edges—blur strength depends on elevation difference between adjacent pixels, so smooth areas get smoothed more while steep cliffs retain sharpness. This prevents smoothing away intentional features like river valleys while eliminating small-scale bumps. Implementation guidance is available at https://gillesleblanc.wordpress.com/2012/08/24/using-gaussian-blurring-on-heightmap/.

Cities Skylines 2 industrial zones especially need flat terrain. Place large flat plateau regions (minimum 500m × 500m) in your buildable zones specifically for industrial development. Use height normalization in these regions: identify target height values (e.g., 100m, 150m, 200m elevation), apply thresholding to force values within ±5m of targets, and use falloff functions to create smooth transitions to surrounding terrain.

---

## Critical implementation resources and code repositories

**For Python development**, use these production-ready libraries. The perlin-numpy library (https://github.com/pvigier/perlin-numpy) provides NumPy-vectorized Perlin noise with fractal fBm support and tileable noise options—by far the fastest pure-Python noise implementation. Install with `pip3 install git+https://github.com/pvigier/perlin-numpy`. For more noise variety, FastNoiseLite's Python wrapper (https://github.com/tizilogic/PyFastNoiseLite) supports OpenSimplex2, Perlin, Value, Cellular noise with domain warping and fractal types including ridged and PingPong. Install via `pip install pyfastnoiselite`.

For erosion simulation in Python, terrain-erosion-3-ways (https://github.com/dandrino/terrain-erosion-3-ways) implements hydraulic simulation, river network generation with Delaunay triangulation, and even machine learning approaches using Progressive GANs. The code is well-documented with academic references and comparison of methods. It exports 512×512 heightmaps but scales to larger resolutions.

**For C# development**, FastNoiseLite (https://github.com/Auburn/FastNoiseLite) is the industry standard—a single-file drop-in (FastNoiseLite.cs) with multiple noise types, fractal types (FBm, Ridged, PingPong), domain warping, and excellent documentation. The live demo at https://auburn.github.io/FastNoiseLite/ lets you preview parameters before implementation. For Unity specifically, SebLague's Hydraulic-Erosion repository (https://github.com/SebLague/Hydraulic-Erosion) provides C# droplet-based erosion with real-time parameter adjustment and before/after visualization. It includes a YouTube tutorial and interactive demo at sebastian.itch.io/hydraulic-erosion.

UnityTerrainErosionGPU (https://github.com/bshishov/UnityTerrainErosionGPU) implements GPU-accelerated hydraulic and thermal erosion using compute shaders. It follows the pipe model with shallow water equations and sediment transport—the same academic foundations as professional tools but in accessible C# code.

**For 16-bit heightmap processing** (CS2's requirement), ImageMagick (https://imagemagick.org/) handles format conversions and depth adjustments. Convert to 16-bit RAW: `convert input.png -colorspace gray -depth 16 GRAY:output.raw`. Resize heightmaps: `convert input.tif -resize 4096x4096 output.png`. Control endianness: `--endian lsb` or `--endian msb`. For C# integration, use Magick.NET (NuGet package Magick.NET-Q16-AnyCPU) which provides full ImageMagick functionality with native ushort (16-bit unsigned) support for programmatic heightmap generation.

The MOOB mod (https://thunderstore.io/c/cities-skylines-ii/p/Cities2Modding/MOOB/) is essential for Cities Skylines 2 heightmap work. It enables map editor access, fixes 16-bit heightmap import/export, provides Windows file dialogs for easier selection, auto-resizes CS1 heightmaps to CS2 scale, and handles 8-bit to 16-bit conversion with anti-terracing blur. The mod is actively developed by the Cities2Modding organization.

**Standalone heightmap generators** worth investigating: wgen (https://github.com/jice-nospam/wgen) is a Rust-based GUI tool that stacks multiple generators (Hills, FBm, MidPoint, Normalize, LandMass, MudSlide, WaterErosion, Island) with 2D/3D preview and exports 16-bit PNG or EXR at any resolution including 4096×4096. The Terrain Height Map Generator (https://terraining.ateliernonta.com/, GitHub: https://github.com/nonta1234/terraining-heightmap-generator) is specifically designed for Cities Skylines, generates from real-world locations using Mapbox API, and outputs correct 4096×4096 at 16-bit with smoothing and noise controls.

---

## CS2 water mechanics introduce critical constraints

Cities Skylines 2's water system has significant limitations that affect heightmap design. **The community consensus is that CS2 water physics are "terrible, actually non-existent compared to CS1"**—water acts like "runny gel" with extremely slow flow rates (half hour+ in-game for water to travel through a canal) and creates backflow and unwanted overflow. Water spawners cannot be removed or hidden, and groundwater reserves hidden under terrain create infinite water sources that cause flooding.

Terrain modifications near water are dangerous. Players report that lowering lake depth can cause massive water rise instead, flattening terrain near underground water reserves causes water to "go bonkers" and form in square shapes, and minor terrain adjustments can flood 1/3 of a city. Water doesn't drain properly without save/reload cycles, and there's no "sponge tool" to remove isolated water pools.

For your heightmap generator, **simplify water features significantly**. Use constant-level water sources for lakes (set to specific heights), border rivers at map edges for river starts, and run water simulation for extended periods (10+ minutes in-editor time) before finalizing the heightmap. Avoid complex groundwater arrangements and intricate water systems that trigger flooding bugs.

For dam-suitable rivers, the CS2 community identifies specific requirements: both sides must be elevated significantly higher than dam roadway (~300-400m valley width), rivers need strong flow (indicated by purple arrows in water overlay), height difference between intake and output sides directly determines power output, and water sources should be placed at high elevation (mountaintops). Generate rivers in steep valleys between elevated terrain with height gradients of 50-100+ meters over short distances.

The technical specifications are confirmed: CS2 requires 4096×4096 resolution, 16-bit grayscale color depth, PNG or TIFF format, and heightmaps placed in `C:/Users/%username%/AppData/LocalLow/Colossal Order/Cities Skylines II/Heightmaps/` (folder name is case-sensitive—must be "Heightmaps" not "heightmaps"). Playable area heightmaps represent 14.336 km with 3.5m per pixel terrain resolution; world map heightmaps represent 57.334 km with 14m per pixel resolution.

---

## Recommended pipeline for CS2 heightmap generation

Synthesizing all research findings, implement this generation pipeline for optimal results.

**Step 1: Generate buildability control map.** Use large-scale Perlin noise with only 1-2 octaves and frequency 0.001 for a 4096×4096 map. Threshold to create binary buildable/unbuildable zones targeting 50% buildable. Apply morphological operations (dilation with 10-pixel radius, then erosion with 8-pixel radius) to create smooth boundaries between zones and consolidate fragmented areas. This ensures large contiguous buildable regions rather than scattered pixels.

**Step 2: Generate base elevation with domain warping.** Apply recursive domain warping following Quilez's formula with strength factor 60. Use ridged noise (`1 - |perlin(x,y)|`) rather than standard fBm for the final evaluation—ridged noise creates natural ridgelines and valley networks. Modulate octave count by buildability mask: buildable zones use only octaves 1-2 with persistence 0.3; unbuildable zones use octaves 1-8 with persistence 0.5. This gives you varied mountainous terrain in scenic areas while keeping buildable areas naturally flatter.

**Step 3: Place river network.** Implement Horton-Strahler hierarchical river generation starting from coastal/lake outlets and growing upstream. Use the drainage basin growing algorithm with noise-directed tree construction. Carve rivers into the heightmap by reducing elevation along river paths—major rivers (Strahler order 5+) carve 20-40m deep valleys, tributaries (order 2-4) carve 5-15m, and streams (order 1) carve 2-5m. Ensure river sources are placed at high elevations (90th percentile of heightmap elevations). For dam-suitable rivers, create narrow valley constrictions (300-400m width) between elevated terrain with 50-100m height drops over 500-1000m distance.

**Step 4: Apply hydraulic erosion.** Run GPU-accelerated pipe model erosion for 500-1000 iterations. Use sediment capacity constant Kc = 0.8 for moderate erosion, erosion rate 0.3, deposition rate 0.3, evaporation rate 0.02, and rain rate 0.0002 (very light continuous rain). Spawn additional particle-based erosion focused on river paths—500 droplets per river segment tracing downhill to deepen valleys and create realistic stream-carved terrain. This eliminates remaining procedural noise patterns and creates natural drainage networks.

**Step 5: Apply thermal erosion.** Run 300-500 iterations of thermal erosion with talus angle 35° and settling rate 0.5. This smooths overly steep slopes, creates scree fields, and prevents unrealistic cliffs while preserving intentional mountain features. Apply heavier thermal erosion specifically in buildable zones (1000 iterations, talus angle 25°) to ensure slopes meet CS2's strict requirements.

**Step 6: Validate and smooth buildable areas.** Calculate slope for every cell: `slope = arctan(sqrt(dh_dx² + dh_dy²)) × 100%`. Measure what percentage falls in 0-5% range. If below 45%, identify buildable-designated cells with slopes exceeding 5% and apply targeted Gaussian blur with sigma = 8 pixels. Repeat validation; if still insufficient, increase blur radius to 12 pixels and iterate. Use Smart Blur to avoid smoothing away river valleys and coastlines.

**Step 7: Generate coastlines and harbors.** Apply multi-scale noise specifically to coastline cells (elevation within 5m of sea level). Use 4 additional octaves of high-frequency noise (32x, 64x, 128x, 256x base frequency) with amplitude 2m to create detailed coastal features. Run sinuosity detection to identify natural harbor locations—pairs of coastline points where straight-line distance is 30-50% of coastline distance indicate bays suitable for shipping. Ensure harbor entrances have consistent water depth and 8-10 cell width channels.

**Step 8: Export at correct specifications.** Convert heightmap to 16-bit unsigned integer (0 = lowest point in your map, 65535 = highest point). For CS2's default 4096m height scale: `pixel_value = (height_in_meters / 4096.0) × 65535`. Export as 4096×4096 PNG or TIFF with 16-bit grayscale color depth. Generate matching world map heightmap at same resolution where the center 1024×1024 region exactly matches the scaled-down playable heightmap. Save to the CS2 Heightmaps folder with correct capitalization.

---

## Academic foundations and further reading

The terrain generation techniques described here build on decades of computer graphics research. Musgrave et al. (1989) pioneered physically-based erosion for terrain synthesis. Prusinkiewicz & Hammel (1993) introduced L-systems for river networks in fractal landscapes. The GPU era brought interactive erosion: Mei et al. (2007) demonstrated fast hydraulic erosion and visualization on GPU using the pipe model (https://inria.hal.science/inria-00402079/document), while Št'ava et al. (2008) enabled interactive terrain modeling with hydraulic erosion.

Modern methods from the last decade provide the most relevant techniques. Guérin et al. (2016) introduced sparse representation of terrains using dictionary-based landform atoms (https://hal.science/hal-01258986). Cordonnier et al. (2016) developed large-scale terrain generation from tectonic uplift and fluvial erosion, working in uplift domain rather than elevation domain for interactive authoring (https://inria.hal.science/hal-01262376/file/2016_cordonnier.pdf). Genevaux et al. (2013) published comprehensive research on terrain generation using procedural models based on hydrology with river-first approaches (https://hal.science/hal-01339224/document).

Recent advances in 2024 include Schott et al.'s terrain amplification using multi-scale erosion (https://dl.acm.org/doi/10.1145/3658200) and Jain et al.'s FastFlow GPU acceleration achieving 34-52× speedup for depression routing (https://onlinelibrary.wiley.com/doi/10.1111/cgf.15243). Machine learning approaches show promise: Panagiotou & Charou (2020) demonstrated procedural 3D terrain generation using GANs (https://arxiv.org/abs/2010.06411), though these methods lack the physical consistency of simulation-based approaches.

The unofficial Cities Skylines 2 Maps Wiki (https://shankscs2.github.io/cs2-maps-wiki/) provides comprehensive tutorials including QGIS workflows for professional heightmap creation from USGS DEM data, with detailed guidance on bathymetry integration, stream burning, and lake burning techniques. The official Paradox map editor documentation (https://www.paradoxinteractive.com/games/cities-skylines-ii/modding/dev-diary-2-map-editor) confirms technical specifications and editor capabilities.

---

## Key recommendations for immediate implementation

Start with the highest-impact changes that address your current problems. **Implement domain warping immediately**—this single technique eliminates the most obvious procedural patterns with minimal code changes. Use the perlin-numpy or FastNoiseLite libraries which include domain warping support. Apply strength factor 40-80 before your main noise evaluation.

**Add constraint-based generation** to guarantee buildable areas. Generate a buildability control map first, then modulate your noise parameters based on this mask. This ensures 45-55% of terrain meets CS2's slope requirements rather than hoping random noise produces usable terrain.

**Integrate hydraulic erosion** as a post-processing step. Even a simple particle-based implementation with 50,000 droplets will dramatically improve realism. The terrain-erosion-3-ways Python code or SebLague's C# implementation provide ready-to-use starting points. Run erosion after initial noise generation but before final smoothing.

**Implement proper river generation** using flow accumulation. Calculate slope-based flow direction for every cell, accumulate drainage area, and place rivers where accumulation exceeds thresholds (10,000+ cells). Carve river valleys by reducing elevation along river paths. This replaces random river placement with physically-based water routing.

**Add buildability validation** to your export process. Calculate slope for every cell and measure what percentage falls in 0-5%, 5-10%, and 10%+ ranges. Display these statistics to users. If buildable percentage is insufficient, automatically apply targeted Gaussian blur to reduce slopes in designated flat areas.

For water features suitable for Cities Skylines 2 gameplay, prioritize simplicity over complexity. Generate 2-4 major rivers with clear valley constrictions for dam placement rather than intricate drainage networks. Create simple coastal regions with identified harbor locations rather than complex archipelagos. Remember that CS2's water physics are problematic—simpler water features create fewer gameplay issues.

The technical implementation order matters. Generate base terrain with domain-warped noise, apply constraint-based octave modulation, place rivers using flow accumulation, run hydraulic erosion simulation, apply thermal erosion for slope smoothing, validate and enhance buildable areas with targeted smoothing, add coastline detail, and finally export at 16-bit precision. This sequence ensures each step enhances rather than undoes previous work.

Testing with real Cities Skylines 2 imports is essential. The MOOB mod enables proper 16-bit import/export and should be your first installation. Import your heightmaps iteratively—generate, import to CS2, test building placement on various terrain types, identify problem areas, adjust generation parameters, and repeat. The CS2 community on Steam discussions and the Cities: Skylines Modding Discord provide feedback on heightmap quality and can identify issues you might miss.

---

## Conclusion: From procedural noise to playable geography

The path from "obvious noise-pattern artifacts" to "realistic, interesting, and buildable terrain" requires combining multiple techniques in thoughtful sequence. **Domain warping eliminates grid-aligned patterns, hydraulic erosion creates geographically plausible features through physical simulation, constraint-based generation guarantees playable flat areas, and proper river networks follow natural drainage physics**. Cities Skylines 2's heightmap requirements—4096×4096 at 16-bit precision—provide sufficient resolution for these techniques to shine. The game's severe slope sensitivity demands unprecedented attention to buildability, but this constraint actually improves map quality by forcing deliberate design of flat buildable zones contrasted with dramatic unbuildable mountains and valleys.

The most successful approach integrates artistic intent with procedural variety. Generate control maps that define where cities should thrive (flat areas) and where nature should dominate (mountains, water). Let physics-based erosion and river generation create realistic details within these boundaries. This philosophy—using constraints to guide rather than limit procedural generation—produces terrain that serves gameplay while maintaining visual interest and geological plausibility.

Your existing CS2_MapCreator repository provides the foundation. Adding domain warping, erosion simulation, constraint-based buildability zones, and hierarchical river networks will transform it from generating unusable bumpy terrain to creating playable, realistic maps worthy of the Cities Skylines 2 community. The resources documented here—FastNoiseLite for noise, hydraulic erosion implementations in both Python and C#, ImageMagick for 16-bit processing, and the MOOB mod for CS2 integration—provide everything needed for implementation. The result will be heightmaps where every terrain feature exists for a reason: flat areas for cities, valleys carved by ancient rivers perfect for dams, coastal bays naturally suited for harbors, and mountains that frame rather than obstruct gameplay.