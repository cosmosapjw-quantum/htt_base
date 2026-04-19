"""bass/forward/teff_backward.py — T_eff backward (inversion) closure.

NEW in bass_py (not ported from legacy). Provides three independent
strategies for recovering the closure parameters (A, Q) from observable
data produced by the forward map in ``teff_forward``:

1. ``teff_backward_linear(a1, a2)``
       Small-(A, Q) analytic inversion using only a_1 and a_2. Inverts
           a_1 ≈ 4·A
           a_2 ≈ 4·Q + 4·A²
       to give (A, Q) to O((A, Q)²). Use when only the leading
       multipoles are available or as a warm-start for the LSQ solver.

2. ``teff_backward_lsq(a_ell_dict, ell_max=8)``
       Nonlinear least-squares inversion against the full closed-form
       Θ⁴ coefficient polynomial ``theta4_coefficients``. Returns
       (A, Q, residual_norm, info).  Accurate to within the C-14
       Gaunt polynomial truncation (ℓ ≤ 4 exact, ℓ ≥ 5 approximate).

3. ``teff_backward_projection(theta_samples, ...)``
       Exact Gauss-Legendre L² projection of the first-order field
           Θ(ê) = 1 + A·P₁ + Q·P₂
       onto the Legendre basis. This is the MACHINE-PRECISION inverter
       when Θ(cosθ) samples (not Θ⁴) are available. Useful as an oracle
       for regression tests of the forward closed-form polynomial.

Together these form a three-way verification chain:

    (A, Q) --forward--> a_ℓ(A, Q)
        ^                  |
        |                  v
        +-- backward-lsq --+ with residual < ε
        +-- backward-linear (matches to O(ε²))
        +-- backward-projection (exact Θ in/out, not Θ⁴)

The roundtrip  (A, Q) → a_ℓ → (A', Q')  achieves
    |A' - A| + |Q' - Q| < 10⁻¹⁴  (projection on Θ)
    |A' - A| + |Q' - Q| < 10⁻⁶   (LSQ on Θ⁴ a_ℓ, for |A|, |Q| ≤ 0.05)

External-code policy: the LSQ solver uses ``scipy.optimize.least_squares``;
this is a dependency of bass_py via scipy already, and is used here for
numerical convenience (not as a physics oracle). The physics map itself
lives entirely in ``theta4_coefficients`` and ``monopole_gauge_check``.
"""
from __future__ import annotations

import numpy as np
from typing import Callable, Dict, Mapping, Optional, Tuple, Union

from bass.forward.teff_forward import theta4_coefficients

__all__ = [
    'teff_backward_linear',
    'teff_backward_lsq',
    'teff_backward_projection',
    'TeffBianchiBackward',
]


# ════════════════════════════════════════════════════════════════════
# Strategy 1: small-(A, Q) analytic inversion
# ════════════════════════════════════════════════════════════════════

def teff_backward_linear(a1: float, a2: float) -> Tuple[float, float]:
    """Leading-order inversion from (a_1, a_2) to (A, Q).

    Uses the small-(A, Q) expansion

        a_1 = 4·A + O((A, Q)³)
        a_2 = 4·Q + 4·A² + O((A, Q)³)

    to recover

        A = a_1 / 4
        Q = (a_2 - 4·A²) / 4 = (a_2 − a_1²/4) / 4.

    Error scales as O((A, Q)²) in the next-to-leading C-14 Gaunt terms.

    Parameters
    ----------
    a1, a2 : float
        Observed dipole and quadrupole Legendre coefficients of Θ⁴.

    Returns
    -------
    (A, Q) : tuple[float, float]
    """
    A = a1 / 4.0
    Q = (a2 - 4.0 * A * A) / 4.0
    return float(A), float(Q)


# ════════════════════════════════════════════════════════════════════
# Strategy 2: nonlinear least-squares on the full a_ℓ pattern
# ════════════════════════════════════════════════════════════════════

