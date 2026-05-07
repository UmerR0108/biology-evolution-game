import random
from evogame.genetics.alleles import Allele
from evogame.genetics.phenotype import NumericPhenotype
from evogame.genetics.gene_types import PolygenicGene

BIG = Allele("A", "large")
SMALL = Allele("a", "small")
VALUES = {BIG: 1.0, SMALL: 0.0}
GENE = PolygenicGene(
    name="body_size",
    alleles=(BIG, SMALL),
    loci=3,
    value_of=VALUES,
)


def test_all_big_alleles_max_value():
    genotype = ((BIG, BIG), (BIG, BIG), (BIG, BIG))
    assert GENE.express(genotype) == NumericPhenotype(6.0)


def test_all_small_alleles_min_value():
    genotype = ((SMALL, SMALL), (SMALL, SMALL), (SMALL, SMALL))
    assert GENE.express(genotype) == NumericPhenotype(0.0)


def test_mixed_genotype_sums_correctly():
    genotype = ((BIG, SMALL), (BIG, BIG), (SMALL, SMALL))
    # 1 + 0 + 1 + 1 + 0 + 0 = 3.0
    assert GENE.express(genotype) == NumericPhenotype(3.0)


def test_random_genotype_has_correct_structure():
    rng = random.Random(3)
    genotype = GENE.random_genotype(rng)
    assert len(genotype) == 3
    for pair in genotype:
        assert len(pair) == 2
        assert all(a in (BIG, SMALL) for a in pair)


def test_inherit_segregates_per_locus():
    rng = random.Random(3)
    parent_a = ((BIG, BIG), (BIG, BIG), (BIG, BIG))
    parent_b = ((SMALL, SMALL), (SMALL, SMALL), (SMALL, SMALL))
    child = GENE.inherit(parent_a, parent_b, rng)
    # Each locus must have exactly one BIG (from A) and one SMALL (from B).
    assert len(child) == 3
    for pair in child:
        assert set(pair) == {BIG, SMALL}
