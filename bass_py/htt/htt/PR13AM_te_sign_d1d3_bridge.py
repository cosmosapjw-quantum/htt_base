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

MIO ownership (PR13AM-MIO-TAG, INDEPENDENT_TRACKS_PLAN v1.2 §19.5):
-------------------------------------------------------------------
The TE-sign D1/D3 bridge is a model-independent diagnostic per BASS_PY_HTT_
TSC_MIO_RESEARCH_PLAN v3 §1.4.1. Physical location is retained under htt/
for import stability; semantic ownership is MIO. The ``__mio_owned__``
flag is the first-line G19 defence (v3 §12.2bis). Any artifact produced by
this module must flow through ``_mio_artifact_name`` to enforce the
``mio_`` filename prefix.
"""
from __future__ import annotations

from typing import Any, Mapping

import numpy as np


__mio_owned__ = True
__mio_rationale__ = (
    "TE-sign D1/D3 pattern is a model-independent diagnostic bridge. "
    "Per BASS_PY_HTT_TSC_MIO_RESEARCH_PLAN v3 §1.4.1, semantic ownership "
    "is MIO; physical location in htt/ is retained for import stability."
)


def _mio_artifact_name(stem: str, version: int = 1) -> str:
    """Enforce v3 §12.2bis naming: 'mio_' prefix + subpackage identifier.

    Parameters
    ----------
    stem : str
        Raw artifact basename (without extension, without prefix).
    version : int, default 1
        Integer version tag suffixed as ``_v{N}``.

    Returns
    -------
    str
        Artifact filename of the form ``mio_pr13am_<stem>_v<N>.json``. If
        ``stem`` already starts with ``mio_`` the existing prefix is kept
        and only the version tag is appended.
    """
    if not stem.startswith("mio_"):
        stem = f"mio_pr13am_{stem}"
    return f"{stem}_v{version}.json"


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
