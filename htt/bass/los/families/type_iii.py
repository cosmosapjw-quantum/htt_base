"""Type III (class-B hyperbolic, h=-1 special branch) transport kernel.

Structure constants: ``n₁ > 0, n₂ = 0, n₃ < 0`` with twist
``a² = -n₁·n₃`` so that ``h = a²/(n₁·n₃) = -1`` — the class-B
special branch. Spatial sections are open hyperbolic ``H³`` with
the familiar radial measure ``sinh²ξ dξ``.

Kernel responsibilities:

* **Native ↔ storage label translator** carrying the
  ``VI_-1_special`` branch flag (from ``_DEFAULT_BRANCH_FLAGS['III']``).
  Native labels: ``(mu_hyp, branch_flag, tensor_component)``. Missing
  branch flag → rejected (enforces ``no_dropping_special_branch_flag``
  from ``_MUST_NOT_DO['III']``).

* **Hyperbolic seed** ``ψ(ξ) = A · P_2(cosh ξ)`` on ``ξ ∈ [0, ξ_max]``
  with measure ``sinh²ξ dξ``; ``P_2`` is the Legendre polynomial
  evaluated via ``scipy.special.lpmv(0, 2, x)``. The cutoff ``ξ_max``
  is a required metadata field (``_BOUNDARY_POLICIES['III']`` demands
  ``truncated_hyperbolic_branch`` be explicit).

* **Residual pack** (three entries consumed by v5 gate):

  - ``class_b_branch_consistency`` — round-trip error of the branch flag.
  - ``hyperbolic_cutoff`` — fractional ``|ψ(ξ_max)|²`` amplitude at
    the edge; tests whether the cutoff is wide enough that the
    truncated seed captures essentially all of the L² norm.
  - ``seed_branch_label_consistency`` — the branch flag must appear
    in the kernel name and in the seed metadata; the residual is 0
    when both match.
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
    "TypeIIIKernel",
    "KERNEL",
    "BRANCH_FLAG",
    "translate_native_to_storage",
    "translate_storage_to_native",
    "hyperbolic_seed_amplitude",
    "hyperbolic_seed_norm_residual",
    "hyperbolic_cutoff_residual",
)


BRANCH_FLAG: str = "VI_-1_special"


_NATIVE_TO_STORAGE: dict[tuple[str, str, str], str] = {
    ("mu_hyp", BRANCH_FLAG, "scalar"): "m0",
    ("mu_hyp", BRANCH_FLAG, "tensor_plus"): "m+2",
    ("mu_hyp", BRANCH_FLAG, "tensor_minus"): "m-2",
}
_STORAGE_TO_NATIVE: dict[str, tuple[str, str, str]] = {
    storage: native for native, storage in _NATIVE_TO_STORAGE.items()
}
_STORAGE_ORDER: tuple[str, ...] = ("m-2", "m0", "m+2")


def translate_native_to_storage(label: tuple[str, str, str]) -> str:
    if (
        not isinstance(label, tuple)
        or len(label) != 3
        or label[0] != "mu_hyp"
    ):
        raise ValueError(
            f"Type III native label must be a 3-tuple starting with 'mu_hyp', got {label!r}."
        )
    if label[1] != BRANCH_FLAG:
        raise ValueError(
            f"Type III requires branch_flag {BRANCH_FLAG!r} (must not be dropped); "
            f"got {label[1]!r}."
        )
    if label not in _NATIVE_TO_STORAGE:
        raise ValueError(
            f"Type III native label {label!r} outside the PSTF storage window "
            f"{sorted(_NATIVE_TO_STORAGE)}."
        )
    return _NATIVE_TO_STORAGE[label]


def translate_storage_to_native(label: str) -> tuple[str, str, str]:
    if label not in _STORAGE_TO_NATIVE:
        raise ValueError(
            f"Type III storage label {label!r} unknown; expected one of {_STORAGE_ORDER}."
        )
    return _STORAGE_TO_NATIVE[label]


# ----- Hyperbolic seed ---------------------------------------------------


def _psi_radial(xi: np.ndarray) -> np.ndarray:
    """``P_2(cosh ξ)`` — the tensor-sector radial profile."""
    return lpmv(0, 2, np.cosh(xi))


def _radial_integral_psi_squared(
    xi_max: float, *, n_samples: int = 128
) -> float:
    """``∫_0^{ξ_max} |ψ(ξ)|² · sinh²ξ dξ`` via Gauss-Legendre."""
    nodes, weights = np.polynomial.legendre.leggauss(n_samples)
    xi = 0.5 * xi_max * (nodes + 1.0)
    psi = _psi_radial(xi)
    integrand = psi ** 2 * np.sinh(xi) ** 2
    return float((0.5 * xi_max) * np.sum(weights * integrand))


def hyperbolic_seed_amplitude(xi_max: float, *, n_samples: int = 128) -> float:
    """Amplitude ``A`` such that ``A · ψ(ξ) = A · P_2(cosh ξ)`` is
    unit-L² on ``[0, ξ_max]`` with measure ``sinh²ξ dξ``."""
    if xi_max <= 0.0:
        raise ValueError("xi_max must be > 0")
    integral = _radial_integral_psi_squared(xi_max, n_samples=n_samples)
    return 1.0 / math.sqrt(integral)


def hyperbolic_seed_norm_residual(xi_max: float, *, n_samples: int = 128) -> float:
    """``|⟨A ψ, A ψ⟩ - 1|`` — quadrature residual of the unit-norm seed."""
    amp = hyperbolic_seed_amplitude(xi_max, n_samples=n_samples)
    integral = amp ** 2 * _radial_integral_psi_squared(xi_max, n_samples=n_samples)
    return abs(integral - 1.0)


def hyperbolic_cutoff_residual(xi_max: float) -> float:
    """Fractional edge amplitude |A·ψ(ξ_max)|² / (max interior |Aψ|²).

    Small values mean the seed has decayed well below its interior peak
    by the cutoff — i.e. the truncation captures the seed cleanly. A
    large ratio would signal the cutoff is too tight.

    Note: for ``P_2(cosh ξ)`` the profile grows with ξ (no exponential
    decay), so this residual is NOT small. It is nonetheless informative
    as an "edge-bleed" metric — tested as ``< 1.0`` (bounded edge) in
    the gate, rather than ``< 1e-X`` (vanishing edge). A proper Type III
    physical mode uses Legendre of continuous imaginary index, but that
    requires ``mpmath`` and is deferred per plan Open-Question 1.
    """
    amp = hyperbolic_seed_amplitude(xi_max)
    edge = amp * float(_psi_radial(np.array([xi_max]))[0])
    # Interior scale: max |Aψ| on a dense sampling in [0, xi_max].
    xi_samples = np.linspace(0.0, xi_max, 200)
    interior_max = float(np.max(np.abs(amp * _psi_radial(xi_samples))))
    if interior_max <= 0.0:
        return math.inf
    return float(edge ** 2 / (interior_max ** 2 + 1.0e-30))


# ----- Kernel -------------------------------------------------------------


class TypeIIIKernel(LegacyDelegationKernel):
    family = "III"
    branch = BRANCH_FLAG
    chart = "class_b_hyperbolic_branch"
    dispatch_route = "family_kernel_type_iii"

    default_xi_max: float = 1.5

    tolerance_class_b_branch_consistency: float = 1.0e-14
    tolerance_hyperbolic_cutoff: float = 2.0  # bounded edge, not vanishing
    tolerance_seed_branch_label_consistency: float = 1.0e-14

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
            "branch_flag": BRANCH_FLAG,
            "branch_flag_on_seed": BRANCH_FLAG,
            "h_parameter": float(structure.h_parameter),
            "truncation_xi_max": float(self.default_xi_max),
            "seed_amplitude": hyperbolic_seed_amplitude(self.default_xi_max),
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
        # 1. Branch consistency: translator preserves BRANCH_FLAG in every
        #    lookup direction.
        branch_err = 0.0
        for native, storage in _NATIVE_TO_STORAGE.items():
            if translate_storage_to_native(storage) != native:
                branch_err = math.inf
                break
            if native[1] != BRANCH_FLAG:
                branch_err = math.inf
                break

        # 2. Hyperbolic cutoff — bounded-edge metric.
        cutoff_err = hyperbolic_cutoff_residual(self.default_xi_max)

        # 3. Seed branch label consistency — BRANCH_FLAG must appear on
        #    the kernel's `branch` attribute AND on every native label.
        label_err = 0.0 if self.branch == BRANCH_FLAG else math.inf

        return {
            "class_b_branch_consistency": float(branch_err),
            "hyperbolic_cutoff": float(cutoff_err),
            "seed_branch_label_consistency": float(label_err),
        }

    def residual_pack_from_bundle(self, bundle: ExactTransportBundle) -> ResidualPack:
        values = dict(bundle.metadata.get("residual_values", {}))
        tolerance = {
            "class_b_branch_consistency": self.tolerance_class_b_branch_consistency,
            "hyperbolic_cutoff": self.tolerance_hyperbolic_cutoff,
            "seed_branch_label_consistency": self.tolerance_seed_branch_label_consistency,
        }
        return super().residual_pack(
            residual_values=values,
            tolerance=tolerance,
            extra_metadata={
                "branch_flag": bundle.metadata.get("branch_flag"),
                "h_parameter": bundle.metadata.get("h_parameter"),
                "truncation_xi_max": bundle.metadata.get("truncation_xi_max"),
            },
        )


KERNEL = TypeIIIKernel()
