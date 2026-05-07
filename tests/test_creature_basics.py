import random
from evogame.genetics.creature import Creature, MutationEvent
from evogame.genetics.alleles import Allele
from evogame.genetics.species.guppy import GUPPY_SCHEMA
from evogame.genetics.phenotype import CategoricalPhenotype, NumericPhenotype


def test_random_creature_has_entry_for_every_gene():
    rng = random.Random(0)
    c = Creature.random(GUPPY_SCHEMA, rng)
    assert set(c.genotype.keys()) == {g.name for g in GUPPY_SCHEMA.genes}


def test_phenotype_returns_one_entry_per_gene():
    rng = random.Random(0)
    c = Creature.random(GUPPY_SCHEMA, rng)
    pheno = c.phenotype
    assert set(pheno.keys()) == {g.name for g in GUPPY_SCHEMA.genes}
    assert isinstance(pheno["color"], CategoricalPhenotype)
    assert isinstance(pheno["body_size"], NumericPhenotype)


def test_mutation_event_records_old_and_new():
    a = Allele("R", "red")
    b = Allele("W", "white")
    ev = MutationEvent(gene_name="color", old=a, new=b)
    assert ev.gene_name == "color"
    assert ev.old == a
    assert ev.new == b


def test_creature_starts_with_empty_mutation_list():
    rng = random.Random(0)
    c = Creature.random(GUPPY_SCHEMA, rng)
    assert c.mutations == []
