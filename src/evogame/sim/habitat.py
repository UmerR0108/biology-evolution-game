"""Captive/home habitat simulation seeded by captured founders."""

import random
from dataclasses import dataclass, field

from evogame.genetics import Creature
from evogame.sim.population import Population, Pressure


class NeutralPressure:
    """Default pressure for captive habitats: every creature survives equally."""

    def fitness(self, creature: Creature) -> float:
        return 1.0


@dataclass
class CaptiveHabitat:
    species_name: str
    carrying_capacity: int
    rng: random.Random
    mutation_rate: float = 0.001
    pressure: Pressure | None = None
    founders: list[Creature] = field(default_factory=list)
    population: Population | None = None
    generation: int = 0

    def add_founder(self, creature: Creature) -> None:
        if creature.schema.name != self.species_name:
            raise ValueError(f"Expected {self.species_name} founder, got {creature.schema.name}")
        self.founders.append(creature)
        if self.population is not None:
            self.population.creatures.append(creature)

    def has_minimum_founders(self) -> bool:
        return len(self.founders) >= 2

    def initialize_from_founders(self) -> None:
        if not self.has_minimum_founders():
            return
        self.population = Population(list(self.founders), self.carrying_capacity, self.rng, self.mutation_rate)
        self.generation = 0

    def tick(self) -> None:
        if self.population is None:
            self.initialize_from_founders()
        if self.population is None or len(self.population.creatures) < 2:
            return
        self.population = self.population.step_generation(self.pressure or NeutralPressure())
        self.generation += 1

    def allele_frequencies(self) -> dict[str, dict[str, float]]:
        if self.population is not None:
            return self.population.allele_frequencies()
        if not self.founders:
            return {}
        return Population(list(self.founders), self.carrying_capacity, self.rng, self.mutation_rate).allele_frequencies()

    def phenotype_counts(self, gene_name: str) -> dict[str, int]:
        creatures = self.population.creatures if self.population is not None else self.founders
        counts: dict[str, int] = {}
        for creature in creatures:
            phenotype = creature.phenotype[gene_name]
            label = getattr(phenotype, "category", str(getattr(phenotype, "value", "unknown")))
            counts[label] = counts.get(label, 0) + 1
        return counts
