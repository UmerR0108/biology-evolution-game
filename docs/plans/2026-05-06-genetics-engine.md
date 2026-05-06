# Genetics Engine Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.
> Each task follows TDD discipline (superpowers:test-driven-development): failing test first, run it, minimal implementation, run again, commit.

**Goal:** Build the species-agnostic genetics engine for the AP Bio evolution game — alleles, four inheritance patterns behind a `GeneType` class hierarchy, a `Creature` class that can breed and mutate, a guppy fixture that exercises all four patterns, and a demo script.

**Architecture:** Per the design doc at `docs/plans/2026-05-06-genetics-engine-design.md`. `Creature(schema, genotype)` delegates inheritance and expression to per-pattern `GeneType` subclasses. RNG is injected explicitly (no global state). Mutation runs after inheritance and records `MutationEvent`s on the offspring.

**Tech Stack:** Python 3.11+, pytest, stdlib `random` and `dataclasses`. Pygame is *not* a dependency of this slice — UI lives in a future plan.

**Conventions used in this plan:**
- All commands run from `D:\game\` unless noted.
- Use the Bash tool with forward-slash paths (`/d/game/...`) — this is a Windows + bash environment.
- Each task ends with a commit using the listed message. Do **not** batch commits across tasks.
- "Run tests" always means `pytest -q` from the repo root unless a narrower target is given.

---

## Task 1: Project scaffold

**Files:**
- Create: `pyproject.toml`
- Create: `src/evogame/__init__.py` (empty)
- Create: `src/evogame/genetics/__init__.py` (empty)
- Create: `tests/__init__.py` (empty)
- Create: `tests/test_smoke.py`
- Create: `README.md`

**Step 1: Write `pyproject.toml`**

```toml
[build-system]
requires = ["setuptools>=68"]
build-backend = "setuptools.build_meta"

[project]
name = "evogame"
version = "0.1.0"
description = "AP Biology evolution simulation game"
requires-python = ">=3.11"
dependencies = []

[project.optional-dependencies]
dev = ["pytest>=8"]

[tool.setuptools.packages.find]
where = ["src"]

[tool.pytest.ini_options]
pythonpath = ["src"]
testpaths = ["tests"]
```

`pythonpath = ["src"]` is what makes `from evogame.genetics... import ...` work in tests without an editable install.

**Step 2: Write `tests/test_smoke.py`**

```python
def test_package_importable():
    import evogame
    import evogame.genetics
```

**Step 3: Write minimal `README.md`**

```markdown
# evogame

AP Biology evolution simulation game.

## Setup

    python -m pip install -e ".[dev]"

## Run tests

    pytest

## Run the breeding demo

    python scripts/breed_demo.py
```

**Step 4: Install dev deps and run the smoke test**

Run: `python -m pip install -e ".[dev]"` then `pytest -q`
Expected: 1 passed.

**Step 5: Commit**

```bash
git add pyproject.toml README.md src/ tests/
git commit -m "chore: project scaffold with src layout and pytest"
```

---

## Task 2: `Allele` dataclass

**Files:**
- Create: `src/evogame/genetics/alleles.py`
- Create: `tests/test_alleles.py`

**Step 1: Write the failing tests**

```python
# tests/test_alleles.py
import pytest
from dataclasses import FrozenInstanceError
from evogame.genetics.alleles import Allele


def test_allele_has_symbol_and_label():
    a = Allele(symbol="R", label="red")
    assert a.symbol == "R"
    assert a.label == "red"


def test_allele_label_defaults_to_empty_string():
    a = Allele(symbol="R")
    assert a.label == ""


def test_allele_is_frozen():
    a = Allele(symbol="R", label="red")
    with pytest.raises(FrozenInstanceError):
        a.symbol = "W"


def test_allele_is_hashable_and_equal_by_value():
    a1 = Allele(symbol="R", label="red")
    a2 = Allele(symbol="R", label="red")
    assert a1 == a2
    assert hash(a1) == hash(a2)
    assert {a1, a2} == {a1}
```

**Step 2: Run tests to verify failure**

Run: `pytest tests/test_alleles.py -q`
Expected: FAIL — `ModuleNotFoundError: No module named 'evogame.genetics.alleles'`.

**Step 3: Write the implementation**

```python
# src/evogame/genetics/alleles.py
from dataclasses import dataclass


@dataclass(frozen=True)
class Allele:
    symbol: str
    label: str = ""
```

**Step 4: Run tests to verify pass**

Run: `pytest tests/test_alleles.py -q`
Expected: 4 passed.

**Step 5: Commit**

```bash
git add src/evogame/genetics/alleles.py tests/test_alleles.py
git commit -m "feat(genetics): add Allele dataclass"
```

---

## Task 3: `Phenotype` types and `GeneType` ABC

**Files:**
- Create: `src/evogame/genetics/phenotype.py`
- Create: `src/evogame/genetics/gene_types.py`
- Create: `tests/test_phenotype.py`

`GeneType` is an ABC — it has no testable behavior of its own beyond "you can't instantiate it." We test that here, then test concrete subclasses in Tasks 4–7.

**Step 1: Write the failing tests**

```python
# tests/test_phenotype.py
import pytest
from evogame.genetics.phenotype import CategoricalPhenotype, NumericPhenotype
from evogame.genetics.gene_types import GeneType


def test_categorical_phenotype_holds_category():
    p = CategoricalPhenotype(category="red")
    assert p.category == "red"


def test_numeric_phenotype_holds_value():
    p = NumericPhenotype(value=3.5)
    assert p.value == 3.5


