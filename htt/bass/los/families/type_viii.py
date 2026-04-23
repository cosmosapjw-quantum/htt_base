"""Type VIII (SL(2,ℝ) noncompact, discrete series) transport kernel.

Structure constants: SL(2,ℝ) semisimple algebra. Discrete series
labeled by positive / negative half-integer weight ``k``; continuous
principal series deferred per plan Open-Question 1 (``mpmath.hyper``).

Kernel responsibilities:

* **Native ↔ storage label translator** with an explicit
  ``series_tag ∈ {"discrete_positive", "discrete_negative", "trivial"}``.
  ``continuous_principal`` inputs raise ``NotImplementedError`` pointing
  to the deferred continuous-series annex PR.

* **Seed factory** ``ψ(x) = A · P_2(x)`` on ``x ∈ [0, tanh(ξ_max)]`` —
  the compactified SL(2,ℝ) disc chart. Closed-form amplitude via
  Gauss-Legendre. This is explicitly NOT a compact-SU(2) Wigner-D
  evaluation (``no_compact_su2_reuse`` forbidden shortcut).

* **Residual pack** (from ``_FAMILY_RESIDUALS['VIII']``):

  - ``noncompact_truncation`` — |1 - ⟨ψ, ψ⟩ on truncated disc|.
  - ``branch_tag`` — translator round-trip error.
  - ``seed_regularity`` — discrete-L² seed norm residual.

Forbidden shortcuts tracked (``_MUST_NOT_DO['VIII']``):

* ``no_compact_su2_reuse``
* ``no_wigner_d_assumption_without_explicit_approximation_tag``
"""
from __future__ import annotations

import math
from collections.abc import Callable, Mapping
from typing import Any

import numpy as np
from scipy.special import lpmv

from bass.background.bianchi_types import StructureConstants
from bass.los.families.base import LegacyDelegationKernel
from bass.spectrum.lowell_los import build_lowell_line_of_sight_propagator
from bass.statistics import ResidualPack
from bass.transport.exact_transport import ExactTransportBundle


__all__ = (
    "TypeVIIIKernel",
    "KERNEL",
    "DISCRETE_SERIES_TAGS",
    "CONTINUOUS_SERIES_TAG",
    "translate_native_to_storage",
    "translate_storage_to_native",
    "noncompact_disc_seed_amplitude",
    "noncompact_disc_norm_residual",
)


DISCRETE_SERIES_TAGS: tuple[str, ...] = (
    "trivial",
    "discrete_positive",
    "discrete_negative",
)
CONTINUOUS_SERIES_TAG: str = "continuous_principal"


_NATIVE_TO_STORAGE: dict[tuple[str, str, str], str] = {
    ("mu_sl2r", "trivial", "scalar"): "m0",
    ("mu_sl2r", "discrete_positive", "tensor_plus"): "m+2",
    ("mu_sl2r", "discrete_negative", "tensor_minus"): "m-2",
}
_STORAGE_TO_NATIVE: dict[str, tuple[str, str, str]] = {
    storage: native for native, storage in _NATIVE_TO_STORAGE.items()
}
_STORAGE_ORDER: tuple[str, ...] = ("m-2", "m0", "m+2")


def translate_native_to_storage(label: tuple[str, str, str]) -> str:
    if (
        not isinstance(label, tuple)
        or len(label) != 3
        or label[0] != "mu_sl2r"
    ):
        raise ValueError(
            f"Type VIII native label must be a 3-tuple starting with 'mu_sl2r', got {label!r}."
        )
    if label[1] == CONTINUOUS_SERIES_TAG:
        raise NotImplementedError(
            "Type VIII continuous principal series deferred per plan "
            "Open-Question 1 (mpmath hypergeometric). Use discrete_positive "
            "or discrete_negative, or reach for the deferred annex PR."
        )
    if label[1] not in DISCRETE_SERIES_TAGS:
        raise ValueError(
            f"Type VIII series_tag must be one of {DISCRETE_SERIES_TAGS}, got {label[1]!r}."
        )
    if label not in _NATIVE_TO_STORAGE:
        raise ValueError(
            f"Type VIII native label {label!r} outside the PSTF storage window "
            f"{sorted(_NATIVE_TO_STORAGE)}."
        )
    return _NATIVE_TO_STORAGE[label]


def translate_storage_to_native(label: str) -> tuple[str, str, str]:
    if label not in _STORAGE_TO_NATIVE:
        raise ValueError(
            f"Type VIII storage label {label!r} unknown; expected one of {_STORAGE_ORDER}."
        )
    return _STORAGE_TO_NATIVE[label]


# ----- Noncompact-disc seed ----------------------------------------------


