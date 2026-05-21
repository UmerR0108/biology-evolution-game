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


def test_pond_view_sample_size(pygame_surface):
    from evogame.ui.pond import PondView
    from evogame.ui.tilemap import build_forest_scene
    rng = random.Random(0)
    pop = [Creature.random(GUPPY_SCHEMA, rng) for _ in range(40)]
    scene = build_forest_scene()
    pond = PondView(bounds=scene.pond_pixel_bounds(), max_visible=10, rng=random.Random(1))
    pond.refresh(pop)
    assert 1 <= len(pond.fish) <= 10


def test_pond_view_fish_stay_in_bounds(pygame_surface):
    from evogame.ui.pond import PondView
    from evogame.ui.tilemap import build_forest_scene
    rng = random.Random(0)
    pop = [Creature.random(GUPPY_SCHEMA, rng) for _ in range(20)]
    scene = build_forest_scene()
    bounds = scene.pond_pixel_bounds()
    pond = PondView(bounds=bounds, max_visible=10, rng=random.Random(2))
    pond.refresh(pop)
    for _ in range(60):
        pond.update(dt_ms=100.0)
    for f in pond.fish:
        assert bounds.collidepoint(f.pos[0], f.pos[1]), \
            f"fish drifted out of bounds: {f.pos} not in {bounds}"


def test_pond_view_draw(pygame_surface):
    from evogame.ui.pond import PondView
    from evogame.ui.tilemap import build_forest_scene
    pop = [Creature.random(GUPPY_SCHEMA, random.Random(0)) for _ in range(8)]
    scene = build_forest_scene()
    pond = PondView(bounds=scene.pond_pixel_bounds(), max_visible=8, rng=random.Random(0))
    pond.refresh(pop)
    pond.draw(pygame_surface, origin=(0, 0))
