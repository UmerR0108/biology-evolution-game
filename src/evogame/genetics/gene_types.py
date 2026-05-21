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


class IncompleteDominanceGene(GeneType):
    def __init__(self, name: str, allele_a: Allele, allele_b: Allele, blend_label: str):
        self.name = name
        self.allele_a = allele_a
        self.allele_b = allele_b
        self.blend_label = blend_label
        self.alleles = (allele_a, allele_b)

    def express(self, genotype: tuple[Allele, Allele]) -> CategoricalPhenotype:
        a, b = genotype
        if a == b == self.allele_a:
            return CategoricalPhenotype(self.allele_a.label or self.allele_a.symbol)
        if a == b == self.allele_b:
            return CategoricalPhenotype(self.allele_b.label or self.allele_b.symbol)
        return CategoricalPhenotype(self.blend_label)

    def random_genotype(self, rng) -> tuple[Allele, Allele]:
        return (rng.choice(self.alleles), rng.choice(self.alleles))

    def inherit(self, parent_a_genotype, parent_b_genotype, rng) -> tuple[Allele, Allele]:
        return (rng.choice(parent_a_genotype), rng.choice(parent_b_genotype))


class MultiAlleleGene(GeneType):
    def __init__(
        self,
        name: str,
        alleles: tuple[Allele, ...],
        dominance_order: tuple[Allele, ...],
    ):
        if set(dominance_order) != set(alleles):
            raise ValueError(
                f"dominance_order must cover exactly the alleles "
                f"in {name!r}; got {dominance_order} vs {alleles}"
            )
        self.name = name
        self.alleles = alleles
        self.dominance_order = dominance_order

    def express(self, genotype: tuple[Allele, Allele]) -> CategoricalPhenotype:
        for allele in self.dominance_order:
            if allele in genotype:
                return CategoricalPhenotype(allele.label or allele.symbol)
        # Unreachable given the constructor guard, but keeps the type checker happy.
        raise RuntimeError(f"No allele in genotype {genotype} matched dominance order")

    def random_genotype(self, rng) -> tuple[Allele, Allele]:
        return (rng.choice(self.alleles), rng.choice(self.alleles))

    def inherit(self, parent_a_genotype, parent_b_genotype, rng) -> tuple[Allele, Allele]:
        return (rng.choice(parent_a_genotype), rng.choice(parent_b_genotype))


class PolygenicGene(GeneType):
    def __init__(
        self,
        name: str,
        alleles: tuple[Allele, ...],
        loci: int,
        value_of: dict[Allele, float],
    ):
        self.name = name
        self.alleles = alleles
        self.loci = loci
        self.value_of = value_of

    def express(self, genotype: tuple[tuple[Allele, Allele], ...]) -> NumericPhenotype:
        total = sum(self.value_of[a] for pair in genotype for a in pair)
        return NumericPhenotype(value=total)

    def random_genotype(self, rng) -> tuple[tuple[Allele, Allele], ...]:
        return tuple(
            (rng.choice(self.alleles), rng.choice(self.alleles))
            for _ in range(self.loci)
        )

    def inherit(self, parent_a_genotype, parent_b_genotype, rng):
        return tuple(
            (rng.choice(pa), rng.choice(pb))
            for pa, pb in zip(parent_a_genotype, parent_b_genotype, strict=True)
        )
