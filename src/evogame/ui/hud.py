import pygame

from evogame.sim.controller import SimController
from evogame.ui.widgets import Button, Slider, Toggle

_FG = (220, 220, 220)
_BG = (25, 25, 35)


class HUD:
    def __init__(self, rect: pygame.Rect, sim: SimController):
        self.rect = rect
        self.sim = sim
        self.paused = False

        # Layout: predator toggle | speed slider | pause button | text status
        y = rect.top + 8
        self.toggle = Toggle(pygame.Rect(rect.left + 10, y, 24, 24), "Predator", initial=False)
        self.slider = Slider(
            pygame.Rect(rect.left + 180, y + 2, 160, 20),
            min_value=0.5,
            max_value=5.0,
            initial=1.0,
        )
        self.pause_button = Button(
            pygame.Rect(rect.left + 360, y, 90, 24),
            "Pause",
            self._toggle_pause,
        )

    @property
    def predator_on(self) -> bool:
        return self.toggle.state

    @property
    def gens_per_second(self) -> float:
        return self.slider.value

    def _toggle_pause(self) -> None:
        if self.sim.extinct:
            self.sim.reset()
            self.toggle.state = self.sim.pressure.predator_on
            self.paused = False
            return
        self.paused = not self.paused

    def handle_event(self, event: pygame.event.Event) -> None:
        prior_toggle = self.toggle.state
        self.toggle.handle_event(event)
        if self.toggle.state != prior_toggle:
            self.sim.set_predator(self.toggle.state)
        self.slider.handle_event(event)
        self.pause_button.handle_event(event)

    def _label(self) -> str:
        if self.sim.extinct:
            return "Restart"
        return "Resume" if self.paused else "Pause"

    def draw(self, surface: pygame.Surface, font: pygame.font.Font) -> None:
        pygame.draw.rect(surface, _BG, self.rect)
        self.toggle.draw(surface, font)
        self.slider.draw(surface, font)
        self.pause_button.label = self._label()
        self.pause_button.draw(surface, font)
        # Status text on the right
        status = f"Gen {self.sim.generation}   Pop {len(self.sim.population)}   Speed {self.gens_per_second:.1f}/s"
        if self.sim.extinct:
            status += "   EXTINCT"
        text = font.render(status, True, _FG)
        surface.blit(text, (self.rect.left + 470, self.rect.top + 12))
