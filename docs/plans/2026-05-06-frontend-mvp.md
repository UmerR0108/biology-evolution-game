# Frontend MVP Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Build a single-window Pygame frontend showing guppies evolving under a toggleable predator pressure, with a live matplotlib allele-frequency chart side-by-side.

**Architecture:** Pure-Python simulation layer (`evogame.sim`) drives a Pygame UI layer (`evogame.ui`). Render loop runs at ~60 FPS; a generation timer advances the sim every `1/speed` seconds. Chart panel uses matplotlib's Agg backend, blits the rendered figure into the pygame window, and only redraws when a new generation is recorded.

**Tech Stack:** Python 3.11+, pygame, matplotlib (Agg backend), pytest. Reuses existing `evogame.genetics` engine (`Creature`, `GUPPY_SCHEMA`) without modification.

**Reference:** [Frontend MVP Design](2026-05-06-frontend-mvp-design.md)

---

## Conventions for every task

- TDD: write the failing test first, run it red, implement, run green, then commit.
- One task = one logical commit. Use Conventional Commits (`feat:`, `test:`, `chore:`).
- All `pytest` runs use `python -m pytest` from repo root (`D:/game`).
- All new code goes under `src/evogame/sim/` or `src/evogame/ui/`. Genetics code is **read-only** for this plan.
- Tests live under `tests/` mirroring the module path (e.g. `tests/sim/test_population.py`).
- Use `random.Random(seed)` for any test that exercises randomness — never the global rng.
- File paths in this plan are absolute (`D:/game/...`) but you can use relative paths in commands when at repo root.

---

## Phase 1 — Simulation layer (no pygame)

### Task 1: Add dependencies and scaffold packages

**Files:**
- Modify: `D:/game/pyproject.toml` (add pygame and matplotlib to `dependencies`)
- Create: `D:/game/src/evogame/sim/__init__.py` (empty)
- Create: `D:/game/src/evogame/ui/__init__.py` (empty)
- Create: `D:/game/tests/sim/__init__.py` (empty)
- Create: `D:/game/tests/ui/__init__.py` (empty)

**Step 1: Update `pyproject.toml`**

Replace the `dependencies = []` line:

```toml
dependencies = [
    "pygame>=2.5",
    "matplotlib>=3.8",
]
```

**Step 2: Create empty package files**

Create the four `__init__.py` files above (zero bytes each).

**Step 3: Reinstall in editable mode**

Run: `python -m pip install -e ".[dev]"`
Expected: installs pygame + matplotlib successfully.

**Step 4: Verify imports**

Run: `python -c "import pygame, matplotlib; print(pygame.version.ver, matplotlib.__version__)"`
Expected: prints two version strings, no error.

**Step 5: Run existing tests to confirm nothing regressed**

Run: `python -m pytest`
Expected: all existing tests pass.

**Step 6: Commit**

```bash
git add pyproject.toml src/evogame/sim src/evogame/ui tests/sim tests/ui
git commit -m "chore(deps): add pygame + matplotlib, scaffold sim/ui packages"
```

---

### Task 2: `PredatorPressure` — fitness function

**Why this comes first:** It's pure logic, no dependencies on the rest of the sim. We can pin its behavior with simple tests.

**Files:**
- Create: `D:/game/src/evogame/sim/pressure.py`
- Create: `D:/game/tests/sim/test_pressure.py`

**Design notes:**
- Reads `creature.phenotype["color"].category`, which is `"red"`, `"pink"`, or `"white"` (per `IncompleteDominanceGene` on `GUPPY_SCHEMA`).
- Predator on: red 0.2, pink 0.5, white 0.9 (red is highly visible to predators).
- Predator off: red 0.9, pink 0.7, white 0.5 (white loses mate appeal — keeps the toggle interesting).
- Unknown color category → 0.5 (neutral; never crashes the sim if a mutation introduces something unexpected).

**Step 1: Write the failing tests**

`D:/game/tests/sim/test_pressure.py`:

```python
import random

import pytest

from evogame.genetics import GUPPY_SCHEMA, Creature
from evogame.sim.pressure import PredatorPressure


def _creature_with_color(color_genotype):
    """Build a guppy with a specific color genotype, defaulting other genes."""
    rng = random.Random(0)
    base = Creature.random(GUPPY_SCHEMA, rng)
    base.genotype["color"] = color_genotype
    return base


def _color_alleles():
    color_gene = next(g for g in GUPPY_SCHEMA.genes if g.name == "color")
    return color_gene.allele_a, color_gene.allele_b  # R, W


def test_red_guppy_lower_fitness_with_predator():
    R, _W = _color_alleles()
    red = _creature_with_color((R, R))
    on = PredatorPressure(predator_on=True).fitness(red)
    off = PredatorPressure(predator_on=False).fitness(red)
    assert on < off


def test_white_guppy_higher_fitness_with_predator():
    _R, W = _color_alleles()
    white = _creature_with_color((W, W))
    on = PredatorPressure(predator_on=True).fitness(white)
    off = PredatorPressure(predator_on=False).fitness(white)
    assert on > off


def test_pink_guppy_intermediate_with_predator():
    R, W = _color_alleles()
    pink = _creature_with_color((R, W))
    p = PredatorPressure(predator_on=True)
    red = _creature_with_color((R, R))
    white = _creature_with_color((W, W))
    assert p.fitness(red) < p.fitness(pink) < p.fitness(white)


def test_fitness_returns_float_in_unit_interval():
    R, W = _color_alleles()
    for genotype in [(R, R), (R, W), (W, W)]:
        c = _creature_with_color(genotype)
        for predator in (True, False):
            f = PredatorPressure(predator_on=predator).fitness(c)
            assert 0.0 <= f <= 1.0
```

**Step 2: Run test, verify it fails**

Run: `python -m pytest tests/sim/test_pressure.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'evogame.sim.pressure'`.

**Step 3: Implement `PredatorPressure`**

`D:/game/src/evogame/sim/pressure.py`:

```python
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
```

**Step 4: Run tests, verify pass**

Run: `python -m pytest tests/sim/test_pressure.py -v`
Expected: 4 passed.

**Step 5: Commit**

```bash
git add src/evogame/sim/pressure.py tests/sim/test_pressure.py
git commit -m "feat(sim): add PredatorPressure with red/pink/white fitness curves"
```

