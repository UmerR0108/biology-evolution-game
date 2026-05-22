from evogame.genetics.alleles import Allele
from evogame.genetics.gene_types import DominantRecessiveGene, IncompleteDominanceGene, PolygenicGene
from evogame.genetics.schema import SpeciesSchema

_B = Allele("B", "brown")
_W = Allele("W", "white")
_coat_color = IncompleteDominanceGene(name="coat_color", allele_a=_B, allele_b=_W, blend_label="tan")

_L = Allele("L", "long")
_s = Allele("s", "short")
_ear_length = DominantRecessiveGene(name="ear_length", dominant=_L, recessive=_s)

_FAST = Allele("F", "fast")
_slow = Allele("f", "slow")
_speed = PolygenicGene(name="speed", alleles=(_FAST, _slow), loci=3, value_of={_FAST: 1.0, _slow: 0.0})

_BOLD = Allele("D", "bold")
_shy = Allele("d", "shy")
_boldness = PolygenicGene(name="boldness", alleles=(_BOLD, _shy), loci=3, value_of={_BOLD: 1.0, _shy: 0.0})

BUNNY_SCHEMA = SpeciesSchema(
    name="bunny",
    genes=(_coat_color, _ear_length, _speed, _boldness),
)