def test_phenotypes_equal_by_value():
    assert CategoricalPhenotype("red") == CategoricalPhenotype("red")
    assert NumericPhenotype(3.0) == NumericPhenotype(3.0)


def test_gene_type_cannot_be_instantiated():
    with pytest.raises(TypeError):
        GeneType()
```

**Step 2: Run tests to verify failure**

Run: `pytest tests/test_phenotype.py -q`
Expected: FAIL with `ModuleNotFoundError`.

**Step 3: Write the implementation**

```python
# src/evogame/genetics/phenotype.py
from dataclasses import dataclass


@dataclass(frozen=True)
class CategoricalPhenotype:
    category: str


@dataclass(frozen=True)
class NumericPhenotype:
    value: float
```

```python
# src/evogame/genetics/gene_types.py
from abc import ABC, abstractmethod
from typing import Any
from evogame.genetics.alleles import Allele
from evogame.genetics.phenotype import CategoricalPhenotype, NumericPhenotype

Phenotype = CategoricalPhenotype | NumericPhenotype


class GeneType(ABC):
    name: str
    alleles: tuple[Allele, ...]

    @abstractmethod
    def express(self, genotype: Any) -> Phenotype: ...

    @abstractmethod
    def random_genotype(self, rng) -> Any: ...

    @abstractmethod
    def inherit(self, parent_a_genotype: Any, parent_b_genotype: Any, rng) -> Any: ...
```

**Step 4: Run tests to verify pass**

Run: `pytest tests/test_phenotype.py -q`
Expected: 4 passed.

**Step 5: Commit**

```bash
git add src/evogame/genetics/phenotype.py src/evogame/genetics/gene_types.py tests/test_phenotype.py
git commit -m "feat(genetics): add Phenotype types and GeneType ABC"
```

---

## Task 4: `DominantRecessiveGene`

**Files:**
- Modify: `src/evogame/genetics/gene_types.py`
- Create: `tests/test_dominant_recessive.py`

**Step 1: Write the failing tests**

```python
# tests/test_dominant_recessive.py
import random
from evogame.genetics.alleles import Allele
from evogame.genetics.phenotype import CategoricalPhenotype
from evogame.genetics.gene_types import DominantRecessiveGene

L = Allele("L", "long")
s = Allele("s", "short")
GENE = DominantRecessiveGene(name="fin_length", dominant=L, recessive=s)


def test_homozygous_dominant_expresses_dominant():
    assert GENE.express((L, L)) == CategoricalPhenotype("long")


def test_heterozygous_expresses_dominant():
    assert GENE.express((L, s)) == CategoricalPhenotype("long")
    assert GENE.express((s, L)) == CategoricalPhenotype("long")


def test_homozygous_recessive_expresses_recessive():
    assert GENE.express((s, s)) == CategoricalPhenotype("short")


def test_alleles_field_contains_both():
    assert set(GENE.alleles) == {L, s}


def test_random_genotype_returns_valid_pair():
    rng = random.Random(0)
    for _ in range(50):
        pair = GENE.random_genotype(rng)
        assert len(pair) == 2
        assert all(a in (L, s) for a in pair)


def test_inherit_picks_one_allele_from_each_parent():
    rng = random.Random(0)
    parent_a = (L, L)
    parent_b = (s, s)
    # Every offspring must be heterozygous (L from A, s from B)
    for _ in range(50):
        child = GENE.inherit(parent_a, parent_b, rng)
        assert set(child) == {L, s}
```

**Step 2: Run tests to verify failure**

Run: `pytest tests/test_dominant_recessive.py -q`
Expected: FAIL — `ImportError: cannot import name 'DominantRecessiveGene'`.

**Step 3: Add the implementation**

Append to `src/evogame/genetics/gene_types.py`:

```python
class DominantRecessiveGene(GeneType):
    def __init__(self, name: str, dominant: Allele, recessive: Allele):
        self.name = name
        self.dominant = dominant
        self.recessive = recessive
        self.alleles = (dominant, recessive)

    def express(self, genotype: tuple[Allele, Allele]) -> CategoricalPhenotype:
        if self.dominant in genotype:
            return CategoricalPhenotype(self.dominant.label or self.dominant.symbol)
        return CategoricalPhenotype(self.recessive.label or self.recessive.symbol)

    def random_genotype(self, rng) -> tuple[Allele, Allele]:
        return (rng.choice(self.alleles), rng.choice(self.alleles))

    def inherit(self, parent_a_genotype, parent_b_genotype, rng) -> tuple[Allele, Allele]:
        return (rng.choice(parent_a_genotype), rng.choice(parent_b_genotype))
```

**Step 4: Run tests to verify pass**

Run: `pytest tests/test_dominant_recessive.py -q`
Expected: 6 passed.

**Step 5: Commit**

```bash
git add src/evogame/genetics/gene_types.py tests/test_dominant_recessive.py
git commit -m "feat(genetics): add DominantRecessiveGene"
```

---

## Task 5: `IncompleteDominanceGene`

**Files:**
- Modify: `src/evogame/genetics/gene_types.py`
- Create: `tests/test_incomplete_dominance.py`

**Step 1: Write the failing tests**

```python
# tests/test_incomplete_dominance.py
import random
from evogame.genetics.alleles import Allele
from evogame.genetics.phenotype import CategoricalPhenotype
from evogame.genetics.gene_types import IncompleteDominanceGene

