"""VER2 startup-closure skeletons for the BASS S2 lane."""
from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np

__all__ = [
    "TightCouplingStartupMetadata",
    "QuadrupoleStartupState",
    "quadrupole_startup_from_sources",
]


@dataclass(frozen=True)
class TightCouplingStartupMetadata:
    """Explicit metadata for the quadrupole-aware startup manifold."""

    closure_name: str = "quadrupole_tca"
    startup_frame: str = "electron_frame"
    startup_scope: str = "approximate_startup_manifold_only"
    quadrupole_aware: bool = True
    residual_monitor_required: bool = True
    hidden_promotion_forbidden: bool = True

    def __post_init__(self) -> None:
        if self.closure_name != "quadrupole_tca":
            raise ValueError("SK-02S2 freezes quadrupole-aware TCA by name")
        if self.startup_frame != "electron_frame":
            raise ValueError("tight-coupling startup is defined in the electron frame")
        if self.startup_scope != "approximate_startup_manifold_only":
            raise ValueError("startup scope drifted beyond the S2 contract")
        if not self.quadrupole_aware:
            raise ValueError("hidden monopole/dipole-only startup is not allowed")
        if not self.hidden_promotion_forbidden:
            raise ValueError("closure promotion must stay explicit in VER2")


@dataclass(frozen=True)
class QuadrupoleStartupState:
    """Approximate startup manifold for `(Theta_2, E_2, Pi)`."""

    theta_2: float
    E_2: float
    combined_source_pi: float
    metadata: TightCouplingStartupMetadata = field(
        default_factory=TightCouplingStartupMetadata
    )

    def __post_init__(self) -> None:
        for name, value in (
            ("theta_2", self.theta_2),
            ("E_2", self.E_2),
            ("combined_source_pi", self.combined_source_pi),
        ):
            if not np.isfinite(value):
                raise ValueError(f"{name} must be finite, got {value!r}")


def quadrupole_startup_from_sources(
    *,
    S_T: float,
    S_E: float,
    gamma_T: float,
    metadata: TightCouplingStartupMetadata | None = None,
) -> QuadrupoleStartupState:
    """Return the explicit TCA startup manifold, not a runtime promotion."""
    if not np.isfinite(S_T):
        raise ValueError(f"S_T must be finite, got {S_T!r}")
    if not np.isfinite(S_E):
        raise ValueError(f"S_E must be finite, got {S_E!r}")
    if not np.isfinite(gamma_T) or gamma_T <= 0.0:
        raise ValueError(
            "gamma_T must be positive finite for the startup manifold"
        )
    sqrt6 = float(np.sqrt(6.0))
    theta_2 = ((4.0 / 3.0) * float(S_T) - (sqrt6 / 3.0) * float(S_E)) / float(gamma_T)
    E_2 = (-(sqrt6 / 3.0) * float(S_T) + 3.0 * float(S_E)) / float(gamma_T)
    combined_source_pi = theta_2 - sqrt6 * E_2
    return QuadrupoleStartupState(
        theta_2=theta_2,
        E_2=E_2,
        combined_source_pi=combined_source_pi,
        metadata=metadata or TightCouplingStartupMetadata(),
    )
