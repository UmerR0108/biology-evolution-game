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
            speed=rng.uniform(8.0, 18.0),
            next_turn_in_ms=rng.uniform(1000.0, 2500.0),
        )
