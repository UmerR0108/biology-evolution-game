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
