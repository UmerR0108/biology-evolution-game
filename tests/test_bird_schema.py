import random

from evogame.genetics import BIRD_SCHEMA


def test_bird_schema_is_exported_for_forest_species():
    assert BIRD_SCHEMA.name == "bird"
    assert {gene.name for gene in BIRD_SCHEMA.genes} >= {
        "beak_shape",
        "wing_span",
        "coloration",
    }


def test_bird_schema_genes_can_randomize_and_express():
    rng = random.Random(0)
    phenotype = {}
    genotype = {}
    for gene in BIRD_SCHEMA.genes:
        genotype[gene.name] = gene.random_genotype(rng)
        phenotype[gene.name] = gene.express(genotype[gene.name])

    assert phenotype["beak_shape"].category in {"pointed", "broad", "curved"}
    assert phenotype["wing_span"].value >= 0
    assert phenotype["coloration"].category in {"brown", "green", "mottled"}
