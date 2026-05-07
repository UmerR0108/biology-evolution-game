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


def _click(pos):
    return pygame.event.Event(pygame.MOUSEBUTTONDOWN, {"pos": pos, "button": 1})


def _motion(pos):
    return pygame.event.Event(pygame.MOUSEMOTION, {"pos": pos, "buttons": (1, 0, 0), "rel": (0, 0)})


def test_predator_toggle_updates_sim():
    sim = _make_sim()
    hud = HUD(pygame.Rect(0, 0, 600, 40), sim)
    # Toggle rect: (10, 8) size 24x24 → click center (22, 20)
    hud.handle_event(_click((22, 20)))
    assert hud.predator_on is True
    assert sim.pressure.predator_on is True


def test_slider_drag_updates_gens_per_second():
    sim = _make_sim()
    hud = HUD(pygame.Rect(0, 0, 600, 40), sim)
    initial = hud.gens_per_second
    # Slider rect: (180, 10) size 160x20 → grab middle, drag right
    hud.handle_event(_click((260, 20)))
    hud.handle_event(_motion((335, 20)))
    assert hud.gens_per_second > initial


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


def test_restart_clears_predator_toggle_to_match_sim():
    sim = SimController(
        schema=GUPPY_SCHEMA,
        initial_size=1,
        carrying_capacity=10,
        rng=random.Random(0),
    )
    hud = HUD(pygame.Rect(0, 0, 600, 40), sim)
    hud.handle_event(_click((22, 20)))  # turn predator ON via toggle click
    sim.tick()
    assert sim.extinct
    hud._toggle_pause()  # restart
    assert hud.predator_on is False
    assert sim.pressure.predator_on is False


def test_label_shows_restart_when_extinct():
    sim = SimController(
        schema=GUPPY_SCHEMA,
        initial_size=1,
        carrying_capacity=10,
        rng=random.Random(0),
    )
    sim.tick()
    hud = HUD(pygame.Rect(0, 0, 600, 40), sim)
    assert hud._label() == "Restart"
