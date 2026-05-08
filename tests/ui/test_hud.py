import pygame

from evogame.ui.hud import StatusStrip


def test_status_strip_draws(pygame_surface):
    strip = StatusStrip(pygame.Rect(0, 0, 1000, 24))
    font = pygame.font.SysFont("arial", 12)
    strip.draw(pygame_surface, font, generation=5, population=42, gens_per_second=1.5,
               extinct=False, journal_open=False)


def test_status_strip_shows_extinct_label(pygame_surface):
    strip = StatusStrip(pygame.Rect(0, 0, 1000, 24))
    font = pygame.font.SysFont("arial", 12)
    strip.draw(pygame_surface, font, generation=5, population=0, gens_per_second=1.0,
               extinct=True, journal_open=False)
