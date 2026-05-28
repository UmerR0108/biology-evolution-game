"""Allele-frequency chart rendering for the field journal.

Matplotlib is used for desktop Python when it is available. Browser builds made
with pygbag run on WebAssembly where matplotlib is not available/reliable, so
this module must import and render without matplotlib too. The pygame fallback
keeps the journal usable instead of crashing the whole app at startup.
"""

from __future__ import annotations

import sys
from dataclasses import dataclass

import pygame

from evogame.sim.recorder import GenerationLog

_DPI = 100
_DEFAULT_GENE = "color"
_WEB_PLATFORM = sys.platform == "emscripten"

if not _WEB_PLATFORM:
    try:  # pragma: no cover - exercised by the normal desktop test path.
        import matplotlib

        matplotlib.use("Agg")
        from matplotlib.backends.backend_agg import FigureCanvasAgg
        from matplotlib.figure import Figure

        _MATPLOTLIB_AVAILABLE = True
    except Exception:  # pragma: no cover - covered by the pygame fallback tests.
        Figure = None  # type: ignore[assignment]
        FigureCanvasAgg = None  # type: ignore[assignment]
        _MATPLOTLIB_AVAILABLE = False
else:  # Avoid importing matplotlib in pygbag/browser builds.
    Figure = None  # type: ignore[assignment]
    FigureCanvasAgg = None  # type: ignore[assignment]
    _MATPLOTLIB_AVAILABLE = False


@dataclass(frozen=True)
class _FallbackLine:
    label: str

    def get_label(self) -> str:
        return self.label


class _FallbackLegend:
    pass


class _FallbackAxes:
    def __init__(self) -> None:
        self._xlabel = ""
        self._ylabel = ""
        self._title = ""
        self._ylim = (0, 1)
        self._lines: list[_FallbackLine] = []
        self._legend: _FallbackLegend | None = None

    def set_metadata(self, *, title: str, labels: list[str]) -> None:
        self._xlabel = "Generation"
        self._ylabel = "Allele frequency"
        self._title = title
        self._ylim = (0, 1)
        self._lines = [_FallbackLine(label) for label in labels]
        self._legend = _FallbackLegend() if labels else None

    def set_placeholder(self) -> None:
        self._xlabel = ""
        self._ylabel = ""
        self._title = ""
        self._ylim = (0, 1)
        self._lines = []
        self._legend = None

    def get_xlabel(self) -> str:
        return self._xlabel

    def get_ylabel(self) -> str:
        return self._ylabel

    def get_title(self) -> str:
        return self._title

    def get_ylim(self) -> tuple[int, int]:
        return self._ylim

    def get_legend(self) -> _FallbackLegend | None:
        return self._legend

    def get_lines(self) -> list[_FallbackLine]:
        return self._lines


class _FallbackFigure:
    def __init__(self) -> None:
        self.axes = [_FallbackAxes()]