R = Allele("R", "red")
W = Allele("W", "white")
GENE = IncompleteDominanceGene(name="color", allele_a=R, allele_b=W, blend_label="pink")


def test_homozygous_a_expresses_a_label():
    assert GENE.express((R, R)) == CategoricalPhenotype("red")


def test_homozygous_b_expresses_b_label():
    assert GENE.express((W, W)) == CategoricalPhenotype("white")


def test_heterozygous_expresses_blend():
    assert GENE.express((R, W)) == CategoricalPhenotype("pink")
    assert GENE.express((W, R)) == CategoricalPhenotype("pink")


def test_random_genotype_returns_valid_pair():
    rng = random.Random(1)
    for _ in range(50):
        pair = GENE.random_genotype(rng)
        assert all(a in (R, W) for a in pair)


def test_inherit_segregates():
    rng = random.Random(1)
    child = GENE.inherit((R, R), (W, W), rng)
    assert set(child) == {R, W}
```

**Step 2: Run tests to verify failure**

Run: `pytest tests/test_incomplete_dominance.py -q`
Expected: FAIL — `ImportError`.

**Step 3: Add the implementation**

Append to `src/evogame/genetics/gene_types.py`:

```python
class IncompleteDominanceGene(GeneType):
    def __init__(self, name: str, allele_a: Allele, allele_b: Allele, blend_label: str):
        self.name = name
        self.allele_a = allele_a
        self.allele_b = allele_b
        self.blend_label = blend_label
        self.alleles = (allele_a, allele_b)

    def express(self, genotype: tuple[Allele, Allele]) -> CategoricalPhenotype:
        a, b = genotype
        if a == b == self.allele_a:
            return CategoricalPhenotype(self.allele_a.label or self.allele_a.symbol)
        if a == b == self.allele_b:
            return CategoricalPhenotype(self.allele_b.label or self.allele_b.symbol)
        return CategoricalPhenotype(self.blend_label)

    def random_genotype(self, rng) -> tuple[Allele, Allele]:
        return (rng.choice(self.alleles), rng.choice(self.alleles))

    def inherit(self, parent_a_genotype, parent_b_genotype, rng) -> tuple[Allele, Allele]:
        return (rng.choice(parent_a_genotype), rng.choice(parent_b_genotype))
```

**Step 4: Run tests to verify pass**

Run: `pytest tests/test_incomplete_dominance.py -q`
Expected: 5 passed.

**Step 5: Commit**

```bash
git add src/evogame/genetics/gene_types.py tests/test_incomplete_dominance.py
git commit -m "feat(genetics): add IncompleteDominanceGene"
```

---

## Task 6: `MultiAlleleGene`

**Files:**
- Modify: `src/evogame/genetics/gene_types.py`
- Create: `tests/test_multi_allele.py`

**Step 1: Write the failing tests**

```python
# tests/test_multi_allele.py
import random
import pytest
from evogame.genetics.alleles import Allele
from evogame.genetics.phenotype import CategoricalPhenotype
from evogame.genetics.gene_types import MultiAlleleGene

T_COLD = Allele("Tc", "cold")
T_MID = Allele("Tm", "mid")
T_WARM = Allele("Tw", "warm")
GENE = MultiAlleleGene(
    name="temp_tolerance",
    alleles=(T_COLD, T_MID, T_WARM),
    dominance_order=(T_COLD, T_MID, T_WARM),  # cold > mid > warm
)


def test_highest_ranked_allele_wins():
    assert GENE.express((T_COLD, T_WARM)) == CategoricalPhenotype("cold")
    assert GENE.express((T_MID, T_WARM)) == CategoricalPhenotype("mid")
    assert GENE.express((T_WARM, T_WARM)) == CategoricalPhenotype("warm")


def test_homozygous_expresses_that_allele():
    assert GENE.express((T_MID, T_MID)) == CategoricalPhenotype("mid")


def test_dominance_ordering_must_cover_all_alleles():
    with pytest.raises(ValueError):
        MultiAlleleGene(
            name="bad",
            alleles=(T_COLD, T_MID, T_WARM),
            dominance_order=(T_COLD, T_MID),  # missing T_WARM
        )


def test_random_genotype_returns_valid_pair():
    rng = random.Random(2)
    for _ in range(50):
        pair = GENE.random_genotype(rng)
        assert all(a in GENE.alleles for a in pair)


def test_inherit_segregates():
    rng = random.Random(2)
    child = GENE.inherit((T_COLD, T_COLD), (T_WARM, T_WARM), rng)
    assert set(child) == {T_COLD, T_WARM}
```

**Step 2: Run tests to verify failure**

Run: `pytest tests/test_multi_allele.py -q`
Expected: FAIL — `ImportError`.

**Step 3: Add the implementation**

Append to `src/evogame/genetics/gene_types.py`:

```python
class MultiAlleleGene(GeneType):
    def __init__(
        self,
        name: str,
        alleles: tuple[Allele, ...],
        dominance_order: tuple[Allele, ...],
    ):
        if set(dominance_order) != set(alleles):
            raise ValueError(
                f"dominance_order must cover exactly the alleles "
                f"in {name!r}; got {dominance_order} vs {alleles}"
            )
        self.name = name
        self.alleles = alleles
        self.dominance_order = dominance_order

    def express(self, genotype: tuple[Allele, Allele]) -> CategoricalPhenotype:
        for allele in self.dominance_order:
            if allele in genotype:
                return CategoricalPhenotype(allele.label or allele.symbol)
        # Unreachable given the constructor guard, but keeps the type checker happy.
        raise RuntimeError(f"No allele in genotype {genotype} matched dominance order")

    def random_genotype(self, rng) -> tuple[Allele, Allele]:
        return (rng.choice(self.alleles), rng.choice(self.alleles))

    def inherit(self, parent_a_genotype, parent_b_genotype, rng) -> tuple[Allele, Allele]:
        return (rng.choice(parent_a_genotype), rng.choice(parent_b_genotype))
