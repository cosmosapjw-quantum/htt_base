"""FB-5.4 — explicit ``k = 0`` limit validator."""
from __future__ import annotations

import numpy as np


__all__ = ["assert_k_zero_limit_matches_background"]


def assert_k_zero_limit_matches_background(
    *,
    k_comoving: float,
    background_state: np.ndarray,
    perturbation_state: np.ndarray,
    atol: float,
    rtol: float,
) -> None:
    """Validate that the perturbation path collapses to the background path.

    ``k = 0`` is a byte-identity gate: the perturbative state must match
    the supplied background anchor exactly, modulo an optional trailing
    block of explicit perturbation auxiliaries that must themselves be
    identically zero.
    """
    k_val = float(k_comoving)
    if not np.isfinite(k_val) or k_val < 0.0:
        raise ValueError(
            f"k_comoving must be finite and non-negative, got {k_comoving!r}"
        )
    if atol < 0.0 or rtol < 0.0:
        raise ValueError(
            f"atol and rtol must be non-negative, got atol={atol}, rtol={rtol}"
        )

    bg = np.asarray(background_state)
    pert = np.asarray(perturbation_state)
    if bg.ndim != 1 or pert.ndim != 1:
        raise ValueError(
            f"background_state and perturbation_state must be 1-D, got "
            f"{bg.shape} and {pert.shape}"
        )
    if not np.all(np.isfinite(bg)) or not np.all(np.isfinite(pert)):
        raise AssertionError("background_state and perturbation_state must be finite")
    if pert.size < bg.size:
        raise AssertionError(
            f"perturbation_state is shorter than background_state: "
            f"{pert.size} < {bg.size}"
        )

    prefix = pert[: bg.size]
    extras = pert[bg.size :]
    if k_val == 0.0:
        if not np.array_equal(prefix, bg):
            raise AssertionError("k = 0 limit is not byte-identical to background")
        if extras.size and not np.array_equal(extras, np.zeros_like(extras)):
            raise AssertionError(
                "k = 0 perturbation auxiliaries must be identically zero"
            )
        return

    if not np.allclose(prefix, bg, atol=atol, rtol=rtol):
        diff = np.max(np.abs(prefix - bg))
        raise AssertionError(
            f"k -> 0 limit mismatch exceeds tolerances: max |Δ| = {diff}, "
            f"atol={atol}, rtol={rtol}"
        )
