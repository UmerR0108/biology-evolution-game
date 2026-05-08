import pygame

from evogame.ui.assets import load_tileset, load_fish_base, load_bunny_frames


def test_load_tileset_returns_named_surfaces(pygame_surface):
    tiles = load_tileset()
    for name in ("grass", "water_nw", "water_ne", "water_sw", "water_se",
                 "tree", "cottage", "char_down"):
        assert name in tiles, f"missing tile: {name}"
        assert isinstance(tiles[name], pygame.Surface)
        w, h = tiles[name].get_size()
        assert w > 0 and h > 0


def test_load_fish_base_is_a_surface(pygame_surface):
    fish = load_fish_base()
    assert isinstance(fish, pygame.Surface)
    w, h = fish.get_size()
    assert w > 0 and h > 0


def test_load_bunny_frames_returns_per_direction_lists(pygame_surface):
    frames = load_bunny_frames()
    for direction in ("down", "up", "left", "right"):
        assert direction in frames, f"missing direction: {direction}"
        assert len(frames[direction]) >= 1
        for surf in frames[direction]:
            assert isinstance(surf, pygame.Surface)


def test_load_player_walk_frames_returns_independent_surfaces(pygame_surface):
    from evogame.ui.assets import load_player_walk_frames
    frames = load_player_walk_frames()
    for direction in ("down", "up", "left", "right"):
        assert direction in frames, f"missing direction: {direction}"
        assert len(frames[direction]) >= 2, f"{direction} should have >=2 walk frames"
        for surf in frames[direction]:
            assert isinstance(surf, pygame.Surface)
            w, h = surf.get_size()
            assert w > 0 and h > 0
    # Independence check: mutating one direction must not affect others.
    assert frames["down"][0] is not frames["up"][0]


def test_load_bunny_frames_returns_independent_surfaces(pygame_surface):
    from evogame.ui.assets import load_bunny_frames
    frames = load_bunny_frames()
    assert frames["down"][0] is not frames["up"][0], \
        "bunny frames must not be aliased across directions"