```

**Step 4: Run tests to verify pass**

Run: `pytest tests/test_multi_allele.py -q`
Expected: 5 passed.

**Step 5: Commit**

```bash
git add src/evogame/genetics/gene_types.py tests/test_multi_allele.py
git commit -m "feat(genetics): add MultiAlleleGene"
```

---

## Task 7: `PolygenicGene`

**Files:**
- Modify: `src/evogame/genetics/gene_types.py`
- Create: `tests/test_polygenic.py`

The polygenic gene is the one that breaks the pattern. Its genotype is a *tuple of pairs* — one pair per locus — not a single pair. Its phenotype is numeric.

**Step 1: Write the failing tests**

```python
# tests/test_polygenic.py
import random
from evogame.genetics.alleles import Allele
from evogame.genetics.phenotype import NumericPhenotype
from evogame.genetics.gene_types import PolygenicGene

BIG = Allele("A", "large")
SMALL = Allele("a", "small")
VALUES = {BIG: 1.0, SMALL: 0.0}
GENE = PolygenicGene(
    name="body_size",
    alleles=(BIG, SMALL),
    loci=3,
    value_of=VALUES,
)


def test_all_big_alleles_max_value():
    genotype = ((BIG, BIG), (BIG, BIG), (BIG, BIG))
    assert GENE.express(genotype) == NumericPhenotype(6.0)


def test_all_small_alleles_min_value():
    genotype = ((SMALL, SMALL), (SMALL, SMALL), (SMALL, SMALL))
    assert GENE.express(genotype) == NumericPhenotype(0.0)


def test_mixed_genotype_sums_correctly():
    genotype = ((BIG, SMALL), (BIG, BIG), (SMALL, SMALL))
    # 1 + 0 + 1 + 1 + 0 + 0 = 3.0
    assert GENE.express(genotype) == NumericPhenotype(3.0)


def test_random_genotype_has_correct_structure():
    rng = random.Random(3)
    genotype = GENE.random_genotype(rng)
    assert len(genotype) == 3
    for pair in genotype:
        assert len(pair) == 2
        assert all(a in (BIG, SMALL) for a in pair)


def test_inherit_segregates_per_locus():
    rng = random.Random(3)
    parent_a = ((BIG, BIG), (BIG, BIG), (BIG, BIG))
    parent_b = ((SMALL, SMALL), (SMALL, SMALL), (SMALL, SMALL))
    child = GENE.inherit(parent_a, parent_b, rng)
    # Each locus must have exactly one BIG (from A) and one SMALL (from B).
    assert len(child) == 3
    for pair in child:
        assert set(pair) == {BIG, SMALL}
```

**Step 2: Run tests to verify failure**

Run: `pytest tests/test_polygenic.py -q`
Expected: FAIL — `ImportError`.

**Step 3: Add the implementation**

Append to `src/evogame/genetics/gene_types.py`:

```python
class PolygenicGene(GeneType):
    def __init__(
        self,
        name: str,
        alleles: tuple[Allele, ...],
        loci: int,
        value_of: dict[Allele, float],
    ):
        self.name = name
        self.alleles = alleles
        self.loci = loci
        self.value_of = value_of

    def express(self, genotype: tuple[tuple[Allele, Allele], ...]) -> NumericPhenotype:
        total = sum(self.value_of[a] for pair in genotype for a in pair)
        return NumericPhenotype(value=total)

    def random_genotype(self, rng) -> tuple[tuple[Allele, Allele], ...]:
        return tuple(
            (rng.choice(self.alleles), rng.choice(self.alleles))
            for _ in range(self.loci)
        )

    def inherit(self, parent_a_genotype, parent_b_genotype, rng):
        return tuple(
            (rng.choice(pa), rng.choice(pb))
            for pa, pb in zip(parent_a_genotype, parent_b_genotype, strict=True)
        )
```

**Step 4: Run tests to verify pass**

Run: `pytest tests/test_polygenic.py -q`
Expected: 5 passed.

**Step 5: Commit**

```bash
git add src/evogame/genetics/gene_types.py tests/test_polygenic.py
git commit -m "feat(genetics): add PolygenicGene"
```

---

## Task 8: `SpeciesSchema`

**Files:**
- Create: `src/evogame/genetics/schema.py`
- Create: `tests/test_schema.py`

**Step 1: Write the failing tests**

```python
# tests/test_schema.py
import pytest
from evogame.genetics.alleles import Allele
from evogame.genetics.gene_types import DominantRecessiveGene
from evogame.genetics.schema import SpeciesSchema


def test_schema_holds_name_and_genes():
    gene = DominantRecessiveGene(
        name="fin_length",
        dominant=Allele("L", "long"),
        recessive=Allele("s", "short"),
    )
    schema = SpeciesSchema(name="guppy", genes=(gene,))
    assert schema.name == "guppy"
    assert schema.genes == (gene,)


def test_schema_rejects_duplicate_gene_names():
    g1 = DominantRecessiveGene("dup", Allele("A"), Allele("a"))
    g2 = DominantRecessiveGene("dup", Allele("B"), Allele("b"))
    with pytest.raises(ValueError):
        SpeciesSchema(name="bad", genes=(g1, g2))