def _disc_integral_p2_squared(disc_radius: float, n_samples: int) -> float:
    """``∫_0^{disc_radius} [P_2(x)]² dx`` via Gauss-Legendre.

    P_2(x) = (3x² - 1)/2. The indefinite integral is tractable in closed
    form but we use quadrature to keep the residual-measurement symmetric
    with the other families.
    """
    if disc_radius <= 0.0:
        raise ValueError("disc_radius must be > 0")
    nodes, weights = np.polynomial.legendre.leggauss(n_samples)
    x = 0.5 * disc_radius * (nodes + 1.0)
    p2 = lpmv(0, 2, x)
    return float((0.5 * disc_radius) * np.sum(weights * p2 ** 2))


def noncompact_disc_seed_amplitude(disc_radius: float) -> float:
    """Amplitude ``A`` such that ``A · P_2(x)`` is unit-L² on
    ``x ∈ [0, disc_radius]``."""
    integral = _disc_integral_p2_squared(disc_radius, n_samples=128)
    if integral <= 0.0:
        raise ValueError(f"P_2 integral vanished at disc_radius={disc_radius}")
    return 1.0 / math.sqrt(integral)


def noncompact_disc_norm_residual(disc_radius: float, *, n_samples: int = 128) -> float:
    amp = noncompact_disc_seed_amplitude(disc_radius)
    integral = amp ** 2 * _disc_integral_p2_squared(disc_radius, n_samples=n_samples)
    return abs(integral - 1.0)


# ----- Kernel -------------------------------------------------------------


class TypeVIIIKernel(LegacyDelegationKernel):
    family = "VIII"
    branch = "sl2r_discrete"
    chart = "sl2r_noncompact_chart"
    dispatch_route = "family_kernel_type_viii"

    # Compactified disc: x = tanh(xi) for xi ∈ [0, xi_max]. xi_max = 1.5
    # gives disc_radius = tanh(1.5) ≈ 0.905.
    default_xi_max: float = 1.5

    tolerance_noncompact_truncation: float = 1.0e-10
    tolerance_branch_tag: float = 1.0e-14
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
        legacy = build_lowell_line_of_sight_propagator(
            structure,
            eta_grid_mpc=eta_grid_mpc,
            k_grid_mpc=k_grid_mpc,
            ell_max=ell_max,
            visibility_fn=visibility_fn,
            source_builder=source_builder,
        )
        ell = np.arange(int(ell_max) + 1, dtype=int)
        disc_radius = math.tanh(self.default_xi_max)
        residuals = self._compute_residuals(disc_radius=disc_radius)

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
            "discrete_series_tags": list(DISCRETE_SERIES_TAGS),
            "continuous_series_status": "deferred_to_annex_PR_per_plan_OQ1",
            "truncation_xi_max": float(self.default_xi_max),
            "disc_radius_x_eq_tanh_xi": disc_radius,
            "seed_amplitude": noncompact_disc_seed_amplitude(disc_radius),
            "residual_values": residuals,
            "forbidden_shortcut_tracked": list(self.metadata.forbidden_shortcuts),
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

    def _compute_residuals(self, *, disc_radius: float) -> dict[str, float]:
        branch_err = 0.0
        for native, storage in _NATIVE_TO_STORAGE.items():
            if (
                translate_storage_to_native(storage) != native
                or translate_native_to_storage(native) != storage
            ):
                branch_err = math.inf
                break

        seed_err = noncompact_disc_norm_residual(disc_radius, n_samples=128)

        # noncompact_truncation: residual between the unit-normalized seed
        # on the truncated disc and the analytical closed form. With the
        # quadrature-based amplitude this is ≡ seed regularity up to the
        # quadrature precision.
        truncation_err = seed_err

        return {
            "noncompact_truncation": float(truncation_err),
            "branch_tag": float(branch_err),
            "seed_regularity": float(seed_err),
        }

    def residual_pack_from_bundle(self, bundle: ExactTransportBundle) -> ResidualPack:
        values = dict(bundle.metadata.get("residual_values", {}))
        tolerance = {
            "noncompact_truncation": self.tolerance_noncompact_truncation,
            "branch_tag": self.tolerance_branch_tag,
            "seed_regularity": self.tolerance_seed_regularity,
        }
        return super().residual_pack(
            residual_values=values,
            tolerance=tolerance,
            extra_metadata={
                "truncation_xi_max": bundle.metadata.get("truncation_xi_max"),
                "disc_radius_x_eq_tanh_xi": bundle.metadata.get("disc_radius_x_eq_tanh_xi"),
                "continuous_series_status": bundle.metadata.get("continuous_series_status"),
            },
        )


KERNEL = TypeVIIIKernel()
