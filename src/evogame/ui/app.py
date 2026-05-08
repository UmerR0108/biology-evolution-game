import random

import pygame

from evogame.genetics import GUPPY_SCHEMA
from evogame.sim.controller import SimController
from evogame.ui.chart_panel import ChartPanel
from evogame.ui.hud import HUD
from evogame.ui.player import Player
from evogame.ui.world_panel import WorldPanel

_WINDOW_W = 1000
_WINDOW_H = 620
_HUD_H = 40
_INITIAL_POP = 30
_CARRYING_CAPACITY = 60


class App:
    def __init__(self, seed: int | None = None):
        pygame.init()
        pygame.display.set_caption("evogame — guppy")
        self.screen = pygame.display.set_mode((_WINDOW_W, _WINDOW_H))
        self.font = pygame.font.SysFont("arial", 14)
        self.clock = pygame.time.Clock()
        self.running = True

        rng = random.Random(seed)
        self.sim = SimController(
            schema=GUPPY_SCHEMA,
            initial_size=_INITIAL_POP,
            carrying_capacity=_CARRYING_CAPACITY,
            rng=rng,
        )

        hud_rect = pygame.Rect(0, 0, _WINDOW_W, _HUD_H)
        world_rect = pygame.Rect(0, _HUD_H, _WINDOW_W // 2, _WINDOW_H - _HUD_H)
        chart_rect = pygame.Rect(_WINDOW_W // 2, _HUD_H, _WINDOW_W // 2, _WINDOW_H - _HUD_H)

        self.hud = HUD(hud_rect, self.sim)
        self.world_panel = WorldPanel(world_rect)
        self.chart_panel = ChartPanel(chart_rect)
        self.chart_panel.update(self.sim.log)

        scene = self.world_panel.scene
        self.player = Player(
            pos=(scene.tilemap.pixel_width / 2, scene.tilemap.pixel_height * 0.7)
        )

        self._gen_timer_ms = 0.0

    def shutdown(self) -> None:
        pygame.quit()

    def _handle_events(self) -> None:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            self.hud.handle_event(event)

    def step_one_frame(self, dt_ms: float) -> None:
        self._handle_events()
        keys = pygame.key.get_pressed()
        self.player.handle_input(keys)
        self.player.update(dt_ms, self.world_panel.scene)
        if not self.hud.paused and not self.sim.extinct:
            interval_ms = 1000.0 / self.hud.gens_per_second
            self._gen_timer_ms += dt_ms
            while self._gen_timer_ms >= interval_ms:
                self._gen_timer_ms -= interval_ms
                self.sim.tick()
                self.chart_panel.update(self.sim.log)
                if self.sim.extinct:
                    break
        self._render()

    def _render(self) -> None:
        self.screen.fill((10, 10, 15))
        self.world_panel.draw(self.screen, player=self.player)
        self.chart_panel.draw(self.screen)
        self.hud.draw(self.screen, self.font)
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
