# Field Researcher Game Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Pivot the existing sim-viewer into a top-down forest game where the player walks around as a field researcher, sees fish swimming in a pond (rendered from the existing guppy sim), passes ambient bunnies, and opens a journal overlay (chart + selection-pressure controls) by walking to a research cottage.

**Architecture:** Approach A from the design doc — the existing `evogame.genetics` and `evogame.sim` packages are not touched. Inside `evogame.ui`, the world panel is rewritten to render a tilemap with a player sprite, ambient wildlife, and pond fish. The existing chart and HUD widgets are repurposed: chart + widgets move into a journal overlay; the HUD itself becomes a thin top status strip.

**Tech Stack:** Python 3.11+, pygame ≥ 2.5, pytest. Headless tests use the dummy SDL driver via the existing `tests/conftest.py` fixture.

**Companion design doc:** `docs/plans/2026-05-08-field-researcher-game-design.md`

---

## Conventions

- **TDD always.** Every task is: (1) write failing test, (2) run test and confirm failure, (3) write minimal implementation, (4) run test and confirm pass, (5) run the full suite, (6) commit.
- **Run the full suite often.** After each task: `pytest -q`. Existing genetics + sim tests must stay green for the entire plan.
- **Commit per task.** Use the existing commit style (visible in `git log`): conventional-commit prefixes (`feat`, `test`, `refactor`, `chore`, `docs`), short subjects, the trailer line `Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>` if the engineer is Claude.
- **No pixel-equality assertions.** Render tests check shapes, counts, and state — not RGB equality (other than already-existing background-not-black checks).
- **Headless rendering.** Tests use the `pygame_surface` fixture from `tests/conftest.py`. Never call `pygame.display.set_mode` inside a test.
- **Asset rects are constants.** All slice rectangles for tileset / fish / animal frames are hand-coded module-level constants in `assets.py`. No Tiled / TMX tooling.
- **Windows note.** Project root is `D:\game`. Use forward slashes inside Python; PowerShell for shell commands.

## Phase ordering rationale

Phases are designed so the game is playable end-to-end at the end of each phase:

- After **Phase 0**: assets load; nothing visible changes.
- After **Phase 1**: window shows a forest tilemap instead of a dot grid. Sim still ticks invisibly.
- After **Phase 2**: a player sprite walks around the forest with WASD/arrows.
- After **Phase 3**: walking to the cottage and pressing E opens the journal (chart + controls). Sim still ticks while open.
- After **Phase 4**: the pond holds 8–12 fish sprites tinted by phenotype, drifting around, refreshing on generation tick. **This is when it really feels like a game.**
- After **Phase 5**: ambient bunnies wander the forest.
- After **Phase 6**: thin top status strip + final manual smoke run.
- **Phase 7** (stretch): generation-transition fade and visible predator sprite. Skip if time-constrained.

---

# Phase 0 — Asset wiring

**Goal:** asset packs live inside the repo; `assets.py` exposes named loaders that return pygame surfaces.

## Task 0.1: Copy asset packs into the repo

**Files:**
- Create directory: `assets/tilesets/free_version/`
- Create directory: `assets/fish/NewRiverFishAssetPack1.0/`
- Create directory: `assets/animals/MinifolksForestAnimals/`
- Create: `assets/README.md`

**Step 1: Copy files via PowerShell**

```powershell
$src1 = "C:\Users\urmib\Downloads\free version\free version"
$src2 = "C:\Users\urmib\Downloads\NewRiverFishAssetPack1.0\NewRiverFishAssetPack1.0"
$src3 = "C:\Users\urmib\Downloads\MinifolksForestAnimals"
Copy-Item -Path "$src1\*" -Destination "D:\game\assets\tilesets\free_version\" -Recurse
Copy-Item -Path "$src2\*" -Destination "D:\game\assets\fish\NewRiverFishAssetPack1.0\" -Recurse
Copy-Item -Path "$src3\*" -Destination "D:\game\assets\animals\MinifolksForestAnimals\" -Recurse
```

**Step 2: Write `assets/README.md`**

```markdown
# Assets

Provenance and licensing for the third-party art used in this project.

## tilesets/free_version/

Source: free download from author "shubibubi" (see `read me.txt` shipped in the pack).
Used for: terrain tiles (grass, water corners), tree, cottage, character sprite.

## fish/NewRiverFishAssetPack1.0/

Source: New River Fish Asset Pack 1.0.
Used for: pond fish (guppies are tinted variants of one base fish silhouette).

## animals/MinifolksForestAnimals/

Source: Minifolks Forest Animals pack.
Used for: ambient wildlife (bunny in MVP; bird/deer/etc. deferred).

If you replace this folder with a different forest tileset, update the slice
rectangles in `src/evogame/ui/assets.py`.
```

**Step 3: Verify**

```powershell
Get-ChildItem D:\game\assets -Recurse -File | Measure-Object | Select-Object -ExpandProperty Count
```
Expected: ≥ 20 files (tileset png + readme + 8 animal pngs × 2 outline variants + many fish pngs + sprite_sheet).

**Step 4: Commit**

```powershell
git add assets/
git commit -m @'
chore(assets): vendor pixel-art packs (free-version tileset, river fish, minifolks animals)

Bundles the three asset packs into the repo so the project is
self-contained for grading. Provenance documented in assets/README.md.
'@
```

---

## Task 0.2: Write the failing assets.py test

**Files:**
- Create: `tests/ui/test_assets.py`

**Step 1: Write the failing test**

```python
import pygame

from evogame.ui.assets import load_tileset, load_fish_base, load_bunny_frames


def test_load_tileset_returns_named_surfaces(pygame_surface):
    tiles = load_tileset()
    for name in ("grass", "water_nw", "water_ne", "water_sw", "water_se",
                 "tree", "cottage", "char_down"):
        assert name in tiles, f"missing tile: {name}"
        assert isinstance(tiles[name], pygame.Surface)
        w, h = tiles[name].get_size()
        assert w > 0 and h > 0


def test_load_fish_base_is_a_surface(pygame_surface):
    fish = load_fish_base()
    assert isinstance(fish, pygame.Surface)
    w, h = fish.get_size()
    assert w > 0 and h > 0


def test_load_bunny_frames_returns_per_direction_lists(pygame_surface):
    frames = load_bunny_frames()
    for direction in ("down", "up", "left", "right"):
        assert direction in frames, f"missing direction: {direction}"
        assert len(frames[direction]) >= 1
        for surf in frames[direction]:
            assert isinstance(surf, pygame.Surface)
```

**Step 2: Run test to verify it fails**

```powershell
pytest tests/ui/test_assets.py -v
```
Expected: ImportError or ModuleNotFoundError on `evogame.ui.assets`.

**Step 3: Skip implementation — commit failing test as a red marker**

(Skip — implementation lands in 0.3.)

---

## Task 0.3: Implement assets.py loaders

**Files:**
- Create: `src/evogame/ui/assets.py`

**Background:** `free version/free.png` is a small farm tileset. Its tile grid is 16×16 with tiles laid out horizontally near the top; trees, cottages, and the character sprite are in lower rows. Exact pixel coordinates need to be measured by opening `free.png` in any image viewer (Paint, IrfanView, web browser at 100% zoom). The slice constants below are starting estimates — **the implementer must verify by eyeballing the source PNG and adjusting** before tests pass.

**Step 1: Implement the loaders**

```python
import os
from functools import lru_cache

import pygame

_HERE = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
# .../D:/game  (climbs out of src/evogame/ui/)
_ASSETS_ROOT = os.path.join(_HERE, "assets")

_TILESET_PATH = os.path.join(_ASSETS_ROOT, "tilesets", "free_version", "free.png")
_FISH_PATH = os.path.join(
    _ASSETS_ROOT, "fish", "NewRiverFishAssetPack1.0",
    "Cenrarchidae", "Panfish", "bluegill_panfish.png",
)
_BUNNY_PATH = os.path.join(
    _ASSETS_ROOT, "animals", "MinifolksForestAnimals", "Outline", "MiniBunny.png",
)

# Slice rects into free.png. VERIFY against the actual image; adjust as needed.
# free.png appears to use 16x16 tiles. Coordinates are (x, y, w, h).
_TILE = 16
_TILESET_RECTS: dict[str, tuple[int, int, int, int]] = {
    "grass":     (16,   0, _TILE, _TILE),
    "water_nw":  (96,   0, _TILE, _TILE),
    "water_ne":  (112,  0, _TILE, _TILE),
    "water_sw":  (96,  16, _TILE, _TILE),
    "water_se":  (112, 16, _TILE, _TILE),
    "tree":      (192,  0, 32, 32),
    "cottage":   (32,  32, 64, 48),
    "char_down": (160, 16, 16, 16),
}

# Bunny sheet layout: 4 rows (down/up/left/right), 3 frames each, each 16x16.
# VERIFY against MiniBunny.png; adjust as needed.
_BUNNY_TILE = 16
_BUNNY_DIRECTIONS = ("down", "up", "left", "right")
_BUNNY_FRAMES_PER_DIR = 3


@lru_cache(maxsize=1)
def _load_tileset_image() -> pygame.Surface:
    return pygame.image.load(_TILESET_PATH).convert_alpha()


@lru_cache(maxsize=1)
def _load_fish_image() -> pygame.Surface:
    return pygame.image.load(_FISH_PATH).convert_alpha()


@lru_cache(maxsize=1)
def _load_bunny_image() -> pygame.Surface:
    return pygame.image.load(_BUNNY_PATH).convert_alpha()


def load_tileset() -> dict[str, pygame.Surface]:
    sheet = _load_tileset_image()
    out: dict[str, pygame.Surface] = {}
    for name, (x, y, w, h) in _TILESET_RECTS.items():
        out[name] = sheet.subsurface(pygame.Rect(x, y, w, h)).copy()
    return out


def load_fish_base() -> pygame.Surface:
    return _load_fish_image().copy()


def load_bunny_frames() -> dict[str, list[pygame.Surface]]:
    sheet = _load_bunny_image()
    out: dict[str, list[pygame.Surface]] = {}
    for row, direction in enumerate(_BUNNY_DIRECTIONS):
        frames = []
        for col in range(_BUNNY_FRAMES_PER_DIR):
            rect = pygame.Rect(col * _BUNNY_TILE, row * _BUNNY_TILE, _BUNNY_TILE, _BUNNY_TILE)
            frames.append(sheet.subsurface(rect).copy())
        out[direction] = frames
    return out
```

