from dataclasses import dataclass


@dataclass(frozen=True)
class Allele:
    symbol: str
    label: str = ""
