import pygame

from evogame.ui.player import Player


def test_player_starts_at_given_position(pygame_surface):
    p = Player(pos=(100.0, 100.0))
    assert p.pos == (100.0, 100.0)
    assert p.velocity == (0.0, 0.0)


def test_player_handle_input_sets_velocity_for_arrow_keys(pygame_surface):
    p = Player(pos=(100.0, 100.0))
    keys_pressed = {pygame.K_RIGHT: True, pygame.K_d: False,
                    pygame.K_LEFT: False, pygame.K_a: False,
                    pygame.K_UP: False, pygame.K_w: False,
                    pygame.K_DOWN: False, pygame.K_s: False}
    p.handle_input(keys_pressed)
    vx, vy = p.velocity
    assert vx > 0 and vy == 0


def test_player_handle_input_diagonal_normalizes(pygame_surface):
    p = Player(pos=(100.0, 100.0))
    keys_pressed = {pygame.K_RIGHT: False, pygame.K_d: True,
                    pygame.K_LEFT: False, pygame.K_a: False,
                    pygame.K_UP: False, pygame.K_w: True,
                    pygame.K_DOWN: False, pygame.K_s: False}
    p.handle_input(keys_pressed)
    vx, vy = p.velocity
    speed_sq = vx * vx + vy * vy
    # Magnitude should be ~Player.SPEED, not sqrt(2)*SPEED
    assert abs(speed_sq ** 0.5 - Player.SPEED) < 1.0


def test_player_update_advances_position(pygame_surface):
    from evogame.ui.tilemap import build_forest_scene
    p = Player(pos=(200.0, 200.0))
    p.velocity = (Player.SPEED, 0.0)
    scene = build_forest_scene()
    p.update(dt_ms=1000.0, scene=scene)
    assert p.pos[0] == 200.0 + Player.SPEED
    assert p.pos[1] == 200.0


def test_player_update_clamps_to_scene(pygame_surface):
    from evogame.ui.tilemap import build_forest_scene
    p = Player(pos=(0.0, 0.0))
    p.velocity = (-Player.SPEED, 0.0)
    scene = build_forest_scene()
    p.update(dt_ms=1000.0, scene=scene)
    assert p.pos[0] == 0.0  # clamped


def test_player_cannot_walk_into_pond(pygame_surface):
    from evogame.ui.tilemap import build_forest_scene, TILE_PIXELS
    scene = build_forest_scene()
    bounds = scene.pond_pixel_bounds()
    # Place player just left of pond, moving right.
    p = Player(pos=(bounds.left - 4.0, bounds.top + bounds.height / 2))
    p.velocity = (Player.SPEED, 0.0)
    p.update(dt_ms=1000.0, scene=scene)
    # Player feet should not be inside the pond rect.
    feet_x = p.pos[0] + p.size[0] / 2
    feet_y = p.pos[1] + p.size[1] - 2
    assert not bounds.collidepoint(feet_x, feet_y), \
        f"player walked into pond: feet=({feet_x},{feet_y}) bounds={bounds}"
