import math
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


def test_allele_frequencies_empty_population():
    pop = _make_population(0)
    assert pop.allele_frequencies() == {}


def test_allele_frequencies_sum_to_one_per_gene():
    pop = _make_population(20)
    freqs = pop.allele_frequencies()
    for gene_name, gene_freqs in freqs.items():
        total = sum(gene_freqs.values())
        assert math.isclose(total, 1.0, abs_tol=1e-9), f"{gene_name} sums to {total}"


def test_allele_frequencies_includes_all_genes():
    pop = _make_population(20)
    freqs = pop.allele_frequencies()
    expected_genes = {g.name for g in GUPPY_SCHEMA.genes}
    assert set(freqs.keys()) == expected_genes


def test_allele_frequencies_homozygous_population():
    """A population where every creature is homozygous RR has color frequency R=1.0."""
    rng = random.Random(0)
    creatures = []
    color_gene = next(g for g in GUPPY_SCHEMA.genes if g.name == "color")
    R = color_gene.allele_a  # R
    for _ in range(10):
        c = Creature.random(GUPPY_SCHEMA, rng)
        c.genotype["color"] = (R, R)
        creatures.append(c)
    pop = Population(creatures=creatures, carrying_capacity=20, rng=rng)
    color_freqs = pop.allele_frequencies()["color"]
    assert color_freqs[R.symbol] == 1.0


def test_allele_frequencies_polygenic_counts_all_loci():
    """Polygenic genes must tally every locus, not just the first."""
    rng = random.Random(0)
    body = next(g for g in GUPPY_SCHEMA.genes if g.name == "body_size")
    A = body.alleles[0]
    creatures = [Creature.random(GUPPY_SCHEMA, rng) for _ in range(5)]
    for c in creatures:
        c.genotype["body_size"] = ((A, A), (A, A), (A, A))
    pop = Population(creatures=creatures, carrying_capacity=10, rng=rng)
    assert pop.allele_frequencies()["body_size"][A.symbol] == 1.0