---

### Task 3: `Population.step_generation` — fitness-weighted breeding

**Files:**
- Create: `D:/game/src/evogame/sim/population.py`
- Create: `D:/game/tests/sim/test_population.py`

**Design notes:**
- `Population` wraps `list[Creature]` plus a fixed `carrying_capacity` and an injected `rng`.
- `step_generation(pressure)` returns a **new** `Population` (immutable-style — easier to reason about). The old one is discarded by the caller.
- Algorithm:
  1. If `len(self) < 2`: extinction → return empty `Population`.
  2. Compute fitness for each creature.
  3. If all fitnesses are 0: extinction → return empty `Population`.
  4. Sample `min(carrying_capacity, len(self) * 2)` parents with `random.choices(weights=fitnesses)`.
  5. Pair parents `(p[0],p[1]), (p[2],p[3])...`; each pair produces one offspring via `Creature.breed`.
- Carrying capacity caps the *next* generation size, not parent sampling.

**Step 1: Write the failing tests**

`D:/game/tests/sim/test_population.py`:

```python
import random

import pytest

from evogame.genetics import GUPPY_SCHEMA, Creature
from evogame.sim.population import Population
from evogame.sim.pressure import PredatorPressure


def _make_population(n: int, seed: int = 0, capacity: int = 60) -> Population:
    rng = random.Random(seed)
    creatures = [Creature.random(GUPPY_SCHEMA, rng) for _ in range(n)]
    return Population(creatures=creatures, carrying_capacity=capacity, rng=rng)


def test_empty_population_stays_empty():
    pop = _make_population(0)
    next_pop = pop.step_generation(PredatorPressure(predator_on=False))
    assert len(next_pop) == 0


def test_single_creature_cannot_breed():
    pop = _make_population(1)
    next_pop = pop.step_generation(PredatorPressure(predator_on=False))
    assert len(next_pop) == 0


def test_normal_population_produces_offspring():
    pop = _make_population(20)
    next_pop = pop.step_generation(PredatorPressure(predator_on=False))
    assert len(next_pop) > 0


def test_carrying_capacity_caps_size():
    pop = _make_population(50, capacity=30)
    next_pop = pop.step_generation(PredatorPressure(predator_on=False))
    assert len(next_pop) <= 30


def test_offspring_share_schema():
    pop = _make_population(10)
    next_pop = pop.step_generation(PredatorPressure(predator_on=False))
    assert all(c.schema is GUPPY_SCHEMA for c in next_pop.creatures)


def test_predator_pressure_skews_population_toward_white():
    """Under predator pressure for many generations, white alleles should dominate."""
    rng = random.Random(42)
    creatures = [Creature.random(GUPPY_SCHEMA, rng) for _ in range(40)]
    pop = Population(creatures=creatures, carrying_capacity=40, rng=rng)
    pressure = PredatorPressure(predator_on=True)
    for _ in range(20):
        pop = pop.step_generation(pressure)
        if len(pop) == 0:
            pytest.skip("Population went extinct in this seed; rare but possible")
    colors = [c.phenotype["color"].category for c in pop.creatures]
    # With predator on, "red" should be rare after 20 generations
    assert colors.count("red") < colors.count("white")
```

**Step 2: Run test, verify it fails**

Run: `python -m pytest tests/sim/test_population.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'evogame.sim.population'`.

**Step 3: Implement `Population`**

`D:/game/src/evogame/sim/population.py`:

```python
from dataclasses import dataclass, field
from typing import Protocol

from evogame.genetics import Creature


class Pressure(Protocol):
    def fitness(self, creature: Creature) -> float: ...


@dataclass
class Population:
    creatures: list[Creature]
    carrying_capacity: int
    rng: object  # random.Random; keeping loose for typing simplicity
    mutation_rate: float = 0.001

    def __len__(self) -> int:
        return len(self.creatures)

    def step_generation(self, pressure: Pressure) -> "Population":
        if len(self.creatures) < 2:
            return Population([], self.carrying_capacity, self.rng, self.mutation_rate)

        fitnesses = [pressure.fitness(c) for c in self.creatures]
        if sum(fitnesses) == 0:
            return Population([], self.carrying_capacity, self.rng, self.mutation_rate)

        target_size = min(self.carrying_capacity, len(self.creatures) * 2)
        parents = self.rng.choices(self.creatures, weights=fitnesses, k=target_size * 2)
        offspring = [
            parents[i].breed(parents[i + 1], self.rng, self.mutation_rate)
            for i in range(0, target_size * 2, 2)
        ]
        return Population(offspring, self.carrying_capacity, self.rng, self.mutation_rate)
```

**Step 4: Run tests, verify pass**

Run: `python -m pytest tests/sim/test_population.py -v`
Expected: 6 passed.

**Step 5: Commit**

```bash
git add src/evogame/sim/population.py tests/sim/test_population.py
git commit -m "feat(sim): add Population with fitness-weighted generation step"
```

---

### Task 4: `Population.allele_frequencies`

**Files:**
- Modify: `D:/game/src/evogame/sim/population.py` (add method)
- Modify: `D:/game/tests/sim/test_population.py` (add tests)

**Design notes:**
- Returns `dict[str, dict[str, float]]`: `{gene_name: {allele_symbol: frequency}}`.
- Frequencies sum to 1.0 per gene.
- Handle both flat genotype shape (`(allele, allele)`) and polygenic shape (`((a, a), (a, a), ...)`) — same logic as `_mutate_entry` in `creature.py`.
- Empty population returns `{}`.

**Step 1: Add failing tests**

Append to `D:/game/tests/sim/test_population.py`:

```python
import math


def test_allele_frequencies_empty_population():
    pop = _make_population(0)
    assert pop.allele_frequencies() == {}


def test_allele_frequencies_sum_to_one_per_gene():
    pop = _make_population(20)
    freqs = pop.allele_frequencies()
    for gene_name, gene_freqs in freqs.items():
        total = sum(gene_freqs.values())
        assert math.isclose(total, 1.0, abs_tol=1e-9), f"{gene_name} sums to {total}"


def test_allele_frequencies_includes_all_genes():
    pop = _make_population(20)
    freqs = pop.allele_frequencies()
    expected_genes = {g.name for g in GUPPY_SCHEMA.genes}
    assert set(freqs.keys()) == expected_genes


def test_allele_frequencies_homozygous_population():
    """A population where every creature is homozygous RR has color frequency R=1.0, W=0.0."""
    rng = random.Random(0)
    creatures = []
    color_gene = next(g for g in GUPPY_SCHEMA.genes if g.name == "color")
    R = color_gene.allele_a  # R
    for _ in range(10):
        c = Creature.random(GUPPY_SCHEMA, rng)
        c.genotype["color"] = (R, R)
        creatures.append(c)
    pop = Population(creatures=creatures, carrying_capacity=20, rng=rng)
    color_freqs = pop.allele_frequencies()["color"]
    assert color_freqs[R.symbol] == 1.0
```

**Step 2: Run, verify failure**

Run: `python -m pytest tests/sim/test_population.py -v -k allele_freq`
Expected: 4 fails — `AttributeError: 'Population' object has no attribute 'allele_frequencies'`.

**Step 3: Implement**

Add method to `Population` in `D:/game/src/evogame/sim/population.py`:

```python
    def allele_frequencies(self) -> dict[str, dict[str, float]]:
        if not self.creatures:
            return {}
        schema = self.creatures[0].schema
        result: dict[str, dict[str, float]] = {}
        for gene in schema.genes:
            counts: dict[str, int] = {}
            for creature in self.creatures:
                entry = creature.genotype[gene.name]
                _accumulate_alleles(entry, counts)
            total = sum(counts.values())
            result[gene.name] = {sym: c / total for sym, c in counts.items()}
        return result
```

Add helper at module level (above `Population`):

```python
def _accumulate_alleles(entry, counts: dict[str, int]) -> None:
    """Walk a genotype entry (flat tuple or nested tuple-of-pairs) and tally allele symbols."""
    first = entry[0]
    if isinstance(first, tuple):  # polygenic
        for pair in entry:
            for allele in pair:
                counts[allele.symbol] = counts.get(allele.symbol, 0) + 1
    else:
        for allele in entry:
            counts[allele.symbol] = counts.get(allele.symbol, 0) + 1
```

**Step 4: Run tests, verify pass**

Run: `python -m pytest tests/sim/test_population.py -v`
Expected: 10 passed.

**Step 5: Commit**

```bash
git add src/evogame/sim/population.py tests/sim/test_population.py
git commit -m "feat(sim): add Population.allele_frequencies for flat and polygenic genes"
```

---

### Task 5: `GenerationLog`

**Files:**
- Create: `D:/game/src/evogame/sim/recorder.py`
- Create: `D:/game/tests/sim/test_recorder.py`

**Design notes:**
- A `GenerationLog` is a list of `GenerationRecord` (frozen dataclass): `gen, allele_freqs, predator_on, population_size`.
- `record(...)` appends. `frequencies_over_time(gene_name)` returns `dict[allele_symbol, list[float]]` for chart plotting.
- Missing alleles in earlier generations show as 0.0 (so the chart line starts at 0 when a mutation introduces a new allele).

**Step 1: Write failing tests**

`D:/game/tests/sim/test_recorder.py`:

```python
from evogame.sim.recorder import GenerationLog, GenerationRecord


def test_log_starts_empty():
    log = GenerationLog()
    assert len(log) == 0


def test_record_appends():
    log = GenerationLog()
    log.record(gen=0, allele_freqs={"color": {"R": 0.5, "W": 0.5}}, predator_on=False, population_size=20)
    assert len(log) == 1
    assert log.records[0].gen == 0
    assert log.records[0].population_size == 20


def test_frequencies_over_time_basic():
    log = GenerationLog()
    log.record(0, {"color": {"R": 0.5, "W": 0.5}}, False, 20)
    log.record(1, {"color": {"R": 0.7, "W": 0.3}}, True, 18)
    series = log.frequencies_over_time("color")
    assert series == {"R": [0.5, 0.7], "W": [0.5, 0.3]}


def test_frequencies_over_time_handles_new_allele():
    """An allele that appears in gen 1 but not gen 0 should show 0.0 for gen 0."""
    log = GenerationLog()
    log.record(0, {"color": {"R": 0.5, "W": 0.5}}, False, 20)
    log.record(1, {"color": {"R": 0.4, "W": 0.4, "M": 0.2}}, False, 20)
    series = log.frequencies_over_time("color")
    assert series == {"R": [0.5, 0.4], "W": [0.5, 0.4], "M": [0.0, 0.2]}


def test_frequencies_over_time_missing_gene():
    log = GenerationLog()
    log.record(0, {"color": {"R": 1.0}}, False, 20)
    assert log.frequencies_over_time("nonexistent") == {}
```

**Step 2: Run, verify failure**

Run: `python -m pytest tests/sim/test_recorder.py -v`
Expected: FAIL — module not found.

**Step 3: Implement**

`D:/game/src/evogame/sim/recorder.py`:

```python
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
```

**Step 4: Run, verify pass**

Run: `python -m pytest tests/sim/test_recorder.py -v`
Expected: 5 passed.

**Step 5: Commit**

```bash
git add src/evogame/sim/recorder.py tests/sim/test_recorder.py
git commit -m "feat(sim): add GenerationLog with per-allele time-series accessor"
```

---

### Task 6: `SimController` — owns population, pressure, log

**Files:**
- Create: `D:/game/src/evogame/sim/controller.py`
- Create: `D:/game/tests/sim/test_controller.py`

**Design notes:**
- The controller is the single object the UI talks to. Holds: `population`, `pressure`, `log`, `generation` counter, `extinct` flag.
- `tick()` advances one generation, records, increments counter. No-op if `extinct`.
- `reset()` rebuilds a fresh starting population and clears the log.
- `set_predator(on: bool)` swaps the pressure (the toggle).

**Step 1: Write failing tests**

`D:/game/tests/sim/test_controller.py`:

```python
import random

from evogame.genetics import GUPPY_SCHEMA
from evogame.sim.controller import SimController


def test_controller_starts_with_initial_population():
    sim = SimController(schema=GUPPY_SCHEMA, initial_size=10, carrying_capacity=20, rng=random.Random(0))
    assert len(sim.population) == 10
    assert sim.generation == 0
    assert not sim.extinct
    assert len(sim.log) == 1  # initial state recorded


def test_tick_advances_generation():
    sim = SimController(schema=GUPPY_SCHEMA, initial_size=20, carrying_capacity=40, rng=random.Random(0))
    sim.tick()
    assert sim.generation == 1
    assert len(sim.log) == 2


def test_tick_records_predator_state():
    sim = SimController(schema=GUPPY_SCHEMA, initial_size=20, carrying_capacity=40, rng=random.Random(0))
    sim.set_predator(True)
    sim.tick()
    assert sim.log.records[-1].predator_on is True


def test_extinction_freezes_simulation():
    sim = SimController(schema=GUPPY_SCHEMA, initial_size=1, carrying_capacity=10, rng=random.Random(0))
    sim.tick()
    assert sim.extinct
    gen_before = sim.generation
    sim.tick()
    assert sim.generation == gen_before  # frozen


def test_reset_restores_initial_state():
    sim = SimController(schema=GUPPY_SCHEMA, initial_size=10, carrying_capacity=20, rng=random.Random(0))
    sim.tick()
    sim.tick()
    sim.reset()
    assert sim.generation == 0
    assert len(sim.population) == 10
    assert not sim.extinct
    assert len(sim.log) == 1
```

**Step 2: Run, verify failure**

Run: `python -m pytest tests/sim/test_controller.py -v`
Expected: FAIL — module not found.

**Step 3: Implement**

`D:/game/src/evogame/sim/controller.py`:

```python
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
        rng,
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
        self.population = self._fresh_population()
        self.log = GenerationLog()
        self.generation = 0
        self.extinct = False
        self._record()
```

**Step 4: Run, verify pass**

Run: `python -m pytest tests/sim/test_controller.py -v`
Expected: 5 passed.

**Step 5: Commit**

```bash
git add src/evogame/sim/controller.py tests/sim/test_controller.py
git commit -m "feat(sim): add SimController owning population, pressure, log"
```

---

## Phase 2 — UI layer

### Task 7: Pygame headless test fixture

**Files:**
- Create: `D:/game/tests/conftest.py`

**Why:** All UI tests must run without a display server. Setting `SDL_VIDEODRIVER=dummy` before pygame imports makes pygame work headlessly. We do this once via a session fixture.

**Step 1: Create the fixture**

`D:/game/tests/conftest.py`:

```python
import os

import pytest


@pytest.fixture(scope="session", autouse=True)
def _headless_pygame():
    """Force pygame's SDL backend into dummy mode so tests don't need a display."""
    os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
    os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
    yield


@pytest.fixture
def pygame_surface():
    """Provide a 200x200 pygame Surface for UI rendering tests."""
    import pygame

    pygame.init()
    surface = pygame.Surface((200, 200))
    yield surface
    pygame.quit()
```

**Step 2: Verify pygame can init in dummy mode**

Run:
```bash
python -c "import os; os.environ['SDL_VIDEODRIVER']='dummy'; import pygame; pygame.init(); s = pygame.Surface((100,100)); print('OK', s.get_size())"
```
Expected: `OK (100, 100)`.

**Step 3: Run all existing tests to make sure the fixture doesn't break anything**

Run: `python -m pytest`
Expected: all existing tests still pass.

**Step 4: Commit**

```bash
git add tests/conftest.py
git commit -m "test: add headless pygame fixture for UI tests"
```

---

### Task 8: `WorldPanel` — draws creatures as colored circles

**Files:**
- Create: `D:/game/src/evogame/ui/world_panel.py`
- Create: `D:/game/tests/ui/test_world_panel.py`

**Design notes:**
- Constructor: `WorldPanel(rect: pygame.Rect)`. Stores the rect.
- `draw(surface, creatures)`: paints a pond-blue background, then a circle per creature.
- Color mapping: `{"red": (220,40,40), "pink": (240,140,160), "white": (240,240,240)}` with grey fallback `(128,128,128)`.
- Radius: `4 + body_size_phenotype.value * 0.5` (body_size phenotype is `NumericPhenotype` with values 0–6 from 3 polygenic loci × 2 alleles × 1.0).
- Position: deterministic from creature index — grid layout inside the rect, padded.

**Step 1: Write failing tests**

`D:/game/tests/ui/test_world_panel.py`:

```python
import random

import pygame
import pytest

from evogame.genetics import GUPPY_SCHEMA, Creature
from evogame.ui.world_panel import WorldPanel


def test_world_panel_draws_without_error(pygame_surface):
    rng = random.Random(0)
    creatures = [Creature.random(GUPPY_SCHEMA, rng) for _ in range(10)]
    panel = WorldPanel(pygame.Rect(0, 0, 200, 200))
    panel.draw(pygame_surface, creatures)


def test_world_panel_handles_empty_creatures(pygame_surface):
    panel = WorldPanel(pygame.Rect(0, 0, 200, 200))
    panel.draw(pygame_surface, [])  # must not raise


def test_world_panel_paints_background(pygame_surface):
    """After drawing with no creatures, the panel area should be the pond color (not black)."""
    panel = WorldPanel(pygame.Rect(0, 0, 200, 200))
    panel.draw(pygame_surface, [])
    pixel = pygame_surface.get_at((100, 100))
    assert pixel != (0, 0, 0, 255), "panel background should not be black"
```

**Step 2: Run, verify failure**

Run: `python -m pytest tests/ui/test_world_panel.py -v`
Expected: FAIL — module not found.

**Step 3: Implement**

`D:/game/src/evogame/ui/world_panel.py`:

```python
import pygame

from evogame.genetics import Creature

_POND = (60, 110, 150)
_COLOR_MAP = {
    "red": (220, 40, 40),
    "pink": (240, 140, 160),
    "white": (240, 240, 240),
}
_FALLBACK = (128, 128, 128)


class WorldPanel:
    def __init__(self, rect: pygame.Rect):
        self.rect = rect

    def draw(self, surface: pygame.Surface, creatures: list[Creature]) -> None:
        pygame.draw.rect(surface, _POND, self.rect)
        if not creatures:
            return
        cols = max(1, int(len(creatures) ** 0.5) + 1)
        cell_w = max(1, (self.rect.width - 20) // cols)
        cell_h = cell_w
        for i, creature in enumerate(creatures):
            col = i % cols
            row = i // cols
            cx = self.rect.left + 10 + col * cell_w + cell_w // 2
            cy = self.rect.top + 10 + row * cell_h + cell_h // 2
            if cy > self.rect.bottom - 10:
                break
            color_cat = creature.phenotype["color"].category
            color = _COLOR_MAP.get(color_cat, _FALLBACK)
            body_size = creature.phenotype["body_size"].value
            radius = max(3, int(4 + body_size * 0.5))
            pygame.draw.circle(surface, color, (cx, cy), radius)
```

