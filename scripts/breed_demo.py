"""Breed two random guppies and print parent + offspring genotypes/phenotypes.

Usage:
    python scripts/breed_demo.py [--seed N] [--mutation-rate R]
"""
import argparse
import random
import sys
from pathlib import Path

# Allow running directly without `pip install -e .`
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from evogame.genetics.creature import Creature
from evogame.genetics.species.guppy import GUPPY_SCHEMA


def format_creature(label: str, creature: Creature) -> str:
    lines = [f"{label} ({creature.schema.name}):"]
    pheno = creature.phenotype
    for gene in creature.schema.genes:
        entry = creature.genotype[gene.name]
        p = pheno[gene.name]
        # Numeric vs categorical — duck-type via attribute presence.
        value = getattr(p, "category", None) or f"{p.value:.1f}"
        lines.append(f"  {gene.name}: {_format_entry(entry)} -> {value}")
    return "\n".join(lines)


def _format_entry(entry) -> str:
    first = entry[0]
    if isinstance(first, tuple):  # polygenic: tuple of pairs
        return " | ".join("".join(a.symbol for a in pair) for pair in entry)
    return "".join(a.symbol for a in entry)


def run_demo(rng: random.Random, mutation_rate: float) -> tuple[Creature, Creature, Creature]:
    parent_a = Creature.random(GUPPY_SCHEMA, rng)
    parent_b = Creature.random(GUPPY_SCHEMA, rng)
    child = parent_a.breed(parent_b, rng, mutation_rate=mutation_rate)

    print(format_creature("Parent A", parent_a))
    print()
    print(format_creature("Parent B", parent_b))
    print()
    print(format_creature("Offspring", child))
    if child.mutations:
        print()
        print(f"Mutations this generation: {len(child.mutations)}")
        for ev in child.mutations:
            print(f"  {ev.gene_name}: {ev.old.symbol} -> {ev.new.symbol}")
    return parent_a, parent_b, child


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--mutation-rate", type=float, default=0.05)
    args = parser.parse_args()
    run_demo(random.Random(args.seed), args.mutation_rate)


if __name__ == "__main__":
    main()
