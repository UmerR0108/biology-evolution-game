import random
from dataclasses import dataclass
from typing import Protocol

from evogame.genetics import Creature


class Pressure(Protocol):
    def fitness(self, creature: Creature) -> float: ...


def _accumulate_alleles(entry, counts: dict[str, int]) -> None:
    """Walk a genotype entry (flat tuple or nested tuple-of-pairs) and tally allele symbols."""
    first = entry[0]
    if isinstance(first, tuple):  # polygenic
        for pair in entry:
            for allele in pair:
                counts[allele.symbol] = counts.get(allele.symbol, 0) + 1
    else:
        for allele in entry:
            counts[allele.symbol] = counts.get(allele.symbol, 0) + 1


@dataclass
class Population:
    creatures: list[Creature]
    carrying_capacity: int
    rng: random.Random
    mutation_rate: float = 0.001

    def __len__(self) -> int:
        return len(self.creatures)

    def step_generation(self, pressure: Pressure) -> "Population":
        if len(self.creatures) < 2:
            return Population([], self.carrying_capacity, self.rng, self.mutation_rate)

        fitnesses = [pressure.fitness(c) for c in self.creatures]
        if sum(fitnesses) == 0:
            return Population([], self.carrying_capacity, self.rng, self.mutation_rate)

        target_size = min(self.carrying_capacity, len(self.creatures) * 2)
        parents = self.rng.choices(self.creatures, weights=fitnesses, k=target_size * 2)
        offspring = [
            parents[i].breed(parents[i + 1], self.rng, self.mutation_rate)
            for i in range(0, target_size * 2, 2)
        ]
        return Population(offspring, self.carrying_capacity, self.rng, self.mutation_rate)

    def allele_frequencies(self) -> dict[str, dict[str, float]]:
        if not self.creatures:
            return {}
        schema = self.creatures[0].schema
        result: dict[str, dict[str, float]] = {}
        for gene in schema.genes:
            counts: dict[str, int] = {}
            for creature in self.creatures:
                entry = creature.genotype[gene.name]
                _accumulate_alleles(entry, counts)
            total = sum(counts.values())
            result[gene.name] = {sym: c / total for sym, c in counts.items()}
        return result
