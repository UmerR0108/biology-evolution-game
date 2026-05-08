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
    app.hud.paused = True
    app.step_one_frame(2000)
    assert app.sim.generation == 0
    app.shutdown()


def test_app_runs_for_n_generations():
    app = App(seed=0)
    app.run_for_generations(5, max_frames=200)
    assert app.sim.generation == 5
    app.shutdown()