**Step 4: Run, verify pass**

Run: `python -m pytest tests/ui/test_world_panel.py -v`
Expected: 3 passed.

**Step 5: Commit**

```bash
git add src/evogame/ui/world_panel.py tests/ui/test_world_panel.py
git commit -m "feat(ui): add WorldPanel rendering creatures as colored circles"
```

---

### Task 9: `ChartPanel` — matplotlib → pygame surface

**Files:**
- Create: `D:/game/src/evogame/ui/chart_panel.py`
- Create: `D:/game/tests/ui/test_chart_panel.py`

**Design notes:**
- Uses matplotlib's Agg backend explicitly so it never tries to open a window.
- Holds a `Figure` + `FigureCanvasAgg`, plus a cached pygame Surface.
- `update(log)`: re-plots the `color` gene's allele frequencies over time. Called by App when a generation ticks.
- `draw(surface)`: blits the cached surface to `self.rect`'s top-left.
- If the log has 0 records, draws a placeholder "No data yet" surface (still a valid Surface).

**Step 1: Write failing tests**

`D:/game/tests/ui/test_chart_panel.py`:

```python
import pygame
import pytest

from evogame.sim.recorder import GenerationLog
from evogame.ui.chart_panel import ChartPanel


def test_chart_panel_handles_empty_log(pygame_surface):
    panel = ChartPanel(pygame.Rect(0, 0, 200, 200))
    panel.update(GenerationLog())
    panel.draw(pygame_surface)  # must not raise


def test_chart_panel_renders_after_records(pygame_surface):
    log = GenerationLog()
    log.record(0, {"color": {"R": 0.5, "W": 0.5}}, False, 20)
    log.record(1, {"color": {"R": 0.7, "W": 0.3}}, True, 18)
    panel = ChartPanel(pygame.Rect(0, 0, 200, 200))
    panel.update(log)
    panel.draw(pygame_surface)
    # any non-background pixel proves something was drawn
    found_non_background = any(
        pygame_surface.get_at((x, y))[:3] != (0, 0, 0)
        for x in range(0, 200, 20) for y in range(0, 200, 20)
    )
    assert found_non_background


def test_chart_panel_returns_surface_on_draw(pygame_surface):
    log = GenerationLog()
    log.record(0, {"color": {"R": 1.0}}, False, 10)
    panel = ChartPanel(pygame.Rect(0, 0, 200, 200))
    panel.update(log)
    panel.draw(pygame_surface)
    # smoke: the panel rect area should differ from a freshly cleared surface
    other = pygame.Surface((200, 200))
    assert pygame_surface.get_at((50, 50)) != other.get_at((50, 50))
```

**Step 2: Run, verify failure**

Run: `python -m pytest tests/ui/test_chart_panel.py -v`
Expected: FAIL — module not found.

**Step 3: Implement**

`D:/game/src/evogame/ui/chart_panel.py`:

```python
import matplotlib

matplotlib.use("Agg")

import pygame
from matplotlib.backends.backend_agg import FigureCanvasAgg
from matplotlib.figure import Figure

from evogame.sim.recorder import GenerationLog

_DPI = 100
_GENE = "color"


class ChartPanel:
    def __init__(self, rect: pygame.Rect):
        self.rect = rect
        width_in = max(1.0, rect.width / _DPI)
        height_in = max(1.0, rect.height / _DPI)
        self.figure = Figure(figsize=(width_in, height_in), dpi=_DPI)
        self.canvas = FigureCanvasAgg(self.figure)
        self._surface: pygame.Surface | None = None
        self._render_placeholder()

    def _render_placeholder(self) -> None:
        self.figure.clear()
        ax = self.figure.add_subplot(1, 1, 1)
        ax.text(0.5, 0.5, "Awaiting data...", ha="center", va="center")
        ax.set_axis_off()
        self._blit_to_surface()

    def _blit_to_surface(self) -> None:
        self.canvas.draw()
        raw = self.canvas.buffer_rgba()
        size = self.canvas.get_width_height()
        self._surface = pygame.image.frombuffer(bytes(raw), size, "RGBA")

    def update(self, log: GenerationLog) -> None:
        if len(log) == 0:
            self._render_placeholder()
            return
        series = log.frequencies_over_time(_GENE)
        self.figure.clear()
        ax = self.figure.add_subplot(1, 1, 1)
        gens = [r.gen for r in log.records]
        for allele, values in sorted(series.items()):
            ax.plot(gens, values, label=allele, linewidth=2)
        ax.set_ylim(0, 1)
        ax.set_xlabel("Generation")
        ax.set_ylabel("Allele frequency")
        ax.set_title(f"{_GENE} alleles")
        ax.legend(loc="best", fontsize="small")
        ax.grid(True, alpha=0.3)
        self.figure.tight_layout()
        self._blit_to_surface()

    def draw(self, surface: pygame.Surface) -> None:
        if self._surface is not None:
            surface.blit(self._surface, self.rect.topleft)
```

**Step 4: Run, verify pass**

Run: `python -m pytest tests/ui/test_chart_panel.py -v`
Expected: 3 passed.

**Step 5: Commit**

```bash
git add src/evogame/ui/chart_panel.py tests/ui/test_chart_panel.py
git commit -m "feat(ui): add ChartPanel rendering matplotlib allele frequencies into pygame"
```

---

### Task 10: HUD widgets (button, toggle, slider)

**Files:**
- Create: `D:/game/src/evogame/ui/widgets.py`
- Create: `D:/game/tests/ui/test_widgets.py`

