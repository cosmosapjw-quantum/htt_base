"""
bass/teff/inverse_T_to_F.py  (Week 3 Day 1)
============================================

Paper I inverse map F^{-1} : (T_0, T_1, ..., T_L) -> Theta(mu) (and optionally
refined eta(mu)) for axisymmetric fields.

Role in Paper I / Paper III-A
------------------------------
Given observed axisymmetric multipoles

    T_ell = (2 ell + 1) / 2 * int_{-1}^{1} dmu Theta(mu)^{n+1}
                                         * I_n(xi, eta(mu))
                                         * P_ell(mu)

the inverse problem is to recover Theta(mu) = Sum_ell Theta_ell P_ell(mu) from
the truncated observation set {T_0, ..., T_L}. When eta(mu) is supplied
externally (e.g., from chemistry closure or from BBN calibration for
neutrinos), the remaining Theta degrees of freedom are recovered via Newton
iteration with the Paper III-A Jacobian

    J_{ell m} = dT_ell / dTheta_m
              = (2 ell + 1) / 2 * int dmu (n+1) Theta(mu)^n
                                        * I_n(xi, eta(mu))
                                        * P_ell(mu) P_m(mu).

This is the Gram-metric Jacobian in the Theta^n I_n weighted Legendre inner
product. At the isotropic background it reduces to a diagonal matrix whose
inverse gives the linear-response inverse used as the initial Newton guess.

Paper I cross-references
------------------------
  - Prop 5 (linear-response forward map -> its inverse = zeroth-order guess)
  - Prop 8 (regression-exact extraction via Gram solve)
  - Appendix B (Paper III-A Jacobian structure)

Interpretive stance
-------------------
For one-field species (photons, eta == 0) the problem is well-posed with
L + 1 equations for L + 1 unknowns (Theta_0, ..., Theta_L). For two-field
species the Day 1 scope treats eta(mu) as *given* (a `AxisymmetricField` the
caller supplies); simultaneous recovery of (Theta, eta) from two moment
orders (n = 2, 3) is deferred to a later day per the Week 3 schedule.

Admissibility
-------------
During Newton iteration the candidate Theta(mu) is guarded so that
Theta(mu) > 0 on [-1, 1]. If a Newton step would drive the field
non-positive, a back-tracking line search halves the step until safe.

Convention
----------
Dimensional T convention: T_0 = Theta_0^{n+1} * I_n(xi, eta_bg) at isotropy.
This matches `forward_F_to_T.axisymmetric_F`; it is the sole convention used
in this module.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional
import math

import numpy as np
from scipy.special import eval_legendre

from tsc.charts.laguerre_basis import xi_moment
from tsc.charts.forward_F_to_T import (
    AxisymmetricField,
    ForwardResult,
    axisymmetric_F,
    check_theta_positive,
    check_be_admissibility,
)


# ============================================================================
# Section 1 - Linear-response inverse (initial guess)
# ============================================================================

def linear_response_inverse(
    T_ell_obs: np.ndarray,
    xi: int,
    eta_bg: float = 0.0,
    moment_order: int = 3,
) -> np.ndarray:
    """Invert the linear-response forward map.

    At linear order in anisotropy the forward map reads

        T_0 = Theta_0^{n+1} * I_n(xi, eta_bg)
        T_ell = (n+1) * Theta_0^n * Theta_ell * I_n(xi, eta_bg)    (ell >= 1)

    so the inverse is analytic:

        Theta_0 = (T_0 / I_n)^{1 / (n+1)}
        Theta_ell = T_ell / [(n+1) * Theta_0^n * I_n]              (ell >= 1).

    This provides the Newton iteration's initial guess.

    Parameters
    ----------
    T_ell_obs : ndarray shape (L+1,)
        Observed axisymmetric multipoles [T_0, T_1, ..., T_L].
    xi : int
        Statistics parameter in {-1, 0, +1}.
    eta_bg : float, optional
        Background fugacity used in the linear-response point. For one-field
        species eta_bg = 0. For two-field species pass eta_bg = eta_0
        (monopole of the supplied eta field).
    moment_order : int, optional
        n in I_n (default 3, energy moments).

    Returns
    -------
    ndarray shape (L+1,)
        Legendre coefficients [Theta_0, Theta_1, ..., Theta_L].

    Raises
    ------
    ValueError
        If T_0 <= 0 (cannot take real root).
    """
    T_ell = np.asarray(T_ell_obs, dtype=float)
    if T_ell.ndim != 1:
        raise ValueError(f"T_ell_obs must be 1D, got shape {T_ell.shape}")
    if T_ell[0] <= 0:
        raise ValueError(
            f"Linear-response inverse requires T_0 > 0, got T_0 = {T_ell[0]}"
        )

    I_n = xi_moment(moment_order, xi, eta_bg)
    if I_n <= 0:
        raise ValueError(
            f"Background I_n({moment_order}, xi={xi}, eta={eta_bg}) "
            f"= {I_n} must be positive"
        )

    n = moment_order
    Theta = np.zeros_like(T_ell)
    Theta[0] = (T_ell[0] / I_n) ** (1.0 / (n + 1))
    if len(T_ell) > 1:
        denom = (n + 1) * (Theta[0] ** n) * I_n
        Theta[1:] = T_ell[1:] / denom
    return Theta


# ============================================================================
# Section 2 - Paper III-A Jacobian
# ============================================================================

def _build_jacobian(
    Theta_coeffs: np.ndarray,
    xi: int,
    eta: Optional[AxisymmetricField],
    moment_order: int,
    L_out: int,
    n_quad: int,
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Assemble J_{ell m} = dT_ell / dTheta_m and return auxiliaries.

    The Jacobian reads

        J_{ell m} = (2 ell + 1) / 2
                    * int dmu (n+1) Theta(mu)^n I_n(xi, eta(mu))
                                  * P_ell(mu) P_m(mu)

    which is symmetric up to the (2 ell + 1) / 2 row scaling; the full
    matrix is stored un-symmetrized to match the forward-map row convention.

    Returns
    -------
    J : ndarray (L_out+1, L_Theta+1) where L_Theta = len(Theta_coeffs) - 1
    F_vals : ndarray (L_out+1,)  forward-map evaluation T_ell at Theta_coeffs
    weight : ndarray (n_quad,)   for reuse in residual assembly if desired
    """
    n = moment_order
    Theta = AxisymmetricField(coeffs=Theta_coeffs, name="Theta_iter")
    L_Theta = Theta.L_max

    # Gauss-Legendre on [-1, 1]
    mu, w = np.polynomial.legendre.leggauss(n_quad)

    Theta_vals = Theta.evaluate(mu)
    eta_vals = np.zeros_like(mu) if eta is None else eta.evaluate(mu)

    # Forward integrand: weight_F = Theta^{n+1} * I_n
    I_vals = np.array([
        xi_moment(n, xi, float(eta_val)) for eta_val in eta_vals
    ])
    weight_F = (Theta_vals ** (n + 1)) * I_vals

    # Jacobian integrand: weight_J = (n+1) * Theta^n * I_n
    weight_J = (n + 1) * (Theta_vals ** n) * I_vals

    # Legendre table P_ell(mu) for ell = 0, ..., max(L_out, L_Theta)
    L_max_ell = max(L_out, L_Theta)
    P_table = np.array([
        eval_legendre(ell, mu) for ell in range(L_max_ell + 1)
    ])  # shape (L_max_ell+1, n_quad)

    # Forward T_ell = (2 ell + 1) / 2 * sum_i w_i * weight_F_i * P_ell_i
    F_vals = np.array([
        (2 * ell + 1) / 2.0 * float(np.sum(w * weight_F * P_table[ell]))
        for ell in range(L_out + 1)
    ])

    # Jacobian rows
    J = np.zeros((L_out + 1, L_Theta + 1))
    for ell in range(L_out + 1):
        row_pre = (2 * ell + 1) / 2.0
        for m in range(L_Theta + 1):
            integ = float(np.sum(w * weight_J * P_table[ell] * P_table[m]))
            J[ell, m] = row_pre * integ

    return J, F_vals, weight_F