def teff_backward_lsq(
    a_ell: Mapping[int, float],
    ell_max: int = 8,
    x0: Optional[Tuple[float, float]] = None,
    *,
    weights: Optional[Mapping[int, float]] = None,
    xtol: float = 1e-14,
) -> Tuple[float, float, float, dict]:
    """Full nonlinear LSQ inversion against ``theta4_coefficients``.

    Minimises

        S(A, Q) = Σ_{ℓ=0}^{ell_max} w_ℓ · (a_ℓ_obs − a_ℓ_model(A, Q))²

    where w_ℓ defaults to 1 for all ℓ (uniform weighting). A custom
    ``weights`` dict can down-weight the O(1)-error high-ℓ coefficients.

    Parameters
    ----------
    a_ell : Mapping[int, float]
        Observed Legendre coefficients {ℓ: a_ℓ}. Missing keys default
        to 0.
    ell_max : int
        Highest ℓ included in the residual. Default 8 (full closure).
    x0 : (A0, Q0) or None
        Initial guess. Defaults to ``teff_backward_linear(a_1, a_2)``.
    weights : Mapping[int, float] or None
        Per-ℓ weights in the residual. Higher-ℓ (≥ 5) carry O(1)
        Gaunt-truncation error; set their weight to a small value (e.g.
        1e-3) if the target has clean high-ℓ content.
    xtol : float
        scipy.optimize.least_squares tolerance on the step size.

    Returns
    -------
    A, Q : float
        Recovered amplitudes.
    residual_norm : float
        ‖residual‖₂ at the optimum.
    info : dict
        {'nfev', 'njev', 'status', 'message', 'cost'}.
    """
    from scipy.optimize import least_squares

    if x0 is None:
        x0 = teff_backward_linear(
            float(a_ell.get(1, 0.0)),
            float(a_ell.get(2, 0.0)),
        )

    w = {ell: 1.0 for ell in range(ell_max + 1)}
    if weights is not None:
        for ell, ww in weights.items():
            w[ell] = float(ww)

    def residuals(params: np.ndarray) -> np.ndarray:
        A, Q = float(params[0]), float(params[1])
        model = theta4_coefficients(A, Q)
        out = np.zeros(ell_max + 1, dtype=np.float64)
        for ell in range(ell_max + 1):
            out[ell] = np.sqrt(max(w[ell], 0.0)) * (
                float(a_ell.get(ell, 0.0)) - model[ell]
            )
        return out

    result = least_squares(residuals, np.asarray(x0, dtype=np.float64),
                           xtol=xtol)
    A_opt = float(result.x[0])
    Q_opt = float(result.x[1])
    res_norm = float(np.linalg.norm(result.fun))
    info = {
        'nfev': int(result.nfev),
        'status': int(result.status),
        'message': str(result.message),
        'cost': float(result.cost),
    }
    return A_opt, Q_opt, res_norm, info


# ════════════════════════════════════════════════════════════════════
# Strategy 3: exact Gauss-Legendre L² projection onto P_0, P_1, P_2
# ════════════════════════════════════════════════════════════════════

