"""BASS closure surfaces.

Legacy reduction helpers remain present, while the VER2 S2 packet adds an
explicit quadrupole-aware startup-manifold contract.
"""

from bass.closure.stiff_closure import (
    QuadrupoleStartupState,
    TightCouplingStartupMetadata,
    quadrupole_startup_from_sources,
)

__all__ = [
    "TightCouplingStartupMetadata",
    "QuadrupoleStartupState",
    "quadrupole_startup_from_sources",
]
