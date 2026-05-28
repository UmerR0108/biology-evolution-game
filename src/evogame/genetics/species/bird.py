from evogame.genetics.alleles import Allele
from evogame.genetics.gene_types import IncompleteDominanceGene, MultiAlleleGene, PolygenicGene
from evogame.genetics.schema import SpeciesSchema

_POINTED = Allele("P", "pointed")
_BROAD = Allele("B", "broad")
_CURVED = Allele("C", "curved")
_beak_shape = MultiAlleleGene(
    name="beak_shape",
    alleles=(_POINTED, _BROAD, _CURVED),
    dominance_order=(_POINTED, _BROAD, _CURVED),
)

_LONG = Allele("L", "long")
_SHORT = Allele("s", "short")
_wing_span = PolygenicGene(
    name="wing_span",
    alleles=(_LONG, _SHORT),
    loci=3,
    value_of={_LONG: 1.0, _SHORT: 0.0},
)

_BROWN = Allele("Br", "brown")
_GREEN = Allele("G", "green")
_coloration = IncompleteDominanceGene(
    name="coloration",
    allele_a=_BROWN,
    allele_b=_GREEN,
    blend_label="mottled",
)

BIRD_SCHEMA = SpeciesSchema(
    name="bird",
    genes=(_beak_shape, _wing_span, _coloration),
)
