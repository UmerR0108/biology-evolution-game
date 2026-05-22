import random

import pygame

from evogame.genetics import Creature, GUPPY_SCHEMA
from evogame.ui.fishing import FishingMinigame


def _fish(n=4):
    rng = random.Random(0)
    return [Creature.random(GUPPY_SCHEMA, rng) for _ in range(n)]


def test_fishing_minigame_selects_candidate_from_population():
    candidates = _fish()
    game = FishingMinigame(candidates, random.Random(1))

    assert game.selected in candidates


def test_fishing_minigame_success_returns_selected_creature():
    game = FishingMinigame(_fish(), random.Random(1), duration_ms=5000)
    game.progress = 0.99
    game.tension = game.zone_center

    result = game.update(100)

    assert result is not None
    assert result.success is True
    assert result.creature is game.selected


def test_fishing_minigame_failure_returns_no_creature():
    game = FishingMinigame(_fish(), random.Random(1), duration_ms=10)

    result = game.update(20)

    assert result is not None
    assert result.success is False
    assert result.creature is None


def test_fishing_tension_rises_when_action_key_held():
    game = FishingMinigame(_fish(), random.Random(1))
    before = game.tension

    game.handle_event(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_SPACE))
    game.update(100)

    assert game.tension > before


def test_fishing_draw_does_not_raise(pygame_surface):
    font = pygame.font.Font(None, 20)
    FishingMinigame(_fish(), random.Random(1)).draw(pygame_surface, font)
