from dataclasses import dataclass, field


@dataclass(frozen=True)
class GenerationRecord:
    gen: int
    allele_freqs: dict[str, dict[str, float]]
    predator_on: bool
    population_size: int


@dataclass
class GenerationLog:
    records: list[GenerationRecord] = field(default_factory=list)

    def __len__(self) -> int:
        return len(self.records)

    def record(
        self,
        gen: int,
        allele_freqs: dict[str, dict[str, float]],
        predator_on: bool,
        population_size: int,
    ) -> None:
        snapshot = {gene: dict(freqs) for gene, freqs in allele_freqs.items()}
        self.records.append(
            GenerationRecord(
                gen=gen,
                allele_freqs=snapshot,
                predator_on=predator_on,
                population_size=population_size,
            )
        )

    def frequencies_over_time(self, gene_name: str) -> dict[str, list[float]]:
        ordered_alleles: dict[str, None] = {}
        for r in self.records:
            for sym in r.allele_freqs.get(gene_name, {}):
                ordered_alleles.setdefault(sym, None)
        if not ordered_alleles:
            return {}
        series: dict[str, list[float]] = {a: [] for a in ordered_alleles}
        for r in self.records:
            gene_freqs = r.allele_freqs.get(gene_name, {})
            for allele in ordered_alleles:
                series[allele].append(gene_freqs.get(allele, 0.0))
        return series
