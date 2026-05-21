import math
from typing import Mapping

import pygame

from evogame.ui.assets import load_player_walk_frames
from evogame.ui.tilemap import Scene, TILE_PIXELS


_FRAME_ADVANCE_MS = 150.0  # ms per walk frame


def _is_walkable_at(scene: Scene, x: float, y: float) -> bool:
    return scene.is_walkable_at_pixel(x, y)


class Player:
    SPEED = 120.0  # pixels per second
    SPRINT_SPEED = 180.0  # pixels per second while holding Shift

    def __init__(self, pos: tuple[float, float]):
        self.pos = pos
        self.velocity: tuple[float, float] = (0.0, 0.0)
        self.size = (TILE_PIXELS, TILE_PIXELS)
        self._facing: str = "down"
        self._frame_index: float = 0.0
        self._frames: dict[str, list[pygame.Surface]] | None = None

    def _ensure_frames(self) -> dict[str, list[pygame.Surface]]:
        if self._frames is None:
            raw = load_player_walk_frames()
            # Scale 28x28 source to TILE_PIXELS x TILE_PIXELS for consistent world feel.
            self._frames = {
                d: [pygame.transform.scale(f, self.size) for f in frames]
                for d, frames in raw.items()
            }
        return self._frames

    def handle_input(self, keys: Mapping[int, bool]) -> None:
        def pressed(key: int) -> bool:
            if hasattr(keys, "get"):
                return bool(keys.get(key, False))
            try:
                return bool(keys[key])
            except (IndexError, KeyError):
                return False

        dx = (1 if pressed(pygame.K_RIGHT) or pressed(pygame.K_d) else 0) \
           - (1 if pressed(pygame.K_LEFT)  or pressed(pygame.K_a) else 0)
        dy = (1 if pressed(pygame.K_DOWN)  or pressed(pygame.K_s) else 0) \
           - (1 if pressed(pygame.K_UP)    or pressed(pygame.K_w) else 0)
        if dx == 0 and dy == 0:
            self.velocity = (0.0, 0.0)
            return
        speed = self.SPRINT_SPEED if pressed(pygame.K_LSHIFT) or pressed(pygame.K_RSHIFT) else self.SPEED
        mag = math.hypot(dx, dy)
        self.velocity = (dx / mag * speed, dy / mag * speed)
        vx, vy = self.velocity
        if vx != 0 or vy != 0:
            if abs(vx) > abs(vy):
                self._facing = "right" if vx > 0 else "left"
            else:
                self._facing = "down" if vy > 0 else "up"

    def update(self, dt_ms: float, scene: Scene) -> None:
        vx, vy = self.velocity
        dt = dt_ms / 1000.0
        max_delta = max(abs(vx * dt), abs(vy * dt))
        steps = max(1, math.ceil(max_delta / (TILE_PIXELS / 3)))
        step_dt = dt / steps
        for _ in range(steps):
            # X axis
            new_x = self.pos[0] + vx * step_dt
            feet_y = self.pos[1] + self.size[1] - 2
            feet_x_test = new_x + self.size[0] / 2
            if 0 <= new_x <= scene.tilemap.pixel_width - self.size[0] \
               and _is_walkable_at(scene, feet_x_test, feet_y):
                x = new_x
            else:
                x = max(0.0, min(scene.tilemap.pixel_width - self.size[0], self.pos[0]))
            # Y axis
            new_y = self.pos[1] + vy * step_dt
            feet_x_keep = x + self.size[0] / 2
            feet_y_test = new_y + self.size[1] - 2
            if 0 <= new_y <= scene.tilemap.pixel_height - self.size[1] \
               and _is_walkable_at(scene, feet_x_keep, feet_y_test):
                y = new_y
            else:
                y = max(0.0, min(scene.tilemap.pixel_height - self.size[1], self.pos[1]))
            self.pos = (x, y)
        # Advance walk-cycle frame index when moving; idle holds first frame.
        moving = self.velocity != (0.0, 0.0)
        if moving:
            self._frame_index += dt_ms / _FRAME_ADVANCE_MS
        else:
            self._frame_index = 0.0

    def draw(self, surface: pygame.Surface, origin: tuple[int, int]) -> None:
        frames = self._ensure_frames()
        dir_frames = frames.get(self._facing) or frames["down"]
        frame = dir_frames[int(self._frame_index) % len(dir_frames)]
        surface.blit(frame, (int(origin[0] + self.pos[0]), int(origin[1] + self.pos[1])))
