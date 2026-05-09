"""Asset loaders for the field-researcher game.

Slices the vendored sprite sheets into named surfaces. Slice rects are
hand-coded constants verified against the source PNGs.

Notes on the source assets:
- ``free.png`` is a 208x160 grass/dirt/houses tileset. We use it for
  grass, the tree, and the cottage. It has no water tiles and no
  humanoid character, so those come from other sheets.
- ``Water+.png`` is a 192x224 water tileset on a 16x16 grid. We pull
  one clean water tile out of it and reuse it for the four ``water_*``
  corners (the surrounding rendering varies the tile elsewhere; for
  now a single tile is plenty better-looking than synthesized blue
  squares).
- ``lablady_spritesheet_BOXED.png`` is a 1112x256 character sheet on
  a 32x32 grid. Each cell has a 1-2px yellow guide border around it
  (hence the BOXED suffix), so we slice the inside of each cell at
  offset (2, 2) with a 28x28 size to drop the yellow lines. The sheet
  is split into four horizontal blocks; the WALK block starts at
  ``_LABLADY_WALK_BLOCK_X`` and contains WALK(right/left/up/down) on
  the first four rows, four frames each.
- ``MiniBunny.png`` is a single-direction sheet (all frames face the
  same way), so ``load_bunny_frames`` returns the same frame layout
  under every direction key - but each direction now gets independent
  Surface copies so callers can mutate them safely.
"""

import os
from functools import lru_cache

import pygame

# .../<project>/  - climbs out of src/evogame/ui/assets.py
_HERE = os.path.dirname(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
)
_ASSETS_ROOT = os.path.join(_HERE, "assets")

_TILESET_PATH = os.path.join(_ASSETS_ROOT, "tilesets", "free_version", "free.png")
_FISH_PATH = os.path.join(
    _ASSETS_ROOT, "fish", "NewRiverFishAssetPack1.0",
    "Cenrarchidae", "Panfish", "bluegill_panfish.png",
)
_BUNNY_PATH = os.path.join(
    _ASSETS_ROOT, "animals", "MinifolksForestAnimals", "Outline", "MiniBunny.png",
)
_LABLADY_PATH = os.path.join(
    _ASSETS_ROOT, "characters", "lablady", "lablady_spritesheet_BOXED.png",
)
_WATER_PATH = os.path.join(
    _ASSETS_ROOT, "tilesets", "water_plus", "Water+.png",
)
_TREE_PACK_ROOT = os.path.join(_ASSETS_ROOT, "trees", "tree_pack")
_POND_COMPOSITE_PATH = os.path.join(_ASSETS_ROOT, "water", "wateranimate2.png")

_TILE = 16

# Slice rects for sprites in free.png. Verified against the PNG by
# computing per-tile alpha density and per-sprite bounding boxes.
_TILESET_RECTS: dict[str, tuple[int, int, int, int]] = {
    # tile (1, 0) - solid grass
    "grass":     (16,   0, _TILE, _TILE),
    # tree at the right of the houses row, bbox ~(160, 48)-(175, 79)
    "tree":      (160, 48, 16, 32),
    # left cottage; bbox (0, 55)-(79, 127), tile-aligned to (0, 48, 80, 80)
    "cottage":   (0,   48, 80, 80),
}

# Water+.png is on a 16x16 grid. (48, 0, 16, 16) is a clean wave-pattern
# water tile near the top of the sheet. We reuse it for all four water
# corners; varying the corners would need explicit edge tiles which
# Water+.png doesn't expose in a 4-corner layout.
_WATER_TILE_RECT: tuple[int, int, int, int] = (48, 0, _TILE, _TILE)
# TODO: replace with NW/NE/SW/SE shoreline edge tiles from Water+.png
# when pond rendering needs visible corners. For now all 4 keys point
# at the same clean wave tile.
_WATER_KEYS: tuple[str, ...] = ("water_nw", "water_ne", "water_sw", "water_se")

# Lablady spritesheet layout. Cells are 32x32 with a 1-2px yellow guide
# border. We slice 28x28 at offset (2, 2) inside each cell to drop the
# yellow lines.
_LABLADY_CELL = 32
_LABLADY_SPRITE = 28
_LABLADY_TRIM = 2

# Block 3 (zero-indexed: 2) of the four horizontal blocks holds the WALK
# rows. Yellow column origins step by 32: 564, 596, 628, 660 (we slice
# these for WALK frames 0-3). Subsequent columns continue the pattern
# past 660 but the WALK row is only 4 frames wide.
_LABLADY_WALK_BLOCK_X = 564

