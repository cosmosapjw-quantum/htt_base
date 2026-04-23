"""Shared infrastructure for family-specific transport kernels (S3).

Two helper base classes:

* ``LegacyDelegationKernel`` — wraps the existing
  ``build_lowell_line_of_sight_propagator`` inside the new
  ``FamilyTransportKernel`` shape. This is how Type I lands in S3: the
  math doesn't change, only the wrapping. Other families will override
  ``build_transport_bundle`` with family-specific numerics in S4/S5.
* ``NotImplementedKernel`` — raises ``FamilyBackendNotImplemented`` on
  invocation. S3 ships ten of these (II through IX) so the registry is
  shape-complete even before any Wave A/B numerics land.

The registry itself (``KNOWN_FAMILIES``, ``get_family_kernel``) lives in
``bass.los.families.__init__`` to keep this file focused on behavior.
"""
from __future__ import annotations

from collections.abc import Callable, Mapping
from dataclasses import dataclass, field
from typing import Any, ClassVar

import numpy as np

from bass.background.bianchi_types import FamilySpec, StructureConstants, get_family_spec
from bass.los.family_backend_protocol import (
    _BOUNDARY_POLICIES,
    _CHART_DEFAULTS,
    _COLLOCATION_NOTES,
    _FAMILY_RESIDUALS,
    _MUST_NOT_DO,
    _NATIVE_LABELS,
    _OPERATOR_KERNELS,
    _V5_VERIFICATION_BUNDLE,
)
from bass.spectrum.lowell_los import build_lowell_line_of_sight_propagator
from bass.statistics import ResidualPack, build_residual_pack
from bass.transport.exact_transport import (
    ExactTransportBundle,
    FamilyBackendNotImplemented,
)


__all__ = (
    "FamilyMetadata",
    "LegacyDelegationKernel",
    "NotImplementedKernel",
    "family_metadata_from_registry",
)


@dataclass(frozen=True)
class FamilyMetadata:
    """Frozen metadata block pulled from ``family_backend_protocol.py``.

    Every family kernel carries one of these so downstream code can
    inspect chart/boundary/operator/shortcut-forbidden data without
    reaching back into the protocol module.
    """

    family: str
    chart: str
    boundary_policy: str
    operator_kernel: str
    native_label: str
    required_residuals: tuple[str, ...]
    forbidden_shortcuts: tuple[str, ...]
    collocation_notes: tuple[str, ...]
    family_spec: FamilySpec
    verification_crosscheck_pass: bool


def family_metadata_from_registry(family: str) -> FamilyMetadata:
    """Assemble a ``FamilyMetadata`` from the frozen v5 registries."""
    if family not in _CHART_DEFAULTS:
        raise KeyError(f"Unknown Bianchi family '{family}'")
    return FamilyMetadata(
        family=family,
        chart=_CHART_DEFAULTS[family],
        boundary_policy=_BOUNDARY_POLICIES.get(family, "unspecified"),
        operator_kernel=_OPERATOR_KERNELS.get(family, "unspecified"),
        native_label=_NATIVE_LABELS.get(family, f"mu_{family.lower()}"),
        required_residuals=tuple(_FAMILY_RESIDUALS.get(family, ())),
        forbidden_shortcuts=tuple(_MUST_NOT_DO.get(family, ())),
        collocation_notes=tuple(_COLLOCATION_NOTES.get(family, ())),
        family_spec=get_family_spec(family),
        verification_crosscheck_pass=bool(
            _V5_VERIFICATION_BUNDLE.get("crosscheck_pass", False)
        ),
    )


# ---------------------------------------------------------------------------
# Reference kernel: delegates to the legacy builder.
# ---------------------------------------------------------------------------


