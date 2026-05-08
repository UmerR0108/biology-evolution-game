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
        # If the spawn position is on a non-walkable tile (e.g. inside the
        # pond), snap to the nearest walkable tile center so subsequent
        # walkability checks behave sensibly.
        col = int(self.pos[0] // TILE_PIXELS)
        row = int(self.pos[1] // TILE_PIXELS)
        if not self.scene.tilemap.is_walkable(col, row):
            snapped = self._nearest_walkable(col, row)
            if snapped is not None:
                sc, sr = snapped
                self.pos = (
                    sc * TILE_PIXELS + TILE_PIXELS / 2,
                    sr * TILE_PIXELS + TILE_PIXELS / 2,
                )

    def _nearest_walkable(self, col: int, row: int) -> tuple[int, int] | None:
        tm = self.scene.tilemap
        max_radius = max(tm.cols, tm.rows)
        for radius in range(1, max_radius + 1):
            for dr in range(-radius, radius + 1):
                for dc in range(-radius, radius + 1):
                    if max(abs(dr), abs(dc)) != radius:
                        continue
                    nc, nr = col + dc, row + dr
                    if tm.is_walkable(nc, nr):
                        return (nc, nr)
        return None

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
