import random
from evogame.genetics.species.guppy import GUPPY_SCHEMA
from evogame.genetics.gene_types import (
    DominantRecessiveGene,
    IncompleteDominanceGene,
    MultiAlleleGene,
    PolygenicGene,
)


def test_guppy_schema_has_four_genes():
    assert GUPPY_SCHEMA.name == "guppy"
    assert len(GUPPY_SCHEMA.genes) == 4


def test_guppy_schema_exercises_all_four_patterns():
    by_type = {type(g) for g in GUPPY_SCHEMA.genes}
    assert by_type == {
        DominantRecessiveGene,
        IncompleteDominanceGene,
        MultiAlleleGene,
        PolygenicGene,
    }


def test_every_gene_can_produce_a_random_genotype():
    rng = random.Random(0)
    for gene in GUPPY_SCHEMA.genes:
        genotype = gene.random_genotype(rng)
        # Should also be expressible without error.
        gene.express(genotype)