```

**Step 2: Run tests to verify failure**

Run: `pytest tests/test_schema.py -q`
Expected: FAIL — `ModuleNotFoundError`.

**Step 3: Write the implementation**

```python
# src/evogame/genetics/schema.py
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
```

**Step 4: Run tests to verify pass**

Run: `pytest tests/test_schema.py -q`
Expected: 2 passed.

**Step 5: Commit**

```bash
git add src/evogame/genetics/schema.py tests/test_schema.py
git commit -m "feat(genetics): add SpeciesSchema"
```

---

## Task 9: Guppy schema fixture

**Files:**
- Create: `src/evogame/genetics/species/__init__.py` (empty)
- Create: `src/evogame/genetics/species/guppy.py`
- Create: `tests/test_guppy_schema.py`

**Step 1: Write the failing tests**

```python
# tests/test_guppy_schema.py
import random
from evogame.genetics.species.guppy import GUPPY_SCHEMA
from evogame.genetics.gene_types import (
    DominantRecessiveGene,
    IncompleteDominanceGene,
    MultiAlleleGene,
    PolygenicGene,
)


def test_guppy_schema_has_four_genes():
    assert GUPPY_SCHEMA.name == "guppy"
    assert len(GUPPY_SCHEMA.genes) == 4


def test_guppy_schema_exercises_all_four_patterns():
    by_type = {type(g) for g in GUPPY_SCHEMA.genes}
    assert by_type == {
        DominantRecessiveGene,
        IncompleteDominanceGene,
        MultiAlleleGene,
        PolygenicGene,
    }


def test_every_gene_can_produce_a_random_genotype():
    rng = random.Random(0)
    for gene in GUPPY_SCHEMA.genes:
        genotype = gene.random_genotype(rng)
        # Should also be expressible without error.
        gene.express(genotype)
```

**Step 2: Run tests to verify failure**

Run: `pytest tests/test_guppy_schema.py -q`
Expected: FAIL — `ModuleNotFoundError`.

**Step 3: Write the implementation**

```python
# src/evogame/genetics/species/guppy.py
from evogame.genetics.alleles import Allele
from evogame.genetics.gene_types import (
    DominantRecessiveGene,
    IncompleteDominanceGene,
    MultiAlleleGene,
    PolygenicGene,
)
from evogame.genetics.schema import SpeciesSchema

# color: incomplete dominance — RR red / RW pink / WW white
_R = Allele("R", "red")
_W = Allele("W", "white")
_color = IncompleteDominanceGene(
    name="color", allele_a=_R, allele_b=_W, blend_label="pink"
)

# fin_length: simple dominant/recessive
_L = Allele("L", "long")
_s = Allele("s", "short")
_fin_length = DominantRecessiveGene(name="fin_length", dominant=_L, recessive=_s)

# temp_tolerance: multi-allele, dominance cold > mid > warm
_T_cold = Allele("Tc", "cold")
_T_mid = Allele("Tm", "mid")
_T_warm = Allele("Tw", "warm")
_temp_tolerance = MultiAlleleGene(
    name="temp_tolerance",
    alleles=(_T_cold, _T_mid, _T_warm),
    dominance_order=(_T_cold, _T_mid, _T_warm),
)

# body_size: polygenic, 3 loci, A=+1.0, a=+0.0
_BIG = Allele("A", "large")
_SMALL = Allele("a", "small")
_body_size = PolygenicGene(
    name="body_size",
    alleles=(_BIG, _SMALL),
    loci=3,
    value_of={_BIG: 1.0, _SMALL: 0.0},
)

GUPPY_SCHEMA = SpeciesSchema(
    name="guppy",
    genes=(_color, _fin_length, _temp_tolerance, _body_size),
)
```

**Step 4: Run tests to verify pass**

Run: `pytest tests/test_guppy_schema.py -q`
Expected: 3 passed.

**Step 5: Commit**

```bash
git add src/evogame/genetics/species/ tests/test_guppy_schema.py
git commit -m "feat(genetics): add guppy schema exercising all four patterns"
```

---

## Task 10: `MutationEvent` + `Creature` (no breeding yet)

**Files:**
- Create: `src/evogame/genetics/creature.py`
- Create: `tests/test_creature_basics.py`

This task gets `Creature` to the point of "I can construct one, get its phenotype, and build a random one from a schema." Breeding and mutation come in the next two tasks.

**Step 1: Write the failing tests**

```python
# tests/test_creature_basics.py
import random
from evogame.genetics.creature import Creature, MutationEvent
from evogame.genetics.alleles import Allele
from evogame.genetics.species.guppy import GUPPY_SCHEMA
from evogame.genetics.phenotype import CategoricalPhenotype, NumericPhenotype


def test_random_creature_has_entry_for_every_gene():
    rng = random.Random(0)
    c = Creature.random(GUPPY_SCHEMA, rng)
    assert set(c.genotype.keys()) == {g.name for g in GUPPY_SCHEMA.genes}


def test_phenotype_returns_one_entry_per_gene():
    rng = random.Random(0)
    c = Creature.random(GUPPY_SCHEMA, rng)
    pheno = c.phenotype
    assert set(pheno.keys()) == {g.name for g in GUPPY_SCHEMA.genes}
    assert isinstance(pheno["color"], CategoricalPhenotype)
    assert isinstance(pheno["body_size"], NumericPhenotype)


