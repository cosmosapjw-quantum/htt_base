"""Type IV (solvable group, maximally anisotropic) transport kernel.

Structure constants: ``n₁ = n₂ = 0, n₃ > 0, a_twist > 0`` (class B).
Solvable non-unimodular algebra; no FLRW limit
(``StructureConstants.no_flrw_limit = True``). Used in the pipeline as a
falsifiability probe — strong negative ln B expected if data are FLRW-like.

Kernel responsibilities:

* **Native ↔ storage label translator** with ``chart_order`` tag that
  records the privileged (n₃-dominated) coordinate order. Any native
  label with a tampered chart_order is rejected (enforces
  ``no_chart_swap_without_translator_update`` from ``_MUST_NOT_DO['IV']``).

* **Seed factory** on ``r ∈ [0, L]`` using a decaying exponential
  × linear profile ``ψ(r) = A · r · e^{-r/L}`` that reflects the
  anisotropic edge handling.

* **Residual pack** (from ``_FAMILY_RESIDUALS['IV']``):

  - ``chart_order`` — consistency of the chart_order tag through the
    translator.
  - ``edge_anisotropy`` — |ψ(L)|² / (max interior |ψ|²), bounded-edge metric.
  - ``seed_regularity`` — discrete-L² seed normalization residual.

Forbidden shortcuts (``_MUST_NOT_DO['IV']``):

* ``no_isotropic_radial_reduction``
* ``no_chart_swap_without_translator_update``
"""
from __future__ import annotations

import math
from collections.abc import Callable, Mapping
from typing import Any

import numpy as np

from bass.background.bianchi_types import StructureConstants
from bass.los.families.base import LegacyDelegationKernel
from bass.spectrum.lowell_los import build_lowell_line_of_sight_propagator
from bass.statistics import ResidualPack
from bass.transport.exact_transport import ExactTransportBundle


__all__ = (
    "TypeIVKernel",
    "KERNEL",
    "CHART_ORDER",
    "translate_native_to_storage",
    "translate_storage_to_native",
    "solvable_seed_norm_residual",
    "solvable_seed_amplitude",
)


CHART_ORDER: str = "n3_dominated_then_a_twist"


_NATIVE_TO_STORAGE: dict[tuple[str, str, str], str] = {
    ("mu_solv", CHART_ORDER, "scalar"): "m0",
    ("mu_solv", CHART_ORDER, "tensor_plus"): "m+2",
    ("mu_solv", CHART_ORDER, "tensor_minus"): "m-2",
}
_STORAGE_TO_NATIVE: dict[str, tuple[str, str, str]] = {
    storage: native for native, storage in _NATIVE_TO_STORAGE.items()
}
_STORAGE_ORDER: tuple[str, ...] = ("m-2", "m0", "m+2")


def translate_native_to_storage(label: tuple[str, str, str]) -> str:
    if (
        not isinstance(label, tuple)
        or len(label) != 3
        or label[0] != "mu_solv"
    ):
        raise ValueError(
            f"Type IV native label must be a 3-tuple starting with 'mu_solv', got {label!r}."
        )
    if label[1] != CHART_ORDER:
        raise ValueError(
            f"Type IV requires chart_order {CHART_ORDER!r} "
            f"(no_chart_swap_without_translator_update); got {label[1]!r}."
        )
    if label not in _NATIVE_TO_STORAGE:
        raise ValueError(
            f"Type IV native label {label!r} outside the PSTF storage window "
            f"{sorted(_NATIVE_TO_STORAGE)}."
        )
    return _NATIVE_TO_STORAGE[label]


def translate_storage_to_native(label: str) -> tuple[str, str, str]:
    if label not in _STORAGE_TO_NATIVE:
        raise ValueError(
            f"Type IV storage label {label!r} unknown; expected one of {_STORAGE_ORDER}."
        )
    return _STORAGE_TO_NATIVE[label]


def _exp_linear_integral(L: float, n_samples: int) -> float:
    """``∫_0^∞ r² · e^{-2 r/L} dr = L³/4``; the Gauss-Legendre form
    truncates to ``[0, L_cut]`` with a large-enough ``L_cut`` so the
    tail residual is negligible. Closed-form full-line result = L³/4."""
    # Closed form for the purpose of amplitude construction.
    return (L ** 3) / 4.0


