"""Simple timing/tension fishing minigame."""

import random
from dataclasses import dataclass

import pygame

from evogame.genetics import Creature


@dataclass
class FishingResult:
    success: bool
    creature: Creature | None = None
    reason: str | None = None


class FishingMinigame:
    def __init__(self, candidates: list[Creature], rng: random.Random, duration_ms: float = 5000.0):
        if not candidates:
            raise ValueError("FishingMinigame needs at least one candidate fish")
        self.rng = rng
        self.duration_ms = duration_ms
        self.elapsed_ms = 0.0
        self.selected = rng.choice(candidates)
        self.tension = 0.45
        self.zone_center = rng.uniform(0.35, 0.65)
        self.zone_width = 0.30
        self.progress = 0.0
        self.action_held = False
        self.finished = False

    def handle_event(self, event: pygame.event.Event) -> None:
        if event.type == pygame.KEYDOWN and event.key in (pygame.K_SPACE, pygame.K_RETURN):
            self.action_held = True
        elif event.type == pygame.KEYUP and event.key in (pygame.K_SPACE, pygame.K_RETURN):
            self.action_held = False

    def _in_catch_zone(self) -> bool:
        half = self.zone_width / 2
        return self.zone_center - half <= self.tension <= self.zone_center + half

    def update(self, dt_ms: float) -> FishingResult | None:
        if self.finished:
            return None
        self.elapsed_ms += dt_ms
        dt = dt_ms / 1000.0
        self.tension += (0.85 if self.action_held else -0.55) * dt
        self.tension = max(0.0, min(1.0, self.tension))
        if self._in_catch_zone():
            self.progress += 1.1 * dt
        else:
            self.progress = max(0.0, self.progress - 0.45 * dt)
        if self.progress >= 1.0:
            self.finished = True
            return FishingResult(True, self.selected, "caught")
        if self.elapsed_ms >= self.duration_ms or self.tension <= 0.0 or self.tension >= 1.0:
            self.finished = True
            return FishingResult(False, None, "escaped")
        return None

    def draw(self, surface: pygame.Surface, font: pygame.font.Font) -> None:
        panel = pygame.Rect(0, 0, 360, 116)
        panel.center = surface.get_rect().center
        pygame.draw.rect(surface, (30, 38, 54), panel, border_radius=8)
        pygame.draw.rect(surface, (220, 230, 240), panel, 2, border_radius=8)
        surface.blit(font.render("Fishing: keep tension in the gold zone", True, (240, 240, 230)), (panel.left + 16, panel.top + 12))
        bar = pygame.Rect(panel.left + 26, panel.top + 48, panel.width - 52, 16)
        pygame.draw.rect(surface, (88, 103, 126), bar)
        zone = pygame.Rect(bar.left + int((self.zone_center - self.zone_width / 2) * bar.width), bar.top, int(self.zone_width * bar.width), bar.height)
        pygame.draw.rect(surface, (255, 210, 78), zone)
        x = bar.left + int(self.tension * bar.width)
        pygame.draw.line(surface, (255, 255, 255), (x, bar.top - 4), (x, bar.bottom + 4), 3)
        prog = pygame.Rect(bar.left, panel.top + 82, int(bar.width * self.progress), 10)
        pygame.draw.rect(surface, (86, 198, 126), prog)
