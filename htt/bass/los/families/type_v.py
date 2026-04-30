"""Type V (open hyperbolic) transport kernel.

Structure constants: ``n₁ = n₂ = n₃ = 0, a_twist > 0`` — the maximally
symmetric open FLRW analogue. Spatial sections are open hyperbolic H³
(curvature k = -1 after normalization). FLRW limit exists as σ → 0.

Kernel responsibilities:

* **Native ↔ storage label translator** with an explicit
  ``chart_metadata`` tag marked ``"open_chart"`` — any native label
  missing that tag is rejected (enforces
  ``no_hidden_flrw_import_without_open_chart_metadata`` from
  ``_MUST_NOT_DO['V']``).

* **Seed factory** reuses the hyperbolic Legendre builder from
  ``type_iii`` but with the Type V radial cutoff (``ξ_max``)
  policy ``open_hyperbolic_radial_cutoff``.

* **Residual pack** (``_FAMILY_RESIDUALS['V']``):

  - ``open_anchor_limit`` — |transfer_T[m0] - Type I m0| in σ→0 limit.
  - ``label_translator_roundtrip`` — exact, 0.
  - ``seed_regularity`` — |⟨seed, seed⟩ - 1|.
"""
from __future__ import annotations

import math
from collections.abc import Callable, Mapping
from typing import Any

import numpy as np

from bass.background.bianchi_types import StructureConstants, type_i_constants
from bass.los.families.base import LegacyDelegationKernel
from bass.los.families.type_iii import (
    hyperbolic_seed_amplitude,
    hyperbolic_seed_norm_residual,
)
from bass.spectrum.lowell_los import (
    apply_type_v_open_hyperbolic_transfer_envelope,
    build_lowell_line_of_sight_propagator,
)
from bass.statistics import ResidualPack
from bass.transport.exact_transport import ExactTransportBundle


__all__ = (
    "TypeVKernel",
    "KERNEL",
    "CHART_METADATA",
    "translate_native_to_storage",
    "translate_storage_to_native",
)


CHART_METADATA: str = "open_chart"


_NATIVE_TO_STORAGE: dict[tuple[str, str, str], str] = {
    ("mu_open", CHART_METADATA, "scalar"): "m0",
    ("mu_open", CHART_METADATA, "tensor_plus"): "m+2",
    ("mu_open", CHART_METADATA, "tensor_minus"): "m-2",
}
_STORAGE_TO_NATIVE: dict[str, tuple[str, str, str]] = {
    storage: native for native, storage in _NATIVE_TO_STORAGE.items()
}
_STORAGE_ORDER: tuple[str, ...] = ("m-2", "m0", "m+2")


def translate_native_to_storage(label: tuple[str, str, str]) -> str:
    if (
        not isinstance(label, tuple)
        or len(label) != 3
        or label[0] != "mu_open"
    ):
        raise ValueError(
            f"Type V native label must be a 3-tuple starting with 'mu_open', got {label!r}."
        )
    if label[1] != CHART_METADATA:
        raise ValueError(
            f"Type V requires chart metadata tag {CHART_METADATA!r} (no_hidden_flrw_import "
            f"without_open_chart_metadata); got {label[1]!r}."
        )
    if label not in _NATIVE_TO_STORAGE:
        raise ValueError(
            f"Type V native label {label!r} outside the PSTF storage window "
            f"{sorted(_NATIVE_TO_STORAGE)}."
        )
    return _NATIVE_TO_STORAGE[label]


def translate_storage_to_native(label: str) -> tuple[str, str, str]:
    if label not in _STORAGE_TO_NATIVE:
        raise ValueError(
            f"Type V storage label {label!r} unknown; expected one of {_STORAGE_ORDER}."
        )
    return _STORAGE_TO_NATIVE[label]


