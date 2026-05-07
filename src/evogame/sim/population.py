import random
from dataclasses import dataclass
from typing import Protocol

from evogame.genetics import Creature


class Pressure(Protocol):
    def fitness(self, creature: Creature) -> float: ...


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
