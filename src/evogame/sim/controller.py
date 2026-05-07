import random

from evogame.genetics import Creature, SpeciesSchema
from evogame.sim.population import Population
from evogame.sim.pressure import PredatorPressure
from evogame.sim.recorder import GenerationLog


class SimController:
    def __init__(
        self,
        schema: SpeciesSchema,
        initial_size: int,
        carrying_capacity: int,
        rng: random.Random,
        mutation_rate: float = 0.001,
    ):
        self.schema = schema
        self.initial_size = initial_size
        self.carrying_capacity = carrying_capacity
        self.rng = rng
        self.mutation_rate = mutation_rate
        self.pressure = PredatorPressure(predator_on=False)
        self.population: Population = self._fresh_population()
        self.log = GenerationLog()
        self.generation = 0
        self.extinct = False
        self._record()

    def _fresh_population(self) -> Population:
        creatures = [Creature.random(self.schema, self.rng) for _ in range(self.initial_size)]
        return Population(creatures, self.carrying_capacity, self.rng, self.mutation_rate)

    def _record(self) -> None:
        self.log.record(
            gen=self.generation,
            allele_freqs=self.population.allele_frequencies(),
            predator_on=self.pressure.predator_on,
            population_size=len(self.population),
        )

    def tick(self) -> None:
        if self.extinct:
            return
        self.population = self.population.step_generation(self.pressure)
        self.generation += 1
        self._record()
        if len(self.population) == 0:
            self.extinct = True

    def set_predator(self, on: bool) -> None:
        self.pressure = PredatorPressure(predator_on=on)

    def reset(self) -> None:
        self.pressure = PredatorPressure(predator_on=False)
        self.population = self._fresh_population()
        self.log = GenerationLog()
        self.generation = 0
        self.extinct = False
        self._record()
