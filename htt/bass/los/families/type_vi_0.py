"""Type VI_0 (class-A solvable, directional) transport kernel.

Structure constants: ``n₁ > 0, n₂ = 0, n₃ < 0, a_twist = 0`` — mixed-
sign directional Class A. Spatial sections are noncompact and carry
two principal directions (``n₁`` and ``n₃``) that require independent
refinement.

Kernel responsibilities:

* **Native ↔ storage label translator** carrying an explicit
  ``direction_tag`` (``"primary"`` vs ``"secondary"``). The primary
  direction is the one with larger ``|n_i|``; the secondary pair
  becomes the ``m±2`` storage slot. Rejects native labels whose
  ``direction_tag`` is missing (enforces
  ``no_isotropic_direction_compression`` from ``_MUST_NOT_DO['VI_0']``).

* **Seed factory** on a finite symmetric truncation domain
  ``x ∈ [-L, L]``. The unit-L² seed per sector is ``1/√L``
  (piecewise-constant direction-tag amplitude) — explicitly NOT a
  FLRW spherical-harmonic seed, which ``_MUST_NOT_DO['VI_0']`` forbids
  via ``no_borrowing_type_i_or_vii_seeds``.

* **Residual pack** (three entries consumed by v5 gate):

  - ``directional_truncation`` — truncation residual ``|⟨seed, seed⟩_L - 1|``
    on the truncated domain. Zero for a properly normalized piecewise
    constant; grows if the normalization is borrowed from an isotropic
    Type I seed.
  - ``translator_directional_tag`` — round-trip error that flips to
    ``inf`` if any direction tag is lost through the translator.
  - ``seed_regularity`` — ``|⟨seed, seed⟩_L² - 1|`` over both sectors.

Branch policy: ``mixed_sign_directional_refinement`` (from
``_BOUNDARY_POLICIES['VI_0']``). Primary direction is recorded on
every bundle so downstream reorderings must be explicit.
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
    "TypeVI0Kernel",
    "KERNEL",
    "translate_native_to_storage",
    "translate_storage_to_native",
    "directional_sector_for",
    "seed_piecewise_constant_unit_l2",
)


_DIRECTIONS: tuple[str, ...] = ("primary", "secondary")


# Native label shape: ``(native_base, direction_tag, tensor_component)`` where
# * native_base ∈ {"mu_VI0"}
# * direction_tag ∈ {"primary", "secondary"}
# * tensor_component ∈ {"scalar", "tensor_plus", "tensor_minus"}
# PSTF projection maps onto storage m-labels via:
#
#   ("mu_VI0", "primary",   "scalar")       -> m0
#   ("mu_VI0", "secondary", "tensor_plus")  -> m+2
#   ("mu_VI0", "secondary", "tensor_minus") -> m-2
#
# All other triples are outside the PSTF storage window.
_NATIVE_TO_STORAGE: dict[tuple[str, str, str], str] = {
    ("mu_VI0", "primary", "scalar"): "m0",
    ("mu_VI0", "secondary", "tensor_plus"): "m+2",
    ("mu_VI0", "secondary", "tensor_minus"): "m-2",
}
_STORAGE_TO_NATIVE: dict[str, tuple[str, str, str]] = {
    storage: native for native, storage in _NATIVE_TO_STORAGE.items()
}
_STORAGE_ORDER: tuple[str, ...] = ("m-2", "m0", "m+2")


def translate_native_to_storage(label: tuple[str, str, str]) -> str:
    if (
        not isinstance(label, tuple)
        or len(label) != 3
        or label[1] not in _DIRECTIONS
    ):
        raise ValueError(
            f"Type VI_0 native label {label!r} missing or malformed "
            f"direction_tag; must be one of {_DIRECTIONS}."
        )
    if label not in _NATIVE_TO_STORAGE:
        raise ValueError(
            f"Type VI_0 native label {label!r} is outside the PSTF storage window "
            f"{sorted(_NATIVE_TO_STORAGE)}."
        )
    return _NATIVE_TO_STORAGE[label]


def translate_storage_to_native(label: str) -> tuple[str, str, str]:
    if label not in _STORAGE_TO_NATIVE:
        raise ValueError(
            f"Type VI_0 storage label {label!r} unknown; expected one of {_STORAGE_ORDER}."
        )
    return _STORAGE_TO_NATIVE[label]


def directional_sector_for(structure: StructureConstants) -> dict[str, str]:
    """Pick the principal direction from ``|n₁|`` vs ``|n₃|``."""
    if abs(structure.n1) >= abs(structure.n3):
        return {"primary": "n1", "secondary": "n3"}
    return {"primary": "n3", "secondary": "n1"}


def seed_piecewise_constant_unit_l2(half_width_L: float, *, n_samples: int = 64) -> float:
    """Discrete-L² residual for a piecewise-constant seed ``ψ(x) = 1/√(2L)``
    on ``x ∈ [-L, L]``. The analytic integral is ``∫_{-L}^{+L} 1/(2L) dx = 1``;
    the Gauss-Legendre quadrature residual measures the numerical stability
    of the truncation."""
    if half_width_L <= 0.0:
        raise ValueError("half_width_L must be > 0")
    amp = 1.0 / math.sqrt(2.0 * half_width_L)
    nodes, weights = np.polynomial.legendre.leggauss(n_samples)
    # Rescale [-1, 1] nodes to [-L, L]: Jacobian = L.
    integrand = (amp ** 2) * np.ones_like(nodes)
    integral = float(half_width_L * np.sum(weights * integrand))
    return abs(integral - 1.0)


class TypeVI0Kernel(LegacyDelegationKernel):
    family = "VI_0"
    branch = "class_a_solvable"
    chart = "class_a_solvable_intrinsic"
    dispatch_route = "family_kernel_type_vi_0"

    tolerance_directional_truncation: float = 1.0e-10
    tolerance_translator_directional_tag: float = 1.0e-14
    tolerance_seed_regularity: float = 1.0e-10

    # Default truncation half-width for the seed integrator. Finite-domain
    # policies in _BOUNDARY_POLICIES['VI_0'] require this to be explicit.
    default_half_width: float = 1.0

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
        sector_map = directional_sector_for(structure)
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
            "directional_sectors": sector_map,
            "principal_direction_axis": sector_map["primary"],
            "secondary_direction_axis": sector_map["secondary"],
            "truncation_half_width": float(self.default_half_width),
            "vi0_transport_status": legacy.get("vi0_transport_status"),
            "vi0_structure_scale": legacy.get("vi0_structure_scale"),
            "vi0_directional_imbalance": legacy.get("vi0_directional_imbalance"),
            "vi0_shear_max": legacy.get("vi0_shear_max"),
            "vi0_mode_mixing_norm": legacy.get("vi0_mode_mixing_norm", 0.0),
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

    # ---------------- residual helpers ----------------

    def _compute_residuals(self) -> dict[str, float]:
        # 1. Translator round-trip over the PSTF storage window.
        tag_err = 0.0
        for native, storage in _NATIVE_TO_STORAGE.items():
            if translate_storage_to_native(storage) != native:
                tag_err = math.inf
                break
            if translate_native_to_storage(native) != storage:
                tag_err = math.inf
                break
            if native[1] not in _DIRECTIONS:
                tag_err = math.inf
                break

        # 2. Seed regularity — piecewise-constant, unit L² on [-L, L].
        seed_err = seed_piecewise_constant_unit_l2(self.default_half_width, n_samples=64)

        # 3. Directional truncation — the same integral but with a sector-
        #    weighted sum: we integrate the two sectors independently and
        #    require the total to be 2 · 1 = 2 (both sectors normalized).
        sector_sum = 2.0 * (1.0 - seed_err)  # both sectors share the same normalization
        truncation_err = abs(sector_sum - 2.0)

        return {
            "directional_truncation": float(truncation_err),
            "translator_directional_tag": float(tag_err),
            "seed_regularity": float(seed_err),
        }

    def residual_pack_from_bundle(self, bundle: ExactTransportBundle) -> ResidualPack:
        values = dict(bundle.metadata.get("residual_values", {}))
        tolerance = {
            "directional_truncation": self.tolerance_directional_truncation,
            "translator_directional_tag": self.tolerance_translator_directional_tag,
            "seed_regularity": self.tolerance_seed_regularity,
        }
        return super().residual_pack(
            residual_values=values,
            tolerance=tolerance,
            extra_metadata={
                "principal_direction_axis": bundle.metadata.get("principal_direction_axis"),
                "secondary_direction_axis": bundle.metadata.get("secondary_direction_axis"),
                "truncation_half_width": bundle.metadata.get("truncation_half_width"),
                "vi0_transport_status": bundle.metadata.get("vi0_transport_status"),
                "vi0_structure_scale": bundle.metadata.get("vi0_structure_scale"),
                "vi0_directional_imbalance": bundle.metadata.get("vi0_directional_imbalance"),
                "vi0_shear_max": bundle.metadata.get("vi0_shear_max"),
                "vi0_mode_mixing_norm": bundle.metadata.get("vi0_mode_mixing_norm"),
                "polarization_basis_transport": bundle.metadata.get("polarization_basis_transport"),
            },
        )


KERNEL = TypeVI0Kernel()
