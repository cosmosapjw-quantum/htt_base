"""Type VII_0 (helical Euclidean, h=0) transport kernel.

Structure constants: ``n₁ > 0, n₂ = 0, n₃ > 0, a_twist = 0`` — class A
with a helical/screw embedding on a flat isotropic-like background. FLRW
limit exists.

Kernel responsibilities:

* **Native ↔ storage label translator** carrying an explicit
  ``helicity ∈ {"+", "-"}`` tag. Scalar projects to ``m0``; the two
  helicities project to ``m±2``.

* **Seed factory** uses the spherical Bessel ``j_ell`` on
  ``r ∈ [0, R]`` — a helical Euclidean mode with explicit radial
  cutoff. Normalization via ``scipy.special.spherical_jn``.

* **Residual pack** entries (from ``_FAMILY_RESIDUALS['VII_0']``):

  - ``helical_anchor_limit`` — |transfer_T[m0] - Type I m0| over (k, ell).
  - ``label_translator_roundtrip`` — exact, 0.
  - ``seed_regularity`` — |⟨seed, seed⟩ - 1|.

Forbidden shortcuts (``_MUST_NOT_DO['VII_0']``):

* ``no_hidden_branch_choice`` — kernel name carries explicit h=0 tag
* ``no_local_boost_folded_into_backend`` — boost is a separate layer
"""
from __future__ import annotations

import math
from collections.abc import Callable, Mapping
from typing import Any

import numpy as np
from scipy.special import spherical_jn

from bass.background.bianchi_types import StructureConstants, type_i_constants
from bass.los.families.base import LegacyDelegationKernel
from bass.spectrum.lowell_los import build_lowell_line_of_sight_propagator
from bass.statistics import ResidualPack
from bass.transport.exact_transport import ExactTransportBundle


__all__ = (
    "TypeVII0Kernel",
    "KERNEL",
    "translate_native_to_storage",
    "translate_storage_to_native",
    "spherical_bessel_seed_amplitude",
    "spherical_bessel_seed_norm_residual",
)


_NATIVE_TO_STORAGE: dict[tuple[str, str, str], str] = {
    ("mu_VII0", "0", "scalar"): "m0",
    ("mu_VII0", "+", "tensor_plus"): "m+2",
    ("mu_VII0", "-", "tensor_minus"): "m-2",
}
_STORAGE_TO_NATIVE: dict[str, tuple[str, str, str]] = {
    storage: native for native, storage in _NATIVE_TO_STORAGE.items()
}
_STORAGE_ORDER: tuple[str, ...] = ("m-2", "m0", "m+2")


def translate_native_to_storage(label: tuple[str, str, str]) -> str:
    if (
        not isinstance(label, tuple)
        or len(label) != 3
        or label[0] != "mu_VII0"
    ):
        raise ValueError(
            f"Type VII_0 native label must be a 3-tuple starting with 'mu_VII0', got {label!r}."
        )
    if label not in _NATIVE_TO_STORAGE:
        raise ValueError(
            f"Type VII_0 native label {label!r} outside the PSTF storage window "
            f"{sorted(_NATIVE_TO_STORAGE)}."
        )
    return _NATIVE_TO_STORAGE[label]


def translate_storage_to_native(label: str) -> tuple[str, str, str]:
    if label not in _STORAGE_TO_NATIVE:
        raise ValueError(
            f"Type VII_0 storage label {label!r} unknown; expected one of {_STORAGE_ORDER}."
        )
    return _STORAGE_TO_NATIVE[label]


def _spherical_bessel_integral(ell: int, k: float, R: float, n_samples: int = 128) -> float:
    """``∫_0^R [j_ell(k r)]² r² dr`` via Gauss-Legendre."""
    nodes, weights = np.polynomial.legendre.leggauss(n_samples)
    r = 0.5 * R * (nodes + 1.0)
    integrand = spherical_jn(ell, k * r) ** 2 * r ** 2
    return float((0.5 * R) * np.sum(weights * integrand))


def spherical_bessel_seed_amplitude(ell: int, k: float, R: float) -> float:
    """Amplitude ``A`` such that ``A · j_ell(k r)`` has unit L² norm
    on the ball ``r ∈ [0, R]`` with measure ``r² dr``."""
    if R <= 0.0 or k <= 0.0:
        raise ValueError("R and k must be > 0")
    integral = _spherical_bessel_integral(ell, k, R)
    if integral <= 0.0:
        raise ValueError(f"spherical Bessel integral vanished at ell={ell}, k={k}, R={R}")
    return 1.0 / math.sqrt(integral)


