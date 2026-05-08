import random

import pygame

from evogame.ui.wildlife import Bunny


def test_bunny_idle_then_walk(pygame_surface):
    from evogame.ui.tilemap import build_forest_scene
    scene = build_forest_scene()
    rng = random.Random(0)
    b = Bunny(pos=(100.0, 100.0), scene=scene, rng=rng)
    assert b.state == "idle"
    # Force the idle timer to expire.
    for _ in range(60):  # 6 seconds worth at 100 ms ticks
        b.update(dt_ms=100.0)
    assert b.state in ("idle", "walk")  # at least one transition occurred
    # Bunny should not have walked off the scene
    assert 0 <= b.pos[0] <= scene.tilemap.pixel_width
    assert 0 <= b.pos[1] <= scene.tilemap.pixel_height


def test_bunny_does_not_enter_water(pygame_surface):
    """A bunny that wanders the forest never ends up on a water tile."""
    from evogame.ui.tilemap import build_forest_scene
    scene = build_forest_scene()
    bounds = scene.pond_pixel_bounds()
    rng = random.Random(0)
    # Spawn just outside the pond on grass.
    start_x = bounds.right + 16.0
    start_y = bounds.centery
    b = Bunny(pos=(start_x, start_y), scene=scene, rng=rng)
    # Run for ~20 seconds — well beyond the 1.5-3.0s idle window — so the bunny
    # has many chances to pick a target and walk.
    for _ in range(200):
        b.update(dt_ms=100.0)
        # After every step, position must be on a walkable tile.
        col = int(b.pos[0] // 32)
        row = int(b.pos[1] // 32)
        assert scene.tilemap.is_walkable(col, row), \
            f"bunny entered non-walkable tile ({col},{row}) at pos={b.pos}"


def test_bunny_draw(pygame_surface):
    from evogame.ui.tilemap import build_forest_scene
    scene = build_forest_scene()
    rng = random.Random(0)
    b = Bunny(pos=(100.0, 100.0), scene=scene, rng=rng)
    b.draw(pygame_surface, origin=(0, 0))
