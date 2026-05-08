"""Tilemap for the field-researcher game.

Holds a 2D grid of tile-name strings and renders ground tiles by
blitting scaled tileset surfaces. Water tiles report as non-walkable
so the player collision check can use ``is_walkable`` directly.

Only 16x16 source tiles from ``load_tileset`` are rendered here -
larger object sprites (tree, cottage) and the character sprite are
drawn by other code on top of the ground layer.
"""

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
