import pygame

from evogame.ui.tilemap import Tilemap, TILE_PIXELS


def test_tilemap_dimensions():
    grid = [
        ["grass", "grass", "water_nw"],
        ["grass", "grass", "water_sw"],
    ]
    tm = Tilemap(grid)
    assert tm.cols == 3
    assert tm.rows == 2
    assert tm.pixel_width == 3 * TILE_PIXELS
    assert tm.pixel_height == 2 * TILE_PIXELS


def test_tilemap_is_walkable_water_blocks():
    grid = [
        ["grass", "water_nw"],
        ["grass", "water_sw"],
    ]
    tm = Tilemap(grid)
    assert tm.is_walkable(0, 0) is True   # grass
    assert tm.is_walkable(1, 0) is False  # water


def test_tilemap_draw_paints_grass_pixels(pygame_surface):
    grid = [["grass"] * 4 for _ in range(4)]
    tm = Tilemap(grid)
    tm.draw(pygame_surface, origin=(0, 0))
    # Grass tile is not pure black; somewhere in the painted region pixel != black.
    pixel = pygame_surface.get_at((TILE_PIXELS // 2, TILE_PIXELS // 2))
    assert pixel != (0, 0, 0, 255)


def test_forest_scene_has_pond_and_dimensions():
    from evogame.ui.tilemap import build_forest_scene, TILE_PIXELS
    scene = build_forest_scene()
    # scene must fit inside 1000x596 (window height minus 24px status strip)
    assert scene.tilemap.pixel_width <= 1000
    assert scene.tilemap.pixel_height <= 596
    assert scene.tilemap.pixel_width >= 32 * TILE_PIXELS or scene.tilemap.cols >= 28
    # has at least one pond tile and at least one tree object
    pond_tiles = [
        (c, r) for r in range(scene.tilemap.rows) for c in range(scene.tilemap.cols)
        if scene.tilemap.grid[r][c].startswith("water_")
    ]
    assert len(pond_tiles) >= 4, "scene must include a 2x2-or-larger pond"
    assert any(o.kind == "tree" for o in scene.objects)
    assert any(o.kind == "cottage" for o in scene.objects)


def test_forest_scene_pond_bounds_are_inside_grid():
    from evogame.ui.tilemap import build_forest_scene
    scene = build_forest_scene()
    bounds = scene.pond_pixel_bounds()
    assert bounds.width > 0 and bounds.height > 0
    assert bounds.left >= 0 and bounds.top >= 0
    assert bounds.right <= scene.tilemap.pixel_width
    assert bounds.bottom <= scene.tilemap.pixel_height
