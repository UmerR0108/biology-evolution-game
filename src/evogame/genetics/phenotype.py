from dataclasses import dataclass


@dataclass(frozen=True)
class CategoricalPhenotype:
    category: str


@dataclass(frozen=True)
class NumericPhenotype:
    value: float
