"""FB-9 skeleton package for massive neutrinos.

Every public surface in this package must preserve the invariant
``Sigma_mnu = 0 -> byte-identical to the LB-1 massless
NeutrinoBackground`` by keeping the zero-mass runtime on the existing
LB-1 path until the full FB-9 implementation lands.
"""
from bass.species.massive_neutrino.phase_space import phase_space_grid


__all__ = [
    "phase_space_grid",
]