# Within the WALK block, rows 0..3 are right / left / up / down (in that
# order, matching the labels printed beside the rows on the sheet).
_LABLADY_WALK_ROWS: dict[str, int] = {
    "right": 0,
    "left":  1,
    "up":    2,
    "down":  3,
}
# Each WALK row has 4 frames in the first 4 columns of the block.
_LABLADY_WALK_FRAME_COUNT = 4

# The placeholder ``char_down`` tile used by ``load_tileset`` is the
# first frame of WALK(down) - same sprite the player will animate from.
_LABLADY_CHAR_DOWN_RECT: tuple[int, int, int, int] = (
    _LABLADY_WALK_BLOCK_X + _LABLADY_TRIM,
    _LABLADY_WALK_ROWS["down"] * _LABLADY_CELL + _LABLADY_TRIM,
    _LABLADY_SPRITE,
    _LABLADY_SPRITE,
)

# wateranimate2.png is 576x386. The right portion holds composite tiles;
# the rect below carves out the grass-bordered pond — a single 96x96 tile
# we can scale to fit the pond's bounding box and blit over the grass
# tilemap. Verified by visual inspection plus pixel sampling at the four
# edges: bottom row at y=187..191 is solid grass color (47, 129, 54),
# confirming no neighboring-tile bleed.
_POND_COMPOSITE_RECT: tuple[int, int, int, int] = (384, 96, 96, 96)

# Tree Pack color suffixes as they appear in the source filenames.
# The pack uses ALL CAPS suffixes with spaces (e.g. "TREE 6_YELLOWISH GREEN.png").
_TREE_COLOR_SUFFIXES: dict[str, str] = {
    "green": "GREEN",
    "teal": "TEAL",
    "yellowish_green": "YELLOWISH GREEN",
    "sandy_green": "SANDY GREEN",
    "red": "RED",
    "orange": "ORANGE",
    "yellow": "YELLOW",
    "rose": "ROSE",
    "purple": "PURPLE",
}

_BUNNY_TILE = 16
# MiniBunny.png is a single-direction sheet. We pick three clean frames
# from the top row of bunny sprites (y=16, x=0/16/32). Each direction
# key gets independent Surface copies so callers can mutate freely.
_BUNNY_DIRECTIONS = ("down", "up", "left", "right")
_BUNNY_FRAME_RECTS: tuple[tuple[int, int, int, int], ...] = (
    (0,  16, _BUNNY_TILE, _BUNNY_TILE),
    (16, 16, _BUNNY_TILE, _BUNNY_TILE),
    (32, 16, _BUNNY_TILE, _BUNNY_TILE),
)


def _maybe_convert_alpha(surface: pygame.Surface) -> pygame.Surface:
    """Call ``convert_alpha`` if a display is set; otherwise return as-is.

    ``convert_alpha`` is a no-op surface optimization that requires
    ``pygame.display.set_mode`` to have been called. In headless tests
    we run without a display, so we skip the conversion.
    """
    if pygame.display.get_surface() is not None:
        return surface.convert_alpha()
    return surface


@lru_cache(maxsize=1)
def _load_tileset_image() -> pygame.Surface:
    return _maybe_convert_alpha(pygame.image.load(_TILESET_PATH))


@lru_cache(maxsize=1)
def _load_fish_image() -> pygame.Surface:
    return _maybe_convert_alpha(pygame.image.load(_FISH_PATH))


@lru_cache(maxsize=1)
def _load_bunny_image() -> pygame.Surface:
    return _maybe_convert_alpha(pygame.image.load(_BUNNY_PATH))


@lru_cache(maxsize=1)
def _load_lablady_image() -> pygame.Surface:
    return _maybe_convert_alpha(pygame.image.load(_LABLADY_PATH))


@lru_cache(maxsize=1)
def _load_water_image() -> pygame.Surface:
    return _maybe_convert_alpha(pygame.image.load(_WATER_PATH))


@lru_cache(maxsize=1)
def _load_pond_composite_image() -> pygame.Surface:
    return _maybe_convert_alpha(pygame.image.load(_POND_COMPOSITE_PATH))


