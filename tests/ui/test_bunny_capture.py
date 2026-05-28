import random

import pygame

from evogame.genetics import BUNNY_SCHEMA, Creature
from evogame.ui.bunny_capture import BunnyCaptureMinigame


def _bunny(seed=0):
    return Creature.random(BUNNY_SCHEMA, random.Random(seed))


def test_bunny_capture_enter_inside_skill_check_zone_catches_bunny():
    creature = _bunny()
    game = BunnyCaptureMinigame(creature, random.Random(1), duration_ms=5000)
    game.target_center = 0.50
    game.target_width = 0.20
    game.marker_position = 0.50

    game.handle_event(pygame.event.Event(pygame.KEYDOWN, {"key": pygame.K_RETURN}))
    result = game.update(0)

    assert result is not None
    assert result.success is True
    assert result.creature is creature
    assert result.reason == "caught"


def test_bunny_capture_enter_outside_skill_check_zone_spooks_bunny():
    game = BunnyCaptureMinigame(_bunny(), random.Random(1), duration_ms=5000)
    game.target_center = 0.50
    game.target_width = 0.20
    game.marker_position = 0.95

    game.handle_event(pygame.event.Event(pygame.KEYDOWN, {"key": pygame.K_RETURN}))
    result = game.update(0)

    assert result is not None
    assert result.success is False
    assert result.creature is None
    assert result.reason == "missed"


def test_bunny_capture_waiting_too_long_fails():
    game = BunnyCaptureMinigame(_bunny(), random.Random(1), duration_ms=10)

    result = game.update(20)

    assert result is not None
    assert result.success is False
    assert result.creature is None
    assert result.reason == "spooked"


def test_bunny_capture_target_width_uses_speed_and_boldness_traits():
    slow_bold = _bunny(1)
    fast_shy = _bunny(2)
    easy = BunnyCaptureMinigame(slow_bold, random.Random(1))
    hard = BunnyCaptureMinigame(fast_shy, random.Random(1))

    assert easy.target_width != hard.target_width


def test_bunny_capture_draw_does_not_raise(pygame_surface):
    font = pygame.font.Font(None, 20)
    BunnyCaptureMinigame(_bunny(), random.Random(1)).draw(pygame_surface, font)


def test_bunny_capture_mouse_click_does_not_attempt_capture():
    game = BunnyCaptureMinigame(_bunny(), random.Random(1), duration_ms=5000)
    game.target_center = 0.50
    game.target_width = 0.20

    game.handle_event(pygame.event.Event(pygame.MOUSEBUTTONDOWN, {"button": 1, "pos": game.bar_rect.center}))
    result = game.update(0)

    assert result is None
    assert game.finished is False
