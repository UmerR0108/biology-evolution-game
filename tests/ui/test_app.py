import pygame
import pytest

from evogame.ui.app import App


def test_app_initializes_without_error():
    app = App(seed=0)
    assert app.sim.generation == 0
    assert app.running is True
    app.shutdown()


def test_app_advances_generation_after_enough_time():
    app = App(seed=0)
    # default speed is 1.0 gen/sec → 1000ms triggers exactly 1 generation
    app.step_one_frame(1100)
    assert app.sim.generation >= 1
    app.shutdown()


def test_app_does_not_advance_when_paused():
    app = App(seed=0)
    app.journal.paused = True
    app.step_one_frame(2000)
    assert app.sim.generation == 0
    app.shutdown()


def test_app_runs_for_n_generations():
    app = App(seed=0)
    app.run_for_generations(5, max_frames=200)
    assert app.sim.generation == 5
    app.shutdown()


def test_app_does_not_advance_when_extinct():
    app = App(seed=0)
    app.sim.extinct = True
    app.step_one_frame(2000)
    assert app.sim.generation == 0
    app.shutdown()


def test_app_quit_event_stops_running():
    app = App(seed=0)
    pygame.event.post(pygame.event.Event(pygame.QUIT))
    app.step_one_frame(0)
    assert app.running is False
    app.shutdown()


def test_app_j_key_toggles_journal():
    app = App(seed=0)
    assert app.journal.open is False
    pygame.event.post(pygame.event.Event(pygame.KEYDOWN, {"key": pygame.K_j}))
    app.step_one_frame(0)
    assert app.journal.open is True
    pygame.event.post(pygame.event.Event(pygame.KEYDOWN, {"key": pygame.K_j}))
    app.step_one_frame(0)
    assert app.journal.open is False
    app.shutdown()


def test_app_escape_closes_journal_when_open():
    app = App(seed=0)
    app.journal.open = True
    pygame.event.post(pygame.event.Event(pygame.KEYDOWN, {"key": pygame.K_ESCAPE}))
    app.step_one_frame(0)
    assert app.journal.open is False
    assert app.running is True
    app.shutdown()


def test_app_escape_quits_when_journal_closed():
    app = App(seed=0)
    assert app.journal.open is False
    pygame.event.post(pygame.event.Event(pygame.KEYDOWN, {"key": pygame.K_ESCAPE}))
    app.step_one_frame(0)
    assert app.running is False
    app.shutdown()


def test_app_e_near_cottage_opens_journal():
    app = App(seed=0)
    # Move player adjacent to cottage.
    cottage = next(o for o in app.world_panel.scene.objects if o.kind == "cottage")
    from evogame.ui.tilemap import TILE_PIXELS
    app.player.pos = (cottage.col * TILE_PIXELS + 16.0, cottage.row * TILE_PIXELS + 16.0)
    assert app.world_panel.cottage_in_range(app.player) is True
    pygame.event.post(pygame.event.Event(pygame.KEYDOWN, {"key": pygame.K_e}))
    app.step_one_frame(0)
    assert app.journal.open is True
    app.shutdown()
