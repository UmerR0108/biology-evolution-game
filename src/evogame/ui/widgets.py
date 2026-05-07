from typing import Callable

import pygame


_BG = (40, 40, 50)
_FG = (220, 220, 220)
_ACCENT = (90, 180, 90)
_TRACK = (80, 80, 100)


class Button:
    def __init__(self, rect: pygame.Rect, label: str, on_click: Callable[[], None]):
        self.rect = rect
        self.label = label
        self.on_click = on_click

    def handle_event(self, event: pygame.event.Event) -> None:
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.rect.collidepoint(event.pos):
                self.on_click()

    def draw(self, surface: pygame.Surface, font: pygame.font.Font) -> None:
        pygame.draw.rect(surface, _BG, self.rect)
        pygame.draw.rect(surface, _FG, self.rect, 1)
        text = font.render(self.label, True, _FG)
        surface.blit(text, text.get_rect(center=self.rect.center))


class Toggle:
    def __init__(self, rect: pygame.Rect, label: str, initial: bool):
        self.rect = rect
        self.label = label
        self.state = initial

    def handle_event(self, event: pygame.event.Event) -> None:
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.rect.collidepoint(event.pos):
                self.state = not self.state

    def draw(self, surface: pygame.Surface, font: pygame.font.Font) -> None:
        pygame.draw.rect(surface, _BG, self.rect)
        pygame.draw.rect(surface, _FG, self.rect, 1)
        if self.state:
            inner = self.rect.inflate(-8, -8)
            pygame.draw.rect(surface, _ACCENT, inner)
        text = font.render(self.label, True, _FG)
        surface.blit(text, (self.rect.right + 6, self.rect.top + 2))


class Slider:
    def __init__(
        self,
        rect: pygame.Rect,
        min_value: float,
        max_value: float,
        initial: float,
    ):
        self.rect = rect
        self.min_value = min_value
        self.max_value = max_value
        self.value = max(min_value, min(max_value, initial))
        self._dragging = False

    def _set_value_from_x(self, x: int) -> None:
        ratio = (x - self.rect.left) / max(1, self.rect.width)
        ratio = max(0.0, min(1.0, ratio))
        self.value = self.min_value + ratio * (self.max_value - self.min_value)

    def handle_event(self, event: pygame.event.Event) -> None:
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.rect.collidepoint(event.pos):
                self._dragging = True
                self._set_value_from_x(event.pos[0])
        elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            self._dragging = False
        elif event.type == pygame.MOUSEMOTION and self._dragging:
            self._set_value_from_x(event.pos[0])

    def draw(self, surface: pygame.Surface, font: pygame.font.Font) -> None:
        track = pygame.Rect(self.rect.left, self.rect.centery - 3, self.rect.width, 6)
        pygame.draw.rect(surface, _TRACK, track)
        ratio = (self.value - self.min_value) / max(1e-9, self.max_value - self.min_value)
        knob_x = int(self.rect.left + ratio * self.rect.width)
        pygame.draw.circle(surface, _ACCENT, (knob_x, self.rect.centery), 8)
