import random

import pygame

from evogame.genetics import GUPPY_SCHEMA, Creature
from evogame.ui.pond import tint_fish, VisibleFish


def test_tint_fish_returns_a_surface(pygame_surface):
    surf = tint_fish(category="red")
    assert isinstance(surf, pygame.Surface)


def test_tint_fish_caches_per_color(pygame_surface):
    a = tint_fish("red")
    b = tint_fish("red")
    c = tint_fish("white")
    assert a is b
    assert a is not c


def test_visible_fish_constructed_from_creature(pygame_surface):
    rng = random.Random(0)
    creature = Creature.random(GUPPY_SCHEMA, rng)
    fish = VisibleFish.from_creature(creature, pos=(100.0, 100.0), rng=rng)
    assert fish.color in {"red", "pink", "white"}
    assert fish.scale > 0
