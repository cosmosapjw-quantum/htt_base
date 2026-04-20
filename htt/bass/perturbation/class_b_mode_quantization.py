"""FB-5.5 — Class B / Type V mode-quantisation metadata."""
from __future__ import annotations

import math

from bass.background.bianchi_types import StructureConstants


__all__ = ["quantise_class_b_mode"]


_CLASS_B_LIKE = {"V", "III", "IV", "VI_h", "VII_h"}
_VALID_BRANCHES = {"principal", "supplementary"}


def _twist_offset(structure: StructureConstants) -> float:
    if structure.label == "V":
        return float(structure.a_twist ** 2)
    h_abs = abs(float(structure.h_parameter))
    return float(structure.a_twist ** 2 / (1.0 + h_abs))


def _mode_family(label: str) -> str:
    if label == "V":
        return "hyperbolic"
    if label == "VII_h":
        return "spiral"
    return "class_b_abelian_plane"


def quantise_class_b_mode(
    structure: StructureConstants,
    *,
    eigenvalue: float,
    branch: str = "principal",
) -> dict[str, object]:
    """Quantise one Class-B-like scalar mode.

    Parameters
    ----------
    structure
        Per-type structure constants. Supported labels are ``V``,
        ``III``, ``IV``, ``VI_h``, and ``VII_h``.
    eigenvalue
        Positive scalar spectral magnitude ``lambda_pos`` such that the
        Laplacian eigenvalue is ``-lambda_pos``.
    branch
        ``"principal"`` or ``"supplementary"``. The returned metadata is
        purely descriptive; the current FB-5 helper stack uses the
        branch label to keep the hyperbolic / spiral spectrum explicit
        without widening the shipped ``HarmonicMode`` descriptor.
    """
    if structure.label not in _CLASS_B_LIKE:
        raise ValueError(
            f"quantise_class_b_mode supports only {_CLASS_B_LIKE}, got "
            f"{structure.label!r}"
        )
    eigen = float(eigenvalue)
    if not math.isfinite(eigen) or eigen <= 0.0:
        raise ValueError(
            f"eigenvalue must be finite and positive, got {eigenvalue!r}"
        )
    if branch not in _VALID_BRANCHES:
        raise ValueError(
            f"branch must be one of {_VALID_BRANCHES}, got {branch!r}"
        )

    twist_offset = _twist_offset(structure)
    base_k_sq = max(eigen - twist_offset, 0.0)
    h_parameter = float(structure.h_parameter)
    if structure.label == "V":
        h_denom = 1.0
    else:
        h_denom = 1.0 + abs(h_parameter)

    return {
        "type_label": structure.label,
        "branch": branch,
        "mode_family": _mode_family(structure.label),
        "spectrum_kind": "continuous",
        "laplacian_eigenvalue": -eigen,
        "effective_eigenvalue": eigen,
        "base_wavenumber": math.sqrt(base_k_sq),
        "base_wavenumber_sq": base_k_sq,
        "twist_offset": twist_offset,
        "a_twist": float(structure.a_twist),
        "h_parameter": h_parameter,
        "h_denominator": h_denom,
        "quantised_label": (
            f"{structure.label}:{branch}:"
            f"k={math.sqrt(base_k_sq):.12g}:lambda={eigen:.12g}"
        ),
    }
