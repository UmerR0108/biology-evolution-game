from abc import ABC, abstractmethod
from typing import Any
from evogame.genetics.alleles import Allele
from evogame.genetics.phenotype import CategoricalPhenotype, NumericPhenotype

Phenotype = CategoricalPhenotype | NumericPhenotype


class GeneType(ABC):
    name: str
    alleles: tuple[Allele, ...]

    @abstractmethod
    def express(self, genotype: Any) -> Phenotype: ...

    @abstractmethod
    def random_genotype(self, rng) -> Any: ...

    @abstractmethod
    def inherit(self, parent_a_genotype: Any, parent_b_genotype: Any, rng) -> Any: ...
