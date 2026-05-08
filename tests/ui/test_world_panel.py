import pygame

from evogame.ui.world_panel import WorldPanel


def test_world_panel_draws_scene_without_error(pygame_surface):
    panel = WorldPanel(pygame.Rect(0, 0, 200, 200))
    panel.draw(pygame_surface)


def test_world_panel_paints_background(pygame_surface):
    panel = WorldPanel(pygame.Rect(0, 0, 200, 200))
    panel.draw(pygame_surface)
    pixel = pygame_surface.get_at((100, 100))
    assert pixel != (0, 0, 0, 255), "panel background should show grass, not black"
