import random
from scripts.breed_demo import format_creature, run_demo


def test_format_creature_includes_all_gene_names():
    rng = random.Random(0)
    out = format_creature("Parent A", _make_creature(rng))
    assert "Parent A" in out
    for name in ("color", "fin_length", "temp_tolerance", "body_size"):
        assert name in out


def test_run_demo_returns_three_creatures_and_prints():
    rng = random.Random(42)
    parents_and_child = run_demo(rng=rng, mutation_rate=0.5)
    assert len(parents_and_child) == 3  # parent_a, parent_b, child
    a, b, child = parents_and_child
    # Same schema across all three.
    assert a.schema is b.schema is child.schema


def _make_creature(rng):
    from evogame.genetics.creature import Creature
    from evogame.genetics.species.guppy import GUPPY_SCHEMA
    return Creature.random(GUPPY_SCHEMA, rng)