# ============================================================================
# Section 3 - Newton iteration result container
# ============================================================================

@dataclass(frozen=True)
class InverseResult:
    """Container for Newton-iteration inverse map output.

    Attributes
    ----------
    Theta : AxisymmetricField
        Recovered direction-dependent temperature field.
    n_iter : int
        Newton iterations performed (0 = converged at initial guess).
    residual_history : tuple of float
        ||F(Theta^{(k)}) - T_obs||_2 / ||T_obs||_2 per iteration including
        the initial guess (index 0).
    converged : bool
        True iff the final relative residual is below `tol`.
    jacobian_cond : float
        Condition number of the final Paper III-A Jacobian.
    n_line_search : int
        Total back-tracking line search steps used (admissibility guard).
    initial_guess_kind : str
        Label for the initial guess source.
    """
    Theta: AxisymmetricField
    n_iter: int
    residual_history: tuple
    converged: bool
    jacobian_cond: float
    n_line_search: int
    initial_guess_kind: str

    @property
    def final_residual(self) -> float:
        """Final relative residual ||F(Theta) - T_obs|| / ||T_obs||."""
        return self.residual_history[-1]


# ============================================================================
# Section 4 - Newton iteration main driver
# ============================================================================

def invert_T_to_Theta_axisymmetric(
    T_ell_obs: np.ndarray,
    xi: int,
    eta: Optional[AxisymmetricField] = None,
    moment_order: int = 3,
    L_Theta: Optional[int] = None,
    max_iter: int = 50,
    tol: float = 1e-10,
    n_quad: Optional[int] = None,
    initial_guess: Optional[AxisymmetricField] = None,
    line_search_max: int = 12,
    check_admissibility: bool = True,
) -> InverseResult:
    """Newton-iteration inverse of the Paper I forward map (axisymmetric).

    Solves for Theta(mu) = Sum_ell Theta_ell P_ell(mu) such that
    `axisymmetric_F(xi, Theta, eta, L_out=L_T)` reproduces T_ell_obs.

    Algorithm
    ---------
    1. Initial guess: `linear_response_inverse(T_ell_obs, xi, eta_0, n)` where
       eta_0 is the monopole of eta (0 if eta is None), unless `initial_guess`
       is supplied.
    2. At each iterate, assemble F and J via `_build_jacobian`.
    3. Newton step: dTheta = -solve(J, F - T_obs). Reject if Theta + dTheta
       fails admissibility; back-track with dTheta /= 2.
    4. Terminate when ||F - T_obs|| / ||T_obs|| < tol or max_iter reached.

    Parameters
    ----------
    T_ell_obs : ndarray shape (L_T+1,)
        Observed axisymmetric multipoles.
    xi : int
        Statistics in {-1, 0, +1}.
    eta : AxisymmetricField, optional
        Given fugacity field. None => one-field (eta == 0).
    moment_order : int, optional
        n in I_n (default 3).
    L_Theta : int, optional
        Highest Theta multipole to recover. Defaults to L_T (square system).
    max_iter : int, optional
        Maximum Newton iterations (default 50).
    tol : float, optional
        Relative residual convergence target (default 1e-10).
    n_quad : int, optional
        Gauss-Legendre points; heuristic default scales with L.
    initial_guess : AxisymmetricField, optional
        Override the linear-response initial guess.
    line_search_max : int, optional
        Maximum back-tracking halvings per Newton step.
    check_admissibility : bool, optional
        If True, reject steps that violate Theta > 0 (and eta <= 0 for BE).

    Returns
    -------
    InverseResult
        Recovered Theta plus diagnostics.

    Raises
    ------
    ValueError
        Bad xi / moment_order, or initial guess violates admissibility.
    RuntimeError
        Newton iteration fails to make progress under back-tracking.
    """
    if xi not in (-1, 0, +1):
        raise ValueError(f"xi must be in {{-1, 0, +1}}, got {xi}")
    if moment_order not in (2, 3, 4):
        raise ValueError(f"moment_order must be 2, 3, 4, got {moment_order}")

    T_obs = np.asarray(T_ell_obs, dtype=float)
    if T_obs.ndim != 1:
        raise ValueError(f"T_ell_obs must be 1D, got shape {T_obs.shape}")
    L_T = len(T_obs) - 1
    if L_Theta is None:
        L_Theta = L_T
    if L_Theta != L_T:
        raise ValueError(
            f"Day 1 scope requires square system L_Theta == L_T "
            f"(got L_Theta = {L_Theta}, L_T = {L_T})"
        )

    # Background fugacity monopole for linear-response inverse
    eta_bg = 0.0 if eta is None else float(eta.coeffs[0])

    # BE admissibility sanity on given eta
    if xi == +1 and eta is not None:
        if not check_be_admissibility(eta):
            raise ValueError("BE requires eta(mu) <= 0 on [-1, 1]")

    # Initial guess
    if initial_guess is not None:
        Theta_coeffs = np.asarray(initial_guess.coeffs, dtype=float).copy()
        # Pad / truncate to L_Theta+1
        if len(Theta_coeffs) < L_Theta + 1:
            Theta_coeffs = np.concatenate([
                Theta_coeffs, np.zeros(L_Theta + 1 - len(Theta_coeffs))
            ])
        else:
            Theta_coeffs = Theta_coeffs[: L_Theta + 1]
        guess_kind = "user_supplied"
    else:
        Theta_coeffs = linear_response_inverse(
            T_obs, xi, eta_bg=eta_bg, moment_order=moment_order,
        )
        guess_kind = "linear_response"

    # Check initial admissibility
    Theta_current = AxisymmetricField(coeffs=Theta_coeffs, name="Theta_init")
    if check_admissibility and not check_theta_positive(Theta_current):
        raise ValueError(
            "Initial guess violates Theta(mu) > 0; supply a different "
            "initial_guess or check the observation."
        )

    # Quadrature size heuristic
    if n_quad is None:
        # Theta^{n+1} is polynomial of degree (n+1) * L_Theta in mu-series
        # approximation; combined with P_ell P_m test functions gives total
        # degree (n+1) * L_Theta + 2 * L_T. Gauss-Legendre of order k
        # integrates polynomials up to 2k - 1 exactly.
        min_order = (moment_order + 1) * L_Theta + 2 * L_T
        L_eta = 0 if eta is None else eta.L_max
        n_quad = max(32, min_order + 4 * L_eta + 8)

    # Norm of observation for relative residual
    T_norm = float(np.linalg.norm(T_obs))
    if T_norm == 0.0:
        raise ValueError("All-zero observation T_obs is not invertible")

    residual_history = []
    total_ls_steps = 0
    jacobian_cond = np.nan
    converged = False

    # Initial residual
    _, F_vals, _ = _build_jacobian(
        Theta_coeffs, xi, eta, moment_order, L_T, n_quad,
    )
    r = F_vals - T_obs
    rel_res = float(np.linalg.norm(r)) / T_norm
    residual_history.append(rel_res)

    if rel_res < tol:
        converged = True
        n_iter = 0
        # Still compute final Jacobian cond for reporting
        J, _, _ = _build_jacobian(
            Theta_coeffs, xi, eta, moment_order, L_T, n_quad,
        )
        jacobian_cond = float(np.linalg.cond(J))
        return InverseResult(
            Theta=AxisymmetricField(coeffs=Theta_coeffs, name="Theta_inv"),
            n_iter=n_iter,
            residual_history=tuple(residual_history),
            converged=converged,
            jacobian_cond=jacobian_cond,
            n_line_search=total_ls_steps,
            initial_guess_kind=guess_kind,
        )

    # Newton iterations
    n_iter = 0
    for k in range(max_iter):
        n_iter = k + 1
        J, F_vals, _ = _build_jacobian(
            Theta_coeffs, xi, eta, moment_order, L_T, n_quad,
        )
        r = F_vals - T_obs

        # Solve J * dTheta = -r
        try:
            dTheta = np.linalg.solve(J, -r)
        except np.linalg.LinAlgError as e:
            raise RuntimeError(
                f"Newton step failed at iter {n_iter}: Jacobian singular ({e})"
            )

        # Line search with admissibility guard
        alpha = 1.0
        accepted = False
        for ls in range(line_search_max + 1):
            candidate = Theta_coeffs + alpha * dTheta
            Theta_cand = AxisymmetricField(
                coeffs=candidate, name="Theta_cand",
            )
            # Admissibility
            ok = True
            if check_admissibility and not check_theta_positive(Theta_cand):
                ok = False
            if ok:
                # Check residual decrease (Armijo-like lenient)
                _, F_cand, _ = _build_jacobian(
                    candidate, xi, eta, moment_order, L_T, n_quad,
                )
                r_cand = F_cand - T_obs
                rel_cand = float(np.linalg.norm(r_cand)) / T_norm
                if rel_cand < rel_res * (1.0 - 1e-4 * alpha) or alpha < 2 ** (-line_search_max):
                    Theta_coeffs = candidate
                    rel_res = rel_cand
                    accepted = True
                    break
            alpha *= 0.5
            total_ls_steps += 1

        residual_history.append(rel_res)

        if not accepted:
            raise RuntimeError(
                f"Newton iter {n_iter}: back-tracking line search exhausted "
                f"({line_search_max} halvings) without admissible progress."
            )

        if rel_res < tol:
            converged = True
            break

    # Final Jacobian diagnostics
    J_final, _, _ = _build_jacobian(
        Theta_coeffs, xi, eta, moment_order, L_T, n_quad,
    )
    jacobian_cond = float(np.linalg.cond(J_final))

    return InverseResult(
        Theta=AxisymmetricField(coeffs=Theta_coeffs, name="Theta_inv"),
        n_iter=n_iter,
        residual_history=tuple(residual_history),
        converged=converged,
        jacobian_cond=jacobian_cond,
        n_line_search=total_ls_steps,
        initial_guess_kind=guess_kind,
    )


