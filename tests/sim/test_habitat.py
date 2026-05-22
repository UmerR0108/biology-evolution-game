import random

from evogame.genetics import Creature, GUPPY_SCHEMA
from evogame.sim.habitat import CaptiveHabitat


def test_captive_habitat_starts_empty():
    habitat = CaptiveHabitat("guppy", 20, random.Random(0))

    assert habitat.founders == []
    assert habitat.population is None
    assert habitat.generation == 0


def test_captive_habitat_adds_founders():
    rng = random.Random(1)
    founder = Creature.random(GUPPY_SCHEMA, rng)
    habitat = CaptiveHabitat("guppy", 20, rng)

    habitat.add_founder(founder)

    assert habitat.founders == [founder]


def test_captive_habitat_requires_two_founders_to_evolve():
    rng = random.Random(2)
    habitat = CaptiveHabitat("guppy", 20, rng)
    habitat.add_founder(Creature.random(GUPPY_SCHEMA, rng))

    habitat.tick()

    assert habitat.population is None
    assert habitat.generation == 0


def test_captive_habitat_population_is_seeded_only_from_founders():
    rng = random.Random(3)
    founders = [Creature.random(GUPPY_SCHEMA, rng) for _ in range(2)]
    habitat = CaptiveHabitat("guppy", 20, rng)
    for founder in founders:
        habitat.add_founder(founder)

    habitat.initialize_from_founders()

    assert habitat.population is not None
    assert habitat.population.creatures == founders


def test_captive_habitat_tick_advances_generation_independently():
    rng = random.Random(4)
    habitat = CaptiveHabitat("guppy", 20, rng)
    for _ in range(2):
        habitat.add_founder(Creature.random(GUPPY_SCHEMA, rng))

    habitat.tick()

    assert habitat.population is not None
    assert habitat.generation == 1
    assert len(habitat.population.creatures) > 0


def test_captive_habitat_allele_frequencies_reflect_founder_effect():
    rng = random.Random(5)
    habitat = CaptiveHabitat("guppy", 20, rng)
    for _ in range(2):
        habitat.add_founder(Creature.random(GUPPY_SCHEMA, rng))

    freqs = habitat.allele_frequencies()

    assert set(freqs) == {gene.name for gene in GUPPY_SCHEMA.genes}
