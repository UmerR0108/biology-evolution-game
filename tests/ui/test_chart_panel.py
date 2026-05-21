import pygame

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


def test_chart_panel_axes_have_labels_and_legend():
    log = GenerationLog()
    log.record(0, {"color": {"R": 0.5, "W": 0.5}}, False, 20)
    log.record(1, {"color": {"R": 0.7, "W": 0.3}}, True, 18)
    panel = ChartPanel(pygame.Rect(0, 0, 400, 300))
    panel.update(log)
    ax = panel.figure.axes[0]
    assert ax.get_xlabel() == "Generation"
    assert ax.get_ylabel() == "Allele frequency"
    assert ax.get_title() == "color alleles"
    assert ax.get_ylim() == (0, 1)
    assert ax.get_legend() is not None
    assert len(ax.get_lines()) == 2


def test_chart_panel_can_plot_selected_gene():
    log = GenerationLog()
    log.record(0, {"color": {"R": 0.5, "W": 0.5}, "fin_length": {"L": 0.8, "s": 0.2}}, False, 20)
    log.record(1, {"color": {"R": 0.7, "W": 0.3}, "fin_length": {"L": 0.6, "s": 0.4}}, True, 18)
    panel = ChartPanel(pygame.Rect(0, 0, 400, 300), gene="fin_length")

    panel.update(log)

    ax = panel.figure.axes[0]
    assert panel.gene == "fin_length"
    assert ax.get_title() == "fin_length alleles"
    assert [line.get_label() for line in ax.get_lines()] == ["L", "s"]