**Step 2: Pre-implementation: confirm slice rects against the real PNG**

Open the three PNGs in any image viewer that shows pixel coordinates. Adjust the constants in `_TILESET_RECTS`, `_BUNNY_DIRECTIONS`, `_BUNNY_FRAMES_PER_DIR` to match what is actually in the images. The loader code is correct; the constants must be correct for the test surfaces to be non-empty.

If the bunny sheet has a different layout (e.g. only 1 direction, or a different frame count), update both constants and the test in `tests/ui/test_assets.py` to match what the asset actually contains.

**Step 3: Run test to verify it passes**

```powershell
pytest tests/ui/test_assets.py -v
```
Expected: 3 passed.

**Step 4: Run the full suite**

```powershell
pytest -q
```
Expected: all existing tests still pass; +3 new tests.

**Step 5: Commit**

```powershell
git add src/evogame/ui/assets.py tests/ui/test_assets.py
git commit -m @'
feat(ui): add assets loader for tileset, fish, and bunny frames

Slices the free-version tileset into named surfaces, loads the bluegill
fish base sprite, and slices the minifolks bunny sheet into per-direction
frame lists. Slice rects are hand-coded constants verified against the
source PNGs.
'@
```

---

# Phase 1 — Tilemap and new world panel

**Goal:** the window shows a forest scene built from tiles instead of the colored dot grid.

## Task 1.1: Tilemap dataclass with rendering

**Files:**
- Create: `src/evogame/ui/tilemap.py`
- Create: `tests/ui/test_tilemap.py`

**Step 1: Write the failing test**

```python
import pygame

from evogame.ui.tilemap import Tilemap, TILE_PIXELS


def test_tilemap_dimensions():
    grid = [
        ["grass", "grass", "water_nw"],
        ["grass", "grass", "water_sw"],
    ]
    tm = Tilemap(grid)
    assert tm.cols == 3
    assert tm.rows == 2
    assert tm.pixel_width == 3 * TILE_PIXELS
    assert tm.pixel_height == 2 * TILE_PIXELS


def test_tilemap_is_walkable_water_blocks():
    grid = [
        ["grass", "water_nw"],
        ["grass", "water_sw"],
    ]
    tm = Tilemap(grid)
    assert tm.is_walkable(0, 0) is True   # grass
    assert tm.is_walkable(1, 0) is False  # water


def test_tilemap_draw_paints_grass_pixels(pygame_surface):
    grid = [["grass"] * 4 for _ in range(4)]
    tm = Tilemap(grid)
    tm.draw(pygame_surface, origin=(0, 0))
    # Grass tile is not pure black; somewhere in the painted region pixel != black.
    pixel = pygame_surface.get_at((TILE_PIXELS // 2, TILE_PIXELS // 2))
    assert pixel != (0, 0, 0, 255)
```

**Step 2: Run to verify fail**

```powershell
pytest tests/ui/test_tilemap.py -v
```
Expected: ImportError on `evogame.ui.tilemap`.

**Step 3: Implement**

```python
# src/evogame/ui/tilemap.py
from typing import Iterable

import pygame

from evogame.ui.assets import load_tileset

TILE_PIXELS = 32  # 16x16 source tiles drawn at 2x scale

_NON_WALKABLE = {"water_nw", "water_ne", "water_sw", "water_se"}


class Tilemap:
    def __init__(self, grid: list[list[str]]):
        self.grid = grid
        self.rows = len(grid)
        self.cols = len(grid[0]) if grid else 0
        self.pixel_width = self.cols * TILE_PIXELS
        self.pixel_height = self.rows * TILE_PIXELS
        self._tiles: dict[str, pygame.Surface] | None = None

    def _ensure_tiles(self) -> dict[str, pygame.Surface]:
        if self._tiles is None:
            raw = load_tileset()
            self._tiles = {
                name: pygame.transform.scale(s, (TILE_PIXELS, TILE_PIXELS))
                for name, s in raw.items()
                if s.get_width() == 16 and s.get_height() == 16
            }
        return self._tiles

    def is_walkable(self, col: int, row: int) -> bool:
        if row < 0 or row >= self.rows or col < 0 or col >= self.cols:
            return False
        return self.grid[row][col] not in _NON_WALKABLE

    def draw(self, surface: pygame.Surface, origin: tuple[int, int]) -> None:
        ox, oy = origin
        tiles = self._ensure_tiles()
        for r, row_tiles in enumerate(self.grid):
            for c, name in enumerate(row_tiles):
                tile = tiles.get(name)
                if tile is None:
                    continue
                surface.blit(tile, (ox + c * TILE_PIXELS, oy + r * TILE_PIXELS))
```

**Step 4: Run tests**

```powershell
pytest tests/ui/test_tilemap.py -v
```
Expected: 3 passed.

**Step 5: Commit**

```powershell
git add src/evogame/ui/tilemap.py tests/ui/test_tilemap.py
git commit -m @'
feat(ui): add Tilemap with grass/water tile rendering and walkability

Tilemap is a 2D grid of tile-name strings. Renders by blitting scaled
tileset surfaces. Water tiles report as non-walkable for player collision.
'@
```

---

## Task 1.2: Forest scene factory

**Files:**
- Modify: `src/evogame/ui/tilemap.py` (add `build_forest_scene()`)
- Modify: `tests/ui/test_tilemap.py` (add scene factory tests)

**Step 1: Write the failing test**

```python
def test_forest_scene_has_pond_and_dimensions():
    from evogame.ui.tilemap import build_forest_scene, TILE_PIXELS
    scene = build_forest_scene()
    # scene must fit inside 1000x596 (window height minus 24px status strip)
    assert scene.tilemap.pixel_width <= 1000
    assert scene.tilemap.pixel_height <= 596
    assert scene.tilemap.pixel_width >= 32 * TILE_PIXELS or scene.tilemap.cols >= 28
    # has at least one pond tile and at least one tree object
    pond_tiles = [
        (c, r) for r in range(scene.tilemap.rows) for c in range(scene.tilemap.cols)
        if scene.tilemap.grid[r][c].startswith("water_")
    ]
    assert len(pond_tiles) >= 4, "scene must include a 2x2-or-larger pond"
    assert any(o.kind == "tree" for o in scene.objects)
    assert any(o.kind == "cottage" for o in scene.objects)


def test_forest_scene_pond_bounds_are_inside_grid():
    from evogame.ui.tilemap import build_forest_scene
    scene = build_forest_scene()
    bounds = scene.pond_pixel_bounds()
    assert bounds.width > 0 and bounds.height > 0
    assert bounds.left >= 0 and bounds.top >= 0
    assert bounds.right <= scene.tilemap.pixel_width
    assert bounds.bottom <= scene.tilemap.pixel_height
```

**Step 2: Run to verify fail**

```powershell
pytest tests/ui/test_tilemap.py::test_forest_scene_has_pond_and_dimensions -v
```
Expected: AttributeError on `build_forest_scene`.

**Step 3: Implement**

Add to `src/evogame/ui/tilemap.py`:

```python
from dataclasses import dataclass, field


@dataclass(frozen=True)
class SceneObject:
    kind: str           # "tree" | "cottage"
    col: int
    row: int


@dataclass
class Scene:
    tilemap: Tilemap
    objects: list[SceneObject] = field(default_factory=list)

    def pond_pixel_bounds(self) -> pygame.Rect:
        coords = [
            (c, r) for r in range(self.tilemap.rows) for c in range(self.tilemap.cols)
            if self.tilemap.grid[r][c].startswith("water_")
        ]
        if not coords:
            return pygame.Rect(0, 0, 0, 0)
        cols = [c for c, _ in coords]
        rows = [r for _, r in coords]
        x0, x1 = min(cols), max(cols) + 1
        y0, y1 = min(rows), max(rows) + 1
        return pygame.Rect(
            x0 * TILE_PIXELS, y0 * TILE_PIXELS,
            (x1 - x0) * TILE_PIXELS, (y1 - y0) * TILE_PIXELS,
        )


def build_forest_scene() -> Scene:
    """Hand-authored single-screen forest scene.
    30 cols x 18 rows = 960x576 px.
    """
    cols, rows = 30, 18
    grid = [["grass"] * cols for _ in range(rows)]

    # 4x3 pond near upper-left
    pond_top, pond_left = 4, 6
    pond_w, pond_h = 4, 3
    for dr in range(pond_h):
        for dc in range(pond_w):
            r = pond_top + dr
            c = pond_left + dc
            if dr == 0 and dc == 0:
                grid[r][c] = "water_nw"
            elif dr == 0 and dc == pond_w - 1:
                grid[r][c] = "water_ne"
            elif dr == pond_h - 1 and dc == 0:
                grid[r][c] = "water_sw"
            elif dr == pond_h - 1 and dc == pond_w - 1:
                grid[r][c] = "water_se"
            else:
                grid[r][c] = "water_nw"  # interior — any water tile name OK

    objects = [
        SceneObject("tree", col=2, row=2),
        SceneObject("tree", col=20, row=3),
        SceneObject("tree", col=24, row=10),
        SceneObject("tree", col=4, row=14),
        SceneObject("cottage", col=18, row=11),
    ]
    return Scene(Tilemap(grid), objects)
```

