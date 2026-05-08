import random

import pygame

from evogame.genetics import GUPPY_SCHEMA
from evogame.sim.controller import SimController
from evogame.ui.hud import StatusStrip
from evogame.ui.journal import Journal
from evogame.ui.player import Player
from evogame.ui.world_panel import WorldPanel

_WINDOW_W = 1000
_WINDOW_H = 620
_STATUS_H = 24
_INITIAL_POP = 30
_CARRYING_CAPACITY = 60


class App:
    def __init__(self, seed: int | None = None):
        pygame.init()
        pygame.display.set_caption("evogame — guppy field site")
        self.screen = pygame.display.set_mode((_WINDOW_W, _WINDOW_H))
        self.font = pygame.font.SysFont("arial", 14)
        self.small_font = pygame.font.SysFont("arial", 12)
        self.clock = pygame.time.Clock()
        self.running = True

        rng = random.Random(seed)
        self.sim = SimController(
            schema=GUPPY_SCHEMA,
            initial_size=_INITIAL_POP,
            carrying_capacity=_CARRYING_CAPACITY,
            rng=rng,
        )

        status_rect = pygame.Rect(0, 0, _WINDOW_W, _STATUS_H)
        world_rect = pygame.Rect(0, _STATUS_H, _WINDOW_W, _WINDOW_H - _STATUS_H)
        screen_rect = pygame.Rect(0, 0, _WINDOW_W, _WINDOW_H)

        self.status_strip = StatusStrip(status_rect)
        self.world_panel = WorldPanel(world_rect)
        self.journal = Journal(screen_rect, self.sim)

        scene = self.world_panel.scene
        self.player = Player(pos=(scene.tilemap.pixel_width / 2,
                                  scene.tilemap.pixel_height * 0.7))
        self.world_panel.pond_view.refresh(self.sim.population.creatures)
        self._gen_timer_ms = 0.0

    def shutdown(self) -> None:
        pygame.quit()

    def _handle_events(self) -> None:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
                continue
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_j:
                    self.journal.toggle()
                    continue
                if event.key == pygame.K_e and self.world_panel.cottage_in_range(self.player):
                    self.journal.open = True
                    continue
                if event.key == pygame.K_ESCAPE:
                    if self.journal.open:
                        self.journal.open = False
                    else:
                        self.running = False
                    continue
            if self.journal.open:
                self.journal.handle_event(event)

    def step_one_frame(self, dt_ms: float) -> None:
        self._handle_events()
        if not self.journal.open:
            keys = pygame.key.get_pressed()
            self.player.handle_input(keys)
            self.player.update(dt_ms, self.world_panel.scene)
        if not self.journal.paused and not self.sim.extinct:
            interval_ms = 1000.0 / self.journal.gens_per_second
            self._gen_timer_ms += dt_ms
            while self._gen_timer_ms >= interval_ms:
                self._gen_timer_ms -= interval_ms
                self.sim.tick()
                self.journal.on_sim_tick()
                self.world_panel.pond_view.refresh(self.sim.population.creatures)
                if self.sim.extinct:
                    break
        # Drift fish every frame (even when paused or journal open).
        self.world_panel.pond_view.update(dt_ms)
        self.world_panel.update_wildlife(dt_ms)
        self._render()

    def _render(self) -> None:
        self.screen.fill((10, 10, 15))
        self.world_panel.draw(self.screen, player=self.player, font=self.small_font)
        self.status_strip.draw(
            self.screen, self.small_font,
            generation=self.sim.generation,
            population=len(self.sim.population),
            gens_per_second=self.journal.gens_per_second,
            extinct=self.sim.extinct,
            journal_open=self.journal.open,
        )
        self.journal.draw(self.screen, self.font)
        pygame.display.flip()

    def run(self) -> None:
        while self.running:
            dt_ms = self.clock.tick(60)
            self.step_one_frame(dt_ms)
        self.shutdown()

    def run_for_generations(self, target: int, max_frames: int = 1000) -> None:
        """Test helper: step until sim reaches the target generation or max_frames hits."""
        frames = 0
        while self.sim.generation < target and frames < max_frames:
            self.step_one_frame(100)
            frames += 1
