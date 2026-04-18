"""bass/hierarchy/closure_diagnostics.py (LB-3) — Closure error probes.

Tools for quantifying how much the tower-top truncation biases the
low-ℓ dynamics. Spec §8 defines the error metric:

    err_ℓ = || Π_ℓ(L=L_ref) − Π_ℓ(L=L_trunc) ||_F   for ℓ = 0..L_trunc

and ``measure_closure_error`` below returns the per-ℓ Frobenius-norm
(i.e. sum-of-squared-components) differences between the ``dy/dη``
produced at two different truncation depths, given the same
low-ℓ state. This is the "RHS-difference" variant of the spec's
convergence probe — practical because no integration is needed; if
the RHS agrees between two truncation depths, so do the integrated
trajectories over a short window.

Standalone integration-based convergence studies are carried by the
LB-3 gallery script (``plots/physics_gallery/09_pstf_hierarchy/``).

References
----------
- ``docs/lowell_bianchi/03_closure_truncation_spec.md`` §8, §11.5.
- Pitrou 2009 (CQG 26:065006) §4 — convergence methodology.
- Ma-Bertschinger 1995 §6 — truncation error scaling.
"""
from __future__ import annotations

from typing import Callable, Dict, Optional

import numpy as np

from bass.hierarchy.closure_interface import ClosureStrategy
from bass.hierarchy.pstf_tensor import (
    PSTFHierarchyState,
    hierarchy_total_size,
    pack_hierarchy,
    unpack_hierarchy,
)


__all__ = [
    "measure_closure_error",
]


def _truncate_state(
    state: PSTFHierarchyState, L_target: int,
) -> PSTFHierarchyState:
    """Return a copy of ``state`` truncated to depth ``L_target``.

    Keeps ranks 0..L_target; drops higher ranks so the truncated run
    will fetch ``Π_{L_target + 1}`` / ``Π_{L_target + 2}`` from its
    closure instead of from residual content of the deeper state.
    """
    if L_target > state.L:
        raise ValueError(
            f"L_target ({L_target}) exceeds state.L ({state.L})"
        )
    tensors = [state.tensors[ell].copy() for ell in range(L_target + 1)]
    return PSTFHierarchyState(L=L_target, tensors=tensors)


def measure_closure_error(
    state_ref: PSTFHierarchyState,
    driver: Callable[..., np.ndarray],
    *,
    L_trunc: int,
    closure_ref: ClosureStrategy,
    closure_trunc: ClosureStrategy,
    driver_kwargs: Optional[dict] = None,
) -> Dict[int, float]:
    """Per-ℓ Frobenius-norm of the ``dy/dη`` difference between a
    reference-depth run and a truncation to ``L_trunc``.

    Parameters
    ----------
    state_ref : PSTFHierarchyState
        Reference tower at depth ``L_ref = state_ref.L``. Its ℓ ≤
        L_trunc ranks are inherited by the truncated run verbatim;
        the L_trunc+1..L_ref ranks are *discarded* in the truncated
        run (supplanted by the truncated closure).
    driver : callable
        The RHS callable. Standard LB-2b signature:
        ``driver(eta, y_flat, *, L_max, bg_table, tetrad_state,
        closure, collision, …)``.
    L_trunc : int
        Truncated (shallower) depth whose error we want to measure.
        Must satisfy ``0 <= L_trunc <= state_ref.L``.
    closure_ref, closure_trunc : ClosureStrategy
        Closure strategies used at the reference and truncated runs
        respectively. ``L_trunc == state_ref.L`` with identical
        closures must produce exactly zero error (spec C-14
        guardrail).
    driver_kwargs : dict, optional
        Extra keyword arguments forwarded to ``driver``. Must include
        ``'eta'`` (conformal time [Mpc] at which to evaluate). Must
        also include any other driver-specific kwargs (``bg_table``,
        ``tetrad_state``, ``collision``, …).

    Returns
    -------
    dict[int, float]
        Mapping ``ell → || dy_ref_{ℓ} − dy_trunc_{ℓ} ||_F`` for
        ``ell = 0..L_trunc``. Units are those of the driver's
        ``dy/dη`` vector (``1/Mpc²`` in the LB-2b photon case).

    Notes
    -----
    The metric is a **right-hand-side** divergence between truncation
    depths — useful for questions of the form "does the tower close
    self-consistently at L_trunc?". If the RHS is independent of
    ranks above L_trunc (because the closure supplies a good proxy
    for ``Π_{L_trunc+1}`` / ``Π_{L_trunc+2}``), the truncation is
    self-consistent. Trajectory-integrated convergence is orthogonal
    and is covered by the LB-3 gallery script on a short Bianchi I
    window.

    Reference: spec §8, §11.5 (C-13..C-15); Pitrou 2009 §4.
    """
    L_ref = state_ref.L
    if L_trunc < 0:
        raise ValueError(f"L_trunc must be non-negative, got {L_trunc}")
    if L_trunc > L_ref:
        raise ValueError(
            f"L_trunc ({L_trunc}) must be <= state_ref.L ({L_ref})"
        )
    kwargs = dict(driver_kwargs) if driver_kwargs else {}
    if "eta" not in kwargs:
        raise ValueError(
            "driver_kwargs must include 'eta' (conformal time for the "
            "RHS evaluation)"
        )
    eta = kwargs.pop("eta")

    # Reference run: full state_ref at depth L_ref.
    y_ref = pack_hierarchy(state_ref)
    dy_ref = driver(
        eta, y_ref,
        L_max=L_ref,
        closure=closure_ref,
        **kwargs,
    )

    # Truncated run: first L_trunc+1 ranks of state_ref.
    state_trunc = _truncate_state(state_ref, L_trunc)
    y_trunc = pack_hierarchy(state_trunc)
    dy_trunc = driver(
        eta, y_trunc,
        L_max=L_trunc,
        closure=closure_trunc,
        **kwargs,
    )

    expected_ref = hierarchy_total_size(L_ref)
    expected_trunc = hierarchy_total_size(L_trunc)
    if dy_ref.shape != (expected_ref,):
        raise RuntimeError(
            f"Reference driver returned dy shape {dy_ref.shape}, "
            f"expected ({expected_ref},)"
        )
    if dy_trunc.shape != (expected_trunc,):
        raise RuntimeError(
            f"Truncated driver returned dy shape {dy_trunc.shape}, "
            f"expected ({expected_trunc},)"
        )

    # Unpack and compare per-ℓ (only ranks present in the truncated run).
    state_dy_ref = unpack_hierarchy(dy_ref, L_ref)
    state_dy_trunc = unpack_hierarchy(dy_trunc, L_trunc)
    errors: Dict[int, float] = {}
    for ell in range(L_trunc + 1):
        diff = (
            state_dy_ref.tensors[ell].components
            - state_dy_trunc.tensors[ell].components
        )
        errors[ell] = float(np.sqrt(np.sum(diff ** 2)))
    return errors
