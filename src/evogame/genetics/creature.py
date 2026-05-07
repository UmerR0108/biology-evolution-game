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


def _mutate_entry(gene, entry, rng, mutation_rate, gene_name, mutations):
    """Walk every allele in `entry`; with probability `mutation_rate`,
    replace it with a different allele drawn uniformly from the gene's pool.
    Records each replacement in `mutations`. Returns the (possibly new) entry."""
    pool = gene.alleles

    def maybe_mutate(allele):
        if rng.random() >= mutation_rate:
            return allele
        alternatives = [a for a in pool if a != allele]
        if not alternatives:  # gene has only one allele — can't mutate
            return allele
        new_allele = rng.choice(alternatives)
        mutations.append(MutationEvent(gene_name=gene_name, old=allele, new=new_allele))
        return new_allele

    first = entry[0]
    if isinstance(first, tuple):  # polygenic — entry is a tuple of pairs
        return tuple(tuple(maybe_mutate(a) for a in pair) for pair in entry)
    return tuple(maybe_mutate(a) for a in entry)


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
        mutations: list[MutationEvent] = []
        offspring_genotype = {}
        for gene in self.schema.genes:
            inherited = gene.inherit(
                self.genotype[gene.name], mate.genotype[gene.name], rng
            )
            offspring_genotype[gene.name] = _mutate_entry(
                gene, inherited, rng, mutation_rate, gene.name, mutations
            )
        return Creature(self.schema, offspring_genotype, mutations=mutations)
