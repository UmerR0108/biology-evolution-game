import math
import random
from dataclasses import dataclass

import pygame

from evogame.ui.assets import load_bunny_frames
from evogame.ui.tilemap import Scene, TILE_PIXELS

_IDLE_MIN_MS = 1500.0
_IDLE_MAX_MS = 3000.0
_BUNNY_SPEED = 24.0  # px/sec
_FRAME_ADVANCE_MS = 350.0


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
            if self.scene.is_walkable_at_pixel(tx, ty):
                return (tx, ty)
        return None

    def _update_direction(self, dx: float, dy: float) -> None:
        if abs(dx) > abs(dy):
            self._direction = "right" if dx > 0 else "left"
        else:
            self._direction = "down" if dy > 0 else "up"

    def _enter_idle(self) -> None:
        self.state = "idle"
        self._target = None
        self._frame_index = 0.0
        self._timer_ms = self.rng.uniform(_IDLE_MIN_MS, _IDLE_MAX_MS)

    def update(self, dt_ms: float) -> None:
        if self.state == "idle":
            self._timer_ms -= dt_ms
            if self._timer_ms <= 0:
                target = self._pick_target()
                if target is not None:
                    self._target = target
                    self.state = "walk"
                else:
                    self._enter_idle()
            return
        # walking
        if self._target is None:
            self._enter_idle()
            return
        tx, ty = self._target
        dx, dy = tx - self.pos[0], ty - self.pos[1]
        dist = math.hypot(dx, dy)
        if dist < 2.0:
            self._enter_idle()
            return
        self._update_direction(dx, dy)
        step = _BUNNY_SPEED * dt_ms / 1000.0
        if step >= dist:
            nx, ny = tx, ty
        else:
            nx = self.pos[0] + dx / dist * step
            ny = self.pos[1] + dy / dist * step
        if self.scene.is_walkable_at_pixel(nx, ny):
            self.pos = (nx, ny)
        else:
            # Abandon target if blocked.
            self._enter_idle()
            return
        if step >= dist:
            self._enter_idle()
            return
        self._frame_index = (self._frame_index + dt_ms / _FRAME_ADVANCE_MS) % 3.0

    def draw(self, surface: pygame.Surface, origin: tuple[int, int]) -> None:
        frames = load_bunny_frames()
        dir_frames = frames.get(self._direction) or next(iter(frames.values()))
        frame = dir_frames[int(self._frame_index) % len(dir_frames)]
        # Scale the full paired 32x16 source to a readable 32x24 world sprite.
        frame = pygame.transform.scale(frame, (32, 24))
        surface.blit(frame, (int(origin[0] + self.pos[0] - 16), int(origin[1] + self.pos[1] - 12)))