def test_mutation_event_records_old_and_new():
    a = Allele("R", "red")
    b = Allele("W", "white")
    ev = MutationEvent(gene_name="color", old=a, new=b)
    assert ev.gene_name == "color"
    assert ev.old == a
    assert ev.new == b


def test_creature_starts_with_empty_mutation_list():
    rng = random.Random(0)
    c = Creature.random(GUPPY_SCHEMA, rng)
    assert c.mutations == []
```

**Step 2: Run tests to verify failure**

Run: `pytest tests/test_creature_basics.py -q`
Expected: FAIL — `ModuleNotFoundError`.

**Step 3: Write the implementation**

```python
# src/evogame/genetics/creature.py
from dataclasses import dataclass, field
from typing import Any
from evogame.genetics.alleles import Allele
from evogame.genetics.schema import SpeciesSchema
from evogame.genetics.phenotype import CategoricalPhenotype, NumericPhenotype

Phenotype = CategoricalPhenotype | NumericPhenotype


@dataclass(frozen=True)
class MutationEvent:
    gene_name: str
    old: Allele
    new: Allele


class Creature:
    def __init__(
        self,
        schema: SpeciesSchema,
        genotype: dict[str, Any],
        mutations: list[MutationEvent] | None = None,
    ):
        self.schema = schema
        self.genotype = genotype
        self.mutations: list[MutationEvent] = mutations if mutations is not None else []

    @classmethod
    def random(cls, schema: SpeciesSchema, rng) -> "Creature":
        genotype = {g.name: g.random_genotype(rng) for g in schema.genes}
        return cls(schema, genotype)

    @property
    def phenotype(self) -> dict[str, Phenotype]:
        return {g.name: g.express(self.genotype[g.name]) for g in self.schema.genes}
```

**Step 4: Run tests to verify pass**

Run: `pytest tests/test_creature_basics.py -q`
Expected: 4 passed.

**Step 5: Commit**

```bash
git add src/evogame/genetics/creature.py tests/test_creature_basics.py
git commit -m "feat(genetics): add Creature class with random factory and phenotype"
```

---

## Task 11: `Creature.breed` (without mutation) + same-species guard

**Files:**
- Modify: `src/evogame/genetics/creature.py`
- Create: `tests/test_creature_inheritance.py`

**Step 1: Write the failing tests**

```python
# tests/test_creature_inheritance.py
import random
import pytest
from evogame.genetics.creature import Creature
from evogame.genetics.alleles import Allele
from evogame.genetics.gene_types import DominantRecessiveGene
from evogame.genetics.schema import SpeciesSchema
from evogame.genetics.species.guppy import GUPPY_SCHEMA


def test_breed_with_zero_mutation_rate_records_no_mutations():
    rng = random.Random(0)
    a = Creature.random(GUPPY_SCHEMA, rng)
    b = Creature.random(GUPPY_SCHEMA, rng)
    child = a.breed(b, rng, mutation_rate=0.0)
    assert child.mutations == []


def test_offspring_has_full_genotype():
    rng = random.Random(0)
    a = Creature.random(GUPPY_SCHEMA, rng)
    b = Creature.random(GUPPY_SCHEMA, rng)
    child = a.breed(b, rng, mutation_rate=0.0)
    assert set(child.genotype.keys()) == {g.name for g in GUPPY_SCHEMA.genes}


def _alleles_in_entry(entry):
    """Flatten a genotype entry (single pair OR tuple of pairs) into a list of alleles."""
    first = entry[0]
    if isinstance(first, tuple):  # polygenic
        return [a for pair in entry for a in pair]
    return list(entry)


def test_every_offspring_allele_traces_to_a_parent():
    """Mendelian invariant: with mutation_rate=0, every child allele came from a parent."""
    for seed in range(20):
        rng = random.Random(seed)
        a = Creature.random(GUPPY_SCHEMA, rng)
        b = Creature.random(GUPPY_SCHEMA, rng)
        child = a.breed(b, rng, mutation_rate=0.0)
        for gene_name, child_entry in child.genotype.items():
            parent_alleles = set(
                _alleles_in_entry(a.genotype[gene_name])
                + _alleles_in_entry(b.genotype[gene_name])
            )
            for allele in _alleles_in_entry(child_entry):
                assert allele in parent_alleles, (
                    f"Allele {allele} in child {gene_name!r} not in parents"
                )


def test_breed_with_different_schema_raises():
    rng = random.Random(0)
    other_schema = SpeciesSchema(
        name="other",
        genes=(DominantRecessiveGene("x", Allele("A"), Allele("a")),),
    )
    a = Creature.random(GUPPY_SCHEMA, rng)
    b = Creature.random(other_schema, rng)
    with pytest.raises(ValueError, match="same species"):
        a.breed(b, rng, mutation_rate=0.0)
```

**Step 2: Run tests to verify failure**

Run: `pytest tests/test_creature_inheritance.py -q`
Expected: FAIL — `AttributeError: 'Creature' object has no attribute 'breed'`.

**Step 3: Add `breed` to `Creature` (no mutation yet — that's Task 12)**

Append inside the `Creature` class in `src/evogame/genetics/creature.py`:

```python
    def breed(self, mate: "Creature", rng, mutation_rate: float = 0.001) -> "Creature":
        if self.schema is not mate.schema:
            raise ValueError(
                f"Cannot breed creatures of different species "
                f"({self.schema.name!r} vs {mate.schema.name!r}); must be same species"
            )
        offspring_genotype = {
            g.name: g.inherit(self.genotype[g.name], mate.genotype[g.name], rng)
            for g in self.schema.genes
        }
        # Mutation handling lands in the next task.
        return Creature(self.schema, offspring_genotype)