# ============================================================================
# Section 5 - Roundtrip helper
# ============================================================================

def roundtrip_relative_error(
    Theta_true: AxisymmetricField,
    xi: int,
    eta: Optional[AxisymmetricField] = None,
    moment_order: int = 3,
    L_out: Optional[int] = None,
    tol: float = 1e-10,
    n_quad: Optional[int] = None,
) -> tuple[float, InverseResult]:
    """Roundtrip F^{-1} o F applied to Theta_true and return closure error.

    Parameters
    ----------
    Theta_true : AxisymmetricField
        Ground truth direction-dependent temperature.
    xi : int
    eta : AxisymmetricField, optional
    moment_order : int
    L_out : int, optional
        Number of multipoles to use in forward map; defaults to Theta_true.L_max.
    tol : float, optional
    n_quad : int, optional

    Returns
    -------
    max_relative_error : float
        max_ell |Theta_ell^{rec} - Theta_ell^{true}| / max(|Theta_ell^{true}|, 1e-300).
        The per-coefficient scale is guarded against division by zero for
        vanishing true coefficients.
    result : InverseResult
    """
    if L_out is None:
        L_out = Theta_true.L_max

    fwd = axisymmetric_F(
        xi=xi, Theta=Theta_true, eta=eta,
        L_out=L_out, moment_order=moment_order, n_quad=n_quad,
    )
    result = invert_T_to_Theta_axisymmetric(
        T_ell_obs=fwd.T_ell, xi=xi, eta=eta,
        moment_order=moment_order, L_Theta=L_out,
        tol=tol, n_quad=n_quad,
    )

    # Pad Theta_true.coeffs to L_out+1
    true_coeffs = np.zeros(L_out + 1)
    n_true = min(len(Theta_true.coeffs), L_out + 1)
    true_coeffs[:n_true] = Theta_true.coeffs[:n_true]

    rec_coeffs = result.Theta.coeffs
    scale = np.maximum(np.abs(true_coeffs), 1e-300)
    per_mode_err = np.abs(rec_coeffs - true_coeffs) / scale

    # If Theta_ell is zero in truth, report absolute; else relative
    # Use an informative mixed-scale max
    absolute_floor = 1e-12  # machine-ish
    mixed = np.where(
        np.abs(true_coeffs) > absolute_floor,
        per_mode_err,
        np.abs(rec_coeffs - true_coeffs),  # absolute for zero modes
    )
    max_rel = float(np.max(mixed))
    return max_rel, result


