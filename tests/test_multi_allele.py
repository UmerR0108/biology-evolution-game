import random
import pytest
from evogame.genetics.alleles import Allele
from evogame.genetics.phenotype import CategoricalPhenotype
from evogame.genetics.gene_types import MultiAlleleGene

T_COLD = Allele("Tc", "cold")
T_MID = Allele("Tm", "mid")
T_WARM = Allele("Tw", "warm")
GENE = MultiAlleleGene(
    name="temp_tolerance",
    alleles=(T_COLD, T_MID, T_WARM),
    dominance_order=(T_COLD, T_MID, T_WARM),  # cold > mid > warm
)


def test_highest_ranked_allele_wins():
    assert GENE.express((T_COLD, T_WARM)) == CategoricalPhenotype("cold")
    assert GENE.express((T_MID, T_WARM)) == CategoricalPhenotype("mid")
    assert GENE.express((T_WARM, T_WARM)) == CategoricalPhenotype("warm")


def test_homozygous_expresses_that_allele():
    assert GENE.express((T_MID, T_MID)) == CategoricalPhenotype("mid")


def test_dominance_ordering_must_cover_all_alleles():
    with pytest.raises(ValueError):
        MultiAlleleGene(
            name="bad",
            alleles=(T_COLD, T_MID, T_WARM),
            dominance_order=(T_COLD, T_MID),  # missing T_WARM
        )


def test_random_genotype_returns_valid_pair():
    rng = random.Random(2)
    for _ in range(50):
        pair = GENE.random_genotype(rng)
        assert all(a in GENE.alleles for a in pair)


def test_inherit_segregates():
    rng = random.Random(2)
    child = GENE.inherit((T_COLD, T_COLD), (T_WARM, T_WARM), rng)
    assert set(child) == {T_COLD, T_WARM}
