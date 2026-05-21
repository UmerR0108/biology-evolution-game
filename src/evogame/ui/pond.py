"""Pond rendering primitives: VisibleFish dataclass and tinted fish surfaces.

``tint_fish(category)`` multiplies the bluegill base sprite by a per-category
RGB tint (red / pink / white) so fish in the pond visually reflect their
color phenotype. The result is cached per category so we don't re-blit the
overlay every frame.

``VisibleFish.from_creature`` extracts color and body-size phenotypes from a
``Creature`` and snapshots them onto a render-only dataclass: the fish keeps
no reference to the creature itself.
"""

import math
import random
from dataclasses import dataclass
from functools import lru_cache

import pygame

from evogame.genetics import Creature
from evogame.ui.assets import load_fish_base

# Per-category multiplicative tints applied to the base bluegill sprite.
# White is the identity multiplier so albino guppies display the raw sprite.
_COLOR_MULT: dict[str, tuple[float, float, float]] = {
    "red":   (1.0, 0.4, 0.4),
    "pink":  (1.0, 0.7, 0.8),
    "white": (1.0, 1.0, 1.0),
}


@lru_cache(maxsize=8)
def tint_fish(category: str) -> pygame.Surface:
    """Return the base fish sprite multiplied by the per-category tint.

    Cached per category, so repeated calls with the same category return
    the identical Surface instance. Unknown categories fall back to the
    identity (white) multiplier.
    """
    base = load_fish_base()
    out = base.copy()
    mult = _COLOR_MULT.get(category, (1.0, 1.0, 1.0))
    overlay = pygame.Surface(out.get_size(), pygame.SRCALPHA)
    overlay.fill(
        (int(mult[0] * 255), int(mult[1] * 255), int(mult[2] * 255), 255)
    )
    out.blit(overlay, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
    return out


@dataclass
class VisibleFish:
    """Render-only snapshot of a guppy in the pond.

    Holds the visible attributes derived from a ``Creature`` plus the
    per-fish wander state (heading, speed, next turn timer). Independent
    of the source creature once constructed.
    """

    color: str
    scale: float
    pos: tuple[float, float]
    heading: float  # radians
    speed: float
    next_turn_in_ms: float

    @classmethod
    def from_creature(
        cls,
        creature: Creature,
        pos: tuple[float, float],
        rng: random.Random,
    ) -> "VisibleFish":
        """Build a VisibleFish from a creature's color + body-size phenotypes."""
        ph = creature.phenotype
        color = ph["color"].category
        # body_size phenotype is numeric (0..6 for guppy 3-locus polygenic).
        size_value = float(ph["body_size"].value)
        scale = 1.0 + (size_value - 3.0) * 0.06  # ~0.82..1.18 range
        return cls(
            color=color,
            scale=scale,
            pos=pos,
            heading=rng.uniform(0, 2 * math.pi),
            speed=rng.uniform(3.0, 8.0),
            next_turn_in_ms=rng.uniform(1800.0, 4200.0),
        )


class PondView:
    def __init__(self, bounds: pygame.Rect, max_visible: int, rng: random.Random):
        self.bounds = bounds
        self.max_visible = max_visible
        self.rng = rng
        self.fish: list[VisibleFish] = []

    def _random_pos_in_bounds(self) -> tuple[float, float]:
        margin = 6
        x = self.rng.uniform(self.bounds.left + margin, self.bounds.right - margin)
        y = self.rng.uniform(self.bounds.top + margin, self.bounds.bottom - margin)
        return (x, y)

    def refresh(self, population: list[Creature]) -> None:
        if not population or self.bounds.width <= 12 or self.bounds.height <= 12:
            self.fish = []
            return
        n = min(len(population), self.max_visible)
        sampled = self.rng.sample(population, n)
        self.fish = [
            VisibleFish.from_creature(c, self._random_pos_in_bounds(), self.rng)
            for c in sampled
        ]

    def update(self, dt_ms: float) -> None:
        margin = 6
        for f in self.fish:
            f.next_turn_in_ms -= dt_ms
            if f.next_turn_in_ms <= 0:
                f.heading = self.rng.uniform(0, 2 * math.pi)
                f.next_turn_in_ms = self.rng.uniform(1800.0, 4200.0)
            dt = dt_ms / 1000.0
            nx = f.pos[0] + math.cos(f.heading) * f.speed * dt
            ny = f.pos[1] + math.sin(f.heading) * f.speed * dt
            # Reflect off pond bounds.
            if nx < self.bounds.left + margin or nx > self.bounds.right - margin:
                f.heading = math.pi - f.heading
                nx = max(self.bounds.left + margin, min(self.bounds.right - margin, nx))
            if ny < self.bounds.top + margin or ny > self.bounds.bottom - margin:
                f.heading = -f.heading
                ny = max(self.bounds.top + margin, min(self.bounds.bottom - margin, ny))
            f.pos = (nx, ny)

    def draw(self, surface: pygame.Surface, origin: tuple[int, int]) -> None:
        ox, oy = origin
        for f in self.fish:
            ripple_w = max(18, int(24 * f.scale))
            ripple_h = max(8, int(11 * f.scale))
            ripple_rect = pygame.Rect(0, 0, ripple_w, ripple_h)
            ripple_rect.center = (int(ox + f.pos[0]), int(oy + f.pos[1]))
            pygame.draw.ellipse(surface, (179, 226, 239), ripple_rect, 1)
            sprite = tint_fish(f.color)
            water_scale = f.scale * 0.72
            w, h = sprite.get_size()
            sprite = pygame.transform.scale(
                sprite,
                (max(1, int(w * water_scale)), max(1, int(h * water_scale))),
            )
            # Flip horizontally based on heading direction
            if math.cos(f.heading) < 0:
                sprite = pygame.transform.flip(sprite, True, False)
            sprite.set_alpha(150)
            sw, sh = sprite.get_size()
            surface.blit(sprite, (int(ox + f.pos[0] - sw / 2), int(oy + f.pos[1] - sh / 2)))
