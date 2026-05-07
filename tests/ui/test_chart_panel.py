import pygame
import pytest

from evogame.sim.recorder import GenerationLog
from evogame.ui.chart_panel import ChartPanel


def test_chart_panel_handles_empty_log(pygame_surface):
    panel = ChartPanel(pygame.Rect(0, 0, 200, 200))
    panel.update(GenerationLog())
    panel.draw(pygame_surface)  # must not raise


def test_chart_panel_renders_after_records(pygame_surface):
    log = GenerationLog()
    log.record(0, {"color": {"R": 0.5, "W": 0.5}}, False, 20)
    log.record(1, {"color": {"R": 0.7, "W": 0.3}}, True, 18)
    panel = ChartPanel(pygame.Rect(0, 0, 200, 200))
    panel.update(log)
    panel.draw(pygame_surface)
    # any non-background pixel proves something was drawn
    found_non_background = any(
        pygame_surface.get_at((x, y))[:3] != (0, 0, 0)
        for x in range(0, 200, 20) for y in range(0, 200, 20)
    )
    assert found_non_background


def test_chart_panel_returns_surface_on_draw(pygame_surface):
    log = GenerationLog()
    log.record(0, {"color": {"R": 1.0}}, False, 10)
    panel = ChartPanel(pygame.Rect(0, 0, 200, 200))
    panel.update(log)
    panel.draw(pygame_surface)
    # smoke: the panel rect area should differ from a freshly cleared surface
    other = pygame.Surface((200, 200))
    assert pygame_surface.get_at((50, 50)) != other.get_at((50, 50))
