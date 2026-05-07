import random

import pytest

from evogame.genetics import GUPPY_SCHEMA, Creature
from evogame.sim.population import Population
from evogame.sim.pressure import PredatorPressure


def _make_population(n: int, seed: int = 0, capacity: int = 60) -> Population:
    rng = random.Random(seed)
    creatures = [Creature.random(GUPPY_SCHEMA, rng) for _ in range(n)]
    return Population(creatures=creatures, carrying_capacity=capacity, rng=rng)


def test_empty_population_stays_empty():
    pop = _make_population(0)
    next_pop = pop.step_generation(PredatorPressure(predator_on=False))
    assert len(next_pop) == 0


def test_single_creature_cannot_breed():
    pop = _make_population(1)
    next_pop = pop.step_generation(PredatorPressure(predator_on=False))
    assert len(next_pop) == 0


def test_normal_population_produces_offspring():
    pop = _make_population(20)
    next_pop = pop.step_generation(PredatorPressure(predator_on=False))
    assert len(next_pop) > 0


def test_carrying_capacity_caps_size():
    pop = _make_population(50, capacity=30)
    next_pop = pop.step_generation(PredatorPressure(predator_on=False))
    assert len(next_pop) <= 30


def test_offspring_share_schema():
    pop = _make_population(10)
    next_pop = pop.step_generation(PredatorPressure(predator_on=False))
    assert all(c.schema is GUPPY_SCHEMA for c in next_pop.creatures)


def test_zero_total_fitness_causes_extinction():
    class _ZeroPressure:
        def fitness(self, creature):
            return 0.0

    pop = _make_population(10)
    next_pop = pop.step_generation(_ZeroPressure())
    assert len(next_pop) == 0


def test_predator_pressure_skews_population_toward_white():
    """Under predator pressure for many generations, white alleles should dominate."""
    rng = random.Random(42)
    creatures = [Creature.random(GUPPY_SCHEMA, rng) for _ in range(40)]
    pop = Population(creatures=creatures, carrying_capacity=40, rng=rng)
    pressure = PredatorPressure(predator_on=True)
    for _ in range(20):
        pop = pop.step_generation(pressure)
        if len(pop) == 0:
            pytest.skip("Population went extinct in this seed; rare but possible")
    colors = [c.phenotype["color"].category for c in pop.creatures]
    # With predator on, "red" should be rare after 20 generations
    assert colors.count("red") < colors.count("white")
