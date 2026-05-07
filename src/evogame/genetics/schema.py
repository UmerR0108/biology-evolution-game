from dataclasses import dataclass
from evogame.genetics.gene_types import GeneType


@dataclass(frozen=True)
class SpeciesSchema:
    name: str
    genes: tuple[GeneType, ...]

    def __post_init__(self):
        names = [g.name for g in self.genes]
        if len(names) != len(set(names)):
            raise ValueError(f"Duplicate gene names in schema {self.name!r}: {names}")
