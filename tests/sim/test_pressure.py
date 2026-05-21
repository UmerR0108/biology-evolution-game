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
