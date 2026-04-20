"""FB-5.1 — harmonic-mode context builder for ``k != 0`` perturbations."""
from __future__ import annotations

from typing import Final

import numpy as np

from bass.background.bianchi_types import StructureConstants
from bass.hierarchy.hierarchy_rhs import hierarchy_rhs_photon
from bass.hierarchy.nabla_dispatch import (
    HarmonicMode,
    make_nabla_tilde,
    scalar_laplacian_eigenvalue,
)
from bass.perturbation.class_b_mode_quantization import quantise_class_b_mode


__all__ = ["make_harmonic_mode_rhs_context"]


_MODE_FAMILY: Final[dict[str, str]] = {
    "FLRW": "plane_wave",
    "I": "plane_wave",
    "II": "center_line",
    "III": "class_b_abelian_plane",
    "IV": "class_b_abelian_plane",
    "V": "hyperbolic",
    "VI_0": "abelian_plane",
    "VI_h": "class_b_abelian_plane",
    "VII_0": "helical_axis",
    "VII_h": "spiral",
    "VIII": "cartan_axis",
    "IX": "discrete_s3",
}
_SPECTRUM_KIND: Final[dict[str, str]] = {
    "IX": "discrete",
}


def make_harmonic_mode_rhs_context(
    structure: StructureConstants,
    mode: HarmonicMode,
    *,
    L_max: int,
) -> dict[str, object]:
    """Wrap one harmonic mode into a ready-to-call photon RHS surface.

    The returned dictionary keeps the FB-5.1 state machine explicit: the
    existing :func:`hierarchy_rhs_photon` remains the production driver,
    while this helper supplies the per-mode complex ``nabla_operator``,
    eigenvalue metadata, and a convenience wrapper that binds the two.
    """
    if L_max < 0:
        raise ValueError(f"L_max must be non-negative, got {L_max}")
    if structure.label != mode.type_label:
        raise ValueError(
            f"structure.label={structure.label!r} does not match "
            f"mode.type_label={mode.type_label!r}"
        )

    nabla_operator = make_nabla_tilde(structure, mode)
    laplacian = scalar_laplacian_eigenvalue(structure, mode)
    label = structure.label

    def photon_rhs(
        eta: float,
        y_flat: np.ndarray,
        *,
        bg_table: object,
        tetrad_state: object | None,
        closure: object,
        collision: object,
        collision_aux: object | None = None,
        accel_vector: np.ndarray | None = None,
        vorticity_vector: np.ndarray | None = None,
    ) -> np.ndarray:
        return hierarchy_rhs_photon(
            eta,
            y_flat,
            L_max=L_max,
            bg_table=bg_table,
            tetrad_state=tetrad_state,
            closure=closure,
            collision=collision,
            collision_aux=collision_aux,
            nabla_operator=nabla_operator,
            accel_vector=accel_vector,
            vorticity_vector=vorticity_vector,
        )

    context: dict[str, object] = {
        "structure": structure,
        "mode": mode,
        "L_max": int(L_max),
        "state_dtype": np.dtype(np.complex128),
        "mode_family": _MODE_FAMILY[label],
        "spectrum_kind": _SPECTRUM_KIND.get(label, "continuous"),
        "nabla_operator": nabla_operator,
        "laplacian_eigenvalue": float(laplacian),
        "k_magnitude": float(np.linalg.norm(mode.k_vec)),
        "photon_rhs": photon_rhs,
        "requires_full_operator": False,
    }
    if label in {"V", "III", "IV", "VI_h", "VII_h"}:
        context["mode_quantization"] = quantise_class_b_mode(
            structure,
            eigenvalue=-float(laplacian),
        )
    if label == "IX":
        context["discrete_ell"] = int(mode.ell)  # type: ignore[arg-type]
    return context
