# Evolution Simulation Game — Project Spec

## Project Context
This is an AP Biology class project. The game must demonstrate core evolution concepts through interactive gameplay. Grading priority is on the **biology accuracy and simulation logic**, not graphics polish.

## Core Concept
A 2D top-down game where the player runs a research field station. They catch creatures from the wild, build custom habitats, grow crops to feed them, and watch populations evolve across generations as the player controls selection pressures.

## Core Gameplay Loop
1. **Forage/fish** in different biomes to catch starter creatures with varied traits
2. **Build habitats** with adjustable conditions (temperature, salinity, predators, substrate, vegetation)
3. **Grow crops** in farm plots — crop type determines food shape/size, selecting for matching mouth/beak adaptations
4. **Speed up time** to watch generations turn over
5. **View the DNA panel** showing allele frequencies, mutations, and trait expression over time

## Species Roster (4 total)

### 1. Guppy-style fish (water habitat)
- **Genes:** color, body size, fin length, temperature tolerance
- **Teaches:** sexual selection, predator-driven selection
- **Reference:** Trinidadian guppies (real textbook case)

### 2. Beetle (land habitat)
- **Genes:** shell color, body size, mouth shape
- **Teaches:** camouflage selection, disruptive selection via crop choice
- **Notes:** short generations = fast visible evolution

### 3. Bird (flies between land habitats)
- **Genes:** beak size/shape, body size, feather color
- **Teaches:** adaptive radiation (Darwin's finches)
- **Notes:** different beak shapes for different seed sizes

### 4. Snail (amphibious — water or land)
- **Genes:** shell pattern, shell thickness, size
- **Teaches:** genetic drift (small populations, slow reproduction)
- **Notes:** intentionally low selection pressure so drift dominates

## Genetics System

Each creature has 6-8 genes. Each gene has 2 alleles (one from each parent).

**Inheritance patterns to include:**
- Simple dominant/recessive (most genes)
- Incomplete dominance (e.g., color: RR red, WW white, RW pink)
- Multiple alleles (e.g., camouflage: C1, C2, C3)
- Polygenic traits (e.g., speed = sum of 2-3 genes for continuous variation)

**Mutation:** low rate per reproduction event, mostly neutral, occasionally introduces new alleles.

## Selection Math

Each generation, each creature gets a fitness score:

```
fitness = base_survival 
  × temperature_match(T_allele, habitat_temp)
  × camouflage_match(C_allele, habitat_substrate)
  × food_access(M_allele, available_crops)
  × predator_evasion(speed_genes, predator_present)
```

Fitness = probability of surviving to reproduce. Mate selection can be random or trait-based (sexual selection). Offspring inherit one allele per gene from each parent, with small mutation chance.

**Track allele frequencies in the population each generation. Plot on a graph the player can view.**

## Habitat Variables
Player-adjustable sliders/modules:
- Water temperature
- Salinity
- Substrate color (sand/rock/coral)
- Predator presence and type
- Vegetation density
- Day/night cycle length
- Population carrying capacity

Each variable ties to a gene.

## Crop & Feeding System
Crops have shape and size traits. Wide-mouth fish eat large round crops efficiently; narrow-mouth fish eat small thin crops. Growing one crop type selects for matching mouths. Growing two types in same habitat triggers disruptive selection.

## Speciation Mechanic
Track genetic distance between populations. When two isolated populations diverge past a threshold, they can no longer interbreed even if reunited. Trigger "Speciation event!" notification and add new species to field guide.

## AP Bio Concepts the Game Demonstrates
- Natural selection (beetle camouflage)
- Sexual selection (guppy coloration)
- Adaptive radiation (bird beaks across habitats)
- Genetic drift (snails)
- Disruptive selection (beetles with two crop types)
- Speciation (any species split across isolated habitats)
- Predator-prey coevolution (birds and beetles)
- Hardy-Weinberg equilibrium (baseline the game tracks)
- Founder effect (small starter populations)

## MVP Scope (build this first)
- 1 biome, 1 species with 3-4 genes
- Catch, breed, observe loop working
- Allele frequency graph that updates per generation
- One toggleable selection pressure (predator or temperature)

Then expand to additional species and biomes as time allows.

## Tech Stack
**Recommended:** Python with Pygame, OR Godot (GDScript), OR JavaScript with HTML5 Canvas.
Pick based on what the developer is most comfortable with. Python/Pygame is simplest for a school project.

## Art Assets
Using free CC0 assets from OpenGameArt.org, itch.io, or Flaticon. NOT pixel art — clean illustrated/vector style. Trait variations done via color tinting in code (palette swaps), which mirrors real pigmentation genetics.

## Key Implementation Priorities
1. **Genetics engine first** — get inheritance, mutation, and allele tracking working before anything visual
2. **Reusable creature system** — same code handles all 4 species, just different gene definitions
3. **Allele frequency graph** — this is the centerpiece evidence of evolution working
4. **Field journal** — auto-fills as discoveries happen, doubles as project writeup material

## Field Journal Feature
Auto-logs events: "First mutation observed," "Allele X reached fixation," "Speciation event," "Population crash," etc. Player can export this as the basis for their project writeup.
