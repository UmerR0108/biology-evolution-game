"""Asset loaders for the field-researcher game.

Slices the vendored sprite sheets into named surfaces. Slice rects are
hand-coded constants verified against the source PNGs.

Notes on the source assets:
- ``free.png`` is a 208x160 grass/dirt/houses tileset. It has no water
  tiles, so the four ``water_*`` surfaces are synthesized blue squares
  rather than sliced from the sheet.
- It also has no humanoid character, so ``char_down`` uses a chicken
  sprite from the bottom row as a placeholder.
- ``MiniBunny.png`` is a single-direction sheet (all frames face the same
  way), so ``load_bunny_frames`` aliases the same frame list under every
  direction key the caller asks for.
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

_TILE = 16

# Slice rects for sprites that are actually present in free.png. Verified
# against the PNG by computing per-tile alpha density and per-sprite
# bounding boxes - see the task plan / commit message for details.
_TILESET_RECTS: dict[str, tuple[int, int, int, int]] = {
    # tile (1, 0) - solid grass
    "grass":     (16,   0, _TILE, _TILE),
    # tree at the right of the houses row, bbox ~(160, 48)-(175, 79)
    "tree":      (160, 48, 16, 32),
    # left cottage; bbox (0, 55)-(79, 127), tile-aligned to (0, 48, 80, 80)
    "cottage":   (0,   48, 80, 80),
    # placeholder character: a chicken at tile (0, 8) since free.png has
    # no humanoid; bbox (2, 132)-(13, 143)
    "char_down": (0,  128, 16, 16),
}

# free.png has no water tiles, so the water corners are synthesized.
_WATER_SURFACE_SIZE = (_TILE, _TILE)
_WATER_COLORS: dict[str, tuple[int, int, int]] = {
    # Slightly varied shades so the four corners aren't visually identical.
    "water_nw": (60, 110, 170),
    "water_ne": (70, 120, 180),
    "water_sw": (50, 100, 160),
    "water_se": (65, 115, 175),
}

_BUNNY_TILE = 16
# MiniBunny.png is a single-direction sheet. We pick three clean frames
# from the top row of bunny sprites (y=16, x=0/16/32) and alias them to
# every requested direction.
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


def _make_water_tile(color: tuple[int, int, int]) -> pygame.Surface:
    surf = pygame.Surface(_WATER_SURFACE_SIZE, pygame.SRCALPHA)
    surf.fill((*color, 255))
    return surf


def load_tileset() -> dict[str, pygame.Surface]:
    """Return a dict of named tile surfaces from the free.png sheet.

    The ``water_*`` keys are synthesized colored squares because the
    source tileset has no water tiles. All other keys are sliced from
    ``free.png``.
    """
    sheet = _load_tileset_image()
    out: dict[str, pygame.Surface] = {}
    for name, (x, y, w, h) in _TILESET_RECTS.items():
        out[name] = sheet.subsurface(pygame.Rect(x, y, w, h)).copy()
    for name, color in _WATER_COLORS.items():
        out[name] = _make_water_tile(color)
    return out


def load_fish_base() -> pygame.Surface:
    """Return the bluegill panfish sprite as a single surface."""
    return _load_fish_image().copy()


def load_bunny_frames() -> dict[str, list[pygame.Surface]]:
    """Return per-direction lists of bunny animation frames.

    The source sheet only contains a single facing direction, so the
    same frame list is aliased to every direction key.
    """
    sheet = _load_bunny_image()
    base_frames = [
        sheet.subsurface(pygame.Rect(*rect)).copy()
        for rect in _BUNNY_FRAME_RECTS
    ]
    return {direction: list(base_frames) for direction in _BUNNY_DIRECTIONS}