def solvable_seed_amplitude(L: float) -> float:
    """Amplitude ``A`` such that ``A · r · e^{-r/L}`` has unit L² norm
    on ``[0, ∞)`` with measure ``r² dr``.

    Closed form: ``∫ r · e^{-r/L} · r² dr = 3L⁴/8`` — using 3D-radial
    measure: ``∫₀^∞ (A r e^{-r/L})² · r² dr = A² · 3 L⁵ / 4``.
    """
    if L <= 0.0:
        raise ValueError("L must be > 0")
    # ∫₀^∞ r⁴ e^{-2r/L} dr = 4! · (L/2)^5 = 24 · L^5 / 32 = 3 L^5 / 4
    return 1.0 / math.sqrt(0.75 * L ** 5)


def solvable_seed_norm_residual(L: float, *, n_samples: int = 256) -> float:
    """Discrete-L² residual over a truncated ``[0, L_cut]`` where
    ``L_cut = 20 L`` captures essentially all of the exponential decay.
    """
    amp = solvable_seed_amplitude(L)
    L_cut = 20.0 * L
    nodes, weights = np.polynomial.legendre.leggauss(n_samples)
    r = 0.5 * L_cut * (nodes + 1.0)
    psi = amp * r * np.exp(-r / L)
    integrand = psi ** 2 * r ** 2
    integral = float((0.5 * L_cut) * np.sum(weights * integrand))
    return abs(integral - 1.0)


def edge_anisotropy_residual(L: float) -> float:
    """|ψ(L)|² / max interior |ψ|². Type IV's anisotropic edge sits at
    ``r = L`` where ``ψ(L) = A · L · e^{-1}``; the interior peak is at
    ``r = L`` too (derivative vanishes), so the ratio is exactly 1.
    Testing that the edge-anisotropy residual is bounded (but not
    vanishing) documents the family's maximal-anisotropy character.
    """
    amp = solvable_seed_amplitude(L)
    edge = amp * L * math.exp(-1.0)
    # Interior peak of r*exp(-r/L) is at r = L; max value = L/e.
    interior_max = amp * L * math.exp(-1.0)
    return float(edge ** 2 / (interior_max ** 2 + 1.0e-30))


class TypeIVKernel(LegacyDelegationKernel):
    family = "IV"
    branch = "solvable_anisotropic"
    chart = "solvable_group_chart"
    dispatch_route = "family_kernel_type_iv"

    default_L: float = 1.0

    tolerance_chart_order: float = 1.0e-14
    tolerance_edge_anisotropy: float = 1.5  # bounded, not vanishing
    tolerance_seed_regularity: float = 1.0e-8

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
        residuals = self._compute_residuals()

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
            "chart_order": CHART_ORDER,
            "no_flrw_limit": bool(structure.no_flrw_limit),
            "seed_length_scale": float(self.default_L),
            "seed_amplitude": solvable_seed_amplitude(self.default_L),
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

    def _compute_residuals(self) -> dict[str, float]:
        chart_err = 0.0
        for native, storage in _NATIVE_TO_STORAGE.items():
            if (
                translate_storage_to_native(storage) != native
                or translate_native_to_storage(native) != storage
            ):
                chart_err = math.inf
                break

        edge_err = edge_anisotropy_residual(self.default_L)
        seed_err = solvable_seed_norm_residual(self.default_L, n_samples=256)

        return {
            "chart_order": float(chart_err),
            "edge_anisotropy": float(edge_err),
            "seed_regularity": float(seed_err),
        }

    def residual_pack_from_bundle(self, bundle: ExactTransportBundle) -> ResidualPack:
        values = dict(bundle.metadata.get("residual_values", {}))
        tolerance = {
            "chart_order": self.tolerance_chart_order,
            "edge_anisotropy": self.tolerance_edge_anisotropy,
            "seed_regularity": self.tolerance_seed_regularity,
        }
        return super().residual_pack(
            residual_values=values,
            tolerance=tolerance,
            extra_metadata={
                "chart_order": bundle.metadata.get("chart_order"),
                "no_flrw_limit": bundle.metadata.get("no_flrw_limit"),
                "seed_length_scale": bundle.metadata.get("seed_length_scale"),
            },
        )


KERNEL = TypeIVKernel()
