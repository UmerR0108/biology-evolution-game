import pygame

from evogame.sim.controller import SimController
from evogame.ui.chart_panel import ChartPanel
from evogame.ui.widgets import Button, Slider, Toggle

_BACKDROP = (0, 0, 0, 160)
_PANEL_BG = (28, 28, 38)
_FG = (220, 220, 220)


class Journal:
    def __init__(self, screen_rect: pygame.Rect, sim: SimController):
        self.screen_rect = screen_rect
        self.sim = sim
        self.open = False
        self.paused = False

        # Panel = 80% of screen, centered.
        margin_x = int(screen_rect.width * 0.10)
        margin_y = int(screen_rect.height * 0.10)
        self.panel_rect = pygame.Rect(
            screen_rect.left + margin_x,
            screen_rect.top + margin_y,
            screen_rect.width - 2 * margin_x,
            screen_rect.height - 2 * margin_y,
        )

        # Layout: chart on the left ~70%, controls on the right ~30%.
        chart_w = int(self.panel_rect.width * 0.70)
        controls_x = self.panel_rect.left + chart_w + 16
        self.chart_panel = ChartPanel(pygame.Rect(
            self.panel_rect.left + 16, self.panel_rect.top + 40,
            chart_w - 16, self.panel_rect.height - 56,
        ))

        ctrl_y = self.panel_rect.top + 60
        self.predator_toggle = Toggle(
            pygame.Rect(controls_x, ctrl_y, 24, 24),
            "Predator",
            initial=sim.pressure.predator_on,
        )
        self.speed_slider = Slider(
            pygame.Rect(controls_x, ctrl_y + 50, 180, 20),
            min_value=0.5, max_value=5.0, initial=1.0,
        )
        self.pause_button = Button(
            pygame.Rect(controls_x, ctrl_y + 100, 100, 28),
            "Pause",
            self._toggle_pause,
        )
        self.chart_panel.update(self.sim.log)

    @property
    def gens_per_second(self) -> float:
        return self.speed_slider.value

    def toggle(self) -> None:
        self.open = not self.open

    def _toggle_pause(self) -> None:
        if self.sim.extinct:
            self.sim.reset()
            self.predator_toggle.state = False
            self.paused = False
            return
        self.paused = not self.paused

    def handle_event(self, event: pygame.event.Event) -> None:
        if not self.open:
            return
        prior = self.predator_toggle.state
        self.predator_toggle.handle_event(event)
        if self.predator_toggle.state != prior:
            self.sim.set_predator(self.predator_toggle.state)
        self.speed_slider.handle_event(event)
        self.pause_button.handle_event(event)

    def on_sim_tick(self) -> None:
        self.chart_panel.update(self.sim.log)

    def draw(self, surface: pygame.Surface, font: pygame.font.Font) -> None:
        if not self.open:
            return
        backdrop = pygame.Surface(self.screen_rect.size, pygame.SRCALPHA)
        backdrop.fill(_BACKDROP)
        surface.blit(backdrop, self.screen_rect.topleft)
        pygame.draw.rect(surface, _PANEL_BG, self.panel_rect)
        pygame.draw.rect(surface, _FG, self.panel_rect, 2)
        title = font.render("Field Journal — Pond Site", True, _FG)
        surface.blit(title, (self.panel_rect.left + 16, self.panel_rect.top + 12))
        self.chart_panel.draw(surface)
        self.predator_toggle.draw(surface, font)
        self.speed_slider.draw(surface, font)
        if self.sim.extinct:
            self.pause_button.label = "Restart"
        else:
            self.pause_button.label = "Resume" if self.paused else "Pause"
        self.pause_button.draw(surface, font)
        hint = font.render("J or ESC to close", True, _FG)
        surface.blit(hint, (self.panel_rect.left + 16, self.panel_rect.bottom - 24))
