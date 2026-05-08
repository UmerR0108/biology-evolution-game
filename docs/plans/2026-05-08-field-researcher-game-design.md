# Field Researcher Game — Design

**Date**: 2026-05-08
**Status**: Approved, ready for implementation plan
**Supersedes**: portions of `2026-05-06-frontend-mvp-design.md` related to the world-panel rendering

## Problem

The current build is a sim viewer: split screen of a colored-dot grid (left) and an allele-frequency chart (right) with a HUD bar of widgets on top. It does not feel like a game — there is no character, no animal visuals, no animations, no world to walk through. `PROJECT_SPEC.md` already calls for "a 2D top-down game where the player runs a research field station" — the existing UI skipped that and went straight to the sim view.

The user's reference image is a top-down forest pixel-art aesthetic. The original spec's "NOT pixel art" line is overridden.

## Goals

1. The player walks around a 2D top-down forest scene as a character.
2. Animals are visible as pixel-art sprites that move around.
3. The existing genetics engine, sim controller, recorder, and chart code are preserved unchanged.
4. The allele-frequency chart and selection-pressure controls remain accessible — they are the centerpiece evidence of evolution working — but live behind a diegetic interaction (a research cottage) so they don't crowd the world.

## Non-goals (deferred)

- Scrolling camera / multi-screen world
- Multiple habitats (only the pond ships in MVP)
- Catching, breeding-by-hand, crops, releasing creatures
- Additional species (beetle/bird/snail)
- Day/night cycle, save/load, sound

## Key decisions (from brainstorming)

| Decision | Choice |
|---|---|
| Player role | Field researcher (walk around, observe) |
| Creature presence | Sample sprites in habitat + abstract larger sim population |
| World scope | Forest with 2-3 habitats (target); MVP ships **1 habitat** + ambient wildlife |
| Art source | Three local asset packs: `free version` (tileset), `NewRiverFishAssetPack1.0` (fish), `MinifolksForestAnimals` (animals) |
| HUD/chart placement | Walk to research cottage, press E, opens journal overlay |
| Architecture | Approach A — replace `WorldPanel` only; keep sim/genetics/chart untouched |

## Architecture

### Module layout

Existing packages **untouched**: `evogame.genetics`, `evogame.sim`. Their tests must stay 100% green.

`evogame.ui` package changes:

| Module | Status | Purpose |
|---|---|---|
| `app.py` | modified | Wires scene, player input, sim tick clock, journal overlay |
| `world_panel.py` | rewritten | Scene renderer (tilemap + sprite layers + interaction prompt) |
| `chart_panel.py` | unchanged | Embedded inside the journal overlay |
| `widgets.py` | unchanged | Toggle/Slider/Button reused inside the journal |
| `hud.py` | repurposed | Becomes the thin top status strip (Gen / Pop / Speed). Old HUD widgets move into the journal. |
| `assets.py` | new | Loads tileset, fish sheet, animal sheets, character sprite. Slices into named surfaces. |
| `tilemap.py` | new | Forest scene: 2D grid of tile IDs + list of placed objects (cottage, trees) at fixed positions |
| `player.py` | new | Player position, velocity, sprite, optional 4-direction walk animation |
| `wildlife.py` | new | Ambient wandering animals with simple wander state machine |
| `pond.py` | new | Visible-fish manager: samples from `sim.population.creatures`, owns each fish's screen pos/vel, tints by phenotype |
| `journal.py` | new | Overlay panel; embeds `ChartPanel` and the existing HUD widgets |

### Data flow

```
keyboard input ──► app._handle_events ──┬─► player.handle_input
                                        └─► journal.handle_event (when open)
                                        └─► hud_widgets.handle_event (inside journal)

clock tick (60fps) ──► app.step_one_frame ──┬─► sim.tick (every 1/speed seconds)
                                            ├─► player.update
                                            ├─► wildlife.update
                                            ├─► pond.update (samples + drifts visible fish)
                                            └─► render: tilemap → wildlife → pond fish → player → cottage prompt → journal-if-open → status strip
```

The sim continues to tick on the same time-based clock as today (`SimController.tick()` driven by `slider.value` generations/sec). The slider lives inside the journal now.

## World

Single non-scrolling scene at the existing 1000×620 window.

- Top 24 px: thin status strip (Gen / Pop / Speed).
- Remaining 1000×596: forest scene.
- Tile size: from the `free version` tileset (likely 16×16) rendered at 2× = 32 px effective. Playfield ≈ 30×18 tiles.

Scene composition:
- Grass tiles fill the background.
- 4–6 tree sprites placed at fixed positions for visual interest and as soft obstacles.
- One pond region built from water tiles. The pond's interior cells form a polygon used for fish movement bounds.
- One cottage object (using a sprite from `free.png`) at a fixed position; doubles as the research desk.

## Player

- WASD or arrow keys for 4-directional movement (~120 px/sec).
- Hard bounds clamped to the scene rectangle.
- Soft collision: cannot walk onto water tiles or onto the cottage footprint.
- E key: interact when in range of the cottage → open journal.
- J key: open/close journal from anywhere.
- Walk animation: only if the character sprite has 4-direction frames; verified during implementation. If the sprite is single-frame, MVP ships with a static sprite — no fake walk.

## Pond and fish

