"""PR13AM: TE-sign / D1-D3 bridge directional weight gating.

Scope (HTT-P0-AM, INDEPENDENT_TRACKS_PLAN.md §2.2):
-----------------------------------------------------
Introduces the ``_direction_weight_status`` routine per the v2 patch plan
(BASS_PY_HTT_TSC_RESEARCH_PLAN.md §6.1 / §6.8). The function returns a normalised
weight vector together with provenance metadata, and — when invoked in
``production_mode`` — forbids the silent uniform-weight fallback that was the
documented P0 defect.

This module is intentionally minimal. Other PR13AM responsibilities (TE-sign
selection and D1/D3 bridge numerics) remain TBD and will be added under a
separate track.
"""
from __future__ import annotations

from typing import Any, Mapping

import numpy as np


_FALLBACK_DIAGNOSTIC = "uniform_fallback_diagnostic_only"
_FALLBACK_NATIVE = "native_weights"


def _direction_weight_status(
    direction_npz: Mapping[str, Any],
    prefix: str,
    production_mode: bool = False,
) -> dict[str, Any]:
    """Normalise directional weights and expose fallback provenance.

    Parameters
    ----------
    direction_npz : mapping with a ``'{prefix}_dir_w'`` entry
        Raw directional-weight vector. Typically an ``np.load(...)`` handle.
    prefix : str
        Catalog prefix (``'d1'`` / ``'d3'`` in the te-sign bridge).
    production_mode : bool, default False
        When True, refuses to silently synthesise a uniform-weight fallback.

    Returns
    -------
    dict with keys ``weights``, ``fallback_status``, ``production_allowed``.

    Raises
    ------
    RuntimeError
        If ``production_mode`` and all supplied weights are (≈) zero.
    """
    w = np.asarray(direction_npz[f"{prefix}_dir_w"], dtype=float)
    if np.allclose(w, 0.0):
        if production_mode:
            raise RuntimeError(
                f"{prefix}: all directional weights are zero; "
                "production inference forbidden."
            )
        w = np.ones_like(w)
        return {
            "weights": w / w.sum(),
            "fallback_status": _FALLBACK_DIAGNOSTIC,
            "production_allowed": False,
        }
    return {
        "weights": w / w.sum(),
        "fallback_status": _FALLBACK_NATIVE,
        "production_allowed": True,
    }