```

**Step 4: Run tests to verify pass**

Run: `pytest tests/test_creature_inheritance.py -q`
Expected: 4 passed.

**Step 5: Commit**

```bash
git add src/evogame/genetics/creature.py tests/test_creature_inheritance.py
git commit -m "feat(genetics): add Creature.breed with same-species guard"
```

---

## Task 12: Mutation in `Creature.breed`

**Files:**
- Modify: `src/evogame/genetics/creature.py`
- Create: `tests/test_mutation.py`

**Step 1: Write the failing tests**

```python
# tests/test_mutation.py
import random
from evogame.genetics.creature import Creature
from evogame.genetics.species.guppy import GUPPY_SCHEMA


def _alleles_in_entry(entry):
    first = entry[0]
    if isinstance(first, tuple):
        return [a for pair in entry for a in pair]
    return list(entry)


def test_mutation_rate_zero_records_no_mutations():
    rng = random.Random(0)
    a = Creature.random(GUPPY_SCHEMA, rng)
    b = Creature.random(GUPPY_SCHEMA, rng)
    child = a.breed(b, rng, mutation_rate=0.0)
    assert child.mutations == []


def test_mutation_rate_one_replaces_every_allele_with_a_different_one():
    rng = random.Random(0)
    a = Creature.random(GUPPY_SCHEMA, rng)
    b = Creature.random(GUPPY_SCHEMA, rng)
    child = a.breed(b, rng, mutation_rate=1.0)
    # Every recorded mutation must change the allele to a *different* one.
    assert len(child.mutations) > 0
    for ev in child.mutations:
        assert ev.old != ev.new


def test_mutation_records_match_offspring_genotype():
    """Every recorded MutationEvent's `new` allele should appear in the
    offspring's genotype for that gene."""
    rng = random.Random(1)
    a = Creature.random(GUPPY_SCHEMA, rng)
    b = Creature.random(GUPPY_SCHEMA, rng)
    child = a.breed(b, rng, mutation_rate=1.0)
    for ev in child.mutations:
        offspring_alleles = _alleles_in_entry(child.genotype[ev.gene_name])
        assert ev.new in offspring_alleles


def test_mutated_allele_comes_from_gene_pool():
    rng = random.Random(2)
    a = Creature.random(GUPPY_SCHEMA, rng)
    b = Creature.random(GUPPY_SCHEMA, rng)
    child = a.breed(b, rng, mutation_rate=1.0)
    pool_by_gene = {g.name: set(g.alleles) for g in GUPPY_SCHEMA.genes}
    for ev in child.mutations:
        assert ev.new in pool_by_gene[ev.gene_name]
```

**Step 2: Run tests to verify failure**

Run: `pytest tests/test_mutation.py -q`
Expected: 1 passes (rate=0 test), 3 fail — no mutations recorded yet.

**Step 3: Add mutation logic**

Add a private helper and update `breed` in `src/evogame/genetics/creature.py`:

```python
def _mutate_entry(gene, entry, rng, mutation_rate, gene_name, mutations):
    """Walk every allele in `entry`; with probability `mutation_rate`,
    replace it with a different allele drawn uniformly from the gene's pool.
    Records each replacement in `mutations`. Returns the (possibly new) entry."""
    pool = gene.alleles

    def maybe_mutate(allele):
        if rng.random() >= mutation_rate:
            return allele
        alternatives = [a for a in pool if a != allele]
        if not alternatives:  # gene has only one allele — can't mutate
            return allele
        new_allele = rng.choice(alternatives)
        mutations.append(MutationEvent(gene_name=gene_name, old=allele, new=new_allele))
        return new_allele

    first = entry[0]
    if isinstance(first, tuple):  # polygenic — entry is a tuple of pairs
        return tuple(tuple(maybe_mutate(a) for a in pair) for pair in entry)
    return tuple(maybe_mutate(a) for a in entry)
```

Then change the `breed` method to call it:

```python
    def breed(self, mate: "Creature", rng, mutation_rate: float = 0.001) -> "Creature":
        if self.schema is not mate.schema:
            raise ValueError(
                f"Cannot breed creatures of different species "
                f"({self.schema.name!r} vs {mate.schema.name!r}); must be same species"
            )
        mutations: list[MutationEvent] = []
        offspring_genotype = {}
        for gene in self.schema.genes:
            inherited = gene.inherit(
                self.genotype[gene.name], mate.genotype[gene.name], rng
            )
            offspring_genotype[gene.name] = _mutate_entry(
                gene, inherited, rng, mutation_rate, gene.name, mutations
            )
        return Creature(self.schema, offspring_genotype, mutations=mutations)
```

(`_mutate_entry` is module-level, not a method — no reason for it to live on `Creature`.)

**Step 4: Run tests to verify pass**

Run: `pytest -q`
Expected: All tests pass (existing + new mutation tests).

**Step 5: Commit**

```bash
git add src/evogame/genetics/creature.py tests/test_mutation.py
git commit -m "feat(genetics): add per-allele mutation in Creature.breed"
```

---

## Task 13: Demo script

**Files:**
- Create: `scripts/__init__.py` (empty — keeps `scripts/` from being treated as a stray dir)
- Create: `scripts/breed_demo.py`
- Create: `tests/test_breed_demo.py`

**Step 1: Write the failing test**

We test the demo script's library-style helpers, not its `print` output. The `if __name__ == "__main__":` block is exercised by running the script manually in Step 6.

```python
# tests/test_breed_demo.py
import random
from scripts.breed_demo import format_creature, run_demo