class LegacyDelegationKernel:
    """Family kernel that reuses ``build_lowell_line_of_sight_propagator``.

    Used by Type I directly and as a starting point for any Wave A/B
    family whose kernel eventually overrides only a subset of the
    propagator math. The returned ``ExactTransportBundle`` wraps the
    legacy payload dict without mutating it — the underlying arrays are
    bit-identical.
    """

    family: ClassVar[str] = ""
    branch: ClassVar[str] = "base"
    chart: ClassVar[str] = "native"
    dispatch_route: ClassVar[str] = "family_kernel_legacy_delegation"

    def __init__(self) -> None:
        if not self.family:
            raise TypeError(
                "LegacyDelegationKernel subclasses must set a 'family' class attribute"
            )
        self.metadata = family_metadata_from_registry(self.family)

    # The contract matches FamilyTransportKernel.build_transport_bundle.
    def build_transport_bundle(
        self,
        *,
        structure: StructureConstants,
        eta_grid_mpc: np.ndarray,
        k_grid_mpc: np.ndarray,
        ell_max: int,
        visibility_fn: Callable[[float], float],
        source_builder: Callable[[float, float], Mapping[str, object]],
    ) -> ExactTransportBundle:
        self._assert_label_matches(structure)
        legacy = build_lowell_line_of_sight_propagator(
            structure,
            eta_grid_mpc=eta_grid_mpc,
            k_grid_mpc=k_grid_mpc,
            ell_max=ell_max,
            visibility_fn=visibility_fn,
            source_builder=source_builder,
        )
        ell = np.arange(int(ell_max) + 1, dtype=int)
        meta = {
            "tier": "A",
            "dispatch_route": self.dispatch_route,
            "family_registered": True,
            "chart": self.metadata.chart,
            "boundary_policy": self.metadata.boundary_policy,
            "operator_kernel": self.metadata.operator_kernel,
            "native_label": self.metadata.native_label,
            "verification_crosscheck_pass": self.metadata.verification_crosscheck_pass,
        }
        return ExactTransportBundle(
            family=self.family,
            tier="A",
            dispatch_route=self.dispatch_route,
            transfer_T=np.asarray(legacy["transfer_T"]),
            transfer_E=np.asarray(legacy["transfer_E"]),
            transfer_B=np.asarray(legacy["transfer_B"]),
            propagator_matrix=np.asarray(legacy["propagator_matrix"]),
            ell=ell,
            k_grid_mpc=np.asarray(k_grid_mpc, dtype=float),
            eta_grid_mpc=np.asarray(eta_grid_mpc, dtype=float),
            metadata=meta,
            raw_payload=legacy,
        )

    def residual_pack(
        self,
        *,
        residual_values: Mapping[str, float],
        tolerance: Mapping[str, float],
        extra_metadata: Mapping[str, Any] | None = None,
    ) -> ResidualPack:
        """Assemble a ResidualPack consistent with the family's metadata."""
        meta = {
            "chart": self.metadata.chart,
            "boundary_policy": self.metadata.boundary_policy,
            "operator_kernel": self.metadata.operator_kernel,
            "native_label": self.metadata.native_label,
            "collocation_notes": list(self.metadata.collocation_notes),
        }
        if extra_metadata:
            meta.update(dict(extra_metadata))
        return build_residual_pack(
            family=self.family,
            branch=self.branch,
            backend=self.dispatch_route,
            residual_values=residual_values,
            tolerance=tolerance,
            required_residuals=self.metadata.required_residuals,
            forbidden_shortcuts=self.metadata.forbidden_shortcuts,
            metadata=meta,
            verification_crosscheck_pass=self.metadata.verification_crosscheck_pass,
        )

    def _assert_label_matches(self, structure: StructureConstants) -> None:
        if structure.label != self.family:
            raise ValueError(
                f"{type(self).__name__} expects structure.label == "
                f"{self.family!r}, got {structure.label!r}"
            )


# ---------------------------------------------------------------------------
# Skeleton kernel: raises until Wave A/B lands.
# ---------------------------------------------------------------------------


class NotImplementedKernel:
    """Placeholder kernel for families whose Wave A/B numerics have not landed."""

    family: ClassVar[str] = ""
    branch: ClassVar[str] = "base"
    dispatch_route: ClassVar[str] = "family_kernel_pending"
    deferred_to: ClassVar[str] = "S4/S5"

    def __init__(self) -> None:
        if not self.family:
            raise TypeError(
                "NotImplementedKernel subclasses must set a 'family' class attribute"
            )
        self.metadata = family_metadata_from_registry(self.family)

    def build_transport_bundle(self, **_kwargs) -> ExactTransportBundle:
        raise FamilyBackendNotImplemented(
            f"Family '{self.family}' transport kernel is deferred to "
            f"{self.deferred_to}. Until then, the facade falls back to "
            "the legacy build_lowell_line_of_sight_propagator path "
            "(registering this kernel therefore loses the legacy numerics)."
        )

    def residual_pack(
        self,
        *,
        residual_values: Mapping[str, float] | None = None,
        tolerance: Mapping[str, float] | None = None,
        extra_metadata: Mapping[str, Any] | None = None,
    ) -> ResidualPack:
        values = dict(residual_values or {})
        tol = dict(tolerance or {})
        meta = {
            "chart": self.metadata.chart,
            "boundary_policy": self.metadata.boundary_policy,
            "operator_kernel": self.metadata.operator_kernel,
            "native_label": self.metadata.native_label,
            "deferred_to": self.deferred_to,
            "status": "skeleton",
        }
        if extra_metadata:
            meta.update(dict(extra_metadata))
        # Mark every required residual as violated so the pack cannot pass.
        for label in self.metadata.required_residuals:
            values.setdefault(label, float("nan"))
            tol.setdefault(label, 0.0)
        return build_residual_pack(
            family=self.family,
            branch=self.branch,
            backend=self.dispatch_route,
            residual_values=values,
            tolerance=tol,
            required_residuals=self.metadata.required_residuals,
            forbidden_shortcuts=self.metadata.forbidden_shortcuts,
            metadata=meta,
            verification_crosscheck_pass=self.metadata.verification_crosscheck_pass,
        )
