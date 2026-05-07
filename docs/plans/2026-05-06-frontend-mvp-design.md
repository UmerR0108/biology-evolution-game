# Frontend MVP — Design

**Date:** 2026-05-06
**Status:** Approved, pending implementation plan
**Scope:** First playable build — single Pygame window with side-by-side world view and live allele-frequency chart for the guppy species under predator pressure.

## Goals

- Make evolution visible: a watcher sees creatures change appearance across generations, with a chart that reflects the underlying allele frequencies.
- Reuse the existing `evogame.genetics` engine without modification.
- Stay within the spec's MVP line: 1 biome, 1 species (guppy), 3-4 genes, 1 toggleable selection pressure (predator).

## Non-goals (YAGNI)

No catching/foraging, no habitat sliders beyond the predator toggle, no temperature/salinity/substrate, no other species, no save/load, no field journal export, no swimming animation, no sexual selection model, no speciation tracker. These are deferred to later slices.

## Architecture

One Pygame process, one window, two panels plus a HUD bar:

```
+-----------------------------------------------------+
|  HUD: gen# | speed slider | predator toggle | pause |
+----------------------------+------------------------+
|                            |                        |
|  WORLD PANEL               |  CHART PANEL           |
|  (guppies as colored dots) |  (allele freq lines)   |
|                            |                        |
+----------------------------+------------------------+
```

The render loop runs at ~60 FPS for input responsiveness. A separate generation timer fires every `1 / speed` seconds and advances the simulation by exactly one generation. The chart panel only re-renders its matplotlib figure when the timer ticks (cheap).

## Components

### New

- **`evogame.sim.population.Population`** — list of `Creature`, methods: `step_generation(pressure)`, `allele_frequencies()`, `__len__`.
- **`evogame.sim.pressure.PredatorPressure`** — `fitness(creature) -> float`. Red phenotype low fitness when predator on; white high; pink intermediate. White carries a small fitness cost when predator off (less mate appeal) so the predator toggle creates a genuine trade-off rather than a one-way ratchet.
- **`evogame.sim.recorder.GenerationLog`** — append-only record of `{gen, allele_counts, predator_on, population_size}`.
- **`evogame.ui.world_panel.WorldPanel`** — draws pond background + each creature as a circle (color = color phenotype, radius = body_size phenotype). Positions deterministic from creature index for v1.
- **`evogame.ui.chart_panel.ChartPanel`** — owns a matplotlib `Figure` + `FigureCanvasAgg`, renders to an RGBA buffer, blits as a pygame `Surface`. Redraws only when log length changes.
- **`evogame.ui.hud.HUD`** — predator checkbox, speed slider (0.5–5 gen/sec), pause button, generation counter, population counter, extinction banner.
- **`evogame.ui.app.App`** — owns everything, runs the main loop, dispatches events.
- **`scripts/run_game.py`** — entrypoint: `python scripts/run_game.py`, mirroring `breed_demo.py`.

### Reused unchanged

- `evogame.genetics.creature.Creature` (has `breed`)
- `evogame.genetics.species.guppy.GUPPY_SCHEMA`
- `evogame.genetics.phenotype` (already maps genotype → display traits)

## Data flow per frame

```
input events → HUD state (predator on/off, paused, speed)
     │
generation timer expired and not paused?
     │  yes
     ├─ Population.step_generation(PredatorPressure)
     │     1. fitness[i] for each creature
     │     2. sample 2N parents weighted by fitness (with replacement)
     │     3. pair them, breed → next generation (size capped at carrying capacity)
     │     4. if len == 0 → mark extinction
     ├─ GenerationLog.record(gen, allele_freqs, predator_on, size)
     └─ ChartPanel.invalidate()
     │
render:
     ├─ WorldPanel.draw(creatures)
     ├─ ChartPanel.draw()  (uses cached surface unless invalidated)
     └─ HUD.draw()
```

**Starting population:** 30 random guppies, alleles drawn uniformly from each gene's allele set.
**Carrying capacity:** 60.

## Error handling

- **Extinction** (population reaches 0): sim freezes, "EXTINCT — gen N" overlays the world panel, chart remains visible. The pause button becomes "Restart" and re-seeds the population.
- **Allele fixation**: chart line flattens at 1.0 — falls out of normal rendering, no special case.
- **New mutant allele**: `allele_frequencies()` returns a dict keyed by allele symbol; the chart auto-adds a line for any unseen key on the next redraw.
- **HUD inputs**: clamped to valid ranges in the UI layer so the sim never sees bad input.
- **Missing matplotlib**: hard fail at startup with a clear message pointing to `pip install -e ".[dev]"`.

## Testing

- `tests/test_predator_pressure.py` — fitness ordering for red/pink/white × predator-on/off.
- `tests/test_population.py` — `step_generation` respects carrying capacity, returns size 0 with empty input, allele frequencies sum to 1.0 per gene.
- `tests/test_generation_log.py` — records grow monotonically, frequencies retrievable.
- `tests/test_app_smoke.py` — boot the app with `SDL_VIDEODRIVER=dummy`, run 5 generations, assert generation count incremented and no exception. No pixel asserts.
- All existing genetics tests remain untouched and passing.

## Dependencies added

- `pygame` (runtime)
- `matplotlib` (runtime — already common, but add explicitly to `pyproject.toml`)

Both pinned to current major versions in `pyproject.toml`.

## Open questions for implementation

- Predator fitness curve shape (linear vs. step) — pick simplest that produces visible separation in tests, document the choice in `PredatorPressure`.
- Slider widget: roll a tiny one in pygame primitives or use `pygame_gui`. Prefer rolling a minimal one to avoid the dep unless it costs more than ~30 lines.