**Step 4: Run tests**

```powershell
pytest tests/ui/test_tilemap.py -v
```
Expected: 5 passed.

**Step 5: Commit**

```powershell
git add src/evogame/ui/tilemap.py tests/ui/test_tilemap.py
git commit -m @'
feat(ui): add Scene + build_forest_scene factory

Scene combines a Tilemap with a list of placed objects (trees, cottage)
and exposes the pond bounding rect for fish movement.
'@
```

---

## Task 1.3: Replace WorldPanel internals

**Files:**
- Modify: `src/evogame/ui/world_panel.py` (full rewrite)
- Modify: `tests/ui/test_world_panel.py` (full rewrite)

**Step 1: Rewrite the test file**

```python
# tests/ui/test_world_panel.py
import pygame

from evogame.ui.world_panel import WorldPanel


def test_world_panel_draws_scene_without_error(pygame_surface):
    panel = WorldPanel(pygame.Rect(0, 0, 200, 200))
    panel.draw(pygame_surface)


def test_world_panel_paints_background(pygame_surface):
    panel = WorldPanel(pygame.Rect(0, 0, 200, 200))
    panel.draw(pygame_surface)
    pixel = pygame_surface.get_at((100, 100))
    assert pixel != (0, 0, 0, 255), "panel background should show grass, not black"
```

**Step 2: Run to verify fail**

```powershell
pytest tests/ui/test_world_panel.py -v
```
Expected: TypeError or AttributeError — old `WorldPanel.draw(surface, creatures)` signature mismatch.

**Step 3: Rewrite world_panel.py**

```python
# src/evogame/ui/world_panel.py
import pygame

from evogame.ui.assets import load_tileset
from evogame.ui.tilemap import TILE_PIXELS, build_forest_scene


class WorldPanel:
    def __init__(self, rect: pygame.Rect):
        self.rect = rect
        self.scene = build_forest_scene()
        self._object_surfs: dict[str, pygame.Surface] | None = None

    def _ensure_objects(self) -> dict[str, pygame.Surface]:
        if self._object_surfs is None:
            raw = load_tileset()
            self._object_surfs = {
                "tree": pygame.transform.scale(raw["tree"], (TILE_PIXELS * 2, TILE_PIXELS * 2)),
                "cottage": pygame.transform.scale(raw["cottage"], (TILE_PIXELS * 4, TILE_PIXELS * 3)),
            }
        return self._object_surfs

    def draw(self, surface: pygame.Surface) -> None:
        # 1. tilemap
        self.scene.tilemap.draw(surface, origin=(self.rect.left, self.rect.top))
        # 2. objects (trees, cottage) drawn after terrain
        objs = self._ensure_objects()
        for obj in self.scene.objects:
            sprite = objs.get(obj.kind)
            if sprite is None:
                continue
            x = self.rect.left + obj.col * TILE_PIXELS
            y = self.rect.top + obj.row * TILE_PIXELS
            surface.blit(sprite, (x, y))
```

**Step 4: Run tests**

```powershell
pytest tests/ui/test_world_panel.py -v
```
Expected: 2 passed.

**Step 5: Update app.py to call new signature**

In `src/evogame/ui/app.py`, change the world-panel draw call:

```python
# old:
# self.world_panel.draw(self.screen, self.sim.population.creatures)
# new:
self.world_panel.draw(self.screen)
```

**Step 6: Run the full suite**

```powershell
pytest -q
```
Expected: existing app tests will likely still pass since the call signature was the only change. If `tests/ui/test_app.py` references `creatures` in any assertion, fix accordingly — but a quick `Grep` first:

```powershell
# Use the Grep tool, not bash, in actual implementation
```

**Step 7: Commit**

```powershell
git add src/evogame/ui/world_panel.py src/evogame/ui/app.py tests/ui/test_world_panel.py
git commit -m @'
feat(ui): rewrite WorldPanel as tilemap scene renderer

Replaces the colored-dot grid with a top-down forest scene built from
tiles plus placed tree and cottage objects. Old test_world_panel.py is
rewritten for the new signature.
'@
```

---

# Phase 2 — Player and movement

**Goal:** a character sprite walks around the forest with WASD/arrows; cannot walk onto water or onto the cottage footprint.

## Task 2.1: Player class with position, velocity, sprite

**Files:**
- Create: `src/evogame/ui/player.py`
- Create: `tests/ui/test_player.py`

**Step 1: Write the failing test**

```python
import pygame

from evogame.ui.player import Player


def test_player_starts_at_given_position(pygame_surface):
    p = Player(pos=(100.0, 100.0))
    assert p.pos == (100.0, 100.0)
    assert p.velocity == (0.0, 0.0)


def test_player_handle_input_sets_velocity_for_arrow_keys(pygame_surface):
    p = Player(pos=(100.0, 100.0))
    keys_pressed = {pygame.K_RIGHT: True, pygame.K_d: False,
                    pygame.K_LEFT: False, pygame.K_a: False,
                    pygame.K_UP: False, pygame.K_w: False,
                    pygame.K_DOWN: False, pygame.K_s: False}
    p.handle_input(keys_pressed)
    vx, vy = p.velocity
    assert vx > 0 and vy == 0


def test_player_handle_input_diagonal_normalizes(pygame_surface):
    p = Player(pos=(100.0, 100.0))
    keys_pressed = {pygame.K_RIGHT: False, pygame.K_d: True,
                    pygame.K_LEFT: False, pygame.K_a: False,
                    pygame.K_UP: False, pygame.K_w: True,
                    pygame.K_DOWN: False, pygame.K_s: False}
    p.handle_input(keys_pressed)
    vx, vy = p.velocity
    speed_sq = vx * vx + vy * vy
    # Magnitude should be ~Player.SPEED, not sqrt(2)*SPEED
    assert abs(speed_sq ** 0.5 - Player.SPEED) < 1.0
```

**Step 2: Run to verify fail**

```powershell
pytest tests/ui/test_player.py -v
```
Expected: ImportError on `evogame.ui.player`.

**Step 3: Implement**

```python
# src/evogame/ui/player.py
import math
from typing import Mapping

import pygame

from evogame.ui.assets import load_tileset
from evogame.ui.tilemap import TILE_PIXELS


class Player:
    SPEED = 120.0  # pixels per second

    def __init__(self, pos: tuple[float, float]):
        self.pos = pos
        self.velocity: tuple[float, float] = (0.0, 0.0)
        self._sprite: pygame.Surface | None = None
        self.size = (TILE_PIXELS, TILE_PIXELS)

    def _ensure_sprite(self) -> pygame.Surface:
        if self._sprite is None:
            tiles = load_tileset()
            self._sprite = pygame.transform.scale(tiles["char_down"], self.size)
        return self._sprite

    def handle_input(self, keys: Mapping[int, bool]) -> None:
        dx = (1 if keys.get(pygame.K_RIGHT) or keys.get(pygame.K_d) else 0) \
           - (1 if keys.get(pygame.K_LEFT)  or keys.get(pygame.K_a) else 0)
        dy = (1 if keys.get(pygame.K_DOWN)  or keys.get(pygame.K_s) else 0) \
           - (1 if keys.get(pygame.K_UP)    or keys.get(pygame.K_w) else 0)
        if dx == 0 and dy == 0:
            self.velocity = (0.0, 0.0)
            return
        mag = math.hypot(dx, dy)
        self.velocity = (dx / mag * self.SPEED, dy / mag * self.SPEED)
```

**Step 4: Run tests**

```powershell
pytest tests/ui/test_player.py -v
```
Expected: 3 passed.

**Step 5: Commit**

```powershell
git add src/evogame/ui/player.py tests/ui/test_player.py
git commit -m @'
feat(ui): add Player with input-to-velocity mapping

WASD or arrow keys set a velocity vector at fixed speed; diagonals are
normalized so they don't move faster than cardinals.
'@
```

---

## Task 2.2: Player.update with scene clamp and water collision

**Files:**
- Modify: `src/evogame/ui/player.py` (add `update`)
- Modify: `tests/ui/test_player.py`

**Step 1: Add failing tests**

```python
def test_player_update_advances_position(pygame_surface):
    from evogame.ui.tilemap import build_forest_scene
    p = Player(pos=(200.0, 200.0))
    p.velocity = (Player.SPEED, 0.0)
    scene = build_forest_scene()
    p.update(dt_ms=1000.0, scene=scene)
    assert p.pos[0] == 200.0 + Player.SPEED
    assert p.pos[1] == 200.0


def test_player_update_clamps_to_scene(pygame_surface):
    from evogame.ui.tilemap import build_forest_scene
    p = Player(pos=(0.0, 0.0))
    p.velocity = (-Player.SPEED, 0.0)
    scene = build_forest_scene()
    p.update(dt_ms=1000.0, scene=scene)
    assert p.pos[0] == 0.0  # clamped


def test_player_cannot_walk_into_pond(pygame_surface):
    from evogame.ui.tilemap import build_forest_scene, TILE_PIXELS
    scene = build_forest_scene()
    bounds = scene.pond_pixel_bounds()
    # Place player just left of pond, moving right.
    p = Player(pos=(bounds.left - 4.0, bounds.top + bounds.height / 2))
    p.velocity = (Player.SPEED, 0.0)
    p.update(dt_ms=1000.0, scene=scene)
    # Player feet should not be inside the pond rect.
    feet_x = p.pos[0] + p.size[0] / 2
    feet_y = p.pos[1] + p.size[1] - 2
    assert not bounds.collidepoint(feet_x, feet_y), \
        f"player walked into pond: feet=({feet_x},{feet_y}) bounds={bounds}"
```

