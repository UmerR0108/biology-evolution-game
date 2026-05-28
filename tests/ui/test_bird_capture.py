import random

import pygame

from evogame.genetics import BIRD_SCHEMA, Creature
from evogame.ui.bird_capture import BirdCaptureMinigame


def _bird(seed=0):
    return Creature.random(BIRD_SCHEMA, random.Random(seed))


def test_bird_capture_enter_inside_skill_check_zone_catches_bird():
    creature = _bird()
    game = BirdCaptureMinigame(creature, random.Random(1), duration_ms=5000)
    game.target_center = 0.50
    game.target_width = 0.20
    game.marker_position = 0.50

    game.handle_event(pygame.event.Event(pygame.KEYDOWN, {"key": pygame.K_RETURN}))
    result = game.update(0)

    assert result is not None
    assert result.success is True
    assert result.creature is creature
    assert result.reason == "caught"


def test_bird_capture_enter_outside_skill_check_zone_misses_bird():
    game = BirdCaptureMinigame(_bird(), random.Random(1), duration_ms=5000)
    game.target_center = 0.50
    game.target_width = 0.20
    game.marker_position = 0.05

    game.handle_event(pygame.event.Event(pygame.KEYDOWN, {"key": pygame.K_RETURN}))
    result = game.update(0)

    assert result is not None
    assert result.success is False
    assert result.creature is None
    assert result.reason == "missed"


def test_bird_capture_waiting_too_long_fails():
    game = BirdCaptureMinigame(_bird(), random.Random(1), duration_ms=10)

    result = game.update(20)

    assert result is not None
    assert result.success is False
    assert result.creature is None
    assert result.reason == "flew"


def test_bird_capture_target_width_scales_with_wing_span_difficulty():
    small = _bird(1)
    large = _bird(2)
    easy = BirdCaptureMinigame(small, random.Random(1))
    hard = BirdCaptureMinigame(large, random.Random(1))

    assert easy.target_width != hard.target_width


def test_bird_capture_draw_does_not_raise(pygame_surface):
    font = pygame.font.Font(None, 20)
    BirdCaptureMinigame(_bird(), random.Random(1)).draw(pygame_surface, font)


def test_bird_capture_mouse_click_does_not_attempt_capture():
    game = BirdCaptureMinigame(_bird(), random.Random(1), duration_ms=5000)
    game.target_center = 0.50
    game.target_width = 0.20

    game.handle_event(pygame.event.Event(pygame.MOUSEBUTTONDOWN, {"button": 1, "pos": game.bar_rect.center}))
    result = game.update(0)

    assert result is None
    assert game.finished is False
