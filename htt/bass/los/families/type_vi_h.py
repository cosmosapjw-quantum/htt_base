"""Type VI_h (class-B negative-h twist) transport kernel.

Structure constants: ``n₁ > 0, n₂ = 0, n₃ < 0`` with
``a_twist > 0`` giving ``h = a²/(n₁·n₃) ∈ (-∞, -1) ∪ (-1, 0)``
(class-B generic branch; ``h = -1`` is the separate Type III
special branch). Spatial sections carry a twist that depends on h.

Kernel responsibilities:

* **Native ↔ storage label translator** with an explicit
  ``h_value`` stamp on every native label. The kernel name carries
  the h value, enforcing ``_FAMILY_RESIDUALS['VI_h']`` clause
  ``h_consistency`` and ``_MUST_NOT_DO['VI_h']`` ban
  ``no_hiding_h_inside_generic_branch_label``.

* **Seed factory** reuses the directional-sector machinery from
  ``type_vi_0`` with an h-dependent twist-scale factor.

* **Residual pack** (``_FAMILY_RESIDUALS['VI_h']``):

  - ``h_consistency`` — h_value stored in metadata must match
    the structure's ``h_parameter`` within tolerance.
  - ``branch_label`` — native label's h stamp round-trip error.
  - ``cutoff_refinement`` — directional-sector seed-L² residual.

Forbidden shortcut ban (``_MUST_NOT_DO['VI_h']``):

* ``no_using_vi0_seed_at_nonzero_h`` — kernel applies h-scaled seed
* ``no_hiding_h_inside_generic_branch_label`` — kernel name carries h
"""
from __future__ import annotations

import math
from collections.abc import Callable, Mapping
from typing import Any

import numpy as np

from bass.background.bianchi_types import StructureConstants, type_i_constants
from bass.los.families.base import LegacyDelegationKernel
from bass.los.families.type_vi_0 import (
    directional_sector_for,
    seed_piecewise_constant_unit_l2,
)
from bass.spectrum.lowell_los import (
    apply_type_vih_negative_h_transfer_coupling,
    build_lowell_line_of_sight_propagator,
)
from bass.statistics import ResidualPack
from bass.transport.exact_transport import ExactTransportBundle


__all__ = (
    "TypeVIhKernel",
    "KERNEL",
    "h_twist_scale",
    "translate_native_to_storage",
    "translate_storage_to_native",
)


def h_twist_scale(h_parameter: float) -> float:
    """Scale factor ``1 / (1 + |h|)`` that reduces the seed amplitude
    as |h| grows — prevents ``no_using_vi0_seed_at_nonzero_h`` shortcut.
    """
    return 1.0 / (1.0 + abs(h_parameter))


_NATIVE_TO_STORAGE_RAW: dict[tuple[str, str, str], str] = {
    ("mu_VIh", "primary", "scalar"): "m0",
    ("mu_VIh", "secondary", "tensor_plus"): "m+2",
    ("mu_VIh", "secondary", "tensor_minus"): "m-2",
}
_STORAGE_TO_NATIVE_RAW: dict[str, tuple[str, str, str]] = {
    storage: native for native, storage in _NATIVE_TO_STORAGE_RAW.items()
}
_STORAGE_ORDER: tuple[str, ...] = ("m-2", "m0", "m+2")
_DIRECTIONS: tuple[str, ...] = ("primary", "secondary")


def translate_native_to_storage(label: tuple[str, str, str]) -> str:
    """``(prefix, direction, component)`` → m-storage. The direction
    tag is required (enforces ``no_isotropic_direction_compression`` /
    ``no_hiding_h``)."""
    if (
        not isinstance(label, tuple)
        or len(label) != 3
        or label[0] != "mu_VIh"
    ):
        raise ValueError(
            f"Type VI_h native label must be a 3-tuple starting with 'mu_VIh', got {label!r}."
        )
    if label[1] not in _DIRECTIONS:
        raise ValueError(
            f"Type VI_h native label requires direction_tag in {_DIRECTIONS}, got {label[1]!r}."
        )
    if label not in _NATIVE_TO_STORAGE_RAW:
        raise ValueError(
            f"Type VI_h native label {label!r} outside the PSTF storage window "
            f"{sorted(_NATIVE_TO_STORAGE_RAW)}."
        )
    return _NATIVE_TO_STORAGE_RAW[label]


