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
        self.records.append(
            GenerationRecord(
                gen=gen,
                allele_freqs=allele_freqs,
                predator_on=predator_on,
                population_size=population_size,
            )
        )

    def frequencies_over_time(self, gene_name: str) -> dict[str, list[float]]:
        all_alleles: set[str] = set()
        for r in self.records:
            if gene_name in r.allele_freqs:
                all_alleles.update(r.allele_freqs[gene_name].keys())
        if not all_alleles:
            return {}
        series: dict[str, list[float]] = {a: [] for a in all_alleles}
        for r in self.records:
            gene_freqs = r.allele_freqs.get(gene_name, {})
            for allele in all_alleles:
                series[allele].append(gene_freqs.get(allele, 0.0))
        return series
