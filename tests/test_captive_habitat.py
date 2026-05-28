


def test_captive_habitat_caps_founders_at_carrying_capacity():
    import random

    from evogame.genetics import BUNNY_SCHEMA, Creature
    from evogame.sim.habitat import CaptiveHabitat

    habitat = CaptiveHabitat("bunny", 2, random.Random(0))
    for _ in range(5):
        habitat.add_founder(Creature.random(BUNNY_SCHEMA, random.Random(_)))

    assert len(habitat.founders) == 2


def test_captive_habitat_records_logs_and_trait_predator_pressure():
    import random

    from evogame.genetics import BUNNY_SCHEMA, Creature
    from evogame.sim.habitat import CaptiveHabitat

    habitat = CaptiveHabitat("bunny", 12, random.Random(0))
    habitat.add_founder(Creature.random(BUNNY_SCHEMA, random.Random(1)))
    habitat.add_founder(Creature.random(BUNNY_SCHEMA, random.Random(2)))
    habitat.set_predator(True, gene="speed", preferred_label="slow")
    habitat.tick()

    assert habitat.predator_on is True
    assert habitat.generation == 1
    assert len(habitat.log.records) >= 2
    assert "speed" in habitat.log.records[-1].allele_freqs
    assert len(habitat.population.creatures) <= habitat.carrying_capacity
