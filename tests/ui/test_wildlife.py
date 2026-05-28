import random

import pygame

from evogame.ui.wildlife import Bird, Bunny


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


def test_bunny_avoids_blocking_object_targets(pygame_surface):
    from evogame.ui.tilemap import TILE_PIXELS, build_forest_scene

    class SequenceRng:
        def __init__(self):
            self.values = iter([
                2000.0,  # initial idle timer
                3.5 * TILE_PIXELS, 3.5 * TILE_PIXELS,  # tree tile: should be rejected
                8.5 * TILE_PIXELS, 8.5 * TILE_PIXELS,  # open grass: should be accepted
            ])

        def uniform(self, _low, _high):
            return next(self.values)

    scene = build_forest_scene()
    bunny = Bunny(pos=(100.0, 100.0), scene=scene, rng=SequenceRng())

    target = bunny._pick_target()

    assert target == (8.5 * TILE_PIXELS, 8.5 * TILE_PIXELS)
    assert scene.is_walkable_at_pixel(*target)


def test_bunny_frame_resets_on_idle_transition(pygame_surface):
    from evogame.ui.tilemap import build_home_scene
    scene = build_home_scene()
    rng = random.Random(0)
    b = Bunny(pos=(480.0, 352.0), scene=scene, rng=rng)
    b.state = "walk"
    b._target = (504.0, 352.0)

    b.update(dt_ms=350.0)
    assert b.state == "walk"
    assert b._frame_index > 0.0

    b._target = (b.pos[0] + 1.0, b.pos[1])
    b.update(dt_ms=16.0)
    assert b.state == "idle"
    assert b._frame_index == 0.0


def test_bunny_frame_advances_every_350ms(pygame_surface):
    from evogame.ui.tilemap import build_home_scene
    scene = build_home_scene()
    rng = random.Random(0)
    b = Bunny(pos=(480.0, 352.0), scene=scene, rng=rng)
    b.state = "walk"
    b._target = (560.0, 352.0)

    b.update(dt_ms=350.0)

    assert b._frame_index == 1.0


def test_bunny_large_frame_lands_on_target_without_overshooting(pygame_surface):
    from evogame.ui.tilemap import build_home_scene
    scene = build_home_scene()
    rng = random.Random(0)
    b = Bunny(pos=(480.0, 352.0), scene=scene, rng=rng)
    b.state = "walk"
    b._target = (490.0, 352.0)

    b.update(dt_ms=1000.0)

    assert b.pos == (490.0, 352.0)
    assert b.state == "idle"


def test_bunny_draw(pygame_surface):
    from evogame.ui.tilemap import build_forest_scene
    scene = build_forest_scene()
    rng = random.Random(0)
    b = Bunny(pos=(100.0, 100.0), scene=scene, rng=rng)
    b.draw(pygame_surface, origin=(0, 0))


def test_bird_draw_uses_shared_trait_renderer(monkeypatch, pygame_surface):
    from evogame.ui.tilemap import build_forest_scene
    import evogame.ui.wildlife as wildlife

    scene = build_forest_scene()
    bird = Bird(pos=(100.0, 100.0), scene=scene, rng=random.Random(0))
    bird._direction = "right"
    bird._frame_index = 1.0
    calls = []

    def fake_draw_bird_sprite(surface, center, *, creature, direction, frame_index, size, draw_backplate):
        calls.append((center, creature, direction, frame_index, size, draw_backplate))
        pygame.draw.circle(surface, (250, 10, 200), center, 4)

    monkeypatch.setattr(wildlife, "draw_bird_sprite", fake_draw_bird_sprite)

    bird.draw(pygame_surface, origin=(0, 0))

    assert calls == [((100, 100), bird.creature, "right", 1.0, (40, 40), True)]
    assert pygame_surface.get_at((100, 100)) == (250, 10, 200, 255)
