import math
import random
from dataclasses import dataclass
from typing import ClassVar

import pygame

from evogame.genetics import BIRD_SCHEMA, BUNNY_SCHEMA, Creature
from evogame.genetics.schema import SpeciesSchema
from evogame.ui.assets import load_bird_frames, load_bunny_frames
from evogame.ui.tilemap import Scene

_IDLE_MIN_MS = 1500.0
_IDLE_MAX_MS = 3000.0
_BUNNY_SPEED = 24.0  # px/sec
_BIRD_SPEED = 30.0  # px/sec
_FRAME_ADVANCE_MS = 350.0
_BUNNY_DRAW_SIZE = (40, 30)
_BIRD_DRAW_SIZE = (40, 40)


def _phenotype_label(creature: Creature | None, name: str, default: str = "") -> str:
    if creature is None:
        return default
    value = creature.phenotype.get(name)
    return str(getattr(value, "category", getattr(value, "label", value if value is not None else default)))


def _phenotype_number(creature: Creature | None, name: str, default: float = 0.5) -> float:
    if creature is None:
        return default
    value = creature.phenotype.get(name)
    raw = getattr(value, "value", default)
    try:
        return float(raw)
    except (TypeError, ValueError):
        return default


def draw_bird_sprite(
    surface: pygame.Surface,
    center: tuple[int, int],
    *,
    creature: Creature | None,
    direction: str = "right",
    frame_index: float = 0.0,
    size: tuple[int, int] = _BIRD_DRAW_SIZE,
    draw_backplate: bool = True,
) -> None:
    """Draw one bird everywhere with the same asset plus phenotype accents."""
    cx, cy = center
    wing_score = _phenotype_number(creature, "wing_span", 0.5)
    wing_delta = int(round((wing_score - 0.5) * 8))
    draw_size = (max(24, size[0] + wing_delta), max(24, size[1] + wing_delta))

    if draw_backplate:
        glow = pygame.Surface((draw_size[0] + 8, draw_size[1] + 8), pygame.SRCALPHA)
        pygame.draw.ellipse(glow, (255, 242, 168, 64), glow.get_rect())
        shadow = pygame.Surface((max(4, draw_size[0] - 10), 8), pygame.SRCALPHA)
        pygame.draw.ellipse(shadow, (28, 44, 28, 85), shadow.get_rect())
        surface.blit(glow, (int(cx - glow.get_width() / 2), int(cy - glow.get_height() / 2)))
        surface.blit(shadow, (int(cx - shadow.get_width() / 2), int(cy + draw_size[1] / 2 - 8)))

    frames = load_bird_frames()
    dir_frames = frames.get(direction) or next(iter(frames.values()))
    frame = dir_frames[int(frame_index) % len(dir_frames)]
    frame = pygame.transform.scale(frame, draw_size)
    surface.blit(frame, (int(cx - draw_size[0] / 2), int(cy - draw_size[1] / 2)))

    # Trait accents sit on top of the base sprite instead of replacing/tinting it,
    # preserving repeatability across forest and cage.
    coloration = _phenotype_label(creature, "coloration", "mottled")
    accent_map = {
        "brown": (136, 87, 42),
        "mottled": (210, 183, 86),
        "green": (76, 154, 82),
    }
    accent = accent_map.get(coloration, (210, 183, 86))
    chest = (cx - draw_size[0] // 5, cy + draw_size[1] // 6)
    pygame.draw.circle(surface, accent, chest, max(2, draw_size[0] // 10))
    pygame.draw.circle(surface, (31, 31, 26), chest, max(2, draw_size[0] // 10), 1)

    beak = _phenotype_label(creature, "beak_shape", "pointed")
    beak_root_x = cx + draw_size[0] // 3
    if beak == "broad":
        pts = [(beak_root_x, cy - 2), (beak_root_x + 11, cy - 7), (beak_root_x + 11, cy + 5)]
    elif beak == "curved":
        pts = [(beak_root_x, cy - 2), (beak_root_x + 12, cy - 4), (beak_root_x + 5, cy + 8)]
    else:
        pts = [(beak_root_x, cy - 1), (beak_root_x + 13, cy - 4), (beak_root_x + 3, cy + 3)]
    pygame.draw.polygon(surface, (237, 173, 59), pts)


@dataclass
class Wildlife:
    pos: tuple[float, float]
    scene: Scene
    rng: random.Random
    creature: Creature | None = None

    schema: ClassVar[SpeciesSchema] = BUNNY_SCHEMA
    speed_px_per_sec: ClassVar[float] = _BUNNY_SPEED
    observation_text: ClassVar[str] = "Wildlife nearby: observe traits and foraging"
    prompt_text: ClassVar[str] = "[E/Enter] Observe wildlife: traits and foraging"

    def __post_init__(self):
        if self.creature is None:
            genetics_rng = self.rng if hasattr(self.rng, "choice") else random.Random(0)
            self.creature = Creature.random(self.schema, genetics_rng)
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
        step = self.speed_px_per_sec * dt_ms / 1000.0
        if step >= dist:
            nx, ny = tx, ty
        else:
            nx = self.pos[0] + dx / dist * step
            ny = self.pos[1] + dy / dist * step
        if self.scene.is_walkable_at_pixel(nx, ny):
            self.pos = (nx, ny)
        else:
            self._enter_idle()
            return
        if step >= dist:
            self._enter_idle()
            return
        self._frame_index = (self._frame_index + dt_ms / _FRAME_ADVANCE_MS) % 3.0

    def draw(self, surface: pygame.Surface, origin: tuple[int, int]) -> None:
        pygame.draw.circle(surface, (90, 90, 90), (int(origin[0] + self.pos[0]), int(origin[1] + self.pos[1])), 6)


class Bunny(Wildlife):
    schema: ClassVar[SpeciesSchema] = BUNNY_SCHEMA
    speed_px_per_sec: ClassVar[float] = _BUNNY_SPEED
    observation_text: ClassVar[str] = "Bunny nearby: observe camouflage and foraging"
    prompt_text: ClassVar[str] = "[E/Enter] Observe bunny: camouflage and foraging"

    def draw(self, surface: pygame.Surface, origin: tuple[int, int]) -> None:
        frames = load_bunny_frames()
        dir_frames = frames.get(self._direction) or next(iter(frames.values()))
        frame = dir_frames[int(self._frame_index) % len(dir_frames)]
        # Scale the full paired 32x16 source up so forest bunnies read clearly at a glance.
        frame = pygame.transform.scale(frame, _BUNNY_DRAW_SIZE)
        glow = pygame.Surface((_BUNNY_DRAW_SIZE[0] + 8, _BUNNY_DRAW_SIZE[1] + 8), pygame.SRCALPHA)
        pygame.draw.ellipse(glow, (255, 242, 168, 70), glow.get_rect())
        shadow = pygame.Surface((_BUNNY_DRAW_SIZE[0] - 8, 8), pygame.SRCALPHA)
        pygame.draw.ellipse(shadow, (28, 44, 28, 95), shadow.get_rect())
        surface.blit(glow, (int(origin[0] + self.pos[0] - glow.get_width() / 2), int(origin[1] + self.pos[1] - glow.get_height() / 2)))
        surface.blit(shadow, (int(origin[0] + self.pos[0] - shadow.get_width() / 2), int(origin[1] + self.pos[1] + 8)))
        surface.blit(frame, (int(origin[0] + self.pos[0] - _BUNNY_DRAW_SIZE[0] / 2), int(origin[1] + self.pos[1] - _BUNNY_DRAW_SIZE[1] / 2)))


class Bird(Wildlife):
    schema: ClassVar[SpeciesSchema] = BIRD_SCHEMA
    speed_px_per_sec: ClassVar[float] = _BIRD_SPEED
    observation_text: ClassVar[str] = "Bird nearby: observe beak traits and forest foraging"
    prompt_text: ClassVar[str] = "[E/Enter] Observe bird: beak traits and forest foraging"

    def draw(self, surface: pygame.Surface, origin: tuple[int, int]) -> None:
        draw_bird_sprite(
            surface,
            (int(origin[0] + self.pos[0]), int(origin[1] + self.pos[1])),
            creature=self.creature,
            direction=self._direction,
            frame_index=self._frame_index,
            size=_BIRD_DRAW_SIZE,
            draw_backplate=True,
        )