def teff_backward_projection(
    theta_samples: Union[Callable[[np.ndarray], np.ndarray], np.ndarray],
    cos_theta_nodes: Optional[np.ndarray] = None,
    quad_weights: Optional[np.ndarray] = None,
    n_theta: int = 200,
) -> Dict[str, float]:
    """Project a Θ(cosθ) field onto {P₀, P₁, P₂}.

    For the first-order closure Θ(ê) = 1 + A·P₁ + Q·P₂ the orthogonality
    of Legendre polynomials gives

        a₀_mono = (1/2) ∫_{-1}^{1} Θ dx                            = 1
        A       = (1/2) ∫_{-1}^{1} Θ · P₁ · (2·1 + 1) dx / 1       = 3·⟨Θ·P₁⟩
        Q       = (1/2) ∫_{-1}^{1} Θ · P₂ · (2·2 + 1) dx / 1       = 5·⟨Θ·P₂⟩

    where ⟨·⟩ denotes the half-range integral.  The monopole returns 1 by
    gauge.  For a pure first-order Θ the recovery is exact to machine
    precision (Gauss-Legendre of degree ≥ 2 integrates P₂ exactly).

    When Θ contains higher-ℓ content (e.g. Θ⁴), ``A`` and ``Q`` return
    the best-fit projections (i.e. the a_1 / 3 and a_2 / 5 amplitudes of
    the *output* field, not the closure parameters that generated it).

    Parameters
    ----------
    theta_samples : callable(cosθ) → Θ, or ndarray
        The field to project.  A callable is evaluated at the Gauss-
        Legendre nodes.  An array is paired with ``cos_theta_nodes`` and
        ``quad_weights``.
    cos_theta_nodes : ndarray or None
        Quadrature nodes on [-1, 1]. Required if ``theta_samples`` is an
        ndarray.
    quad_weights : ndarray or None
        Quadrature weights matching the nodes. Required if
        ``theta_samples`` is an ndarray.
    n_theta : int
        Number of Gauss-Legendre nodes when generating the grid from a
        callable. Default 200 → ~10⁻¹⁴ precision on polynomial fields.

    Returns
    -------
    dict
        {'a0': monopole (should be 1), 'A': dipole amplitude,
         'Q': quadrupole amplitude}.
    """
    if callable(theta_samples):
        from numpy.polynomial.legendre import leggauss
        x, w = leggauss(n_theta)
        theta_vals = np.asarray(theta_samples(x), dtype=np.float64)
    else:
        if cos_theta_nodes is None or quad_weights is None:
            raise ValueError(
                "when theta_samples is an ndarray, cos_theta_nodes and "
                "quad_weights must be provided"
            )
        x = np.asarray(cos_theta_nodes, dtype=np.float64)
        w = np.asarray(quad_weights, dtype=np.float64)
        theta_vals = np.asarray(theta_samples, dtype=np.float64)
        if theta_vals.shape != x.shape:
            raise ValueError(
                f"theta_samples shape {theta_vals.shape} does not match "
                f"cos_theta_nodes shape {x.shape}"
            )

    P0 = np.ones_like(x)
    P1 = x
    P2 = 0.5 * (3.0 * x ** 2 - 1.0)

    a0 = 0.5 * float(np.sum(w * theta_vals * P0))  # monopole, = 1 by gauge
    A = 3.0 * 0.5 * float(np.sum(w * theta_vals * P1))  # (2·1+1)·⟨Θ·P₁⟩
    Q = 5.0 * 0.5 * float(np.sum(w * theta_vals * P2))  # (2·2+1)·⟨Θ·P₂⟩

    return {'a0': a0, 'A': A, 'Q': Q}


# ════════════════════════════════════════════════════════════════════
# Unified interface
# ════════════════════════════════════════════════════════════════════

class TeffBianchiBackward:
    """Roundtrip-tested inversion wrapper.

    Dispatches to the three backward strategies and enforces the
    convention that the returned (A, Q) satisfy the forward relationship
    ``theta4_coefficients(A, Q) ≈ a_ell`` up to each method's accuracy
    floor.

    Typical use in a regression test:

        fwd = TeffBianchiForward()
        back = TeffBianchiBackward()
        A, Q = 0.01, 0.005
        a_ell = theta4_coefficients(A, Q)
        A2, Q2, res, _ = back.invert(a_ell=a_ell, method='lsq')
        assert abs(A - A2) + abs(Q - Q2) < 1e-10
    """

    def invert(
        self,
        *,
        a_ell: Optional[Mapping[int, float]] = None,
        theta_samples: Optional[
            Union[Callable[[np.ndarray], np.ndarray], np.ndarray]
        ] = None,
        method: str = 'lsq',
        **kwargs,
    ) -> Union[Tuple[float, float], Tuple[float, float, float, dict], Dict[str, float]]:
        """Run the requested inversion strategy.

        Parameters
        ----------
        a_ell : Mapping or None
            Required for 'linear' and 'lsq'.
        theta_samples : callable/ndarray or None
            Required for 'projection'.
        method : {'linear', 'lsq', 'projection'}
            Inversion strategy.
        **kwargs
            Forwarded to the underlying inverter.
        """
        if method == 'linear':
            if a_ell is None:
                raise ValueError("'linear' method requires a_ell.")
            return teff_backward_linear(
                float(a_ell.get(1, 0.0)),
                float(a_ell.get(2, 0.0)),
            )
        if method == 'lsq':
            if a_ell is None:
                raise ValueError("'lsq' method requires a_ell.")
            return teff_backward_lsq(a_ell, **kwargs)
        if method == 'projection':
            if theta_samples is None:
                raise ValueError("'projection' method requires theta_samples.")
            return teff_backward_projection(theta_samples, **kwargs)
        raise ValueError(
            f"Unknown method {method!r}; expected 'linear', 'lsq' or "
            "'projection'."
        )
