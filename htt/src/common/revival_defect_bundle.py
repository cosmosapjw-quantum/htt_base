"""PR-210: BASS-HTT-MIO constitution and typed DefectBundle.

The legacy tri-stack integration ambition is re-founded as a typed composition
rather than a single scalar. A DefectBundle carries a frame/epoch-indexed
ComponentState (the master departure comparator x_C = Sigma2 - W2 + Omega_tilt +
DeltaOmega_k), a SourceState (kinematic/dynamic source norms), an admissible
class, and BridgeReceipts. Components from different frames or epochs may not be
combined without a validated BridgeReceipt -- that is the decisive falsifier.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Mapping


class Frame(str, Enum):
    NORMAL = "normal"
    MATTER = "matter"
    OBSERVER = "observer"
    ELECTRON = "electron"
    CMB = "cmb"


class BundleError(ValueError):
    """Raised on any typed-composition violation (frame/epoch/magnitude/bridge)."""


@dataclass(frozen=True)
class Epoch:
    scale_factor: float | None = None
    redshift: float | None = None

    def validate(self) -> None:
        if (self.scale_factor is None) == (self.redshift is None):
            raise BundleError("exactly one epoch coordinate is required")
        if self.scale_factor is not None and self.scale_factor <= 0:
            raise BundleError("scale factor a>0")
        if self.redshift is not None and self.redshift < -1:
            raise BundleError("redshift z>-1")

    def key(self) -> tuple[str, float]:
        if self.scale_factor is not None:
            return ("a", float(self.scale_factor))
        return ("z", float(self.redshift))


@dataclass(frozen=True)
class ComponentState:
    Sigma2: float
    W2: float
    Omega_tilt: float
    DeltaOmega_k: float  # signed carrier
    frame: Frame
    epoch: Epoch
    residual: float = 0.0

    def validate(self) -> None:
        self.epoch.validate()
        if min(self.Sigma2, self.W2, self.Omega_tilt) < 0:
            raise BundleError("magnitude components (Sigma2, W2, Omega_tilt) must be nonnegative")


@dataclass(frozen=True)
class SourceState:
    acceleration_norm: float | None = None
    heat_flux_norm: float | None = None
    anisotropic_stress_norm: float | None = None
    electric_weyl_norm: float | None = None
    magnetic_weyl_norm: float | None = None
    frame: Frame = Frame.NORMAL


@dataclass(frozen=True)
class BridgeReceipt:
    bridge_id: str
    source_frame: Frame
    target_frame: Frame
    domain: Mapping[str, object]
    validation_status: str
    provenance_hash: str

    def is_valid(self) -> bool:
        return (self.validation_status == "CERTIFIED"
                and bool(self.provenance_hash))


@dataclass(frozen=True)
class DefectBundle:
    comparator_id: str
    components: ComponentState
    sources: SourceState
    admissible_class: str
    bridges: tuple[BridgeReceipt, ...] = field(default_factory=tuple)


def comparator_value(g: ComponentState) -> float:
    """Master departure comparator x_C = Sigma2 - W2 + Omega_tilt + DeltaOmega_k (+residual)."""
    g.validate()
    return g.Sigma2 - g.W2 + g.Omega_tilt + g.DeltaOmega_k + g.residual


def require_common_frame(*states: ComponentState) -> Frame:
    frames = {s.frame for s in states}
    if len(frames) != 1:
        raise BundleError("frame-mixed comparator forbidden without a bridge")
    return next(iter(frames))


def require_common_epoch(*states: ComponentState) -> tuple[str, float]:
    keys = {s.epoch.key() for s in states}
    if len(keys) != 1:
        raise BundleError("epoch-mixed comparator forbidden without a bridge")
    return next(iter(keys))


def bridge_component(g: ComponentState, receipt: BridgeReceipt) -> ComponentState:
    """Push a component to receipt.target_frame iff the bridge is valid+matching."""
    if not receipt.is_valid():
        raise BundleError(f"bridge {receipt.bridge_id!r} is not CERTIFIED with provenance")
    if receipt.source_frame != g.frame:
        raise BundleError("bridge source frame does not match the component frame")
    return ComponentState(g.Sigma2, g.W2, g.Omega_tilt, g.DeltaOmega_k,
                          receipt.target_frame, g.epoch, g.residual)


def combine(states: list[ComponentState], bridges: tuple[BridgeReceipt, ...] = ()) -> float:
    """Combine components; frame/epoch mixing requires a validated bridge chain.

    Without bridges, all states must already share a frame and epoch. With
    bridges, every off-frame state must be pushed to the common frame first.
    """
    require_common_epoch(*states)
    frames = {s.frame for s in states}
    if len(frames) == 1:
        return sum(comparator_value(s) for s in states)
    if not bridges:
        raise BundleError("frame-mixed combine requires a bridge")
    # target frame = the majority/first; bridge every other frame to it
    target = states[0].frame
    valid = {(b.source_frame, b.target_frame): b for b in bridges if b.is_valid()}
    total = 0.0
    for s in states:
        if s.frame == target:
            total += comparator_value(s)
            continue
        b = valid.get((s.frame, target))
        if b is None:
            raise BundleError(f"no valid bridge {s.frame}->{target} for frame-mixed combine")
        total += comparator_value(bridge_component(s, b))
    return total