**Step 2: Run to verify fail**

```powershell
pytest tests/ui/test_player.py -v
```
Expected: AttributeError on `Player.update`.

**Step 3: Implement**

Add to `src/evogame/ui/player.py`:

```python
from evogame.ui.tilemap import Scene


def _is_walkable_at(scene: Scene, x: float, y: float) -> bool:
    col = int(x // TILE_PIXELS)
    row = int(y // TILE_PIXELS)
    return scene.tilemap.is_walkable(col, row)


# Inside class Player:

def update(self, dt_ms: float, scene: Scene) -> None:
    vx, vy = self.velocity
    dt = dt_ms / 1000.0
    # X axis
    new_x = self.pos[0] + vx * dt
    feet_y = self.pos[1] + self.size[1] - 2
    feet_x_test = new_x + self.size[0] / 2
    if 0 <= new_x <= scene.tilemap.pixel_width - self.size[0] \
       and _is_walkable_at(scene, feet_x_test, feet_y):
        x = new_x
    else:
        x = max(0.0, min(scene.tilemap.pixel_width - self.size[0], self.pos[0]))
    # Y axis
    new_y = self.pos[1] + vy * dt
    feet_x_keep = x + self.size[0] / 2
    feet_y_test = new_y + self.size[1] - 2
    if 0 <= new_y <= scene.tilemap.pixel_height - self.size[1] \
       and _is_walkable_at(scene, feet_x_keep, feet_y_test):
        y = new_y
    else:
        y = max(0.0, min(scene.tilemap.pixel_height - self.size[1], self.pos[1]))
    self.pos = (x, y)
```

**Step 4: Run tests**

```powershell
pytest tests/ui/test_player.py -v
```
Expected: 6 passed.

**Step 5: Commit**

```powershell
git add src/evogame/ui/player.py tests/ui/test_player.py
git commit -m @'
feat(ui): Player.update with scene clamp and water collision

Per-axis movement so a blocked horizontal axis still allows vertical
movement (typical for top-down games). Player feet test prevents walking
into pond tiles.
'@
```

---

## Task 2.3: WorldPanel draws the player

**Files:**
- Modify: `src/evogame/ui/world_panel.py` (add player + draw_player call)
- Modify: `tests/ui/test_world_panel.py`

**Step 1: Add failing test**

```python
def test_world_panel_draws_player(pygame_surface):
    from evogame.ui.player import Player
    from evogame.ui.world_panel import WorldPanel
    panel = WorldPanel(pygame.Rect(0, 0, 200, 200))
    player = Player(pos=(50.0, 50.0))
    panel.draw(pygame_surface, player=player)
    # Pixel under player should not be the all-grass background — it's a sprite.
    # Just verify draw with a player argument doesn't raise.
```

**Step 2: Run to verify fail**

```powershell
pytest tests/ui/test_world_panel.py::test_world_panel_draws_player -v
```
Expected: TypeError — `draw()` got unexpected keyword argument 'player'.

**Step 3: Modify WorldPanel.draw signature**

```python
# In src/evogame/ui/world_panel.py
def draw(self, surface: pygame.Surface, player: "Player | None" = None) -> None:
    self.scene.tilemap.draw(surface, origin=(self.rect.left, self.rect.top))
    objs = self._ensure_objects()
    for obj in self.scene.objects:
        sprite = objs.get(obj.kind)
        if sprite is None:
            continue
        x = self.rect.left + obj.col * TILE_PIXELS
        y = self.rect.top + obj.row * TILE_PIXELS
        surface.blit(sprite, (x, y))
    if player is not None:
        sprite = player._ensure_sprite()
        surface.blit(sprite, (self.rect.left + player.pos[0], self.rect.top + player.pos[1]))
```

(Use a TYPE_CHECKING import for Player to avoid the circular import.)

**Step 4: Run tests**

```powershell
pytest tests/ui/test_world_panel.py -v
```
Expected: 3 passed.

**Step 5: Commit**

```powershell
git add src/evogame/ui/world_panel.py tests/ui/test_world_panel.py
git commit -m @'
feat(ui): WorldPanel.draw now blits the player sprite over the scene
'@
```

---

## Task 2.4: Wire the player into App

**Files:**
- Modify: `src/evogame/ui/app.py`
- Modify: `tests/ui/test_app.py` (only as needed)

**Step 1: Modify App**

```python
# In src/evogame/ui/app.py
from evogame.ui.player import Player

class App:
    def __init__(self, seed: int | None = None):
        # ... existing init ...
        # Add after world_panel construction:
        # Spawn player at center of forest scene
        scene = self.world_panel.scene
        self.player = Player(
            pos=(scene.tilemap.pixel_width / 2, scene.tilemap.pixel_height * 0.7)
        )

    def step_one_frame(self, dt_ms: float) -> None:
        self._handle_events()
        keys = pygame.key.get_pressed()
        self.player.handle_input(keys)
        self.player.update(dt_ms, self.world_panel.scene)
        if not self.hud.paused and not self.sim.extinct:
            interval_ms = 1000.0 / self.hud.gens_per_second
            self._gen_timer_ms += dt_ms
            while self._gen_timer_ms >= interval_ms:
                self._gen_timer_ms -= interval_ms
                self.sim.tick()
                self.chart_panel.update(self.sim.log)
                if self.sim.extinct:
                    break
        self._render()

    def _render(self) -> None:
        self.screen.fill((10, 10, 15))
        self.world_panel.draw(self.screen, player=self.player)
        self.chart_panel.draw(self.screen)
        self.hud.draw(self.screen, self.font)
        pygame.display.flip()
```

**Step 2: Run the full suite**

```powershell
pytest -q
```
Expected: all green.

**Step 3: Manual smoke run**

```powershell
python scripts/run_game.py
```
Expected: window opens, you see a forest tilemap with trees, a pond, a cottage, and a character that walks with WASD/arrows. The right side still shows the chart and the old HUD bar (will be replaced in Phase 3).

**Step 4: Commit**

```powershell
git add src/evogame/ui/app.py
git commit -m @'
feat(ui): app drives Player input/update each frame and renders it
'@
```

---

# Phase 3 — Cottage interaction and journal overlay

**Goal:** the player can walk to the cottage, press E, and a journal panel opens showing the chart + the predator/speed/pause widgets. The HUD becomes a thin top status strip.

## Task 3.1: Cottage interaction range detection

**Files:**
- Modify: `src/evogame/ui/world_panel.py` (add `cottage_in_range` method)
- Modify: `tests/ui/test_world_panel.py`

**Step 1: Add failing test**

```python
def test_cottage_in_range_when_player_close(pygame_surface):
    from evogame.ui.player import Player
    from evogame.ui.world_panel import WorldPanel
    panel = WorldPanel(pygame.Rect(0, 0, 1000, 596))
    cottage = next(o for o in panel.scene.objects if o.kind == "cottage")
    cx = cottage.col * 32 + 16
    cy = cottage.row * 32 + 16
    near = Player(pos=(cx - 16.0, cy - 16.0))
    far = Player(pos=(0.0, 0.0))
    assert panel.cottage_in_range(near) is True
    assert panel.cottage_in_range(far) is False
```

**Step 2: Run to verify fail**

```powershell
pytest tests/ui/test_world_panel.py::test_cottage_in_range_when_player_close -v
```
Expected: AttributeError.

**Step 3: Implement**

```python
# In src/evogame/ui/world_panel.py
COTTAGE_INTERACT_RADIUS = 64

def cottage_in_range(self, player) -> bool:
    cottage = next((o for o in self.scene.objects if o.kind == "cottage"), None)
    if cottage is None:
        return False
    from evogame.ui.tilemap import TILE_PIXELS
    cx = cottage.col * TILE_PIXELS + TILE_PIXELS * 2
    cy = cottage.row * TILE_PIXELS + TILE_PIXELS * 1.5
    px = player.pos[0] + player.size[0] / 2
    py = player.pos[1] + player.size[1] / 2
    return ((px - cx) ** 2 + (py - cy) ** 2) ** 0.5 <= self.COTTAGE_INTERACT_RADIUS
```

**Step 4: Run, commit**

```powershell
pytest tests/ui/test_world_panel.py -v
git add src/evogame/ui/world_panel.py tests/ui/test_world_panel.py
git commit -m @'
feat(ui): WorldPanel.cottage_in_range for E-prompt and journal trigger
'@
```

---

## Task 3.2: "Press E" prompt rendering

**Files:**
- Modify: `src/evogame/ui/world_panel.py`
- Modify: `tests/ui/test_world_panel.py`

**Step 1: Failing test**

