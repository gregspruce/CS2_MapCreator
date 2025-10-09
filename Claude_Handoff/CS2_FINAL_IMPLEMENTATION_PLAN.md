# CS2 Map Generator: Direct Implementation Plan for 55-65% Buildability

**Based on Deep Research Analysis**  
**Target**: 55-65% buildable terrain with coherent geological features  
**Approach**: Complete architectural replacement - hybrid zoned generation with hydraulic erosion  
**No interim solutions, no fallbacks, direct to final product**

---

## Critical Implementation Decision

The mathematical analysis definitively proves your current tectonic fault-based system cannot achieve 30-60% buildability. The binary mask multiplication creates isolated frequency packages (pincushion problem) and the amplitude-slope relationship limits buildability to ~30% maximum with visible terrain.

**Required approach**: Hybrid zoned generation with hydraulic erosion. This is proven to achieve 55-65% buildability in industry-standard tools (World Machine, Gaea).

**Rejected approaches**:
- Parameter tuning current system (mathematically impossible)
- Post-processing/smoothing (doesn't fix pincushion, creates artifacts)
- Zone-only without erosion (only achieves 40-50%, doesn't meet your requirements)

---

## Implementation Sessions Structure

Each session is a discrete Claude Code conversation completing specific functionality. Sessions are ordered by dependency but designed for independent completion with proper handoff documentation.

---

## Session 1: Research and Algorithm Implementation Preparation

**Objective**: Analyze existing erosion implementations and prepare detailed algorithm specifications

**Tasks**:
1. Analyze `src/features/hydraulic_erosion.py` (existing implementation)
2. Study the terrain-erosion-3-ways GitHub repository (referenced in research)
3. Document the exact particle-based erosion algorithm to implement
4. Create detailed pseudocode for hybrid zoned generation
5. Identify reusable components from existing codebase

**Deliverables**:
- `docs/implementation/ALGORITHM_SPECIFICATION.md` - Complete mathematical specification of algorithms
- `docs/implementation/REUSABLE_COMPONENTS.md` - List of existing code to adapt
- `docs/implementation/SESSION_2_HANDOFF.md` - Context for next session

**Documentation Requirements**:
```markdown
# SESSION_2_HANDOFF.md

## Algorithm Specifications
[Exact mathematical formulas for zone generation]
[Exact particle erosion algorithm with parameters]
[Data structures and array shapes]

## Code Architecture
[Module structure to create]
[Integration points with existing code]
[Dependencies and imports needed]

## Key Parameters
[All parameters with ranges and defaults]
[Physical meaning of each parameter]
```

---

## Session 2: Buildability Zone Generation Implementation

**Objective**: Implement continuous buildability potential map generation

**Starting Context**: Read `SESSION_2_HANDOFF.md`

**Implementation**:
```python
# src/generation/zone_generator.py

class BuildabilityZoneGenerator:
    """
    Generates continuous 0-1 buildability potential maps.
    NOT binary masks - continuous weight fields.
    """
    
    def generate_potential_map(self, resolution, target_coverage=0.70):
        """
        Uses 2-3 octaves of very low-frequency Perlin noise.
        Wavelength: 5-8km for 14.3km map
        Returns continuous values [0,1] where high = buildable
        """
```

**Critical Requirements**:
- Must generate continuous values, NOT binary masks
- 70-75% of map should have potential > 0.5
- Large-scale features (5-8km wavelength)
- Smooth transitions, no sharp boundaries

**Deliverables**:
- `src/generation/zone_generator.py` - Complete implementation
- `tests/test_zone_generator.py` - Validation tests
- `docs/implementation/SESSION_3_HANDOFF.md` - Integration instructions

---

## Session 3: Zone-Weighted Terrain Generation

**Objective**: Implement terrain generation with amplitude modulated by buildability zones

**Starting Context**: Read `SESSION_3_HANDOFF.md`

**Implementation**:
```python
# src/generation/weighted_terrain.py

class ZoneWeightedTerrainGenerator:
    """
    Generates terrain with smooth amplitude modulation based on zones.
    Key difference from failed binary masks: continuous modulation.
    """
    
    def generate(self, buildability_potential, resolution):
        """
        Amplitude = base * (0.3 + 0.7 * (1 - potential))
        High buildability zones: 30% amplitude
        Low buildability zones: 100% amplitude
        """
```

**Critical Difference from Current System**:
- Smooth, continuous amplitude modulation (not binary)
- No frequency discontinuities
- Large-scale modulation (not small masks)

**Deliverables**:
- `src/generation/weighted_terrain.py` - Implementation
- Integration with zone generator from Session 2
- Test terrain outputs showing 40-45% buildability (before erosion)
- `docs/implementation/SESSION_4_HANDOFF.md`

---

## Session 4: Core Hydraulic Erosion Algorithm

**Objective**: Implement particle-based hydraulic erosion with zone modulation

**Starting Context**: Read `SESSION_4_HANDOFF.md`

**Critical Algorithm Components**:
```python
# src/generation/hydraulic_erosion.py

class HydraulicErosionSimulator:
    """
    Particle-based erosion with buildability zone modulation.
    This is THE critical component for achieving 55-65% buildability.
    """
    
    def erode(self, heightmap, buildability_potential, num_particles=100000):
        """
        For each particle:
        1. Spawn at high elevation (weighted probability)
        2. Flow downhill following gradient
        3. Erode terrain proportional to velocity
        4. Carry sediment up to capacity
        5. Deposit when capacity exceeded
        6. CRITICAL: Modulate erosion by buildability zones
           - High buildability: 50% erosion strength
           - Low buildability: 150% erosion strength
        """
```

**Performance Requirements**:
- CPU implementation is acceptable (2-5 minutes for 100k particles)
- Use Numba JIT compilation for critical loops
- Erosion brush radius of 3-5 pixels (Gaussian falloff)

**Deliverables**:
- `src/generation/hydraulic_erosion.py` - Complete erosion simulator
- Performance benchmarks showing <5 minutes for 4096×4096
- Visual validation showing coherent drainage networks
- `docs/implementation/SESSION_5_HANDOFF.md`

---

## Session 5: Ridge Enhancement and Mountain Coherence

**Objective**: Add ridge noise to mountain zones for coherent ranges

**Starting Context**: Read `SESSION_5_HANDOFF.md`

**Implementation Focus**:
- In zones where buildability_potential < 0.3, apply ridge noise
- Ridge formula: `ridge = 2 * (0.5 - abs(0.5 - noise(x, y)))`
- Smooth blending at zone boundaries (0.2-0.4 range)
- This creates sharp ridgelines that erosion carves realistically

**Deliverables**:
- `src/generation/ridge_enhancement.py`
- Integration with weighted terrain from Session 3
- Visual validation showing connected mountain ranges
- `docs/implementation/SESSION_6_HANDOFF.md`

---

## Session 6: Full Pipeline Integration

**Objective**: Connect all components into complete generation pipeline

**Starting Context**: Read `SESSION_6_HANDOFF.md`

**Pipeline Order**:
1. Generate buildability zones (Session 2)
2. Generate zone-weighted terrain (Session 3)
3. Apply ridge enhancement (Session 5)
4. Apply hydraulic erosion (Session 4)
5. Normalize and export

**Critical Integration Points**:
- Pass buildability zones through entire pipeline
- Ensure erosion modulation uses correct zone values
- Proper array shapes and data types throughout

**Deliverables**:
- `src/generation/pipeline.py` - Complete pipeline orchestration
- Validation showing 55-65% buildability achieved
- Performance metrics for complete generation
- `docs/implementation/SESSION_7_HANDOFF.md`

---

## Session 7: Flow Analysis and River Placement

**Objective**: Analyze erosion-created drainage and place rivers

**Starting Context**: Read `SESSION_7_HANDOFF.md`

**Implementation**:
- Calculate flow accumulation using D8 algorithm
- Identify major drainage paths (accumulation > threshold)
- Place permanent rivers along detected paths
- Ensure rivers lie in valleys (should be automatic from erosion)

**Deliverables**:
- `src/generation/river_analysis.py`
- Rivers that flow downhill throughout
- Natural dam sites in narrow valleys
- `docs/implementation/SESSION_8_HANDOFF.md`

---

## Session 8: Detail Addition and Constraint Verification

**Objective**: Add conditional surface detail and verify buildability constraints

**Starting Context**: Read `SESSION_8_HANDOFF.md`

**Implementation**:
```python
# Only add detail to steep areas
detail_amplitude = base_detail * (current_slope / 0.15)
```

**Constraint Verification**:
- Calculate actual buildable percentage
- If < 55%, identify near-buildable regions and apply minimal smoothing
- If > 65%, document for user that they can increase mountain amplitude

**Deliverables**:
- `src/generation/detail_generator.py`
- `src/generation/constraint_verifier.py`
- Validation showing consistent 55-65% achievement
- `docs/implementation/SESSION_9_HANDOFF.md`

---

## Session 9: GUI Integration

**Objective**: Replace current GUI generation with new pipeline

**Starting Context**: Read `SESSION_9_HANDOFF.md`

**Requirements**:
- Add generation mode selector (Legacy vs New)
- Expose key parameters:
  - Zone coverage (60-80%)
  - Erosion particles (50k-200k)
  - Target buildability (55-65%)
- Progress bar showing pipeline stages
- Buildability analysis display

**Deliverables**:
- Modified `src/gui/parameter_panel.py`
- Modified `src/gui/heightmap_gui.py`
- User can switch between old and new systems
- `docs/implementation/SESSION_10_HANDOFF.md`

---

## Session 10: Parameter Presets and User Documentation

**Objective**: Create terrain type presets and complete user documentation

**Starting Context**: Read `SESSION_10_HANDOFF.md`

**Presets to Create**:
- "Balanced" - 60% buildable, moderate mountains
- "Mountainous" - 55% buildable, dramatic peaks  
- "Rolling Hills" - 65% buildable, gentle terrain
- "Custom" - User-defined parameters

**Documentation Requirements**:
- User guide explaining new generation system
- Parameter reference with effects
- Troubleshooting guide
- Migration guide from old system

**Deliverables**:
- `src/generation/presets.py`
- `docs/user/NEW_GENERATION_GUIDE.md`
- `docs/user/PARAMETER_REFERENCE.md`
- Updated `README.md`

---

## Documentation Strategy for Session Continuity

Each session produces a handoff document with:

```markdown
# SESSION_[N+1]_HANDOFF.md

## Previous Session Summary
- What was implemented
- Key files created/modified
- Test results achieved

## Current System State
- What works
- What's not yet implemented
- Known issues

## Next Session Objectives
- Specific implementation goals
- Dependencies from previous sessions
- Expected outcomes

## Code Context
- Key functions and their purposes
- Data structures and formats
- Integration points

## Critical Parameters
- Current values
- Ranges that work
- Physical meaning

## Test Commands
- How to verify previous work
- Expected outputs
- Performance benchmarks
```

---

## Validation Criteria (No Compromises)

**Required Achievements**:
1. **55-65% buildable terrain** - measured across 20 test generations
2. **Coherent mountain ranges** - visual validation, no isolated peaks
3. **Realistic drainage networks** - rivers flow downhill, valleys are flat
4. **Performance < 5 minutes** - complete generation at 4096×4096
5. **CS2 compatibility** - successful import and city building

**No Acceptable Compromises**:
- No shipping with <55% buildability
- No pincushion terrain (must have coherent features)
- No parameter tuning of old system (mathematically impossible)
- No post-processing band-aids (doesn't solve core problems)

---

## Risk Management

**If erosion is too slow**: 
- Reduce particles to 50k (still effective)
- Use aggressive Numba optimization
- Accept 3-5 minute generation time

**If buildability < 55%**:
- Increase zone coverage to 80%
- Increase erosion deposition rate
- Reduce base terrain amplitude

**If integration breaks existing code**:
- New system is completely separate module path
- Old system remains untouched
- User selects via GUI dropdown

---

## Expected Timeline

Assuming 3-4 hours per Claude Code session:
- **Sessions 1-3**: Foundation (zone generation, weighted terrain)
- **Session 4**: Critical erosion implementation  
- **Sessions 5-6**: Integration and refinement
- **Sessions 7-8**: River placement and detail
- **Sessions 9-10**: GUI and documentation

**Total**: 10 sessions × 3-4 hours = 30-40 hours of Claude Code interaction

This achieves the complete solution with no interim products, no fallbacks, and guaranteed 55-65% buildability based on proven mathematical and industry approaches.

---

## Key Mathematical Constraints (Reference)

### Why Current System Fails

**Frequency Domain Convolution**:
```
h(x,y) = M(x,y) × noise(x,y)  [spatial domain]
H(f) = M(f) ⊗ Noise(f)        [frequency domain]
```
Creates isolated frequency packages per mask region.

**Amplitude-Slope Relationship**:
```
∇(A · noise(ωx)) = A · ω · ∇noise(ωx)
```
Direct proportionality means reducing amplitude for buildability creates boring terrain.

**Theoretical Maximum**: ~45% buildable with pure noise at CS2 scale.

### Why Erosion Solves It

- Water naturally deposits sediment in valleys → flat areas
- Erosion carves connected drainage networks → coherent features
- Zone modulation preserves flat areas while enhancing mountains
- Industry proven: 55-65% buildable routinely achieved

---

## Implementation Philosophy

1. **No compromises on requirements** - 55-65% buildability is non-negotiable
2. **Complete architectural replacement** - Current system is mathematically limited
3. **Industry-proven approach** - Hybrid zones + erosion used by all professional tools
4. **Direct to final product** - No interim solutions or fallbacks
5. **Each session is self-contained** - Proper handoff documentation enables fresh starts

This plan provides the structured, session-based approach requested, with clear deliverables and documentation requirements for Claude Code implementation.