**Design notes:**
- Pure pygame primitives — no `pygame_gui`. Three widgets:
  - `Button(rect, label, on_click)` — flat rect with text, calls `on_click()` on left-click inside `rect`.
  - `Toggle(rect, label, initial)` — checkbox-style; `state: bool` flips on click.
  - `Slider(rect, min_value, max_value, initial)` — horizontal track + knob; `value: float`. Drag updates value.
- All three expose: `handle_event(event)`, `draw(surface, font)`.
- Tests exercise event handling logic, not pixels.

**Step 1: Write failing tests**

`D:/game/tests/ui/test_widgets.py`:

```python
import pygame
import pytest

from evogame.ui.widgets import Button, Slider, Toggle


def _click_event(pos, button=1):
    return pygame.event.Event(pygame.MOUSEBUTTONDOWN, {"pos": pos, "button": button})


def _release_event(pos, button=1):
    return pygame.event.Event(pygame.MOUSEBUTTONUP, {"pos": pos, "button": button})


def _motion_event(pos, buttons=(1, 0, 0)):
    return pygame.event.Event(pygame.MOUSEMOTION, {"pos": pos, "buttons": buttons, "rel": (0, 0)})


def test_button_invokes_callback_on_click():
    calls = []
    btn = Button(pygame.Rect(0, 0, 100, 30), "Go", lambda: calls.append(True))
    btn.handle_event(_click_event((50, 15)))
    assert calls == [True]


def test_button_ignores_clicks_outside():
    calls = []
    btn = Button(pygame.Rect(0, 0, 100, 30), "Go", lambda: calls.append(True))
    btn.handle_event(_click_event((200, 200)))
    assert calls == []


def test_toggle_flips_state_on_click():
    t = Toggle(pygame.Rect(0, 0, 30, 30), "Predator", initial=False)
    t.handle_event(_click_event((15, 15)))
    assert t.state is True
    t.handle_event(_click_event((15, 15)))
    assert t.state is False


def test_slider_clamps_initial():
    s = Slider(pygame.Rect(0, 0, 100, 20), min_value=1.0, max_value=5.0, initial=10.0)
    assert s.value == 5.0


def test_slider_drag_updates_value():
    s = Slider(pygame.Rect(0, 0, 100, 20), min_value=0.0, max_value=10.0, initial=5.0)
    s.handle_event(_click_event((50, 10)))      # grab knob in middle
    s.handle_event(_motion_event((90, 10)))     # drag near right edge
    assert s.value > 5.0


def test_slider_release_stops_drag():
    s = Slider(pygame.Rect(0, 0, 100, 20), min_value=0.0, max_value=10.0, initial=5.0)
    s.handle_event(_click_event((50, 10)))
    s.handle_event(_release_event((50, 10)))
    s.handle_event(_motion_event((90, 10), buttons=(0, 0, 0)))
    assert s.value == 5.0  # not dragged anymore
```

**Step 2: Run, verify failure**

Run: `python -m pytest tests/ui/test_widgets.py -v`
Expected: FAIL — module not found.

**Step 3: Implement**

`D:/game/src/evogame/ui/widgets.py`:

```python
from dataclasses import dataclass, field
from typing import Callable

import pygame


_BG = (40, 40, 50)
_FG = (220, 220, 220)
_ACCENT = (90, 180, 90)
_TRACK = (80, 80, 100)


class Button:
    def __init__(self, rect: pygame.Rect, label: str, on_click: Callable[[], None]):
        self.rect = rect
        self.label = label
        self.on_click = on_click

    def handle_event(self, event: pygame.event.Event) -> None:
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.rect.collidepoint(event.pos):
                self.on_click()

    def draw(self, surface: pygame.Surface, font: pygame.font.Font) -> None:
        pygame.draw.rect(surface, _BG, self.rect)
        pygame.draw.rect(surface, _FG, self.rect, 1)
        text = font.render(self.label, True, _FG)
        surface.blit(text, text.get_rect(center=self.rect.center))


class Toggle:
    def __init__(self, rect: pygame.Rect, label: str, initial: bool):
        self.rect = rect
        self.label = label
        self.state = initial

    def handle_event(self, event: pygame.event.Event) -> None:
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.rect.collidepoint(event.pos):
                self.state = not self.state

    def draw(self, surface: pygame.Surface, font: pygame.font.Font) -> None:
        pygame.draw.rect(surface, _BG, self.rect)
        pygame.draw.rect(surface, _FG, self.rect, 1)
        if self.state:
            inner = self.rect.inflate(-8, -8)
            pygame.draw.rect(surface, _ACCENT, inner)
        text = font.render(self.label, True, _FG)
        surface.blit(text, (self.rect.right + 6, self.rect.top + 2))


class Slider:
    def __init__(
        self,
        rect: pygame.Rect,
        min_value: float,
        max_value: float,
        initial: float,
    ):
        self.rect = rect
        self.min_value = min_value
        self.max_value = max_value
        self.value = max(min_value, min(max_value, initial))
        self._dragging = False

    def _set_value_from_x(self, x: int) -> None:
        ratio = (x - self.rect.left) / max(1, self.rect.width)
        ratio = max(0.0, min(1.0, ratio))
        self.value = self.min_value + ratio * (self.max_value - self.min_value)

    def handle_event(self, event: pygame.event.Event) -> None:
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.rect.collidepoint(event.pos):
                self._dragging = True
                self._set_value_from_x(event.pos[0])
        elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            self._dragging = False
        elif event.type == pygame.MOUSEMOTION and self._dragging:
            self._set_value_from_x(event.pos[0])

    def draw(self, surface: pygame.Surface, font: pygame.font.Font) -> None:
        track = pygame.Rect(self.rect.left, self.rect.centery - 3, self.rect.width, 6)
        pygame.draw.rect(surface, _TRACK, track)
        ratio = (self.value - self.min_value) / max(1e-9, self.max_value - self.min_value)
        knob_x = int(self.rect.left + ratio * self.rect.width)
        pygame.draw.circle(surface, _ACCENT, (knob_x, self.rect.centery), 8)
```

**Step 4: Run, verify pass**

Run: `python -m pytest tests/ui/test_widgets.py -v`
Expected: 6 passed.

**Step 5: Commit**

```bash
git add src/evogame/ui/widgets.py tests/ui/test_widgets.py
git commit -m "feat(ui): add Button, Toggle, Slider widgets"
```

