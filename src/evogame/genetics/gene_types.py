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


class DominantRecessiveGene(GeneType):
    def __init__(self, name: str, dominant: Allele, recessive: Allele):
        self.name = name
        self.dominant = dominant
        self.recessive = recessive
        self.alleles = (dominant, recessive)

    def express(self, genotype: tuple[Allele, Allele]) -> CategoricalPhenotype:
        if self.dominant in genotype:
            return CategoricalPhenotype(self.dominant.label or self.dominant.symbol)
        return CategoricalPhenotype(self.recessive.label or self.recessive.symbol)

    def random_genotype(self, rng) -> tuple[Allele, Allele]:
        return (rng.choice(self.alleles), rng.choice(self.alleles))

    def inherit(self, parent_a_genotype, parent_b_genotype, rng) -> tuple[Allele, Allele]:
        return (rng.choice(parent_a_genotype), rng.choice(parent_b_genotype))
