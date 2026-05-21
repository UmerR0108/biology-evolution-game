import pytest
from dataclasses import FrozenInstanceError
from evogame.genetics.alleles import Allele


def test_allele_has_symbol_and_label():
    a = Allele(symbol="R", label="red")
    assert a.symbol == "R"
    assert a.label == "red"


def test_allele_label_defaults_to_empty_string():
    a = Allele(symbol="R")
    assert a.label == ""


def test_allele_is_frozen():
    a = Allele(symbol="R", label="red")
    with pytest.raises(FrozenInstanceError):
        a.symbol = "W"


def test_allele_is_hashable_and_equal_by_value():
    a1 = Allele(symbol="R", label="red")
    a2 = Allele(symbol="R", label="red")
    assert a1 == a2
    assert hash(a1) == hash(a2)
    assert {a1, a2} == {a1}
