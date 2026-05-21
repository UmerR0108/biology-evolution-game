import random
import pytest
from evogame.genetics.creature import Creature
from evogame.genetics.alleles import Allele
from evogame.genetics.gene_types import DominantRecessiveGene
from evogame.genetics.schema import SpeciesSchema
from evogame.genetics.species.guppy import GUPPY_SCHEMA


def test_breed_with_zero_mutation_rate_records_no_mutations():
    rng = random.Random(0)
    a = Creature.random(GUPPY_SCHEMA, rng)
    b = Creature.random(GUPPY_SCHEMA, rng)
    child = a.breed(b, rng, mutation_rate=0.0)
    assert child.mutations == []


def test_offspring_has_full_genotype():
    rng = random.Random(0)
    a = Creature.random(GUPPY_SCHEMA, rng)
    b = Creature.random(GUPPY_SCHEMA, rng)
    child = a.breed(b, rng, mutation_rate=0.0)
    assert set(child.genotype.keys()) == {g.name for g in GUPPY_SCHEMA.genes}


def _alleles_in_entry(entry):
    """Flatten a genotype entry (single pair OR tuple of pairs) into a list of alleles."""
    first = entry[0]
    if isinstance(first, tuple):  # polygenic
        return [a for pair in entry for a in pair]
    return list(entry)


def test_every_offspring_allele_traces_to_a_parent():
    """Mendelian invariant: with mutation_rate=0, every child allele came from a parent."""
    for seed in range(20):
        rng = random.Random(seed)
        a = Creature.random(GUPPY_SCHEMA, rng)
        b = Creature.random(GUPPY_SCHEMA, rng)
        child = a.breed(b, rng, mutation_rate=0.0)
        for gene_name, child_entry in child.genotype.items():
            parent_alleles = set(
                _alleles_in_entry(a.genotype[gene_name])
                + _alleles_in_entry(b.genotype[gene_name])
            )
            for allele in _alleles_in_entry(child_entry):
                assert allele in parent_alleles, (
                    f"Allele {allele} in child {gene_name!r} not in parents"
                )


def test_breed_with_different_schema_raises():
    rng = random.Random(0)
    other_schema = SpeciesSchema(
        name="other",
        genes=(DominantRecessiveGene("x", Allele("A"), Allele("a")),),
    )
    a = Creature.random(GUPPY_SCHEMA, rng)
    b = Creature.random(other_schema, rng)
    with pytest.raises(ValueError, match="same species"):
        a.breed(b, rng, mutation_rate=0.0)
