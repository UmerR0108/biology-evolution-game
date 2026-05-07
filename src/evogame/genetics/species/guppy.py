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