- Pond region precomputed from water-tile coords at scene load.
- Visible fish count: 8–12. Sampled from `sim.population.creatures` once per generation tick (deterministic with the sim's RNG; not a separate RNG so the test seeds still control everything).
- Base sprite: one fish from `NewRiverFishAssetPack1.0` (e.g. `bluegill_panfish.png`).
- Color expressed via per-pixel multiply tint of the base sprite, cached by phenotype color category (red / pink / white). Cache prevents per-frame surface allocation.
- Body size phenotype scales the sprite ±20%.
- Per-fish movement: random heading, picks a new heading every 1–2 sec, reflects off pond polygon edges. Optional 2-frame tail wiggle if cheap.
- Generation transition: 200 ms cross-fade between old visible-fish sample and new one. Chart updates simultaneously.
- Predator visual: when the predator toggle is on, render one larger fish sprite (e.g. `large_mouth_bass.png`) lurking in the pond. Pure visual — does not touch sim math. Implement only if MVP time allows.

## Ambient wildlife

- MVP: 2–3 bunnies wandering the grass area, sprite from `MiniBunny.png`.
- Wander state machine, deterministic with a seeded RNG:
  - `idle` (1.5–3 s) → pick random target tile in grass → `walk` to target → `idle`.
- No collision with player; cannot enter water or cottage footprint.
- Bird and deer deferred. Same wander module, different sprite when added.

## Cottage and journal

- Cottage sprite placed at a fixed scene position.
- Player within ~48 px of cottage center → render small "Press E" prompt above the cottage.
- E (or J anywhere) opens the journal overlay:
  - Semi-transparent backdrop dims the scene.
  - Panel ≈ 80% of window. Left ~70%: existing `ChartPanel`. Right ~30%: re-laid-out copy of existing HUD widgets (Predator toggle, Speed slider, Pause button).
  - Sim does **not** pause while journal is open. Chart updates live — that is the point.
  - J or ESC closes the journal. ESC outside the journal becomes a "Quit?" prompt or just closes the window (preserves existing quit-on-window-close).

## Assets

Copy the three packs into the repo (so the project is self-contained for grading):

```
assets/
  tilesets/free_version/free.png
  tilesets/free_version/READ ME.txt
  fish/NewRiverFishAssetPack1.0/...
  animals/MinifolksForestAnimals/...
  README.md   ← provenance + license per pack
```

`assets.py` exposes named loaders:
- `load_tileset()` → returns a dict of named subsurfaces (grass, water_corner_*, tree, cottage, char_down, char_up, char_left, char_right). Hand-coded slice rects.
- `load_fish_base()` → guppy-equivalent fish surface, plus an optional predator surface.
- `load_bunny_anim()` → frame grid sliced by row (direction) and col (frame).

No Tiled/TMX tooling. Slice rects are constants in code.

## Testing

- **Untouched and must remain green**: all `tests/test_*.py` and `tests/sim/*`.
- **Replaced**: `tests/ui/test_world_panel.py` — its dot-grid expectations no longer apply; rewritten to test the tilemap renderer.
- **New ui tests** using a headless `pygame.Surface`:
  - `test_tilemap.py` — known tile grid renders to a surface; water tiles land where expected.
  - `test_player.py` — keyboard events update position; clamped to scene rect; cannot walk onto water.
  - `test_pond.py` — given a `Population`, samples N visible fish; tint cache keys match phenotype color; visible fish positions stay inside the pond polygon over many ticks.
  - `test_wildlife.py` — wander state machine transitions, deterministic under a seeded RNG.
  - `test_journal.py` — E near cottage opens journal; J toggles; sim still ticks while journal is open; widgets inside journal still drive `SimController`.
  - `test_app.py` extension — full event/render path covers the new layout.
- **No pixel-equality assertions** — only shapes, counts, and state.
- **Asset loading in tests**: stub or use a tiny fixture surface so tests don't depend on the real PNGs.

## MVP cut

Ships in the first build:

- Forest scene: grass + trees + pond + cottage
- Player walks with WASD/arrows
- 8–12 fish sprites in pond, color-tinted by phenotype, drift around
- Sim keeps ticking on its own clock; visible fish refresh on generation
- Cottage interaction → journal overlay containing the existing chart + HUD widgets
- 2–3 wandering bunnies

Stretch (in MVP if time allows):
- 4-direction walk animation (depends on character sprite contents)
- Predator visual sprite when toggle is on

Explicitly deferred:
- Scrolling camera
- Second habitat (and any new genetics schema)
- Catching mechanics, crops
- Beetle / bird / snail species
- Day/night cycle, save/load, sound

## Risks

1. **Tileset is smaller than the reference**: `free version` is a farm-style tileset, not the rich forest tileset in the user's reference image. Visual fidelity will not match the screenshot exactly. Acceptable for MVP per user direction; user can drop in a richer tileset later by replacing the asset folder.
2. **Character sprite may be single-direction**: walk animation is conditional on the asset's frame count. If single-frame, MVP ships static.
3. **Bunny sprite slicing**: assumed to be a frame-grid; will verify exact rows/cols in `assets.py` during implementation.
4. **Existing UI tests deletion**: `test_world_panel.py` will be largely replaced. Coverage temporarily dips before being filled by the new tilemap/pond/player tests.

## Implementation plan

To be drafted in a follow-up plan document by the `writing-plans` skill.
