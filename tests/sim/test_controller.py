import random

from evogame.genetics import GUPPY_SCHEMA
from evogame.sim.controller import SimController


def test_controller_starts_with_initial_population():
    sim = SimController(schema=GUPPY_SCHEMA, initial_size=10, carrying_capacity=20, rng=random.Random(0))
    assert len(sim.population) == 10
    assert sim.generation == 0
    assert not sim.extinct
    assert len(sim.log) == 1  # initial state recorded


def test_tick_advances_generation():
    sim = SimController(schema=GUPPY_SCHEMA, initial_size=20, carrying_capacity=40, rng=random.Random(0))
    sim.tick()
    assert sim.generation == 1
    assert len(sim.log) == 2


def test_tick_records_predator_state():
    sim = SimController(schema=GUPPY_SCHEMA, initial_size=20, carrying_capacity=40, rng=random.Random(0))
    sim.set_predator(True)
    sim.tick()
    assert sim.log.records[-1].predator_on is True


def test_extinction_freezes_simulation():
    sim = SimController(schema=GUPPY_SCHEMA, initial_size=1, carrying_capacity=10, rng=random.Random(0))
    sim.tick()
    assert sim.extinct
    gen_before = sim.generation
    log_len_before = len(sim.log)
    sim.tick()
    assert sim.generation == gen_before
    assert len(sim.log) == log_len_before


def test_reset_restores_initial_state():
    sim = SimController(schema=GUPPY_SCHEMA, initial_size=10, carrying_capacity=20, rng=random.Random(0))
    sim.tick()
    sim.tick()
    sim.reset()
    assert sim.generation == 0
    assert len(sim.population) == 10
    assert not sim.extinct
    assert len(sim.log) == 1


def test_reset_restores_predator_off():
    sim = SimController(schema=GUPPY_SCHEMA, initial_size=10, carrying_capacity=20, rng=random.Random(0))
    sim.set_predator(True)
    sim.reset()
    assert sim.pressure.predator_on is False
    assert sim.log.records[0].predator_on is False
