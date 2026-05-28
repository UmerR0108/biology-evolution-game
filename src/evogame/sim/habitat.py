"""Captive/home habitat simulation seeded by captured founders."""

import random
from dataclasses import dataclass, field

from evogame.genetics import Creature
from evogame.sim.population import Population, Pressure
from evogame.sim.recorder import GenerationLog


class NeutralPressure:
    """Default pressure for captive habitats: every creature survives equally."""

    def fitness(self, creature: Creature) -> float:
        return 1.0


@dataclass
class TraitPredatorPressure:
    """Captive predator that prefers prey with one visible trait.

    Preferred creatures survive/reproduce better; non-preferred trait holders
    are still possible, so the population evolves instead of instantly
    collapsing. For numeric traits, ``preferred_label="slow"`` means lower
    values are favored, while any other label favors higher values.
    """

    predator_on: bool = False
    gene: str = "speed"
    preferred_label: str = "slow"

    def fitness(self, creature: Creature) -> float:
        if not self.predator_on:
            return 1.0
        phenotype = creature.phenotype.get(self.gene)
        if phenotype is None:
            return 1.0
        if hasattr(phenotype, "category"):
            return 1.45 if phenotype.category == self.preferred_label else 0.65
        value = float(getattr(phenotype, "value", 0.0))
        if self.preferred_label in {"slow", "small", "short", "shy"}:
            return max(0.35, 1.65 - value * 0.22)
        return max(0.35, 0.55 + value * 0.22)


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
    log: GenerationLog = field(default_factory=GenerationLog)
    predator_on: bool = False
    predator_gene: str = "speed"
    predator_preferred_label: str = "slow"

    def add_founder(self, creature: Creature) -> None:
        if creature.schema.name != self.species_name:
            raise ValueError(f"Expected {self.species_name} founder, got {creature.schema.name}")
        if len(self.founders) >= self.carrying_capacity:
            return
        self.founders.append(creature)
        self._record()
        if self.population is not None and len(self.population.creatures) < self.carrying_capacity:
            self.population.creatures.append(creature)
            self._record()

    def has_minimum_founders(self) -> bool:
        return len(self.founders) >= 2

    def initialize_from_founders(self) -> None:
        if not self.has_minimum_founders():
            return
        self.population = Population(list(self.founders[:self.carrying_capacity]), self.carrying_capacity, self.rng, self.mutation_rate)
        self.generation = 0
        self.log = GenerationLog()
        self._record()

    def _active_pressure(self) -> Pressure:
        if self.pressure is not None:
            return self.pressure
        return TraitPredatorPressure(self.predator_on, self.predator_gene, self.predator_preferred_label)

    def _record(self) -> None:
        creatures = self.population.creatures if self.population is not None else self.founders
        if not creatures:
            return
        pop = self.population or Population(list(creatures), self.carrying_capacity, self.rng, self.mutation_rate)
        self.log.record(
            gen=self.generation,
            allele_freqs=pop.allele_frequencies(),
            predator_on=self.predator_on,
            population_size=len(creatures),
        )

    def set_predator(self, on: bool, *, gene: str | None = None, preferred_label: str | None = None) -> None:
        self.predator_on = on
        if gene is not None:
            self.predator_gene = gene
        if preferred_label is not None:
            self.predator_preferred_label = preferred_label

    def reset(self) -> None:
        self.population = None
        self.generation = 0
        self.log = GenerationLog()
        self.predator_on = False

    def tick(self) -> None:
        if self.population is None:
            self.initialize_from_founders()
        if self.population is None or len(self.population.creatures) < 2:
            return
        self.population = self.population.step_generation(self._active_pressure())
        self.generation += 1
        self._record()

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
