import pytest
from evogame.genetics.phenotype import CategoricalPhenotype, NumericPhenotype
from evogame.genetics.gene_types import GeneType


def test_categorical_phenotype_holds_category():
    p = CategoricalPhenotype(category="red")
    assert p.category == "red"


def test_numeric_phenotype_holds_value():
    p = NumericPhenotype(value=3.5)
    assert p.value == 3.5


def test_phenotypes_equal_by_value():
    assert CategoricalPhenotype("red") == CategoricalPhenotype("red")
    assert NumericPhenotype(3.0) == NumericPhenotype(3.0)


def test_gene_type_cannot_be_instantiated():
    with pytest.raises(TypeError):
        GeneType()
