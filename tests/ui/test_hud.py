import random

import pygame

from evogame.genetics import GUPPY_SCHEMA
from evogame.sim.controller import SimController
from evogame.ui.hud import HUD


def _make_sim():
    return SimController(
        schema=GUPPY_SCHEMA,
        initial_size=10,
        carrying_capacity=20,
        rng=random.Random(0),
    )


def test_hud_starts_with_predator_off_and_unpaused():
    sim = _make_sim()
    hud = HUD(pygame.Rect(0, 0, 600, 40), sim)
    assert hud.predator_on is False
    assert hud.paused is False
    assert 0.5 <= hud.gens_per_second <= 5.0


def test_predator_toggle_updates_sim():
    sim = _make_sim()
    hud = HUD(pygame.Rect(0, 0, 600, 40), sim)
    hud._toggle_predator()  # internal — exercise the wiring
    assert hud.predator_on is True
    assert sim.pressure.predator_on is True


def test_pause_button_flips_state():
    sim = _make_sim()
    hud = HUD(pygame.Rect(0, 0, 600, 40), sim)
    hud._toggle_pause()
    assert hud.paused is True
    hud._toggle_pause()
    assert hud.paused is False


def test_restart_button_resets_sim_when_extinct():
    sim = SimController(
        schema=GUPPY_SCHEMA,
        initial_size=1,  # will go extinct on tick
        carrying_capacity=10,
        rng=random.Random(0),
    )
    sim.tick()
    assert sim.extinct
    hud = HUD(pygame.Rect(0, 0, 600, 40), sim)
    hud._toggle_pause()  # acts as "Restart" when extinct
    assert sim.extinct is False
    assert sim.generation == 0