class TypeVKernel(LegacyDelegationKernel):
    family = "V"
    branch = "open_hyperbolic"
    chart = "hyperbolic_open_chart"
    dispatch_route = "family_kernel_type_v"

    default_xi_max: float = 1.5

    tolerance_open_anchor_limit: float = 5.0e-2
    tolerance_translator_roundtrip: float = 1.0e-14
    tolerance_seed_regularity: float = 1.0e-10

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
        legacy_i = build_lowell_line_of_sight_propagator(
            type_i_constants(),
            eta_grid_mpc=eta_grid_mpc,
            k_grid_mpc=k_grid_mpc,
            ell_max=ell_max,
            visibility_fn=visibility_fn,
            source_builder=source_builder,
        )
        transfer_t, transfer_e, transfer_b, typev_meta = (
            apply_type_v_open_hyperbolic_transfer_envelope(
                structure,
                transfer_T=np.asarray(legacy_i["transfer_T"]),
                transfer_E=np.asarray(legacy_i["transfer_E"]),
                transfer_B=np.asarray(legacy_i["transfer_B"]),
                k_grid_mpc=np.asarray(k_grid_mpc, dtype=float),
            )
        )
        ell = np.arange(int(ell_max) + 1, dtype=int)
        residuals = self._compute_residuals(
            t_v=transfer_t,
            t_i=np.asarray(legacy_i["transfer_T"]),
        )

        meta: dict[str, Any] = {
            "tier": "A",
            "dispatch_route": self.dispatch_route,
            "family_registered": True,
            "chart": self.metadata.chart,
            "boundary_policy": self.metadata.boundary_policy,
            "operator_kernel": self.metadata.operator_kernel,
            "native_label": self.metadata.native_label,
            "verification_crosscheck_pass": self.metadata.verification_crosscheck_pass,
            "storage_order": list(_STORAGE_ORDER),
            "native_to_storage_translator": {
                "|".join(k): v for k, v in _NATIVE_TO_STORAGE.items()
            },
            "chart_metadata": CHART_METADATA,
            "radial_cutoff_xi_max": float(self.default_xi_max),
            "seed_amplitude": hyperbolic_seed_amplitude(self.default_xi_max),
            "residual_values": residuals,
            "forbidden_shortcut_tracked": list(self.metadata.forbidden_shortcuts),
            **typev_meta,
        }
        return ExactTransportBundle(
            family=self.family,
            tier="A",
            dispatch_route=self.dispatch_route,
            transfer_T=transfer_t,
            transfer_E=transfer_e,
            transfer_B=transfer_b,
            propagator_matrix=np.asarray(legacy_i["propagator_matrix"]),
            ell=ell,
            k_grid_mpc=np.asarray(k_grid_mpc, dtype=float),
            eta_grid_mpc=np.asarray(eta_grid_mpc, dtype=float),
            metadata=meta,
            raw_payload={**legacy_i, **typev_meta},
        )

    def _compute_residuals(self, *, t_v: np.ndarray, t_i: np.ndarray) -> dict[str, float]:
        roundtrip_err = 0.0
        for native, storage in _NATIVE_TO_STORAGE.items():
            if (
                translate_storage_to_native(storage) != native
                or translate_native_to_storage(native) != storage
            ):
                roundtrip_err = math.inf
                break

        seed_err = hyperbolic_seed_norm_residual(self.default_xi_max, n_samples=128)

        if t_v.ndim != 3 or t_v.shape != t_i.shape or t_v.shape[-1] != 3:
            anchor_err = math.inf
        else:
            diff = t_v[..., 1] - t_i[..., 1]
            scale = max(float(np.max(np.abs(t_i[..., 1]))), 1.0e-30)
            anchor_err = float(np.max(np.abs(diff)) / scale)

        return {
            "open_anchor_limit": float(anchor_err),
            "label_translator_roundtrip": float(roundtrip_err),
            "seed_regularity": float(seed_err),
        }

    def residual_pack_from_bundle(self, bundle: ExactTransportBundle) -> ResidualPack:
        values = dict(bundle.metadata.get("residual_values", {}))
        tolerance = {
            "open_anchor_limit": self.tolerance_open_anchor_limit,
            "label_translator_roundtrip": self.tolerance_translator_roundtrip,
            "seed_regularity": self.tolerance_seed_regularity,
        }
        return super().residual_pack(
            residual_values=values,
            tolerance=tolerance,
            extra_metadata={
                "chart_metadata": bundle.metadata.get("chart_metadata"),
                "radial_cutoff_xi_max": bundle.metadata.get("radial_cutoff_xi_max"),
            },
        )


KERNEL = TypeVKernel()
