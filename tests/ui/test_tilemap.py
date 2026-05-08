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
