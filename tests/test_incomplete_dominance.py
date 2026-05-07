import random
from evogame.genetics.alleles import Allele
from evogame.genetics.phenotype import CategoricalPhenotype
from evogame.genetics.gene_types import IncompleteDominanceGene

R = Allele("R", "red")
W = Allele("W", "white")
GENE = IncompleteDominanceGene(name="color", allele_a=R, allele_b=W, blend_label="pink")


def test_homozygous_a_expresses_a_label():
    assert GENE.express((R, R)) == CategoricalPhenotype("red")


def test_homozygous_b_expresses_b_label():
    assert GENE.express((W, W)) == CategoricalPhenotype("white")


def test_heterozygous_expresses_blend():
    assert GENE.express((R, W)) == CategoricalPhenotype("pink")
    assert GENE.express((W, R)) == CategoricalPhenotype("pink")


def test_random_genotype_returns_valid_pair():
    rng = random.Random(1)
    for _ in range(50):
        pair = GENE.random_genotype(rng)
        assert all(a in (R, W) for a in pair)


def test_inherit_segregates():
    rng = random.Random(1)
    child = GENE.inherit((R, R), (W, W), rng)
    assert set(child) == {R, W}
