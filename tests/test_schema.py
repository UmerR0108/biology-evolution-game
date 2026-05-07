import pytest
from evogame.genetics.alleles import Allele
from evogame.genetics.gene_types import DominantRecessiveGene
from evogame.genetics.schema import SpeciesSchema


def test_schema_holds_name_and_genes():
    gene = DominantRecessiveGene(
        name="fin_length",
        dominant=Allele("L", "long"),
        recessive=Allele("s", "short"),
    )
    schema = SpeciesSchema(name="guppy", genes=(gene,))
    assert schema.name == "guppy"
    assert schema.genes == (gene,)


def test_schema_rejects_duplicate_gene_names():
    g1 = DominantRecessiveGene("dup", Allele("A"), Allele("a"))
    g2 = DominantRecessiveGene("dup", Allele("B"), Allele("b"))
    with pytest.raises(ValueError):
        SpeciesSchema(name="bad", genes=(g1, g2))
