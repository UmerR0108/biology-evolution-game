from dataclasses import dataclass

from evogame.genetics import Creature

_PREDATOR_ON = {"red": 0.2, "pink": 0.5, "white": 0.9}
_PREDATOR_OFF = {"red": 0.9, "pink": 0.7, "white": 0.5}


@dataclass(frozen=True)
class PredatorPressure:
    predator_on: bool

    def fitness(self, creature: Creature) -> float:
        color = creature.phenotype["color"].category
        table = _PREDATOR_ON if self.predator_on else _PREDATOR_OFF
        return table.get(color, 0.5)
