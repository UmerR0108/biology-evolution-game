import random

import pygame

from evogame.genetics import BUNNY_SCHEMA, Creature
from evogame.ui.bunny_capture import BunnyCaptureMinigame


def _bunny(seed=0):
    return Creature.random(BUNNY_SCHEMA, random.Random(seed))


def test_bunny_capture_minigame_success_returns_bunny_creature():
    creature = _bunny()
    game = BunnyCaptureMinigame(creature, random.Random(1), duration_ms=5000)
    game.distance = 0.01
    game.calm = 0.7

    result = game.update(100)

    assert result is not None
    assert result.success is True
    assert result.creature is creature


def test_bunny_capture_minigame_failure_returns_no_creature():
    game = BunnyCaptureMinigame(_bunny(), random.Random(1), duration_ms=10)

    result = game.update(20)

    assert result is not None
    assert result.success is False
    assert result.creature is None


def test_bunny_capture_difficulty_uses_speed_and_boldness_traits():
    slow_bold = _bunny(1)
    fast_shy = _bunny(2)
    easy = BunnyCaptureMinigame(slow_bold, random.Random(1))
    hard = BunnyCaptureMinigame(fast_shy, random.Random(1))

    assert easy.difficulty != hard.difficulty


def test_bunny_capture_draw_does_not_raise(pygame_surface):
    font = pygame.font.Font(None, 20)
    BunnyCaptureMinigame(_bunny(), random.Random(1)).draw(pygame_surface, font)
