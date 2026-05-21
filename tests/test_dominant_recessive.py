import random
from evogame.genetics.alleles import Allele
from evogame.genetics.phenotype import CategoricalPhenotype
from evogame.genetics.gene_types import DominantRecessiveGene

L = Allele("L", "long")
s = Allele("s", "short")
GENE = DominantRecessiveGene(name="fin_length", dominant=L, recessive=s)


def test_homozygous_dominant_expresses_dominant():
    assert GENE.express((L, L)) == CategoricalPhenotype("long")


def test_heterozygous_expresses_dominant():
    assert GENE.express((L, s)) == CategoricalPhenotype("long")
    assert GENE.express((s, L)) == CategoricalPhenotype("long")


def test_homozygous_recessive_expresses_recessive():
    assert GENE.express((s, s)) == CategoricalPhenotype("short")


def test_alleles_field_contains_both():
    assert set(GENE.alleles) == {L, s}


def test_random_genotype_returns_valid_pair():
    rng = random.Random(0)
    for _ in range(50):
        pair = GENE.random_genotype(rng)
        assert len(pair) == 2
        assert all(a in (L, s) for a in pair)


def test_inherit_picks_one_allele_from_each_parent():
    rng = random.Random(0)
    parent_a = (L, L)
    parent_b = (s, s)
    # Every offspring must be heterozygous (L from A, s from B)
    for _ in range(50):
        child = GENE.inherit(parent_a, parent_b, rng)
        assert set(child) == {L, s}
