import random

from evogame.genetics import BUNNY_SCHEMA, Creature


def test_bunny_schema_exports_expected_species_name():
    assert BUNNY_SCHEMA.name == "bunny"


def test_bunny_random_creature_has_expected_phenotypes():
    bunny = Creature.random(BUNNY_SCHEMA, random.Random(0))

    assert {"coat_color", "ear_length", "speed", "boldness"} <= set(bunny.phenotype)


def test_bunny_coat_color_categories_are_valid():
    categories = {Creature.random(BUNNY_SCHEMA, random.Random(i)).phenotype["coat_color"].category for i in range(20)}

    assert categories <= {"brown", "tan", "white"}


def test_bunny_polygenic_traits_are_numeric():
    bunny = Creature.random(BUNNY_SCHEMA, random.Random(1))

    assert isinstance(bunny.phenotype["speed"].value, (int, float))
    assert isinstance(bunny.phenotype["boldness"].value, (int, float))


def test_bunny_breeding_preserves_bunny_schema():
    rng = random.Random(2)
    a = Creature.random(BUNNY_SCHEMA, rng)
    b = Creature.random(BUNNY_SCHEMA, rng)

    child = a.breed(b, rng)

    assert child.schema is BUNNY_SCHEMA