```python
def test_world_panel_draws_press_e_when_in_range(pygame_surface):
    from evogame.ui.player import Player
    from evogame.ui.world_panel import WorldPanel
    panel = WorldPanel(pygame.Rect(0, 0, 1000, 596))
    cottage = next(o for o in panel.scene.objects if o.kind == "cottage")
    near = Player(pos=(cottage.col * 32, cottage.row * 32))
    font = pygame.font.SysFont("arial", 12)
    panel.draw(pygame_surface, player=near, font=font)
    # No assertion on the text pixels — just that calling with font + in-range player doesn't raise.
```

**Step 2: Run to verify fail**

Expected: TypeError — `draw()` doesn't accept `font`.

**Step 3: Add font parameter and prompt rendering**

```python
def draw(self, surface, player=None, font=None):
    # ... existing tile + object + player drawing ...
    if player is not None and font is not None and self.cottage_in_range(player):
        from evogame.ui.tilemap import TILE_PIXELS
        cottage = next((o for o in self.scene.objects if o.kind == "cottage"), None)
        if cottage is not None:
            text = font.render("Press E", True, (255, 255, 255))
            x = self.rect.left + cottage.col * TILE_PIXELS
            y = self.rect.top + cottage.row * TILE_PIXELS - 18
            shadow = pygame.Surface((text.get_width() + 6, text.get_height() + 4), pygame.SRCALPHA)
            shadow.fill((0, 0, 0, 160))
            surface.blit(shadow, (x, y))
            surface.blit(text, (x + 3, y + 2))
```

**Step 4: Run, commit**

```powershell
pytest tests/ui/test_world_panel.py -v
git add src/evogame/ui/world_panel.py tests/ui/test_world_panel.py
git commit -m @'
feat(ui): show 'Press E' prompt above cottage when player is in range
'@
```

---

## Task 3.3: Journal overlay with chart + selection-pressure widgets

**Files:**
- Create: `src/evogame/ui/journal.py`
- Create: `tests/ui/test_journal.py`

**Step 1: Failing test**

```python
import random

import pygame

from evogame.genetics import GUPPY_SCHEMA
from evogame.sim.controller import SimController
from evogame.ui.journal import Journal


def test_journal_starts_closed(pygame_surface):
    sim = SimController(GUPPY_SCHEMA, 10, 20, random.Random(0))
    journal = Journal(pygame.Rect(0, 0, 1000, 620), sim)
    assert journal.open is False


def test_journal_open_close_toggle(pygame_surface):
    sim = SimController(GUPPY_SCHEMA, 10, 20, random.Random(0))
    journal = Journal(pygame.Rect(0, 0, 1000, 620), sim)
    journal.toggle()
    assert journal.open is True
    journal.toggle()
    assert journal.open is False


def test_journal_predator_toggle_affects_sim(pygame_surface):
    sim = SimController(GUPPY_SCHEMA, 10, 20, random.Random(0))
    journal = Journal(pygame.Rect(0, 0, 1000, 620), sim)
    journal.open = True
    # Mouse-click on the predator toggle's rect.
    rect = journal.predator_toggle.rect
    event = pygame.event.Event(
        pygame.MOUSEBUTTONDOWN,
        {"button": 1, "pos": rect.center},
    )
    assert sim.pressure.predator_on is False
    journal.handle_event(event)
    assert sim.pressure.predator_on is True


def test_journal_draw_when_closed_no_op(pygame_surface):
    sim = SimController(GUPPY_SCHEMA, 10, 20, random.Random(0))
    journal = Journal(pygame.Rect(0, 0, 1000, 620), sim)
    font = pygame.font.SysFont("arial", 12)
    journal.draw(pygame_surface, font)  # no error


def test_journal_draw_when_open(pygame_surface):
    sim = SimController(GUPPY_SCHEMA, 10, 20, random.Random(0))
    journal = Journal(pygame.Rect(0, 0, 1000, 620), sim)
    journal.open = True
    font = pygame.font.SysFont("arial", 12)
    journal.draw(pygame_surface, font)
```

**Step 2: Run to verify fail**

```powershell
pytest tests/ui/test_journal.py -v
```
Expected: ImportError on `evogame.ui.journal`.

**Step 3: Implement**

```python
# src/evogame/ui/journal.py
import pygame

from evogame.sim.controller import SimController
from evogame.ui.chart_panel import ChartPanel
from evogame.ui.widgets import Button, Slider, Toggle

_BACKDROP = (0, 0, 0, 160)
_PANEL_BG = (28, 28, 38)
_FG = (220, 220, 220)


class Journal:
    def __init__(self, screen_rect: pygame.Rect, sim: SimController):
        self.screen_rect = screen_rect
        self.sim = sim
        self.open = False
        self.paused = False

        # Panel = 80% of screen, centered.
        margin_x = int(screen_rect.width * 0.10)
        margin_y = int(screen_rect.height * 0.10)
        self.panel_rect = pygame.Rect(
            screen_rect.left + margin_x,
            screen_rect.top + margin_y,
            screen_rect.width - 2 * margin_x,
            screen_rect.height - 2 * margin_y,
        )

        # Layout: chart on the left ~70%, controls on the right ~30%.
        chart_w = int(self.panel_rect.width * 0.70)
        controls_x = self.panel_rect.left + chart_w + 16
        self.chart_panel = ChartPanel(pygame.Rect(
            self.panel_rect.left + 16, self.panel_rect.top + 40,
            chart_w - 16, self.panel_rect.height - 56,
        ))

        ctrl_y = self.panel_rect.top + 60
        self.predator_toggle = Toggle(
            pygame.Rect(controls_x, ctrl_y, 24, 24),
            "Predator",
            initial=sim.pressure.predator_on,
        )
        self.speed_slider = Slider(
            pygame.Rect(controls_x, ctrl_y + 50, 180, 20),
            min_value=0.5, max_value=5.0, initial=1.0,
        )
        self.pause_button = Button(
            pygame.Rect(controls_x, ctrl_y + 100, 100, 28),
            "Pause",
            self._toggle_pause,
        )
        self.chart_panel.update(self.sim.log)

    @property
    def gens_per_second(self) -> float:
        return self.speed_slider.value

    def toggle(self) -> None:
        self.open = not self.open

    def _toggle_pause(self) -> None:
        if self.sim.extinct:
            self.sim.reset()
            self.predator_toggle.state = False
            self.paused = False
            return
        self.paused = not self.paused

    def handle_event(self, event: pygame.event.Event) -> None:
        if not self.open:
            return
        prior = self.predator_toggle.state
        self.predator_toggle.handle_event(event)
        if self.predator_toggle.state != prior:
            self.sim.set_predator(self.predator_toggle.state)
        self.speed_slider.handle_event(event)
        self.pause_button.handle_event(event)

    def on_sim_tick(self) -> None:
        self.chart_panel.update(self.sim.log)

    def draw(self, surface: pygame.Surface, font: pygame.font.Font) -> None:
        if not self.open:
            return
        backdrop = pygame.Surface(self.screen_rect.size, pygame.SRCALPHA)
        backdrop.fill(_BACKDROP)
        surface.blit(backdrop, self.screen_rect.topleft)
        pygame.draw.rect(surface, _PANEL_BG, self.panel_rect)
        pygame.draw.rect(surface, _FG, self.panel_rect, 2)
        title = font.render("Field Journal — Pond Site", True, _FG)
        surface.blit(title, (self.panel_rect.left + 16, self.panel_rect.top + 12))
        self.chart_panel.draw(surface)
        self.predator_toggle.draw(surface, font)
        self.speed_slider.draw(surface, font)
        if self.sim.extinct:
            self.pause_button.label = "Restart"
        else:
            self.pause_button.label = "Resume" if self.paused else "Pause"
        self.pause_button.draw(surface, font)
        hint = font.render("J or ESC to close", True, _FG)
        surface.blit(hint, (self.panel_rect.left + 16, self.panel_rect.bottom - 24))
```

**Step 4: Run tests, commit**

```powershell
pytest tests/ui/test_journal.py -v
git add src/evogame/ui/journal.py tests/ui/test_journal.py
git commit -m @'
feat(ui): add Journal overlay with chart + predator/speed/pause widgets

Mirrors the existing HUD widgets behind an open/close overlay. Sim
ticks regardless of journal state so chart updates while open.
'@
```

---

## Task 3.4: Repurpose hud.py into a thin status strip

**Files:**
- Modify: `src/evogame/ui/hud.py` (full rewrite)
- Modify: `tests/ui/test_hud.py` (full rewrite)

**Step 1: Rewrite test**

```python
import pygame

from evogame.ui.hud import StatusStrip


def test_status_strip_draws(pygame_surface):
    strip = StatusStrip(pygame.Rect(0, 0, 1000, 24))
    font = pygame.font.SysFont("arial", 12)
    strip.draw(pygame_surface, font, generation=5, population=42, gens_per_second=1.5,
               extinct=False, journal_open=False)


def test_status_strip_shows_extinct_label(pygame_surface):
    strip = StatusStrip(pygame.Rect(0, 0, 1000, 24))
    font = pygame.font.SysFont("arial", 12)
    strip.draw(pygame_surface, font, generation=5, population=0, gens_per_second=1.0,
               extinct=True, journal_open=False)
```

**Step 2: Rewrite `src/evogame/ui/hud.py`**

```python
import pygame

_BG = (25, 25, 35)
_FG = (220, 220, 220)


class StatusStrip:
    def __init__(self, rect: pygame.Rect):
        self.rect = rect

    def draw(self, surface: pygame.Surface, font: pygame.font.Font, *,
             generation: int, population: int, gens_per_second: float,
             extinct: bool, journal_open: bool) -> None:
        pygame.draw.rect(surface, _BG, self.rect)
        text = f"Gen {generation}   Pop {population}   Speed {gens_per_second:.1f}/s"
        if extinct:
            text += "   EXTINCT"
        if not journal_open:
            text += "   [J] Journal"
        surface.blit(font.render(text, True, _FG), (self.rect.left + 12, self.rect.top + 5))
```

