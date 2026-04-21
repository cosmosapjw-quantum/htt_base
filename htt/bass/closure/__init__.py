"""BASS closure surfaces.

Legacy reduction helpers remain present, while the VER2 S2 packet adds an
explicit quadrupole-aware startup-manifold contract.
"""

from bass.closure.stiff_closure import (
    QuadrupoleStartupState,
    StartupGateDecision,
    TightCouplingStartupMetadata,
    decide_startup_gate,
    quadrupole_startup_from_sources,
)

__all__ = [
    "TightCouplingStartupMetadata",
    "QuadrupoleStartupState",
    "StartupGateDecision",
    "quadrupole_startup_from_sources",
    "decide_startup_gate",
]