# ============================================================================
# Section 6 - Jacobian finite-difference check (verification helper)
# ============================================================================

def jacobian_finite_difference(
    Theta_coeffs: np.ndarray,
    xi: int,
    eta: Optional[AxisymmetricField] = None,
    moment_order: int = 3,
    L_out: int = 3,
    n_quad: int = 64,
    h: float = 1e-6,
) -> np.ndarray:
    """Central finite-difference Jacobian for unit testing.

    Returns J_fd[ell, m] ~ (F(Theta + h e_m)_ell - F(Theta - h e_m)_ell) / (2 h).
    """
    L_Theta = len(Theta_coeffs) - 1
    J_fd = np.zeros((L_out + 1, L_Theta + 1))
    for m in range(L_Theta + 1):
        coeffs_p = Theta_coeffs.copy()
        coeffs_m = Theta_coeffs.copy()
        coeffs_p[m] += h
        coeffs_m[m] -= h
        Theta_p = AxisymmetricField(coeffs=coeffs_p, name="Theta_p")
        Theta_m = AxisymmetricField(coeffs=coeffs_m, name="Theta_m")
        fwd_p = axisymmetric_F(
            xi=xi, Theta=Theta_p, eta=eta,
            L_out=L_out, moment_order=moment_order, n_quad=n_quad,
            check_admissibility=False,
        )
        fwd_m = axisymmetric_F(
            xi=xi, Theta=Theta_m, eta=eta,
            L_out=L_out, moment_order=moment_order, n_quad=n_quad,
            check_admissibility=False,
        )
        J_fd[:, m] = (fwd_p.T_ell - fwd_m.T_ell) / (2.0 * h)
    return J_fd