@lru_cache(maxsize=32)
def _load_tree_image(tree_id: str, color: str) -> pygame.Surface:
    """Load and cache a tree sprite by id and color name.

    Tree 9's PNGs are misnamed ``TREE 8_*.png`` in the source pack
    (only ``TREE 9_ROSE.png`` follows the expected naming). We try
    the canonical filename first and fall back to the typo'd one.
    """
    suffix = _TREE_COLOR_SUFFIXES.get(color)
    if suffix is None:
        raise ValueError(
            f"Unknown tree color {color!r}; expected one of "
            f"{sorted(_TREE_COLOR_SUFFIXES)}"
        )
    folder = os.path.join(_TREE_PACK_ROOT, f"Tree {tree_id}")
    candidates = [f"TREE {tree_id}_{suffix}.png"]
    if tree_id == "9":
        # Tree 9 folder ships TREE 8_*.png for most colors due to a
        # typo in the source pack.
        candidates.append(f"TREE 8_{suffix}.png")
    for name in candidates:
        path = os.path.join(folder, name)
        if os.path.exists(path):
            return _maybe_convert_alpha(pygame.image.load(path))
    raise FileNotFoundError(
        f"No tree sprite found for tree_id={tree_id!r}, color={color!r}; "
        f"tried {candidates} in {folder}"
    )


def _lablady_walk_rect(direction: str, frame_index: int) -> pygame.Rect:
    """Return the trimmed slice rect for one lablady WALK frame."""
    row = _LABLADY_WALK_ROWS[direction]
    x = _LABLADY_WALK_BLOCK_X + frame_index * _LABLADY_CELL + _LABLADY_TRIM
    y = row * _LABLADY_CELL + _LABLADY_TRIM
    return pygame.Rect(x, y, _LABLADY_SPRITE, _LABLADY_SPRITE)


def load_tileset() -> dict[str, pygame.Surface]:
    """Return a dict of named tile surfaces.

    ``grass``, ``tree``, and ``cottage`` come from ``free.png``. The
    four ``water_*`` keys come from ``Water+.png`` and currently all
    point at the same clean water tile. ``char_down`` comes from the
    lablady WALK(down) frame 0.
    """
    sheet = _load_tileset_image()
    out: dict[str, pygame.Surface] = {}
    for name, (x, y, w, h) in _TILESET_RECTS.items():
        out[name] = sheet.subsurface(pygame.Rect(x, y, w, h)).copy()

    water_sheet = _load_water_image()
    water_tile = water_sheet.subsurface(pygame.Rect(*_WATER_TILE_RECT)).copy()
    for name in _WATER_KEYS:
        out[name] = water_tile.copy()

    lablady_sheet = _load_lablady_image()
    out["char_down"] = lablady_sheet.subsurface(
        pygame.Rect(*_LABLADY_CHAR_DOWN_RECT)
    ).copy()

    return out


def load_fish_base() -> pygame.Surface:
    """Return the bluegill panfish sprite as a single surface."""
    return _load_fish_image().copy()


def load_bunny_frames() -> dict[str, list[pygame.Surface]]:
    """Return per-direction lists of bunny animation frames.

    The source sheet only contains a single facing direction, so the
    same frame layout is reused for every direction. Each direction
    gets independent ``Surface`` copies so mutating one direction's
    frames does not corrupt the others.
    """
    sheet = _load_bunny_image()
    return {
        direction: [
            sheet.subsurface(pygame.Rect(*rect)).copy()
            for rect in _BUNNY_FRAME_RECTS
        ]
        for direction in _BUNNY_DIRECTIONS
    }


def load_tree_sprite(tree_id: str, color: str = "green") -> pygame.Surface:
    """Return a single tree sprite from the Pixel Art Tree Pack.

    ``tree_id`` is the tree number ("1".."15"). ``color`` is one of
    the keys of ``_TREE_COLOR_SUFFIXES``. Each call returns a fresh
    ``Surface`` copy so callers may tint or mutate freely without
    affecting the cached source image.
    """
    sheet = _load_tree_image(tree_id, color)
    return sheet.copy()


def load_pond_composite() -> pygame.Surface:
    """Return the grass-bordered pond composite tile.

    Sliced from ``wateranimate2.png`` at ``_POND_COMPOSITE_RECT``.
    Callers typically scale this to the pond's bounding box and blit
    it over the underlying grass tilemap.
    """
    sheet = _load_pond_composite_image()
    return sheet.subsurface(pygame.Rect(*_POND_COMPOSITE_RECT)).copy()


def load_player_walk_frames() -> dict[str, list[pygame.Surface]]:
    """Return per-direction WALK animation frames for the player.

    Slices four frames out of each WALK row of the lablady spritesheet.
    Each direction gets independent ``Surface`` copies so the player's
    animation system can tint or mutate frames without aliasing.
    """
    sheet = _load_lablady_image()
    out: dict[str, list[pygame.Surface]] = {}
    for direction in _LABLADY_WALK_ROWS:
        frames = []
        for i in range(_LABLADY_WALK_FRAME_COUNT):
            rect = _lablady_walk_rect(direction, i)
            frames.append(sheet.subsurface(rect).copy())
        out[direction] = frames
    return out