---

### Task 11: `HUD` — composes widgets, draws status text

**Files:**
- Create: `D:/game/src/evogame/ui/hud.py`
- Create: `D:/game/tests/ui/test_hud.py`

**Design notes:**
- `HUD(rect, sim_controller, on_pause_toggle)`: lays out a Toggle (predator), Slider (gen/sec, range 0.5–5.0), Button (pause/restart), and renders text labels (gen #, pop count, extinction banner).
- Exposes `predator_on -> bool`, `gens_per_second -> float`, `paused -> bool`.
- `handle_event(event)` dispatches to widgets.
- The pause button's label flips between "Pause" / "Resume" / "Restart" based on state.
- Extinction overlay drawn over the world panel area, not the HUD — but the HUD owns the "Restart" button which calls `sim.reset()` and clears `paused`.

**Step 1: Write failing tests**

`D:/game/tests/ui/test_hud.py`:

```python
import random

import pygame
import pytest

from evogame.genetics import GUPPY_SCHEMA
from evogame.sim.controller import SimController
from evogame.ui.hud import HUD


def _make_sim():
    return SimController(
        schema=GUPPY_SCHEMA,
        initial_size=10,
        carrying_capacity=20,
        rng=random.Random(0),
    )


def test_hud_starts_with_predator_off_and_unpaused():
    sim = _make_sim()
    hud = HUD(pygame.Rect(0, 0, 600, 40), sim)
    assert hud.predator_on is False
    assert hud.paused is False
    assert 0.5 <= hud.gens_per_second <= 5.0


def test_predator_toggle_updates_sim():
    sim = _make_sim()
    hud = HUD(pygame.Rect(0, 0, 600, 40), sim)
    hud._toggle_predator()  # internal — exercise the wiring
    assert hud.predator_on is True
    assert sim.pressure.predator_on is True


def test_pause_button_flips_state():
    sim = _make_sim()
    hud = HUD(pygame.Rect(0, 0, 600, 40), sim)
    hud._toggle_pause()
    assert hud.paused is True
    hud._toggle_pause()
    assert hud.paused is False


def test_restart_button_resets_sim_when_extinct():
    sim = SimController(
        schema=GUPPY_SCHEMA,
        initial_size=1,  # will go extinct on tick
        carrying_capacity=10,
        rng=random.Random(0),
    )
    sim.tick()
    assert sim.extinct
    hud = HUD(pygame.Rect(0, 0, 600, 40), sim)
    hud._toggle_pause()  # acts as "Restart" when extinct
    assert sim.extinct is False
    assert sim.generation == 0
```

**Step 2: Run, verify failure**

Run: `python -m pytest tests/ui/test_hud.py -v`
Expected: FAIL — module not found.

**Step 3: Implement**

`D:/game/src/evogame/ui/hud.py`:

```python
import pygame

from evogame.sim.controller import SimController
from evogame.ui.widgets import Button, Slider, Toggle

_FG = (220, 220, 220)
_BG = (25, 25, 35)


class HUD:
    def __init__(self, rect: pygame.Rect, sim: SimController):
        self.rect = rect
        self.sim = sim
        self.paused = False

        # Layout: predator toggle | speed slider | pause button | text status
        y = rect.top + 8
        self.toggle = Toggle(pygame.Rect(rect.left + 10, y, 24, 24), "Predator", initial=False)
        self.slider = Slider(
            pygame.Rect(rect.left + 180, y + 2, 160, 20),
            min_value=0.5,
            max_value=5.0,
            initial=1.0,
        )
        self.pause_button = Button(
            pygame.Rect(rect.left + 360, y, 90, 24),
            "Pause",
            self._toggle_pause,
        )

    @property
    def predator_on(self) -> bool:
        return self.toggle.state

    @property
    def gens_per_second(self) -> float:
        return self.slider.value

    def _toggle_predator(self) -> None:
        self.toggle.state = not self.toggle.state
        self.sim.set_predator(self.toggle.state)

    def _toggle_pause(self) -> None:
        if self.sim.extinct:
            self.sim.reset()
            self.paused = False
            return
        self.paused = not self.paused

    def handle_event(self, event: pygame.event.Event) -> None:
        prior_toggle = self.toggle.state
        self.toggle.handle_event(event)
        if self.toggle.state != prior_toggle:
            self.sim.set_predator(self.toggle.state)
        self.slider.handle_event(event)
        self.pause_button.handle_event(event)

    def _label(self) -> str:
        if self.sim.extinct:
            return "Restart"
        return "Resume" if self.paused else "Pause"

    def draw(self, surface: pygame.Surface, font: pygame.font.Font) -> None:
        pygame.draw.rect(surface, _BG, self.rect)
        self.toggle.draw(surface, font)
        self.slider.draw(surface, font)
        self.pause_button.label = self._label()
        self.pause_button.draw(surface, font)
        # Status text on the right
        status = f"Gen {self.sim.generation}   Pop {len(self.sim.population)}   Speed {self.gens_per_second:.1f}/s"
        if self.sim.extinct:
            status += "   EXTINCT"
        text = font.render(status, True, _FG)
        surface.blit(text, (self.rect.left + 470, self.rect.top + 12))
```

**Step 4: Run, verify pass**

Run: `python -m pytest tests/ui/test_hud.py -v`
Expected: 4 passed.

**Step 5: Commit**

```bash
git add src/evogame/ui/hud.py tests/ui/test_hud.py
git commit -m "feat(ui): add HUD composing predator toggle, speed slider, pause button"
```

---

### Task 12: `App` — main loop wiring it all together

**Files:**
- Create: `D:/game/src/evogame/ui/app.py`
- Create: `D:/game/tests/ui/test_app.py`

**Design notes:**
- `App` constructor sets up window (1000×620), font, sim, panels, HUD.
- `run()` is the main loop. We also expose `step_one_frame(dt_ms)` for testability — pass it elapsed time, it advances the generation timer and triggers a tick if due.
- Layout: HUD top (full width, 40 px), world panel left half (480×580), chart panel right half (520×580).
- Window can be closed via the OS close button (QUIT event) — sets `self.running = False`.
- We won't actually call `App.run()` in tests (it loops forever); we test `step_one_frame` and a "run for N generations" helper.

**Step 1: Write failing tests**

`D:/game/tests/ui/test_app.py`:

```python
import pytest

from evogame.ui.app import App


def test_app_initializes_without_error():
    app = App(seed=0)
    assert app.sim.generation == 0
    assert app.running is True
    app.shutdown()


def test_app_advances_generation_after_enough_time():
    app = App(seed=0)
    # default speed is 1.0 gen/sec → 1000ms triggers exactly 1 generation
    app.step_one_frame(1100)
    assert app.sim.generation >= 1
    app.shutdown()


def test_app_does_not_advance_when_paused():
    app = App(seed=0)
    app.hud.paused = True
    app.step_one_frame(2000)
    assert app.sim.generation == 0
    app.shutdown()


def test_app_runs_for_n_generations():
    app = App(seed=0)
    app.run_for_generations(5, max_frames=200)
    assert app.sim.generation == 5
    app.shutdown()
```

**Step 2: Run, verify failure**

Run: `python -m pytest tests/ui/test_app.py -v`
Expected: FAIL — module not found.

**Step 3: Implement**

`D:/game/src/evogame/ui/app.py`:

```python
import random

import pygame

from evogame.genetics import GUPPY_SCHEMA
from evogame.sim.controller import SimController
from evogame.ui.chart_panel import ChartPanel
from evogame.ui.hud import HUD
from evogame.ui.world_panel import WorldPanel

_WINDOW_W = 1000
_WINDOW_H = 620
_HUD_H = 40
_INITIAL_POP = 30
_CARRYING_CAPACITY = 60


class App:
    def __init__(self, seed: int | None = None):
        pygame.init()
        pygame.display.set_caption("evogame — guppy")
        self.screen = pygame.display.set_mode((_WINDOW_W, _WINDOW_H))
        self.font = pygame.font.SysFont("arial", 14)
        self.clock = pygame.time.Clock()
        self.running = True

        rng = random.Random(seed)
        self.sim = SimController(
            schema=GUPPY_SCHEMA,
            initial_size=_INITIAL_POP,
            carrying_capacity=_CARRYING_CAPACITY,
            rng=rng,
        )

        hud_rect = pygame.Rect(0, 0, _WINDOW_W, _HUD_H)
        world_rect = pygame.Rect(0, _HUD_H, _WINDOW_W // 2, _WINDOW_H - _HUD_H)
        chart_rect = pygame.Rect(_WINDOW_W // 2, _HUD_H, _WINDOW_W // 2, _WINDOW_H - _HUD_H)

        self.hud = HUD(hud_rect, self.sim)
        self.world_panel = WorldPanel(world_rect)
        self.chart_panel = ChartPanel(chart_rect)
        self.chart_panel.update(self.sim.log)

        self._gen_timer_ms = 0.0

    def shutdown(self) -> None:
        pygame.quit()

    def _handle_events(self) -> None:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            self.hud.handle_event(event)

    def step_one_frame(self, dt_ms: float) -> None:
        self._handle_events()
        if not self.hud.paused and not self.sim.extinct:
            interval_ms = 1000.0 / self.hud.gens_per_second
            self._gen_timer_ms += dt_ms
            while self._gen_timer_ms >= interval_ms:
                self._gen_timer_ms -= interval_ms
                self.sim.tick()
                self.chart_panel.update(self.sim.log)
                if self.sim.extinct:
                    break
        self._render()

    def _render(self) -> None:
        self.screen.fill((10, 10, 15))
        self.world_panel.draw(self.screen, self.sim.population.creatures)
        self.chart_panel.draw(self.screen)
        self.hud.draw(self.screen, self.font)
        pygame.display.flip()

    def run(self) -> None:
        while self.running:
            dt_ms = self.clock.tick(60)
            self.step_one_frame(dt_ms)
        self.shutdown()

    def run_for_generations(self, target: int, max_frames: int = 1000) -> None:
        """Test helper: step until sim reaches the target generation or max_frames hits."""
        frames = 0
        while self.sim.generation < target and frames < max_frames:
            self.step_one_frame(100)
            frames += 1
```

**Step 4: Run, verify pass**

Run: `python -m pytest tests/ui/test_app.py -v`
Expected: 4 passed.

**Step 5: Run the full test suite to confirm nothing else regressed**

Run: `python -m pytest`
Expected: all pass.

**Step 6: Commit**

```bash
git add src/evogame/ui/app.py tests/ui/test_app.py
git commit -m "feat(ui): add App main loop wiring sim, panels, and HUD"
```

---

### Task 13: Entrypoint script + README update

**Files:**
- Create: `D:/game/scripts/run_game.py`
- Modify: `D:/game/README.md`

**Step 1: Create the entrypoint**

`D:/game/scripts/run_game.py`:

```python
"""Run the evogame frontend MVP — guppy + predator pressure."""

from evogame.ui.app import App


def main() -> None:
    app = App()
    app.run()


if __name__ == "__main__":
    main()
```

**Step 2: Update README**

Replace the README contents:

```markdown
# evogame

AP Biology evolution simulation game.

## Setup

    python -m pip install -e ".[dev]"

## Run the game

    python scripts/run_game.py

You'll see guppies on the left and a live allele-frequency chart on the right. Toggle the predator and watch white alleles climb.

## Run tests

    pytest

## Run the breeding demo

    python scripts/breed_demo.py
```

**Step 3: Smoke-test the entrypoint**

Run: `python -c "from evogame.ui.app import App; app = App(seed=0); app.run_for_generations(3); app.shutdown(); print('OK')"`
Expected: prints `OK` after a brief moment.

**Step 4: Commit**

```bash
git add scripts/run_game.py README.md
git commit -m "feat(ui): add run_game.py entrypoint and document in README"
```

---

## Final verification

After Task 13:

1. Run the full suite: `python -m pytest -v`
   Expected: every test passes.
2. Manually launch: `python scripts/run_game.py`
   Expected: window opens with creatures on the left, "Awaiting data..." flips to a chart within 1–2 seconds, predator toggle and slider respond to clicks, gen counter increments.
3. Toggle predator on; over ~30 generations the red-allele line should fall and white-allele line rise on the chart.
4. Close the window — process exits cleanly.

If any of those fail, debug before declaring the MVP done.
