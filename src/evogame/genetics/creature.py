from dataclasses import dataclass, field
from typing import Any
from evogame.genetics.alleles import Allele
from evogame.genetics.schema import SpeciesSchema
from evogame.genetics.phenotype import CategoricalPhenotype, NumericPhenotype

Phenotype = CategoricalPhenotype | NumericPhenotype


@dataclass(frozen=True)
class MutationEvent:
    gene_name: str
    old: Allele
    new: Allele


class Creature:
    def __init__(
        self,
        schema: SpeciesSchema,
        genotype: dict[str, Any],
        mutations: list[MutationEvent] | None = None,
    ):
        self.schema = schema
        self.genotype = genotype
        self.mutations: list[MutationEvent] = mutations if mutations is not None else []

    @classmethod
    def random(cls, schema: SpeciesSchema, rng) -> "Creature":
        genotype = {g.name: g.random_genotype(rng) for g in schema.genes}
        return cls(schema, genotype)

    @property
    def phenotype(self) -> dict[str, Phenotype]:
        return {g.name: g.express(self.genotype[g.name]) for g in self.schema.genes}

    def breed(self, mate: "Creature", rng, mutation_rate: float = 0.001) -> "Creature":
        if self.schema is not mate.schema:
            raise ValueError(
                f"Cannot breed creatures of different species "
                f"({self.schema.name!r} vs {mate.schema.name!r}); must be same species"
            )
        offspring_genotype = {
            g.name: g.inherit(self.genotype[g.name], mate.genotype[g.name], rng)
            for g in self.schema.genes
        }
        # Mutation handling lands in the next task.
        return Creature(self.schema, offspring_genotype)
