"""Unified Tier-A transport facade (v5 §G4).

``build_exact_transport`` is the single entry point that v5 PR-05 wants.
Today it delegates every Bianchi type (including the degenerate FLRW
case) to ``bass.spectrum.lowell_los.build_lowell_line_of_sight_propagator``
so this stage is a no-op on the numerics side. As family-specific
kernels land in S3–S5 they register themselves in
``_TRANSPORT_DISPATCH`` and this facade dispatches to them.

Bit-identity contract (R1 in the plan):

* ``build_exact_transport`` with ``family_spec`` whose ``family`` key is
  not in ``_TRANSPORT_DISPATCH`` returns the same numerics as calling
  ``build_lowell_line_of_sight_propagator`` directly. The only extra
  work is a single dict lookup per call and the construction of the
  ``ExactTransportBundle`` dataclass, neither of which touch the
  transfer arrays.

The ``ExactTransportBundle`` is intentionally a thin dataclass wrapper
around the legacy dict payload. Legacy consumers that call
``build_lowell_line_of_sight_propagator`` directly still get the raw
dict shape.
"""
from __future__ import annotations

from collections.abc import Callable, Mapping
from dataclasses import dataclass, field
from types import MappingProxyType
from typing import Literal, Protocol, runtime_checkable

import numpy as np

from bass.background.bianchi_types import StructureConstants
from bass.spectrum.lowell_los import build_lowell_line_of_sight_propagator

__all__ = (
    "ExactTransportBundle",
    "FamilyBackendNotImplemented",
    "FamilyTransportKernel",
    "build_exact_transport",
    "register_family_kernel",
    "list_registered_families",
)


class FamilyBackendNotImplemented(NotImplementedError):
    """Raised when a family kernel is requested but not yet wired up."""


@runtime_checkable
class FamilyTransportKernel(Protocol):
    """Structural interface family backends must satisfy.

    Actual implementations land in ``bass.los.families.*``. We keep the
    Protocol deliberately loose — Type IX (compact) will not share the
    same mode-ops shape as Type III (class-B hyperbolic), so an ABC
    would be over-constraining.
    """

    family: str

    def build_transport_bundle(
        self,
        *,
        structure: StructureConstants,
        eta_grid_mpc: np.ndarray,
        k_grid_mpc: np.ndarray,
        ell_max: int,
        visibility_fn: Callable[[float], float],
        source_builder: Callable[[float, float], Mapping[str, object]],
    ) -> "ExactTransportBundle":
        ...


@dataclass(frozen=True)
class ExactTransportBundle:
    """Unified transport output.

    Mirrors the keys returned by ``build_lowell_line_of_sight_propagator``
    and adds the ``family`` + ``tier`` + ``dispatch_route`` provenance
    fields. Legacy dict access is available via ``as_payload()``.
    """

    family: str
    tier: str
    dispatch_route: str
    transfer_T: np.ndarray
    transfer_E: np.ndarray
    transfer_B: np.ndarray
    propagator_matrix: np.ndarray
    ell: np.ndarray
    k_grid_mpc: np.ndarray
    eta_grid_mpc: np.ndarray
    metadata: Mapping[str, object] = field(default_factory=dict)
    raw_payload: Mapping[str, object] = field(default_factory=dict)

    def as_payload(self) -> dict[str, object]:
        """Legacy dict shape; safe to hand to callers that consumed the
        old ``build_lowell_line_of_sight_propagator`` dict."""
        base = dict(self.raw_payload)
        base.update(
            {
                "transfer_T": self.transfer_T,
                "transfer_E": self.transfer_E,
                "transfer_B": self.transfer_B,
                "propagator_matrix": self.propagator_matrix,
                "ell": self.ell,
                "k_grid_mpc": self.k_grid_mpc,
                "eta_grid_mpc": self.eta_grid_mpc,
                "family": self.family,
                "tier": self.tier,
                "dispatch_route": self.dispatch_route,
                "exact_transport_metadata": dict(self.metadata),
            }
        )
        return base


# ---------------------------------------------------------------------------
# Dispatch registry (populated by bass.los.families in S3–S5)
# ---------------------------------------------------------------------------

_TRANSPORT_DISPATCH: dict[str, FamilyTransportKernel] = {}


