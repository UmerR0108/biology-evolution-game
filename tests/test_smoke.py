def test_package_importable():
    import evogame
    import evogame.genetics


def test_public_api_exports():
    from evogame.genetics import (
        Allele,
        Creature,
        GUPPY_SCHEMA,
        DominantRecessiveGene,
        IncompleteDominanceGene,
        MultiAlleleGene,
        PolygenicGene,
        MutationEvent,
        SpeciesSchema,
        CategoricalPhenotype,
        NumericPhenotype,
        GeneType,
    )
    assert GUPPY_SCHEMA.name == "guppy"
