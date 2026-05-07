import matplotlib

matplotlib.use("Agg")

import pygame
from matplotlib.backends.backend_agg import FigureCanvasAgg
from matplotlib.figure import Figure

from evogame.sim.recorder import GenerationLog

_DPI = 100
_GENE = "color"


class ChartPanel:
    def __init__(self, rect: pygame.Rect):
        self.rect = rect
        width_in = max(1.0, rect.width / _DPI)
        height_in = max(1.0, rect.height / _DPI)
        self.figure = Figure(figsize=(width_in, height_in), dpi=_DPI)
        self.canvas = FigureCanvasAgg(self.figure)
        self._surface: pygame.Surface | None = None
        self._render_placeholder()

    def _render_placeholder(self) -> None:
        self.figure.clear()
        ax = self.figure.add_subplot(1, 1, 1)
        ax.text(0.5, 0.5, "Awaiting data...", ha="center", va="center")
        ax.set_axis_off()
        self._blit_to_surface()

    def _blit_to_surface(self) -> None:
        self.canvas.draw()
        raw = self.canvas.buffer_rgba()
        size = self.canvas.get_width_height()
        self._surface = pygame.image.frombuffer(raw, size, "RGBA")

    def update(self, log: GenerationLog) -> None:
        if len(log) == 0:
            self._render_placeholder()
            return
        series = log.frequencies_over_time(_GENE)
        self.figure.clear()
        ax = self.figure.add_subplot(1, 1, 1)
        gens = [r.gen for r in log.records]
        for allele, values in series.items():
            ax.plot(gens, values, label=allele, linewidth=2)
        ax.set_ylim(0, 1)
        ax.set_xlabel("Generation")
        ax.set_ylabel("Allele frequency")
        ax.set_title(f"{_GENE} alleles")
        ax.legend(loc="best", fontsize="small")
        ax.grid(True, alpha=0.3)
        self.figure.tight_layout()
        self._blit_to_surface()

    def draw(self, surface: pygame.Surface) -> None:
        if self._surface is not None:
            surface.blit(self._surface, self.rect.topleft)