def register_family_kernel(kernel: FamilyTransportKernel) -> None:
    """Register a family-specific transport kernel.

    Idempotent re-registration of the same object is allowed; replacing a
    kernel with a different object raises ``RuntimeError`` to prevent
    accidental override during test discovery.
    """
    family = getattr(kernel, "family", None)
    if not isinstance(family, str) or not family:
        raise TypeError(
            "FamilyTransportKernel must expose a non-empty 'family' attribute."
        )
    existing = _TRANSPORT_DISPATCH.get(family)
    if existing is not None and existing is not kernel:
        raise RuntimeError(
            f"Family kernel already registered for '{family}': "
            f"{existing!r}. Refusing to replace with {kernel!r}."
        )
    _TRANSPORT_DISPATCH[family] = kernel


def list_registered_families() -> tuple[str, ...]:
    return tuple(sorted(_TRANSPORT_DISPATCH))


# ---------------------------------------------------------------------------
# Facade
# ---------------------------------------------------------------------------

_LEGACY_ROUTE = "lowell_los_legacy"
_FAMILY_ROUTE = "family_kernel"


def build_exact_transport(
    structure: StructureConstants,
    *,
    eta_grid_mpc: np.ndarray,
    k_grid_mpc: np.ndarray,
    ell_max: int,
    visibility_fn: Callable[[float], float],
    source_builder: Callable[[float, float], Mapping[str, object]],
    tier: Literal["A"] = "A",
    limber_eta_sp_sign: Literal["integrator", "legacy_negative"] = "integrator",
) -> ExactTransportBundle:
    """Build the Tier-A transport bundle for ``structure``.

    The FLRW case (``structure.label == 'FLRW'``) is routed first via
    a direct check — no dict lookup. Registered family kernels are
    checked next. Anything unregistered falls through to the legacy
    ``build_lowell_line_of_sight_propagator`` path, which is the current
    D_2 regression-anchor producer.
    """
    if not isinstance(structure, StructureConstants):
        raise TypeError(
            f"structure must be a StructureConstants, got {type(structure)!r}"
        )
    type_name = str(structure.label)

    kernel: FamilyTransportKernel | None = None
    if type_name != "FLRW":
        kernel = _TRANSPORT_DISPATCH.get(type_name)

    if kernel is not None:
        bundle = kernel.build_transport_bundle(
            structure=structure,
            eta_grid_mpc=np.asarray(eta_grid_mpc, dtype=float),
            k_grid_mpc=np.asarray(k_grid_mpc, dtype=float),
            ell_max=int(ell_max),
            visibility_fn=visibility_fn,
            source_builder=source_builder,
        )
        if not isinstance(bundle, ExactTransportBundle):
            raise TypeError(
                f"Family kernel for '{type_name}' must return "
                f"ExactTransportBundle, got {type(bundle)!r}"
            )
        return bundle

    # Legacy path — unchanged numerics, bit-identical to direct call.
    payload = build_lowell_line_of_sight_propagator(
        structure,
        eta_grid_mpc=eta_grid_mpc,
        k_grid_mpc=k_grid_mpc,
        ell_max=ell_max,
        visibility_fn=visibility_fn,
        source_builder=source_builder,
        limber_eta_sp_sign=limber_eta_sp_sign,
    )

    ell = np.arange(int(ell_max) + 1, dtype=int)
    metadata = {
        "tier": tier,
        "dispatch_route": _LEGACY_ROUTE,
        "family_registered": False,
        "fallback_reason": (
            "flrw_direct_legacy"
            if type_name == "FLRW"
            else f"no_kernel_registered_for_{type_name}"
        ),
        "limber_eta_sp_sign": limber_eta_sp_sign,
    }
    return ExactTransportBundle(
        family=type_name,
        tier=tier,
        dispatch_route=_LEGACY_ROUTE,
        transfer_T=np.asarray(payload["transfer_T"]),
        transfer_E=np.asarray(payload["transfer_E"]),
        transfer_B=np.asarray(payload["transfer_B"]),
        propagator_matrix=np.asarray(payload["propagator_matrix"]),
        ell=ell,
        k_grid_mpc=np.asarray(k_grid_mpc, dtype=float),
        eta_grid_mpc=np.asarray(eta_grid_mpc, dtype=float),
        metadata=MappingProxyType(metadata),
        raw_payload=payload,
    )