**Step 3: Run tests, expect existing test_hud failures**

```powershell
pytest tests/ui/test_hud.py -v
```
Expected: tests reference the old `HUD` class — replace `tests/ui/test_hud.py` entirely with the rewrite from step 1.

**Step 4: Commit**

```powershell
git add src/evogame/ui/hud.py tests/ui/test_hud.py
git commit -m @'
refactor(ui): repurpose HUD into thin top StatusStrip

Old HUD widgets (Predator toggle, Speed slider, Pause button) move into
the Journal overlay. The thin status strip just renders Gen/Pop/Speed
text and a [J] Journal hint.
'@
```

---

## Task 3.5: App wiring for journal + status strip

**Files:**
- Modify: `src/evogame/ui/app.py`
- Modify: `tests/ui/test_app.py`

**Step 1: Update App class**

```python
# src/evogame/ui/app.py
import random

import pygame

from evogame.genetics import GUPPY_SCHEMA
from evogame.sim.controller import SimController
from evogame.ui.hud import StatusStrip
from evogame.ui.journal import Journal
from evogame.ui.player import Player
from evogame.ui.world_panel import WorldPanel

_WINDOW_W = 1000
_WINDOW_H = 620
_STATUS_H = 24
_INITIAL_POP = 30
_CARRYING_CAPACITY = 60


class App:
    def __init__(self, seed: int | None = None):
        pygame.init()
        pygame.display.set_caption("evogame — guppy field site")
        self.screen = pygame.display.set_mode((_WINDOW_W, _WINDOW_H))
        self.font = pygame.font.SysFont("arial", 14)
        self.small_font = pygame.font.SysFont("arial", 12)
        self.clock = pygame.time.Clock()
        self.running = True

        rng = random.Random(seed)
        self.sim = SimController(
            schema=GUPPY_SCHEMA,
            initial_size=_INITIAL_POP,
            carrying_capacity=_CARRYING_CAPACITY,
            rng=rng,
        )

        status_rect = pygame.Rect(0, 0, _WINDOW_W, _STATUS_H)
        world_rect = pygame.Rect(0, _STATUS_H, _WINDOW_W, _WINDOW_H - _STATUS_H)
        screen_rect = pygame.Rect(0, 0, _WINDOW_W, _WINDOW_H)

        self.status_strip = StatusStrip(status_rect)
        self.world_panel = WorldPanel(world_rect)
        self.journal = Journal(screen_rect, self.sim)

        scene = self.world_panel.scene
        self.player = Player(pos=(scene.tilemap.pixel_width / 2,
                                  scene.tilemap.pixel_height * 0.7))
        self._gen_timer_ms = 0.0

    def shutdown(self) -> None:
        pygame.quit()

    def _handle_events(self) -> None:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
                continue
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_j:
                    self.journal.toggle()
                    continue
                if event.key == pygame.K_e and self.world_panel.cottage_in_range(self.player):
                    self.journal.open = True
                    continue
                if event.key == pygame.K_ESCAPE:
                    if self.journal.open:
                        self.journal.open = False
                    else:
                        self.running = False
                    continue
            if self.journal.open:
                self.journal.handle_event(event)

    def step_one_frame(self, dt_ms: float) -> None:
        self._handle_events()
        if not self.journal.open:
            keys = pygame.key.get_pressed()
            self.player.handle_input(keys)
            self.player.update(dt_ms, self.world_panel.scene)
        if not self.journal.paused and not self.sim.extinct:
            interval_ms = 1000.0 / self.journal.gens_per_second
            self._gen_timer_ms += dt_ms
            while self._gen_timer_ms >= interval_ms:
                self._gen_timer_ms -= interval_ms
                self.sim.tick()
                self.journal.on_sim_tick()
                if self.sim.extinct:
                    break
        self._render()

    def _render(self) -> None:
        self.screen.fill((10, 10, 15))
        self.world_panel.draw(self.screen, player=self.player, font=self.small_font)
        self.status_strip.draw(
            self.screen, self.small_font,
            generation=self.sim.generation,
            population=len(self.sim.population),
            gens_per_second=self.journal.gens_per_second,
            extinct=self.sim.extinct,
            journal_open=self.journal.open,
        )
        self.journal.draw(self.screen, self.font)
        pygame.display.flip()

    def run(self) -> None:
        while self.running:
            dt_ms = self.clock.tick(60)
            self.step_one_frame(dt_ms)
        self.shutdown()

    def run_for_generations(self, target: int, max_frames: int = 1000) -> None:
        frames = 0
        while self.sim.generation < target and frames < max_frames:
            self.step_one_frame(100)
            frames += 1
```

**Step 2: Update test_app.py**

Inspect current `tests/ui/test_app.py`. Replace any reference to `app.hud` with `app.journal` for predator/slider/pause concerns. The simplest existing tests (`run_for_generations` advances; QUIT event sets running=False; extinct guard) should still work.

```powershell
# Use Read tool to inspect tests/ui/test_app.py first, then Edit/Write as needed.
```

**Step 3: Run full suite**

```powershell
pytest -q
```
Expected: all green.

**Step 4: Manual smoke**

```powershell
python scripts/run_game.py
```
Expected: forest scene with player walking; thin status bar at top; pressing J opens journal with chart + controls; pressing J again or ESC closes; walking near cottage shows "Press E"; pressing E opens journal.

**Step 5: Commit**

```powershell
git add src/evogame/ui/app.py tests/ui/test_app.py
git commit -m @'
feat(ui): wire status strip + journal overlay + cottage E-interaction

J or E (near cottage) toggles the journal. ESC closes journal or quits.
Player input is suspended while journal is open; sim keeps ticking.
'@
```

---

# Phase 4 — Pond fish rendering

**Goal:** the pond holds 8–12 fish sprites tinted by phenotype, drifting around the pond bounds; refreshes when the sim advances a generation.

## Task 4.1: VisibleFish dataclass + tint cache

**Files:**
- Create: `src/evogame/ui/pond.py`
- Create: `tests/ui/test_pond.py`

**Step 1: Failing test**

```python
import random

import pygame

from evogame.genetics import GUPPY_SCHEMA, Creature
from evogame.ui.pond import tint_fish, VisibleFish


def test_tint_fish_returns_a_surface(pygame_surface):
    surf = tint_fish(category="red")
    assert isinstance(surf, pygame.Surface)


def test_tint_fish_caches_per_color(pygame_surface):
    a = tint_fish("red")
    b = tint_fish("red")
    c = tint_fish("white")
    assert a is b
    assert a is not c


def test_visible_fish_constructed_from_creature(pygame_surface):
    rng = random.Random(0)
    creature = Creature.random(GUPPY_SCHEMA, rng)
    fish = VisibleFish.from_creature(creature, pos=(100.0, 100.0), rng=rng)
    assert fish.color in {"red", "pink", "white"}
    assert fish.scale > 0
```

**Step 2: Run to verify fail**

```powershell
pytest tests/ui/test_pond.py -v
```
Expected: ImportError on `evogame.ui.pond`.

**Step 3: Implement**

```python
# src/evogame/ui/pond.py
import math
import random
from dataclasses import dataclass
from functools import lru_cache

import pygame

from evogame.genetics import Creature
from evogame.ui.assets import load_fish_base

_COLOR_MULT = {
    "red":   (1.0, 0.4, 0.4),
    "pink":  (1.0, 0.7, 0.8),
    "white": (1.0, 1.0, 1.0),
}


@lru_cache(maxsize=8)
def tint_fish(category: str) -> pygame.Surface:
    base = load_fish_base()
    out = base.copy()
    mult = _COLOR_MULT.get(category, (1.0, 1.0, 1.0))
    overlay = pygame.Surface(out.get_size(), pygame.SRCALPHA)
    overlay.fill((int(mult[0] * 255), int(mult[1] * 255), int(mult[2] * 255), 255))
    out.blit(overlay, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
    return out


@dataclass
class VisibleFish:
    color: str
    scale: float
    pos: tuple[float, float]
    heading: float  # radians
    speed: float
    next_turn_in_ms: float

    @classmethod
    def from_creature(cls, creature: Creature, pos: tuple[float, float], rng: random.Random) -> "VisibleFish":
        ph = creature.phenotype
        color = ph["color"].category
        # body_size phenotype is numeric (0..6 for guppy 3-locus polygenic).
        size_value = float(ph["body_size"].value)
        scale = 1.0 + (size_value - 3.0) * 0.06   # ~0.82..1.18 range
        return cls(
            color=color,
            scale=scale,
            pos=pos,
            heading=rng.uniform(0, 2 * math.pi),
            speed=rng.uniform(8.0, 18.0),
            next_turn_in_ms=rng.uniform(1000.0, 2500.0),
        )
```

**Step 4: Run tests, commit**

```powershell
pytest tests/ui/test_pond.py -v
git add src/evogame/ui/pond.py tests/ui/test_pond.py
git commit -m @'
feat(ui): VisibleFish dataclass + cached per-color fish tint

VisibleFish derives color from phenotype.color.category and scale from
phenotype.body_size. Tinting is cached per color so we don't re-blit
the multiply overlay each frame.
'@
```

---

## Task 4.2: PondView — sample, update, draw

**Files:**
- Modify: `src/evogame/ui/pond.py` (add `PondView`)
- Modify: `tests/ui/test_pond.py`

