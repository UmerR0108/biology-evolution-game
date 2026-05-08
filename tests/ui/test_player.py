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
