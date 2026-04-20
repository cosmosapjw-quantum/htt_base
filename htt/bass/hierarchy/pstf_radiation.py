"""VER2 radiation-state skeletons for the BASS S2 lane."""
from __future__ import annotations

from dataclasses import dataclass, field

from bass.collision.polarization import PolarizationHierarchyState, zero_polarization_hierarchy
from bass.hierarchy.frame_contracts import FrameSplitMetadata
from bass.hierarchy.pstf_tensor import PSTFHierarchyState, zero_hierarchy

__all__ = [
    "RadiationNormalization",
    "TruncationMetadata",
    "RadiationPSTFState",
    "make_radiation_state",
    "project_from_angular_samples_stub",
    "reconstruct_on_sphere_stub",
]


@dataclass(frozen=True)
class RadiationNormalization:
    """Explicit normalization contract for `{I,E,B}` multipoles."""

    I0_to_rho_gamma: float = 1.0
    I2_to_pi_gamma: float = 1.0
    E2_convention: str = "explicit_solver_state"
    B2_convention: str = "explicit_solver_state"


@dataclass(frozen=True)
class TruncationMetadata:
    """Explicit low-`ell` truncation record."""

    L: int
    diagnostic_only: bool = False
    allow_L2_override: bool = False
    closure_name: str = "explicit_unset"
    closure_promotion_explicit: bool = True

    def __post_init__(self) -> None:
        if self.L < 2:
            raise ValueError(f"RadiationPSTFState requires L >= 2, got {self.L}")
        if self.L == 2 and not (self.diagnostic_only or self.allow_L2_override):
            raise ValueError(
                "L=2 is diagnostic-only in VER2 unless an explicit override is recorded"
            )
        if not self.closure_promotion_explicit:
            raise ValueError("closure promotion must be explicit in VER2 S2")


@dataclass(frozen=True)
class RadiationPSTFState:
    """Temperature/E/B low-`ell` PSTF bundle."""

    I: PSTFHierarchyState
    E: PolarizationHierarchyState
    B: PSTFHierarchyState
    normalization: RadiationNormalization = field(default_factory=RadiationNormalization)
    truncation: TruncationMetadata = field(default_factory=lambda: TruncationMetadata(L=6))
    frame_metadata: FrameSplitMetadata = field(default_factory=FrameSplitMetadata)

    def __post_init__(self) -> None:
        if self.I.L != self.E.L:
            raise ValueError(f"temperature and E towers must share L; got {self.I.L} vs {self.E.L}")
        if self.I.L != self.B.L:
            raise ValueError(f"temperature and B towers must share L; got {self.I.L} vs {self.B.L}")
        if self.truncation.L != self.I.L:
            raise ValueError(
                f"truncation metadata L={self.truncation.L} must match tower L={self.I.L}"
            )
        if self.frame_metadata.transport_frame != "n_frame":
            raise ValueError("radiation transport state must remain in the n^a frame")

    @property
    def L(self) -> int:
        return self.I.L


def make_radiation_state(
    L: int,
    *,
    diagnostic_only: bool = False,
    allow_L2_override: bool = False,
    closure_name: str = "explicit_unset",
) -> RadiationPSTFState:
    """Factory for an empty `{I,E,B}` radiation bundle."""
    truncation = TruncationMetadata(
        L=L,
        diagnostic_only=diagnostic_only,
        allow_L2_override=allow_L2_override,
        closure_name=closure_name,
    )
    return RadiationPSTFState(
        I=zero_hierarchy(L),
        E=zero_polarization_hierarchy(L),
        B=zero_hierarchy(L),
        truncation=truncation,
    )


def project_from_angular_samples_stub(*args, **kwargs):
    """Projection stub reserved for the executable solver packet."""
    raise NotImplementedError(
        "Angular-sample -> PSTF projection is a VER2 executable-solver task; "
        "SK-02S2 freezes only the state/normalization/truncation contracts."
    )


def reconstruct_on_sphere_stub(*args, **kwargs):
    """Reconstruction stub reserved for the executable solver packet."""
    raise NotImplementedError(
        "PSTF -> angular reconstruction is a VER2 executable-solver task; "
        "SK-02S2 freezes only the state/normalization/truncation contracts."
    )
