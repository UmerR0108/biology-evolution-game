import random

import pygame
import pytest

from evogame.genetics import GUPPY_SCHEMA, Creature
from evogame.ui.world_panel import WorldPanel


def test_world_panel_draws_without_error(pygame_surface):
    rng = random.Random(0)
    creatures = [Creature.random(GUPPY_SCHEMA, rng) for _ in range(10)]
    panel = WorldPanel(pygame.Rect(0, 0, 200, 200))
    panel.draw(pygame_surface, creatures)


def test_world_panel_handles_empty_creatures(pygame_surface):
    panel = WorldPanel(pygame.Rect(0, 0, 200, 200))
    panel.draw(pygame_surface, [])  # must not raise


def test_world_panel_paints_background(pygame_surface):
    """After drawing with no creatures, the panel area should be the pond color (not black)."""
    panel = WorldPanel(pygame.Rect(0, 0, 200, 200))
    panel.draw(pygame_surface, [])
    pixel = pygame_surface.get_at((100, 100))
    assert pixel != (0, 0, 0, 255), "panel background should not be black"
