# Genetics Engine — MVP Design

**Date:** 2026-05-06
**Scope:** Core genetics engine for the AP Bio evolution game. First slice toward the MVP defined in `PROJECT_SPEC.md`. No Pygame, no UI, no selection math — just genes, alleles, inheritance, mutation, and a working breed/observe demo.

## Goals

- A `Creature` class that owns a genotype, can breed with another creature, and can mutate.
- All four inheritance patterns from the spec working end-to-end: simple dominant/recessive, incomplete dominance, multiple alleles, polygenic.
- One species defined as a fixture (guppy) that exercises all four patterns.
- Pytest test suite covering each pattern + inheritance invariants + mutation behavior.
- Demo script that breeds two random guppies and prints parent + offspring genotypes/phenotypes.

## Non-goals (explicitly deferred)

- Selection math, fitness scoring, habitat variables.
- Allele frequency tracking across populations.
- Speciation / genetic distance.
- Novel-allele mutation (mutation only swaps among the existing per-gene allele pool for now).
- Persistence (save/load).
- Any visual or Pygame code.

## Key decisions

### 1. All four inheritance patterns from day 1 (not just dominant/recessive)

The four patterns have meaningfully different data shapes (polygenic references multiple loci; multi-allele needs a dominance ordering; incomplete dominance needs a blend label). Designing the abstraction now is ~30 extra lines and avoids a refactor of the `Gene` class later, which would cascade into every species schema we've written.

### 2. Class hierarchy for gene types (not discriminator + dispatch, not pure data)

`GeneType` ABC with one subclass per inheritance pattern. Each subclass owns its own data shape and its own `express` / `inherit` / `random_genotype` logic. Alternatives considered:

- **Single `Gene` class with a `pattern` discriminator and central dispatch.** Less code, but the central dispatcher becomes a swamp as new patterns (sex-linked, epistatic) get added, and pattern-specific fields can't be type-checked.
- **Pure data + functional dispatch.** Easier to serialize but loses type safety on pattern-specific fields.

The class-hierarchy approach also extends cleanly when speciation / new gene patterns arrive.

### 3. pytest from day 1, plus a separate demo script

The genetics engine is the load-bearing piece of the whole game; regression tests pay for themselves immediately as we add the other three species and the selection math. The demo script keeps the "I can see it work" experience without polluting the test suite with prints.

### 4. Injected `random.Random`, no global RNG

Every randomness-using method takes an explicit `rng` parameter. Tests construct `random.Random(seed)` for reproducibility. No `random.seed()` anywhere in the engine.

### 5. `src/` package layout

Standard Python package layout (`src/evogame/`), prevents accidental imports from CWD, plays nicely with pytest. Keeps imports clean once Pygame and other modules land.

### 6. Per-species schemas as Python modules (not JSON/YAML)

Lets schemas reference their `GeneType` subclasses directly, no parser needed. Can switch to data files later if non-coders need to author species — the `SpeciesSchema` constructor stays the boundary.

## Architecture

```
D:\game\
├── src/evogame/genetics/
│   ├── alleles.py          # Allele dataclass (frozen)
│   ├── gene_types.py       # GeneType ABC + 4 subclasses
│   ├── schema.py           # SpeciesSchema
│   ├── creature.py         # Creature: genotype, phenotype, breed, mutate
│   └── species/guppy.py    # GUPPY_SCHEMA fixture
├── tests/                  # one test_*.py per genetics module
└── scripts/breed_demo.py   # the demo
```

A `Creature` is `(species_schema, genotype)`. The `genotype` is `dict[gene_name, ...]` where the value's shape depends on the gene type (single allele pair for most, tuple of pairs for polygenic). Phenotype is computed lazily by delegating to each `GeneType`.

`Creature.breed(mate, rng, mutation_rate)` walks the schema, asks each `GeneType` to produce an offspring entry from the parents' entries (Mendelian segregation lives on `GeneType`, not on `Creature` — keeps `Creature` generic), then applies mutation per allele.

## Inheritance patterns — concrete shapes

| Subclass | Genotype shape | `express` returns |
|---|---|---|
| `DominantRecessiveGene(dominant, recessive)` | `tuple[Allele, Allele]` | discrete (2 phenotypes) |
| `IncompleteDominanceGene(allele_a, allele_b, blend_label)` | `tuple[Allele, Allele]` | discrete (3 phenotypes) |
| `MultiAlleleGene(alleles, dominance_order)` | `tuple[Allele, Allele]` | discrete (highest-ranked allele present) |
| `PolygenicGene(loci, value_of)` | `tuple[tuple[Allele, Allele], ...]` | numeric (sum across loci) |

`Phenotype` is a small union: `CategoricalPhenotype(category: str)` or `NumericPhenotype(value: float)`.

## Guppy fixture (test species)

Exercises all four patterns in one species — the architectural risk we're validating.

| Gene | Pattern | Alleles |
|---|---|---|
| color | IncompleteDominance | R (red), W (white) → red / pink / white |
| fin_length | DominantRecessive | L (long), s (short) |
| temp_tolerance | MultiAllele | T_cold > T_mid > T_warm |
| body_size | Polygenic | 3 loci, each A (+1.0) / a (+0.0) → continuous 0.0–6.0 |

## Mutation model

- After inheritance, walk every allele in the offspring's genotype.
- With probability `mutation_rate` (default 0.001), replace it with a different allele drawn uniformly from the gene's allele pool.
- Record each replacement as a `MutationEvent(gene_name, old_allele, new_allele)` on the offspring. Cheap to add now, painful to retrofit when the field journal feature lands.
- **Deferred:** novel-allele mutation (introducing alleles not in the original pool). The MVP allele pool is fixed per gene.

## Error handling

Defensive walls are deliberately omitted. Schemas are built at import time — malformed schemas crash at import with a useful traceback. The only runtime guard is `breed`'s same-species check (raises `ValueError` if `self.schema is not mate.schema`). Everything else (missing gene, wrong allele) is a programmer error and crashes loudly.

## Testing

- `test_alleles.py` — frozen, hashable, equal-by-value.
- `test_gene_types.py` — for each subclass, hand-crafted genotype → expected phenotype; `random_genotype(rng)` produces only valid alleles.
- `test_creature_inheritance.py` — exact offspring genotype with seeded RNG and `mutation_rate=0`; Mendelian invariant (every offspring allele traces to a parent) over 100 random pairings; same-species guard raises.
- `test_mutation.py` — `mutation_rate=0` → zero events; `mutation_rate=1.0` → every allele changes to a *different* allele; `MutationEvent` records correctly.

## Demo

`scripts/breed_demo.py` builds two random guppies with a fixed seed, breeds them, prints both parents' and the offspring's genotype + phenotype, plus any mutations. `--seed N` flag overrides.

## Out of scope for the implementation plan that follows this doc

The next step (writing-plans) breaks this into ordered, TDD-style tasks. It does **not** touch:

- Pygame, rendering, input handling.
- The other three species (beetle, bird, snail).
- Population-level concerns (allele frequencies, generations, fitness).
- The field journal.
