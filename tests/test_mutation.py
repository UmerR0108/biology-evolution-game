import random
from evogame.genetics.creature import Creature
from evogame.genetics.species.guppy import GUPPY_SCHEMA


def _alleles_in_entry(entry):
    first = entry[0]
    if isinstance(first, tuple):
        return [a for pair in entry for a in pair]
    return list(entry)


def test_mutation_rate_zero_records_no_mutations():
    rng = random.Random(0)
    a = Creature.random(GUPPY_SCHEMA, rng)
    b = Creature.random(GUPPY_SCHEMA, rng)
    child = a.breed(b, rng, mutation_rate=0.0)
    assert child.mutations == []


def test_mutation_rate_one_replaces_every_allele_with_a_different_one():
    rng = random.Random(0)
    a = Creature.random(GUPPY_SCHEMA, rng)
    b = Creature.random(GUPPY_SCHEMA, rng)
    child = a.breed(b, rng, mutation_rate=1.0)
    # Every recorded mutation must change the allele to a *different* one.
    assert len(child.mutations) > 0
    for ev in child.mutations:
        assert ev.old != ev.new


def test_mutation_records_match_offspring_genotype():
    """Every recorded MutationEvent's `new` allele should appear in the
    offspring's genotype for that gene."""
    rng = random.Random(1)
    a = Creature.random(GUPPY_SCHEMA, rng)
    b = Creature.random(GUPPY_SCHEMA, rng)
    child = a.breed(b, rng, mutation_rate=1.0)
    for ev in child.mutations:
        offspring_alleles = _alleles_in_entry(child.genotype[ev.gene_name])
        assert ev.new in offspring_alleles


def test_mutated_allele_comes_from_gene_pool():
    rng = random.Random(2)
    a = Creature.random(GUPPY_SCHEMA, rng)
    b = Creature.random(GUPPY_SCHEMA, rng)
    child = a.breed(b, rng, mutation_rate=1.0)
    pool_by_gene = {g.name: set(g.alleles) for g in GUPPY_SCHEMA.genes}
    for ev in child.mutations:
        assert ev.new in pool_by_gene[ev.gene_name]