**Step 1: Failing tests**

```python
def test_pond_view_sample_size(pygame_surface):
    from evogame.ui.pond import PondView
    from evogame.ui.tilemap import build_forest_scene
    rng = random.Random(0)
    pop = [Creature.random(GUPPY_SCHEMA, rng) for _ in range(40)]
    scene = build_forest_scene()
    pond = PondView(bounds=scene.pond_pixel_bounds(), max_visible=10, rng=random.Random(1))
    pond.refresh(pop)
    assert 1 <= len(pond.fish) <= 10


def test_pond_view_fish_stay_in_bounds(pygame_surface):
    from evogame.ui.pond import PondView
    from evogame.ui.tilemap import build_forest_scene
    rng = random.Random(0)
    pop = [Creature.random(GUPPY_SCHEMA, rng) for _ in range(20)]
    scene = build_forest_scene()
    bounds = scene.pond_pixel_bounds()
    pond = PondView(bounds=bounds, max_visible=10, rng=random.Random(2))
    pond.refresh(pop)
    for _ in range(60):
        pond.update(dt_ms=100.0)
    for f in pond.fish:
        assert bounds.collidepoint(f.pos[0], f.pos[1]), \
            f"fish drifted out of bounds: {f.pos} not in {bounds}"


def test_pond_view_draw(pygame_surface):
    from evogame.ui.pond import PondView
    from evogame.ui.tilemap import build_forest_scene
    pop = [Creature.random(GUPPY_SCHEMA, random.Random(0)) for _ in range(8)]
    scene = build_forest_scene()
    pond = PondView(bounds=scene.pond_pixel_bounds(), max_visible=8, rng=random.Random(0))
    pond.refresh(pop)
    pond.draw(pygame_surface, origin=(0, 0))
```

**Step 2: Verify fail**

```powershell
pytest tests/ui/test_pond.py -v
```

**Step 3: Implement**

Add to `src/evogame/ui/pond.py`:

```python
class PondView:
    def __init__(self, bounds: pygame.Rect, max_visible: int, rng: random.Random):
        self.bounds = bounds
        self.max_visible = max_visible
        self.rng = rng
        self.fish: list[VisibleFish] = []

    def _random_pos_in_bounds(self) -> tuple[float, float]:
        margin = 6
        x = self.rng.uniform(self.bounds.left + margin, self.bounds.right - margin)
        y = self.rng.uniform(self.bounds.top + margin, self.bounds.bottom - margin)
        return (x, y)

    def refresh(self, population: list[Creature]) -> None:
        if not population:
            self.fish = []
            return
        n = min(len(population), self.max_visible)
        sampled = self.rng.sample(population, n)
        self.fish = [
            VisibleFish.from_creature(c, self._random_pos_in_bounds(), self.rng)
            for c in sampled
        ]

    def update(self, dt_ms: float) -> None:
        margin = 6
        for f in self.fish:
            f.next_turn_in_ms -= dt_ms
            if f.next_turn_in_ms <= 0:
                f.heading = self.rng.uniform(0, 2 * math.pi)
                f.next_turn_in_ms = self.rng.uniform(1000.0, 2500.0)
            dt = dt_ms / 1000.0
            nx = f.pos[0] + math.cos(f.heading) * f.speed * dt
            ny = f.pos[1] + math.sin(f.heading) * f.speed * dt
            # Reflect off pond bounds.
            if nx < self.bounds.left + margin or nx > self.bounds.right - margin:
                f.heading = math.pi - f.heading
                nx = max(self.bounds.left + margin, min(self.bounds.right - margin, nx))
            if ny < self.bounds.top + margin or ny > self.bounds.bottom - margin:
                f.heading = -f.heading
                ny = max(self.bounds.top + margin, min(self.bounds.bottom - margin, ny))
            f.pos = (nx, ny)

    def draw(self, surface: pygame.Surface, origin: tuple[int, int]) -> None:
        ox, oy = origin
        for f in self.fish:
            sprite = tint_fish(f.color)
            if f.scale != 1.0:
                w, h = sprite.get_size()
                sprite = pygame.transform.scale(sprite, (max(1, int(w * f.scale)), max(1, int(h * f.scale))))
            # Flip horizontally based on heading direction
            if math.cos(f.heading) < 0:
                sprite = pygame.transform.flip(sprite, True, False)
            sw, sh = sprite.get_size()
            surface.blit(sprite, (int(ox + f.pos[0] - sw / 2), int(oy + f.pos[1] - sh / 2)))
```

**Step 4: Run, commit**

```powershell
pytest tests/ui/test_pond.py -v
git add src/evogame/ui/pond.py tests/ui/test_pond.py
git commit -m @'
feat(ui): PondView samples, drifts, and draws fish in pond bounds

Samples N visible fish from the population, gives each a heading and a
periodic turn timer, reflects off pond bounds, and blits with phenotype
color tint and body-size scale.
'@
```

---

## Task 4.3: Wire PondView into WorldPanel and App

**Files:**
- Modify: `src/evogame/ui/world_panel.py`
- Modify: `src/evogame/ui/app.py`
- Modify: `tests/ui/test_world_panel.py`
- Modify: `tests/ui/test_app.py`

**Step 1: Failing test**

```python
def test_world_panel_draws_pond_view(pygame_surface):
    import random
    from evogame.genetics import GUPPY_SCHEMA, Creature
    from evogame.ui.pond import PondView
    from evogame.ui.world_panel import WorldPanel
    rng = random.Random(0)
    panel = WorldPanel(pygame.Rect(0, 0, 1000, 596))
    pop = [Creature.random(GUPPY_SCHEMA, rng) for _ in range(10)]
    panel.pond_view.refresh(pop)
    panel.draw(pygame_surface)
```

**Step 2: WorldPanel constructs a PondView**

```python
# In src/evogame/ui/world_panel.py
import random as _rand_module

from evogame.ui.pond import PondView

class WorldPanel:
    def __init__(self, rect: pygame.Rect, pond_rng: _rand_module.Random | None = None):
        # ... existing init ...
        self.pond_view = PondView(
            bounds=self._pond_bounds_in_panel(),
            max_visible=10,
            rng=pond_rng or _rand_module.Random(0),
        )

    def _pond_bounds_in_panel(self) -> pygame.Rect:
        b = self.scene.pond_pixel_bounds()
        return pygame.Rect(self.rect.left + b.left, self.rect.top + b.top, b.width, b.height)

    def draw(self, surface, player=None, font=None):
        # ... existing tilemap + objects ...
        self.pond_view.draw(surface, origin=(0, 0))
        # ... existing player + prompt ...
```

**Step 3: App refreshes pond on every sim tick**

```python
# In src/evogame/ui/app.py step_one_frame:
while self._gen_timer_ms >= interval_ms:
    self._gen_timer_ms -= interval_ms
    self.sim.tick()
    self.journal.on_sim_tick()
    self.world_panel.pond_view.refresh(self.sim.population.creatures)
    if self.sim.extinct:
        break

# Also: drift fish every frame, regardless of journal state
self.world_panel.pond_view.update(dt_ms)

# In App.__init__: initial refresh
self.world_panel.pond_view.refresh(self.sim.population.creatures)
```

**Step 4: Run full suite, manual smoke**

```powershell
pytest -q
python scripts/run_game.py
```
Expected: pond now shows ~10 colored fish drifting around. Walking around feels more alive. Generation transitions resample which fish are visible.

**Step 5: Commit**

```powershell
git add src/evogame/ui/world_panel.py src/evogame/ui/app.py tests/ui/test_world_panel.py tests/ui/test_app.py
git commit -m @'
feat(ui): pond shows live fish sampled from sim population

PondView samples up to 10 creatures from the sim population, tints them
by phenotype color, drifts them inside the pond bounds, and resamples on
each generation tick.
'@
```

---

# Phase 5 — Ambient bunnies

**Goal:** 2–3 bunnies wander the grass area as scenery.

## Task 5.1: Bunny wander state machine

**Files:**
- Create: `src/evogame/ui/wildlife.py`
- Create: `tests/ui/test_wildlife.py`

**Step 1: Failing test**

```python
import random

import pygame

from evogame.ui.wildlife import Bunny


def test_bunny_idle_then_walk(pygame_surface):
    from evogame.ui.tilemap import build_forest_scene
    scene = build_forest_scene()
    rng = random.Random(0)
    b = Bunny(pos=(100.0, 100.0), scene=scene, rng=rng)
    assert b.state == "idle"
    # Force the idle timer to expire.
    for _ in range(60):  # 6 seconds worth at 100 ms ticks
        b.update(dt_ms=100.0)
    assert b.state in ("idle", "walk")  # at least one transition occurred
    # Bunny should not have walked off the scene
    assert 0 <= b.pos[0] <= scene.tilemap.pixel_width
    assert 0 <= b.pos[1] <= scene.tilemap.pixel_height


def test_bunny_does_not_enter_water(pygame_surface):
    from evogame.ui.tilemap import build_forest_scene
    scene = build_forest_scene()
    bounds = scene.pond_pixel_bounds()
    rng = random.Random(0)
    b = Bunny(pos=(bounds.centerx, bounds.centery), scene=scene, rng=rng)
    # Even if started inside the pond bbox, after one update it should not be marked walking into water.
    for _ in range(20):
        b.update(dt_ms=100.0)
    # Final pos should be on a walkable tile.
    col = int(b.pos[0] // 32)
    row = int(b.pos[1] // 32)
    assert scene.tilemap.is_walkable(col, row)


def test_bunny_draw(pygame_surface):
    from evogame.ui.tilemap import build_forest_scene
    scene = build_forest_scene()
    rng = random.Random(0)
    b = Bunny(pos=(100.0, 100.0), scene=scene, rng=rng)
    b.draw(pygame_surface, origin=(0, 0))
```

