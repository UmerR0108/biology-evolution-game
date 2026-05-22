"""Simple approach/calm bunny capture minigame."""

import random
from dataclasses import dataclass

import pygame

from evogame.genetics import Creature


@dataclass
class BunnyCaptureResult:
    success: bool
    creature: Creature | None = None
    reason: str | None = None


class BunnyCaptureMinigame:
    def __init__(self, creature: Creature, rng: random.Random, duration_ms: float = 4500.0):
        self.creature = creature
        self.rng = rng
        self.duration_ms = duration_ms
        self.elapsed_ms = 0.0
        speed = float(creature.phenotype["speed"].value)
        boldness = float(creature.phenotype["boldness"].value)
        self.difficulty = max(0.25, 1.0 + speed * 0.08 - boldness * 0.06)
        self.distance = 1.0
        self.calm = 1.0
        self.approaching = False
        self.finished = False

    def handle_event(self, event: pygame.event.Event) -> None:
        if event.type == pygame.KEYDOWN and event.key in (pygame.K_SPACE, pygame.K_RETURN):
            self.approaching = True
        elif event.type == pygame.KEYUP and event.key in (pygame.K_SPACE, pygame.K_RETURN):
            self.approaching = False

    def update(self, dt_ms: float) -> BunnyCaptureResult | None:
        if self.finished:
            return None
        self.elapsed_ms += dt_ms
        dt = dt_ms / 1000.0
        if self.approaching:
            self.distance -= 0.50 * dt / self.difficulty
            self.calm -= 0.28 * dt * self.difficulty
        else:
            self.distance -= 0.18 * dt / self.difficulty
            self.calm = min(1.0, self.calm + 0.12 * dt)
        self.distance = max(0.0, self.distance)
        if self.distance <= 0.0:
            self.finished = True
            return BunnyCaptureResult(True, self.creature, "caught")
        if self.calm <= 0.0 or self.elapsed_ms >= self.duration_ms:
            self.finished = True
            return BunnyCaptureResult(False, None, "spooked")
        return None

    def draw(self, surface: pygame.Surface, font: pygame.font.Font) -> None:
        panel = pygame.Rect(0, 0, 360, 116)
        panel.center = surface.get_rect().center
        pygame.draw.rect(surface, (45, 34, 28), panel, border_radius=8)
        pygame.draw.rect(surface, (235, 220, 190), panel, 2, border_radius=8)
        surface.blit(font.render("Bunny capture: approach without spooking it", True, (248, 238, 218)), (panel.left + 14, panel.top + 12))
        distance_bar = pygame.Rect(panel.left + 24, panel.top + 48, panel.width - 48, 12)
        calm_bar = pygame.Rect(panel.left + 24, panel.top + 76, panel.width - 48, 12)
        pygame.draw.rect(surface, (92, 80, 70), distance_bar)
        pygame.draw.rect(surface, (92, 80, 70), calm_bar)
        pygame.draw.rect(surface, (108, 186, 112), (distance_bar.left, distance_bar.top, int(distance_bar.width * (1.0 - self.distance)), distance_bar.height))
        pygame.draw.rect(surface, (118, 174, 235), (calm_bar.left, calm_bar.top, int(calm_bar.width * self.calm), calm_bar.height))
