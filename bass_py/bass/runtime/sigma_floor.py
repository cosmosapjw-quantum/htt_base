"""
bass/runtime/sigma_floor.py  (Week 3 Day 2, merged v4.1)
=========================================================

Sobolev-validity floor check on the shear-squared departure parameter Σ².

Motivation
----------
The Sobolev cancellation scope (thesis Appendix / `consolidated_baryon_CDM_
EFT_boundary_notes.md`) is *conditional* on five validity conditions A1–A5.
Numerically, the cancellation's O(10⁻⁷) residual is safe in practice only when
Σ² stays above a floor of roughly 10⁻⁶. Below that floor the theorem label
becomes an overclaim and the trace-side reduction must not proceed.

This module exposes a single gate function consumed through the canonical
decision factory:

    bass/runtime/sigma_floor.py  →  sigma_min_gate(sigma_squared, floor)
    bass/runtime/canonical_decision.py  →  make_canonical_decision(
                                             beta_result, sigma_result, ...
                                           )

The gate accepts scalar or array Σ² input. For an array, the gate fails if
*any* entry drops below the floor; the failing index is included in the
returned diagnostics so callers can locate the offending mode or timestep.

Paper / design cross-refs
-------------------------
- CANONICAL_DECISION_DESIGN.md §2.2 (source-of-truth for threshold logic)
- userMemories: "At Σ² ~ 10⁻⁶ the correction is O(10⁻⁷) — safe in practice"
- `consolidated_baryon_CDM_EFT_boundary_notes.md` (Sobolev scope discussion)
"""
from __future__ import annotations

from typing import Tuple, Union

import numpy as np


# ============================================================================
# Section 1 - Threshold constant
# ============================================================================

SIGMA_FLOOR_DEFAULT: float = 1e-6
"""Sobolev validity floor on Σ². Below this, the cancellation theorem's
residual bound ceases to be safe.

This value is currently pinned here; migration to `ssot.py` is scheduled with
the W5+ SSOT module. Changing this constant is a design-spec update.
"""


# ============================================================================
# Section 2 - Gate
# ============================================================================

def sigma_min_gate(
    sigma_squared: Union[float, np.ndarray],
    floor: float = SIGMA_FLOOR_DEFAULT,
) -> Tuple[bool, dict]:
    """Check Σ² ≥ floor at every evaluation point.

    Parameters
    ----------
    sigma_squared : float or ndarray
        Shear-squared value(s). Non-negative by construction.
    floor : float, optional
        Validity floor. Default `SIGMA_FLOOR_DEFAULT = 1e-6`.

    Returns
    -------
    (passed, diagnostics) : tuple[bool, dict]
        `passed` — True iff min(sigma_squared) ≥ floor.
        `diagnostics` — keys: `sigma_min`, `floor`, `margin_factor`,
        `argmin_index`, `n_samples`. For scalar input the `argmin_index`
        is 0 and `n_samples` is 1.

    Raises
    ------
    ValueError
        `floor` non-positive, `sigma_squared` contains negative values, or
        input is empty.

    Notes
    -----
    * The comparison is inclusive (≥). `sigma_squared == floor` passes.
    * `margin_factor = sigma_min / floor`; values > 1 indicate slack,
      values < 1 indicate violation. 0 means at floor exactly.
    * Rationale for carrying `argmin_index` in diagnostics: when a forward
      stratum fails over a (k, η) grid, the caller needs to locate *where*
      the violation occurred for debugging, not just *that* one occurred.
    """
    if not (floor > 0):
        raise ValueError(f"floor must be positive, got {floor}")

    arr = np.atleast_1d(np.asarray(sigma_squared, dtype=float))
    if arr.size == 0:
        raise ValueError("sigma_squared cannot be empty")
    if np.any(arr < 0):
        bad_idx = int(np.argmin(arr))
        bad_val = float(arr.ravel()[bad_idx])
        raise ValueError(
            f"sigma_squared must be non-negative everywhere; "
            f"found {bad_val} at flat index {bad_idx}"
        )

    flat = arr.ravel()
    argmin = int(np.argmin(flat))
    sigma_min = float(flat[argmin])
    passed = sigma_min >= floor
    margin_factor = sigma_min / floor  # floor > 0 guaranteed above

    diagnostics = {
        "sigma_min": sigma_min,
        "floor": float(floor),
        "margin_factor": float(margin_factor),
        "argmin_index": argmin,
        "n_samples": int(arr.size),
    }
    return passed, diagnostics
