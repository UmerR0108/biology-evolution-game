"""Tilemap for the field-researcher game.

Holds a 2D grid of tile-name strings and renders ground tiles by
blitting scaled tileset surfaces. Water tiles report as non-walkable
so the player collision check can use ``is_walkable`` directly.

Only 16x16 source tiles from ``load_tileset`` are rendered here -
larger object sprites (tree, cottage) and the character sprite are
drawn by other code on top of the ground layer.
"""

from dataclasses import dataclass, field
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
            # Tilemap renders only 16x16 ground tiles. Larger object
            # sprites (tree ~16x32, cottage ~80x80) and the character
            # (28x28) live in the same dict but are drawn elsewhere.
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
                grid[r][c] = "water_nw"  # interior - any water tile name OK

    objects = [
        SceneObject("tree", col=2, row=2),
        SceneObject("tree", col=20, row=3),
        SceneObject("tree", col=24, row=10),
        SceneObject("tree", col=4, row=14),
        SceneObject("cottage", col=18, row=11),
    ]
    return Scene(Tilemap(grid), objects)
