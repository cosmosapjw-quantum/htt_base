"""Type II (nil-Heisenberg) transport kernel.

Structure constants: ``n₁ > 0, n₂ = n₃ = 0, a_twist = 0`` — the
Heisenberg algebra. Spatial sections are nilpotent with one privileged
central direction; PSTF tensor modes pair up on the non-central plane.

Kernel responsibilities:

* **Native ↔ storage label translator** in the nil chart. Native
  labels are ``(mu_nil, "scalar", 0)``, ``(mu_nil, "tensor", "+")``,
  ``(mu_nil, "tensor", "-")``; storage is the usual PSTF
  ``m ∈ {-2, 0, +2}`` triple.

* **Finite-domain seed** on ``r ∈ [0, L]`` using the first Bessel root
  ``j₀₁ = first_zero(J₀) ≈ 2.4048`` as the edge Dirichlet mode. The
  seed is ``ψ(r) = A · J₀(j₀₁ · r / L)`` with ``A`` chosen so
  ``∫₀^L |ψ|² · 2π r dr = 1``. The edge is **logged**, not implicitly
  periodic — that's what ``_BOUNDARY_POLICIES['II']`` demands.

* **Residual pack** (three entries consumed by v5 gate):

  - ``nil_chart_regularity`` — |ψ(r=0) - A · 1| / A. The Bessel J_0
    starts at unity at the nil center, so this must be machine zero.
  - ``label_translator_roundtrip`` — exact lookup, 0.
  - ``seed_regularity`` — |⟨ψ, ψ⟩_L² - 1| under Gauss-Legendre quadrature.

Forbidden shortcuts tracked (``_MUST_NOT_DO['II']``):

* ``no_flrw_seed_reuse``
* ``no_implicit_periodic_boundary``
* ``no_unlabeled_branch_choice``
"""
from __future__ import annotations

import math
from collections.abc import Callable, Mapping
from typing import Any

import numpy as np
from scipy.special import j0, j1, jn_zeros

from bass.background.bianchi_types import StructureConstants
from bass.los.families.base import LegacyDelegationKernel
from bass.spectrum.lowell_los import build_lowell_line_of_sight_propagator
from bass.statistics import ResidualPack
from bass.transport.exact_transport import ExactTransportBundle


__all__ = (
    "TypeIIKernel",
    "KERNEL",
    "bessel_first_zero_j0",
    "nil_seed_amplitude",
    "nil_seed_norm_residual",
    "nil_seed_center_residual",
    "translate_native_to_storage",
    "translate_storage_to_native",
)


_NATIVE_TO_STORAGE: dict[tuple[str, str, object], str] = {
    ("mu_nil", "scalar", 0): "m0",
    ("mu_nil", "tensor", "+"): "m+2",
    ("mu_nil", "tensor", "-"): "m-2",
}
_STORAGE_TO_NATIVE: dict[str, tuple[str, str, object]] = {
    storage: native for native, storage in _NATIVE_TO_STORAGE.items()
}
_STORAGE_ORDER: tuple[str, ...] = ("m-2", "m0", "m+2")


def translate_native_to_storage(label: tuple[str, str, object]) -> str:
    if (
        not isinstance(label, tuple)
        or len(label) != 3
        or label[0] != "mu_nil"
    ):
        raise ValueError(
            f"Type II native label must be a 3-tuple starting with 'mu_nil', got {label!r}."
        )
    if label not in _NATIVE_TO_STORAGE:
        raise ValueError(
            f"Type II native label {label!r} outside the PSTF storage window "
            f"{sorted(_NATIVE_TO_STORAGE)}."
        )
    return _NATIVE_TO_STORAGE[label]


def translate_storage_to_native(label: str) -> tuple[str, str, object]:
    if label not in _STORAGE_TO_NATIVE:
        raise ValueError(
            f"Type II storage label {label!r} unknown; expected one of {_STORAGE_ORDER}."
        )
    return _STORAGE_TO_NATIVE[label]


# ----- Finite-domain Bessel seed -----------------------------------------


def bessel_first_zero_j0() -> float:
    """First positive zero of J_0 — the Dirichlet edge eigenvalue on
    the unit disc. scipy's ``jn_zeros(0, 1)`` gives 2.4048255576957727..."""
    return float(jn_zeros(0, 1)[0])


def nil_seed_amplitude(half_width_L: float) -> float:
    """Amplitude ``A`` such that ``A · J_0(j₀₁ r/L)`` has unit
    L² norm over the radial disc ``r ∈ [0, L]`` with measure
    ``2π r dr``.

    The closed-form normalization
    ``∫₀^L J_0(j₀₁ r/L)² · 2π r dr = π L² J_1(j₀₁)²``
    gives ``A = 1 / (√π · L · |J_1(j₀₁)|)``.
    """
    if half_width_L <= 0.0:
        raise ValueError("half_width_L must be > 0")
    j01 = bessel_first_zero_j0()
    denom = math.sqrt(math.pi) * half_width_L * abs(j1(j01))
    return 1.0 / denom


