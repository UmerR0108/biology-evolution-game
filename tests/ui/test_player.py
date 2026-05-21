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


def test_player_holding_shift_sprints_without_losing_diagonal_normalization(pygame_surface):
    p = Player(pos=(100.0, 100.0))
    keys_pressed = {pygame.K_RIGHT: True, pygame.K_d: False,
                    pygame.K_LEFT: False, pygame.K_a: False,
                    pygame.K_UP: False, pygame.K_w: True,
                    pygame.K_DOWN: False, pygame.K_s: False,
                    pygame.K_LSHIFT: True, pygame.K_RSHIFT: False}
    p.handle_input(keys_pressed)
    vx, vy = p.velocity
    speed = (vx * vx + vy * vy) ** 0.5
    assert abs(speed - Player.SPRINT_SPEED) < 1.0
    assert Player.SPRINT_SPEED > Player.SPEED


def test_player_handle_input_accepts_pygame_pressed_key_sequence(pygame_surface):
    class PressedKeys:
        def __getitem__(self, key: int) -> bool:
            return key in {pygame.K_RIGHT, pygame.K_LSHIFT}

    p = Player(pos=(100.0, 100.0))
    p.handle_input(PressedKeys())
    assert p.velocity == (Player.SPRINT_SPEED, 0.0)


def test_player_update_advances_position(pygame_surface):
    from evogame.ui.tilemap import build_forest_scene
    p = Player(pos=(200.0, 400.0))
    p.velocity = (Player.SPEED, 0.0)
    scene = build_forest_scene()
    p.update(dt_ms=1000.0, scene=scene)
    assert p.pos[0] == 200.0 + Player.SPEED
    assert p.pos[1] == 400.0


def test_player_update_clamps_to_scene(pygame_surface):
    from evogame.ui.tilemap import build_forest_scene
    p = Player(pos=(0.0, 0.0))
    p.velocity = (-Player.SPEED, 0.0)
    scene = build_forest_scene()
    p.update(dt_ms=1000.0, scene=scene)
    assert p.pos[0] == 0.0  # clamped


def test_player_draw_does_not_raise(pygame_surface):
    p = Player(pos=(50.0, 50.0))
    p.draw(pygame_surface, origin=(0, 0))


def test_player_facing_updates_with_velocity(pygame_surface):
    p = Player(pos=(100.0, 100.0))
    keys = {pygame.K_RIGHT: True, pygame.K_d: False, pygame.K_LEFT: False, pygame.K_a: False,
            pygame.K_UP: False, pygame.K_w: False, pygame.K_DOWN: False, pygame.K_s: False}
    p.handle_input(keys)
    assert p._facing == "right"
    keys[pygame.K_RIGHT] = False
    keys[pygame.K_DOWN] = True
    p.handle_input(keys)
    assert p._facing == "down"


def test_player_frame_advances_while_moving(pygame_surface):
    from evogame.ui.tilemap import build_forest_scene
    p = Player(pos=(200.0, 200.0))
    p.velocity = (Player.SPEED, 0.0)
    scene = build_forest_scene()
    prior = p._frame_index
    p.update(dt_ms=300.0, scene=scene)
    assert p._frame_index > prior


def test_player_frame_resets_when_stopped(pygame_surface):
    from evogame.ui.tilemap import build_forest_scene
    p = Player(pos=(200.0, 200.0))
    scene = build_forest_scene()
    p._frame_index = 1.5
    p.velocity = (0.0, 0.0)
    p.update(dt_ms=100.0, scene=scene)
    assert p._frame_index == 0.0


def test_player_cannot_walk_into_pond(pygame_surface):
    from evogame.ui.tilemap import build_forest_scene, TILE_PIXELS
    scene = build_forest_scene()
    bounds = scene.pond_pixel_bounds()
    # Place player just left of pond, moving right.
    p = Player(pos=(bounds.left - TILE_PIXELS / 2 - 4.0, bounds.top + bounds.height / 2))
    p.velocity = (Player.SPEED, 0.0)
    p.update(dt_ms=1000.0, scene=scene)
    # Player feet should not be inside the pond rect.
    feet_x = p.pos[0] + p.size[0] / 2
    feet_y = p.pos[1] + p.size[1] - 2
    assert not bounds.collidepoint(feet_x, feet_y), \
        f"player walked into pond: feet=({feet_x},{feet_y}) bounds={bounds}"


def test_player_cannot_walk_through_cottage(pygame_surface):
    from evogame.ui.tilemap import build_home_scene, TILE_PIXELS
    scene = build_home_scene()
    cottage = next(o for o in scene.objects if o.kind == "cottage")
    # Stand just below the cottage footprint and walk upward toward it.
    p = Player(pos=(cottage.col * TILE_PIXELS + 3 * TILE_PIXELS, (cottage.row + 6) * TILE_PIXELS))
    p.velocity = (0.0, -Player.SPEED)
    p.update(dt_ms=1000.0, scene=scene)
    feet_x = p.pos[0] + p.size[0] / 2
    feet_y = p.pos[1] + p.size[1] - 2
    assert not scene.object_blocks_pixel(feet_x, feet_y), \
        f"player walked through cottage: feet=({feet_x},{feet_y})"