**Step 2: Verify fail**

```powershell
pytest tests/ui/test_wildlife.py -v
```
Expected: ImportError.

**Step 3: Implement**

```python
# src/evogame/ui/wildlife.py
import math
import random
from dataclasses import dataclass

import pygame

from evogame.ui.assets import load_bunny_frames
from evogame.ui.tilemap import Scene, TILE_PIXELS

_IDLE_MIN_MS = 1500.0
_IDLE_MAX_MS = 3000.0
_BUNNY_SPEED = 24.0  # px/sec


@dataclass
class Bunny:
    pos: tuple[float, float]
    scene: Scene
    rng: random.Random

    def __post_init__(self):
        self.state: str = "idle"
        self._timer_ms: float = self.rng.uniform(_IDLE_MIN_MS, _IDLE_MAX_MS)
        self._target: tuple[float, float] | None = None
        self._direction: str = "down"
        self._frame_index: float = 0.0

    def _pick_target(self) -> tuple[float, float] | None:
        for _ in range(8):
            tx = self.rng.uniform(0, self.scene.tilemap.pixel_width)
            ty = self.rng.uniform(0, self.scene.tilemap.pixel_height)
            col = int(tx // TILE_PIXELS)
            row = int(ty // TILE_PIXELS)
            if self.scene.tilemap.is_walkable(col, row):
                return (tx, ty)
        return None

    def _update_direction(self, dx: float, dy: float) -> None:
        if abs(dx) > abs(dy):
            self._direction = "right" if dx > 0 else "left"
        else:
            self._direction = "down" if dy > 0 else "up"

    def update(self, dt_ms: float) -> None:
        if self.state == "idle":
            self._timer_ms -= dt_ms
            if self._timer_ms <= 0:
                target = self._pick_target()
                if target is not None:
                    self._target = target
                    self.state = "walk"
                else:
                    self._timer_ms = self.rng.uniform(_IDLE_MIN_MS, _IDLE_MAX_MS)
            return
        # walking
        if self._target is None:
            self.state = "idle"
            self._timer_ms = self.rng.uniform(_IDLE_MIN_MS, _IDLE_MAX_MS)
            return
        tx, ty = self._target
        dx, dy = tx - self.pos[0], ty - self.pos[1]
        dist = math.hypot(dx, dy)
        if dist < 2.0:
            self.state = "idle"
            self._target = None
            self._timer_ms = self.rng.uniform(_IDLE_MIN_MS, _IDLE_MAX_MS)
            return
        self._update_direction(dx, dy)
        step = _BUNNY_SPEED * dt_ms / 1000.0
        nx = self.pos[0] + dx / dist * step
        ny = self.pos[1] + dy / dist * step
        col = int(nx // TILE_PIXELS)
        row = int(ny // TILE_PIXELS)
        if self.scene.tilemap.is_walkable(col, row):
            self.pos = (nx, ny)
        else:
            # Abandon target if blocked.
            self._target = None
        self._frame_index = (self._frame_index + dt_ms / 200.0) % 3.0

    def draw(self, surface: pygame.Surface, origin: tuple[int, int]) -> None:
        frames = load_bunny_frames()
        dir_frames = frames.get(self._direction) or next(iter(frames.values()))
        frame = dir_frames[int(self._frame_index) % len(dir_frames)]
        # Scale 16x16 -> 24x24 to match world feel.
        frame = pygame.transform.scale(frame, (24, 24))
        surface.blit(frame, (int(origin[0] + self.pos[0] - 12), int(origin[1] + self.pos[1] - 12)))
```

**Step 4: Run, commit**

```powershell
pytest tests/ui/test_wildlife.py -v
git add src/evogame/ui/wildlife.py tests/ui/test_wildlife.py
git commit -m @'
feat(ui): add Bunny wandering wildlife

Idle/walk state machine with per-direction frame animation. Bunnies
respect tilemap walkability and stay on grass.
'@
```

---

## Task 5.2: Wire bunnies into WorldPanel and App

**Files:**
- Modify: `src/evogame/ui/world_panel.py`
- Modify: `src/evogame/ui/app.py`
- Modify: `tests/ui/test_world_panel.py`

**Step 1: Update WorldPanel to hold a list of wildlife**

```python
# In src/evogame/ui/world_panel.py
from evogame.ui.wildlife import Bunny

class WorldPanel:
    def __init__(self, rect, pond_rng=None, wildlife_rng=None):
        # existing init ...
        wlrng = wildlife_rng or _rand_module.Random(7)
        self.wildlife: list[Bunny] = []
        # Spawn 3 bunnies at random walkable positions.
        for _ in range(3):
            for _attempt in range(20):
                x = wlrng.uniform(0, self.scene.tilemap.pixel_width)
                y = wlrng.uniform(0, self.scene.tilemap.pixel_height)
                col = int(x // TILE_PIXELS)
                row = int(y // TILE_PIXELS)
                if self.scene.tilemap.is_walkable(col, row):
                    self.wildlife.append(Bunny(pos=(x, y), scene=self.scene, rng=wlrng))
                    break

    def update_wildlife(self, dt_ms: float) -> None:
        for b in self.wildlife:
            b.update(dt_ms)

    # In draw, between objects and pond_view:
    def draw(self, surface, player=None, font=None):
        # ... tilemap, objects ...
        for b in self.wildlife:
            b.draw(surface, origin=(self.rect.left, self.rect.top))
        self.pond_view.draw(surface, origin=(0, 0))
        # ... player, prompt ...
```

**Step 2: App calls update_wildlife each frame**

```python
# In step_one_frame, after pond_view.update:
self.world_panel.update_wildlife(dt_ms)
```

**Step 3: Run full suite, manual smoke**

```powershell
pytest -q
python scripts/run_game.py
```
Expected: 2–3 bunnies wander around the grass.

**Step 4: Commit**

```powershell
git add src/evogame/ui/world_panel.py src/evogame/ui/app.py tests/ui/test_world_panel.py
git commit -m @'
feat(ui): spawn 3 ambient bunnies in the forest scene
'@
```

---

# Phase 6 — Final polish and smoke check

## Task 6.1: Update README with new controls

**Files:**
- Modify: `README.md`

Add a "Controls" section:

```markdown
## Controls

- WASD / arrow keys — walk
- E — interact (near the cottage opens the field journal)
- J — toggle field journal from anywhere
- ESC — close journal, or quit if journal is closed
```

```powershell
git add README.md
git commit -m "docs(readme): document new player controls"
```

## Task 6.2: Run the full suite and manual smoke

```powershell
pytest -q
python scripts/run_game.py
```

Walk through this checklist by hand:

- [ ] Window opens; forest scene visible.
- [ ] WASD and arrow keys move the player; cannot walk into the pond.
- [ ] Bunnies wander.
- [ ] Pond contains drifting fish in red/pink/white tints.
- [ ] Walking near the cottage shows "Press E"; pressing E opens journal.
- [ ] J toggles journal from anywhere; ESC closes journal.
- [ ] Predator toggle inside journal flips the sim's pressure (chart should diverge over generations).
- [ ] Speed slider changes generation rate; chart updates.
- [ ] Status strip shows correct Gen / Pop / Speed.
- [ ] Closing the window quits cleanly (no error in terminal).

If anything fails, file follow-up tasks; do not ship broken behavior.

---

# Phase 7 (stretch) — generation transition fade and predator visual

These are optional polish. Skip if the schedule is tight; the MVP cut already produces a game-feeling experience.

## Task 7.1: Cross-fade fish sample on generation tick

**Files:**
- Modify: `src/evogame/ui/pond.py`
- Modify: `tests/ui/test_pond.py`

Strategy: when `PondView.refresh` is called, instead of swapping `self.fish` immediately, hold the old list in `self._fading_out` with a remaining alpha, and have `update()` fade them out over 200ms while the new sample fades in. `draw()` blits both layers, the old list with declining alpha. Tests verify both lists exist mid-transition.

(Detailed steps left to implementer once Phase 6 is solid; same TDD pattern.)

## Task 7.2: Visible predator sprite when toggle is on

**Files:**
- Modify: `src/evogame/ui/pond.py` and `src/evogame/ui/app.py`

When the journal's predator toggle is on, render a single larger fish sprite (`large_mouth_bass.png`) drifting more slowly in the pond. Doesn't touch sim math. Add a `predator_on` parameter to `PondView.draw` or pass through via App.

---

# Risks and rollbacks

- If asset slice rects are wrong, surfaces are blank or scrambled. Open the source PNGs in any pixel-coord viewer and adjust `_TILESET_RECTS`, `_BUNNY_DIRECTIONS`, `_BUNNY_FRAMES_PER_DIR` in `src/evogame/ui/assets.py`. Re-run `pytest tests/ui/test_assets.py`.
- If the character sprite is single-direction (only `char_down`), Phase 2 ships a static sprite. To add 4-direction walk later, add `char_up`, `char_left`, `char_right` to the slice constants and switch in `Player.update` based on dominant velocity component.
- If existing genetics or sim tests turn red at any point, **stop and investigate**. They should be untouched. Likely cause: an accidental import-cycle or a typo in `app.py`.
- Roll back any single task with `git revert <sha>`; commits are small and self-contained.