def test_format_creature_includes_all_gene_names():
    rng = random.Random(0)
    out = format_creature("Parent A", _make_creature(rng))
    assert "Parent A" in out
    for name in ("color", "fin_length", "temp_tolerance", "body_size"):
        assert name in out


def test_run_demo_returns_three_creatures_and_prints():
    rng = random.Random(42)
    parents_and_child = run_demo(rng=rng, mutation_rate=0.5)
    assert len(parents_and_child) == 3  # parent_a, parent_b, child
    a, b, child = parents_and_child
    # Same schema across all three.
    assert a.schema is b.schema is child.schema


def _make_creature(rng):
    from evogame.genetics.creature import Creature
    from evogame.genetics.species.guppy import GUPPY_SCHEMA
    return Creature.random(GUPPY_SCHEMA, rng)
```

`scripts/` needs to be importable as a package so pytest can import `scripts.breed_demo`. We add `scripts/__init__.py` for that.

**Step 2: Run tests to verify failure**

Run: `pytest tests/test_breed_demo.py -q`
Expected: FAIL — `ModuleNotFoundError: No module named 'scripts'`.

**Step 3: Write the demo script**

```python
# scripts/breed_demo.py
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
        lines.append(f"  {gene.name}: {_format_entry(entry)} → {value}")
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
            print(f"  {ev.gene_name}: {ev.old.symbol} → {ev.new.symbol}")
    return parent_a, parent_b, child


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--mutation-rate", type=float, default=0.05)
    args = parser.parse_args()
    run_demo(random.Random(args.seed), args.mutation_rate)


if __name__ == "__main__":
    main()
```

**Step 4: Run tests to verify pass**

Run: `pytest -q`
Expected: All tests pass.

**Step 5: Run the demo manually and visually verify**

Run: `python scripts/breed_demo.py`
Expected: Prints three guppy blocks (Parent A, Parent B, Offspring) with genotype symbols and phenotype values, plus possibly a mutation list. Output should be reproducible — running twice with the same default seed gives identical output.

Try once with mutation rate 1.0 to sanity-check mutation reporting:
Run: `python scripts/breed_demo.py --mutation-rate 1.0`
Expected: A long mutation list (every allele changed).

**Step 6: Commit**

```bash
git add scripts/ tests/test_breed_demo.py
git commit -m "feat(genetics): add breed demo script"
```

---

## Task 14: Public API + final verification

**Files:**
- Modify: `src/evogame/genetics/__init__.py`

This task makes the genetics package present a clean public surface (so future code can `from evogame.genetics import Creature, GUPPY_SCHEMA` instead of reaching into submodules) and runs the full suite one last time.

**Step 1: Edit `src/evogame/genetics/__init__.py`**

```python
from evogame.genetics.alleles import Allele
from evogame.genetics.phenotype import CategoricalPhenotype, NumericPhenotype
from evogame.genetics.gene_types import (
    GeneType,
    DominantRecessiveGene,
    IncompleteDominanceGene,
    MultiAlleleGene,
    PolygenicGene,
)
from evogame.genetics.schema import SpeciesSchema
from evogame.genetics.creature import Creature, MutationEvent
from evogame.genetics.species.guppy import GUPPY_SCHEMA

__all__ = [
    "Allele",
    "CategoricalPhenotype",
    "NumericPhenotype",
    "GeneType",
    "DominantRecessiveGene",
    "IncompleteDominanceGene",
    "MultiAlleleGene",
    "PolygenicGene",
    "SpeciesSchema",
    "Creature",
    "MutationEvent",
    "GUPPY_SCHEMA",
]
```

**Step 2: Add a test that the public API exports work**

Append to `tests/test_smoke.py`:

```python
def test_public_api_exports():
    from evogame.genetics import (
        Allele,
        Creature,
        GUPPY_SCHEMA,
        DominantRecessiveGene,
        IncompleteDominanceGene,
        MultiAlleleGene,
        PolygenicGene,
        MutationEvent,
        SpeciesSchema,
        CategoricalPhenotype,
        NumericPhenotype,
        GeneType,
    )
    assert GUPPY_SCHEMA.name == "guppy"
```

**Step 3: Run the full suite**

Run: `pytest -q`
Expected: All tests pass — should be on the order of 35+ tests across the suite.

**Step 4: Run the demo one more time**

Run: `python scripts/breed_demo.py`
Expected: Reproducible output, no errors.

**Step 5: Commit**

```bash
git add src/evogame/genetics/__init__.py tests/test_smoke.py
git commit -m "feat(genetics): export public API from evogame.genetics"
```

---

## Done criteria

After all 14 tasks:

- `pytest -q` is green with ~35+ tests across alleles, phenotype, all four gene types, schema, guppy fixture, creature basics, inheritance, mutation, and the demo script.
- `python scripts/breed_demo.py` prints two random guppy parents and their offspring, with reproducible output for a given `--seed`.
- The genetics engine has no Pygame dependency and no UI code.
- Git history shows one commit per task (14 commits on the feature branch + the design-doc commit).

## What's *not* done — for the next plan

- Population-level concerns (allele frequency tracking, generations, fitness scoring, selection pressures).
- The other three species (beetle, bird, snail) — adding them is now a matter of writing one `<species>.py` schema file each.
- Pygame rendering, UI, habitat sliders, crops, field journal.
- Novel-allele mutation.