class ChartPanel:
    def __init__(self, rect: pygame.Rect, gene: str = _DEFAULT_GENE):
        self.rect = rect
        self.gene = gene
        self._surface: pygame.Surface | None = None
        self._font: pygame.font.Font | None = None
        if _MATPLOTLIB_AVAILABLE:
            width_in = max(1.0, rect.width / _DPI)
            height_in = max(1.0, rect.height / _DPI)
            self.figure = Figure(figsize=(width_in, height_in), dpi=_DPI)
            self.canvas = FigureCanvasAgg(self.figure)
        else:
            self.figure = _FallbackFigure()
            self.canvas = None
        self._render_placeholder()

    def _get_font(self, size: int = 14) -> pygame.font.Font:
        if self._font is None:
            self._font = pygame.font.SysFont("arial", size)
        return self._font

    def _render_placeholder(self) -> None:
        if _MATPLOTLIB_AVAILABLE:
            self.figure.clear()
            ax = self.figure.add_subplot(1, 1, 1)
            ax.text(0.5, 0.5, "Awaiting data...", ha="center", va="center")
            ax.set_axis_off()
            self._blit_to_surface()
            return
        self.figure.axes[0].set_placeholder()
        self._surface = pygame.Surface(self.rect.size, pygame.SRCALPHA)
        self._surface.fill((246, 242, 220, 255))
        pygame.draw.rect(self._surface, (82, 96, 84), self._surface.get_rect(), width=2)
        text = self._get_font().render("Awaiting data...", True, (54, 42, 31))
        self._surface.blit(text, text.get_rect(center=self._surface.get_rect().center))

    def _blit_to_surface(self) -> None:
        self.canvas.draw()
        raw = self.canvas.buffer_rgba()
        size = self.canvas.get_width_height()
        self._surface = pygame.image.frombuffer(raw, size, "RGBA")

    def update(self, log: GenerationLog) -> None:
        if len(log) == 0:
            self._render_placeholder()
            return
        series = log.frequencies_over_time(self.gene)
        if _MATPLOTLIB_AVAILABLE:
            self.figure.clear()
            ax = self.figure.add_subplot(1, 1, 1)
            gens = [r.gen for r in log.records]
            for allele, values in series.items():
                ax.plot(gens, values, label=allele, linewidth=2)
            ax.set_ylim(0, 1)
            ax.set_xlabel("Generation")
            ax.set_ylabel("Allele frequency")
            ax.set_title(f"{self.gene} alleles")
            if series:
                ax.legend(loc="best", fontsize="small")
            else:
                ax.text(0.5, 0.5, f"No {self.gene} data", ha="center", va="center", transform=ax.transAxes)
            ax.grid(True, alpha=0.3)
            self.figure.tight_layout()
            self._blit_to_surface()
            return
        self._render_pygame_chart(log, series)

    def _render_pygame_chart(self, log: GenerationLog, series: dict[str, list[float]]) -> None:
        self.figure.axes[0].set_metadata(title=f"{self.gene} alleles", labels=list(series))
        surface = pygame.Surface(self.rect.size, pygame.SRCALPHA)
        surface.fill((246, 242, 220, 255))
        bounds = surface.get_rect()
        pygame.draw.rect(surface, (82, 96, 84), bounds, width=2)

        font = self._get_font(14)
        small = pygame.font.SysFont("arial", 11)
        title = font.render(f"{self.gene} alleles", True, (54, 42, 31))
        surface.blit(title, (10, 8))

        plot = pygame.Rect(38, 34, max(1, bounds.width - 52), max(1, bounds.height - 62))
        pygame.draw.rect(surface, (255, 252, 235), plot)
        pygame.draw.line(surface, (70, 70, 70), plot.bottomleft, plot.topleft, 2)
        pygame.draw.line(surface, (70, 70, 70), plot.bottomleft, plot.bottomright, 2)
        for i in range(1, 4):
            y = plot.bottom - int(plot.height * i / 4)
            pygame.draw.line(surface, (208, 204, 188), (plot.left, y), (plot.right, y), 1)

        if not series:
            text = font.render(f"No {self.gene} data", True, (54, 42, 31))
            surface.blit(text, text.get_rect(center=plot.center))
            self._surface = surface
            return

        gens = [r.gen for r in log.records]
        min_gen = min(gens)
        max_gen = max(gens)
        gen_span = max(1, max_gen - min_gen)
        palette = [(205, 73, 63), (64, 112, 205), (75, 151, 82), (157, 88, 181), (218, 149, 55), (64, 160, 167)]

        for index, (allele, values) in enumerate(series.items()):
            color = palette[index % len(palette)]
            points: list[tuple[int, int]] = []
            for gen, value in zip(gens, values):
                x = plot.left + int((gen - min_gen) / gen_span * plot.width)
                clamped = max(0.0, min(1.0, value))
                y = plot.bottom - int(clamped * plot.height)
                points.append((x, y))
            if len(points) == 1:
                pygame.draw.circle(surface, color, points[0], 3)
            else:
                pygame.draw.lines(surface, color, False, points, 3)
                for point in points:
                    pygame.draw.circle(surface, color, point, 3)
            label = small.render(allele, True, color)
            surface.blit(label, (plot.right - 48, plot.top + 6 + index * 14))

        xlabel = small.render("Generation", True, (54, 42, 31))
        surface.blit(xlabel, xlabel.get_rect(midtop=(plot.centerx, plot.bottom + 6)))
        ylabel = small.render("Allele frequency", True, (54, 42, 31))
        surface.blit(ylabel, (4, plot.top + 4))
        self._surface = surface

    def draw(self, surface: pygame.Surface) -> None:
        if self._surface is not None:
            surface.blit(self._surface, self.rect.topleft)
