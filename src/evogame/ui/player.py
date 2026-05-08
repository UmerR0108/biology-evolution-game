import math
from typing import Mapping

import pygame

from evogame.ui.assets import load_tileset
from evogame.ui.tilemap import Scene, TILE_PIXELS


def _is_walkable_at(scene: Scene, x: float, y: float) -> bool:
    col = int(x // TILE_PIXELS)
    row = int(y // TILE_PIXELS)
    return scene.tilemap.is_walkable(col, row)


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
