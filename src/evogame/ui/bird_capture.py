"""Simple click-the-zone bird capture minigame."""

import random
from dataclasses import dataclass

import pygame

from evogame.genetics import Creature


@dataclass
class BirdCaptureResult:
    success: bool
    creature: Creature | None = None
    reason: str | None = None


class BirdCaptureMinigame:
    def __init__(self, creature: Creature, rng: random.Random, duration_ms: float = 4200.0):
        self.creature = creature
        self.rng = rng
        self.duration_ms = duration_ms
        self.elapsed_ms = 0.0
        wing_span = float(creature.phenotype.get("wing_span").value) if "wing_span" in creature.phenotype else 1.5
        self.difficulty = max(0.35, 0.85 + wing_span * 0.10)
        self.target_center = rng.uniform(0.30, 0.70)
        self.target_width = max(0.12, min(0.32, 0.30 / self.difficulty))
        self.marker_position = 0.0
        self.marker_direction = 1.0
        self.bar_rect = pygame.Rect(0, 0, 328, 18)
        self.bar_rect.center = (500, 310)
        self.finished = False
        self._pending_result: BirdCaptureResult | None = None

    def _target_bounds(self) -> tuple[float, float]:
        half = self.target_width / 2
        return self.target_center - half, self.target_center + half

    def _ratio_in_target(self, ratio: float) -> bool:
        left, right = self._target_bounds()
        return left <= ratio <= right

    def _attempt_at_ratio(self, ratio: float) -> None:
        if self.finished:
            return
        self.finished = True
        if self._ratio_in_target(ratio):
            self._pending_result = BirdCaptureResult(True, self.creature, "caught")
        else:
            self._pending_result = BirdCaptureResult(False, None, "missed")

    def handle_event(self, event: pygame.event.Event) -> None:
        if self.finished:
            return
        if event.type == pygame.KEYDOWN and event.key in (pygame.K_SPACE, pygame.K_RETURN):
            self._attempt_at_ratio(self.marker_position)

    def update(self, dt_ms: float) -> BirdCaptureResult | None:
        if self._pending_result is not None:
            result = self._pending_result
            self._pending_result = None
            return result
        if self.finished:
            return None
        self.elapsed_ms += dt_ms
        dt = dt_ms / 1000.0
        self.marker_position += self.marker_direction * (1.05 + self.difficulty * 0.25) * dt
        if self.marker_position >= 1.0:
            self.marker_position = 1.0
            self.marker_direction = -1.0
        elif self.marker_position <= 0.0:
            self.marker_position = 0.0
            self.marker_direction = 1.0
        if self.elapsed_ms >= self.duration_ms:
            self.finished = True
            return BirdCaptureResult(False, None, "flew")
        return None

    def draw(self, surface: pygame.Surface, font: pygame.font.Font) -> None:
        panel = pygame.Rect(0, 0, 410, 126)
        panel.center = surface.get_rect().center
        pygame.draw.rect(surface, (34, 42, 34), panel, border_radius=8)
        pygame.draw.rect(surface, (235, 220, 190), panel, 2, border_radius=8)
        surface.blit(font.render("Bird capture: press Enter in the gold skill-check zone", True, (248, 238, 218)), (panel.left + 14, panel.top + 12))
        self.bar_rect = pygame.Rect(panel.left + 28, panel.top + 54, panel.width - 56, 18)
        pygame.draw.rect(surface, (82, 86, 76), self.bar_rect, border_radius=4)
        left, _right = self._target_bounds()
        target = pygame.Rect(
            self.bar_rect.left + int(left * self.bar_rect.width),
            self.bar_rect.top,
            max(3, int(self.target_width * self.bar_rect.width)),
            self.bar_rect.height,
        )
        pygame.draw.rect(surface, (255, 210, 78), target, border_radius=4)
        x = self.bar_rect.left + int(self.marker_position * self.bar_rect.width)
        pygame.draw.line(surface, (255, 255, 255), (x, self.bar_rect.top - 5), (x, self.bar_rect.bottom + 5), 3)
        hint = font.render("Press Enter/Space when the marker reaches gold", True, (225, 214, 190))
        surface.blit(hint, (panel.left + 14, panel.top + 88))