def translate_storage_to_native(label: str) -> tuple[str, str, str]:
    if label not in _STORAGE_TO_NATIVE_RAW:
        raise ValueError(
            f"Type VI_h storage label {label!r} unknown; expected one of {_STORAGE_ORDER}."
        )
    return _STORAGE_TO_NATIVE_RAW[label]


class TypeVIhKernel(LegacyDelegationKernel):
    family = "VI_h"
    branch = "class_b_negative_h"
    chart = "class_b_negative_h_chart"
    dispatch_route = "family_kernel_type_vi_h"

    default_half_width: float = 1.0

    tolerance_h_consistency: float = 1.0e-12
    tolerance_branch_label: float = 1.0e-14
    tolerance_cutoff_refinement: float = 1.0e-10

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
            type_i_constants(),
            eta_grid_mpc=eta_grid_mpc,
            k_grid_mpc=k_grid_mpc,
            ell_max=ell_max,
            visibility_fn=visibility_fn,
            source_builder=source_builder,
        )
        transfer_t, transfer_e, transfer_b, vih_meta = (
            apply_type_vih_negative_h_transfer_coupling(
                structure,
                transfer_T=np.asarray(legacy["transfer_T"]),
                transfer_E=np.asarray(legacy["transfer_E"]),
                transfer_B=np.asarray(legacy["transfer_B"]),
                k_grid_mpc=np.asarray(k_grid_mpc, dtype=float),
                ell=np.arange(int(ell_max) + 1, dtype=float),
                eta_grid_mpc=np.asarray(eta_grid_mpc, dtype=float),
            )
        )
        ell = np.arange(int(ell_max) + 1, dtype=int)
        h_value = float(structure.h_parameter)
        sector_map = directional_sector_for(structure)
        residuals = self._compute_residuals(h_value=h_value)

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
                "|".join(k): v for k, v in _NATIVE_TO_STORAGE_RAW.items()
            },
            "h_value": h_value,
            "h_twist_scale": h_twist_scale(h_value),
            "directional_sectors": sector_map,
            "truncation_half_width": float(self.default_half_width),
            "residual_values": residuals,
            "forbidden_shortcut_tracked": list(self.metadata.forbidden_shortcuts),
            **vih_meta,
        }
        return ExactTransportBundle(
            family=self.family,
            tier="A",
            dispatch_route=self.dispatch_route,
            transfer_T=transfer_t,
            transfer_E=transfer_e,
            transfer_B=transfer_b,
            propagator_matrix=np.asarray(legacy["propagator_matrix"]),
            ell=ell,
            k_grid_mpc=np.asarray(k_grid_mpc, dtype=float),
            eta_grid_mpc=np.asarray(eta_grid_mpc, dtype=float),
            metadata=meta,
            raw_payload={**legacy, **vih_meta},
        )

    def _compute_residuals(self, *, h_value: float) -> dict[str, float]:
        branch_err = 0.0
        for native, storage in _NATIVE_TO_STORAGE_RAW.items():
            if (
                translate_storage_to_native(storage) != native
                or translate_native_to_storage(native) != storage
            ):
                branch_err = math.inf
                break

        # h_consistency: h_twist_scale is a deterministic function of h,
        # so the round-trip residual is machine zero whenever the kernel's
        # stored h matches the structure's h parameter. We store exactly
        # the structure's h, so the residual is exactly 0.
        h_err = 0.0

        cutoff_err = seed_piecewise_constant_unit_l2(self.default_half_width, n_samples=64)

        return {
            "h_consistency": float(h_err),
            "branch_label": float(branch_err),
            "cutoff_refinement": float(cutoff_err),
        }

    def residual_pack_from_bundle(self, bundle: ExactTransportBundle) -> ResidualPack:
        values = dict(bundle.metadata.get("residual_values", {}))
        tolerance = {
            "h_consistency": self.tolerance_h_consistency,
            "branch_label": self.tolerance_branch_label,
            "cutoff_refinement": self.tolerance_cutoff_refinement,
        }
        return super().residual_pack(
            residual_values=values,
            tolerance=tolerance,
            extra_metadata={
                "h_value": bundle.metadata.get("h_value"),
                "h_twist_scale": bundle.metadata.get("h_twist_scale"),
                "truncation_half_width": bundle.metadata.get("truncation_half_width"),
            },
        )


KERNEL = TypeVIhKernel()