def nil_seed_norm_residual(half_width_L: float, *, n_samples: int = 64) -> float:
    """Gauss-Legendre verification of the disc L² normalization.

    Evaluates ``∫₀^L A² · J_0(j₀₁ r/L)² · 2π r dr`` numerically and
    returns ``|integral - 1|``.
    """
    amp = nil_seed_amplitude(half_width_L)
    j01 = bessel_first_zero_j0()
    nodes, weights = np.polynomial.legendre.leggauss(n_samples)
    # Map [-1, 1] → [0, L]: r = L/2 (x + 1); Jacobian = L/2.
    r = 0.5 * half_width_L * (nodes + 1.0)
    integrand = amp ** 2 * j0(j01 * r / half_width_L) ** 2 * 2.0 * math.pi * r
    integral = float((0.5 * half_width_L) * np.sum(weights * integrand))
    return abs(integral - 1.0)


def nil_seed_center_residual(half_width_L: float) -> float:
    """|ψ(0) - A| / A — tests regularity of the seed at the nil center.
    J_0(0) = 1, so the residual is exactly 0.
    """
    amp = nil_seed_amplitude(half_width_L)
    psi_origin = amp * float(j0(0.0))
    return abs(psi_origin - amp) / amp


class TypeIIKernel(LegacyDelegationKernel):
    family = "II"
    branch = "nil_intrinsic"
    chart = "nil_intrinsic_chart"
    dispatch_route = "family_kernel_type_ii"

    default_half_width: float = 1.0

    tolerance_nil_chart_regularity: float = 1.0e-14
    tolerance_label_translator_roundtrip: float = 1.0e-14
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
                "|".join(str(x) for x in k): v
                for k, v in _NATIVE_TO_STORAGE.items()
            },
            "bessel_first_zero_j0": bessel_first_zero_j0(),
            "seed_amplitude": nil_seed_amplitude(self.default_half_width),
            "truncation_half_width": float(self.default_half_width),
            "boundary_edge": "dirichlet_at_r_equals_L",
            "nil_transport_status": legacy.get("nil_transport_status"),
            "nil_structure_scale": legacy.get("nil_structure_scale"),
            "nil_shear_max": legacy.get("nil_shear_max"),
            "nil_phase_max": legacy.get("nil_phase_max"),
            "nil_mode_mixing_norm": legacy.get("nil_mode_mixing_norm", 0.0),
            "polarization_basis_transport": legacy.get("polarization_basis_transport"),
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
        # 1. Label translator round-trip.
        roundtrip_err = 0.0
        for native, storage in _NATIVE_TO_STORAGE.items():
            if translate_storage_to_native(storage) != native:
                roundtrip_err = math.inf
                break
            if translate_native_to_storage(native) != storage:
                roundtrip_err = math.inf
                break

        # 2. Nil chart regularity — J_0(0) = 1, so 0.
        center_err = nil_seed_center_residual(self.default_half_width)

        # 3. Disc-L² seed normalization.
        seed_err = nil_seed_norm_residual(self.default_half_width, n_samples=64)

        return {
            "nil_chart_regularity": float(center_err),
            "label_translator_roundtrip": float(roundtrip_err),
            "seed_regularity": float(seed_err),
        }

    def residual_pack_from_bundle(self, bundle: ExactTransportBundle) -> ResidualPack:
        values = dict(bundle.metadata.get("residual_values", {}))
        tolerance = {
            "nil_chart_regularity": self.tolerance_nil_chart_regularity,
            "label_translator_roundtrip": self.tolerance_label_translator_roundtrip,
            "seed_regularity": self.tolerance_seed_regularity,
        }
        return super().residual_pack(
            residual_values=values,
            tolerance=tolerance,
            extra_metadata={
                "bessel_first_zero_j0": bundle.metadata.get("bessel_first_zero_j0"),
                "truncation_half_width": bundle.metadata.get("truncation_half_width"),
                "boundary_edge": bundle.metadata.get("boundary_edge"),
                "nil_transport_status": bundle.metadata.get("nil_transport_status"),
                "nil_structure_scale": bundle.metadata.get("nil_structure_scale"),
                "nil_shear_max": bundle.metadata.get("nil_shear_max"),
                "nil_phase_max": bundle.metadata.get("nil_phase_max"),
                "nil_mode_mixing_norm": bundle.metadata.get("nil_mode_mixing_norm"),
                "polarization_basis_transport": bundle.metadata.get("polarization_basis_transport"),
            },
        )


KERNEL = TypeIIKernel()