def spherical_bessel_seed_norm_residual(
    ell: int, k: float, R: float, *, n_samples: int = 128
) -> float:
    amp = spherical_bessel_seed_amplitude(ell, k, R)
    integral = amp ** 2 * _spherical_bessel_integral(ell, k, R, n_samples=n_samples)
    return abs(integral - 1.0)


class TypeVII0Kernel(LegacyDelegationKernel):
    family = "VII_0"
    branch = "helical_euclidean"
    chart = "helical_euclidean_chart"
    dispatch_route = "family_kernel_type_vii_0"

    default_R: float = 1.0
    default_k_seed: float = 1.0
    default_ell_seed: int = 2

    tolerance_anchor_limit: float = 5.0e-2
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
        legacy_vii0 = build_lowell_line_of_sight_propagator(
            structure,
            eta_grid_mpc=eta_grid_mpc,
            k_grid_mpc=k_grid_mpc,
            ell_max=ell_max,
            visibility_fn=visibility_fn,
            source_builder=source_builder,
        )
        legacy_i = build_lowell_line_of_sight_propagator(
            type_i_constants(),
            eta_grid_mpc=eta_grid_mpc,
            k_grid_mpc=k_grid_mpc,
            ell_max=ell_max,
            visibility_fn=visibility_fn,
            source_builder=source_builder,
        )
        ell = np.arange(int(ell_max) + 1, dtype=int)
        residuals = self._compute_residuals(
            t_vii0=np.asarray(legacy_vii0["transfer_T"]),
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
            "helicity_tags": ["0", "+", "-"],
            "radial_cutoff_R": float(self.default_R),
            "seed_basis": "spherical_jn",
            "h_parameter": 0.0,
            "residual_values": residuals,
            "forbidden_shortcut_tracked": list(self.metadata.forbidden_shortcuts),
        }
        return ExactTransportBundle(
            family=self.family,
            tier="A",
            dispatch_route=self.dispatch_route,
            transfer_T=np.asarray(legacy_vii0["transfer_T"]),
            transfer_E=np.asarray(legacy_vii0["transfer_E"]),
            transfer_B=np.asarray(legacy_vii0["transfer_B"]),
            propagator_matrix=np.asarray(legacy_vii0["propagator_matrix"]),
            ell=ell,
            k_grid_mpc=np.asarray(k_grid_mpc, dtype=float),
            eta_grid_mpc=np.asarray(eta_grid_mpc, dtype=float),
            metadata=meta,
            raw_payload=legacy_vii0,
        )

    def _compute_residuals(
        self, *, t_vii0: np.ndarray, t_i: np.ndarray
    ) -> dict[str, float]:
        roundtrip_err = 0.0
        for native, storage in _NATIVE_TO_STORAGE.items():
            if (
                translate_storage_to_native(storage) != native
                or translate_native_to_storage(native) != storage
            ):
                roundtrip_err = math.inf
                break

        seed_err = spherical_bessel_seed_norm_residual(
            self.default_ell_seed, self.default_k_seed, self.default_R, n_samples=128
        )

        if t_vii0.ndim != 3 or t_vii0.shape != t_i.shape or t_vii0.shape[-1] != 3:
            anchor_err = math.inf
        else:
            diff = t_vii0[..., 1] - t_i[..., 1]
            scale = max(float(np.max(np.abs(t_i[..., 1]))), 1.0e-30)
            anchor_err = float(np.max(np.abs(diff)) / scale)

        return {
            "helical_anchor_limit": float(anchor_err),
            "label_translator_roundtrip": float(roundtrip_err),
            "seed_regularity": float(seed_err),
        }

    def residual_pack_from_bundle(self, bundle: ExactTransportBundle) -> ResidualPack:
        values = dict(bundle.metadata.get("residual_values", {}))
        tolerance = {
            "helical_anchor_limit": self.tolerance_anchor_limit,
            "label_translator_roundtrip": self.tolerance_translator_roundtrip,
            "seed_regularity": self.tolerance_seed_regularity,
        }
        return super().residual_pack(
            residual_values=values,
            tolerance=tolerance,
            extra_metadata={
                "radial_cutoff_R": bundle.metadata.get("radial_cutoff_R"),
                "h_parameter": bundle.metadata.get("h_parameter"),
            },
        )


KERNEL = TypeVII0Kernel()
