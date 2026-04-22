"""BASS transport surfaces.

This package contains both the legacy/reduced transport helpers and the VER2
S2 geodesic/screen-basis skeleton contracts.
"""

from importlib import import_module

from bass.transport.geodesics import (
    PhotonGeodesicRhs,
    PhotonGeodesicState,
    ScreenBasisState,
    hard_redshift_check,
    photon_geodesic_rhs,
    redshift_log_derivative,
)

__all__ = [
    "ScreenBasisState",
    "PhotonGeodesicState",
    "PhotonGeodesicRhs",
    "TierAState",
    "TierARayRhs",
    "TierAScreenBasisRhs",
    "redshift_log_derivative",
    "hard_redshift_check",
    "photon_geodesic_rhs",
    "ray_rhs",
    "screen_basis_rhs",
    "collision_source_tierA",
]


_TIER_A_EXPORTS = {
    "TierAState",
    "TierARayRhs",
    "TierAScreenBasisRhs",
    "ray_rhs",
    "screen_basis_rhs",
    "collision_source_tierA",
}


def __getattr__(name: str):
    if name in _TIER_A_EXPORTS:
        module = import_module("bass.transport.ver3_tiera_transport")
        value = getattr(module, name)
        globals()[name] = value
        return value
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
