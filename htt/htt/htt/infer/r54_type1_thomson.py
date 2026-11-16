"""R54 homogeneous-mode (k = 0) Thomson response of the CMB quadrupole to type-I shear.

Scope (claim ceiling C0, transfer source = first-order homogeneous-mode Thomson
system; this is NOT a native Bianchi Boltzmann solver, AGENTS.md boundary 1;
``bass/collision/thomson_pstf.py`` remains the owner of the general collision
operator):

* closed-form temperature and E-mode history kernels K_T, K_E (R54-EQ-03);
* the linear shear / photon / neutrino quadrupole system with radiation
  anisotropic stress (R54-EQ-05), which replaces the perfect-fluid history
  operator ``I_hist`` of R51 wherever a present-day or cross-epoch shear is
  quoted;
* history functionals Sigma_T, Sigma_E (R54-EQ-04) that are fixed by the
  ionization history alone and do not depend on the shear dynamics.

Conventions (identical to ``r51_source_bound_response``): metric (-,+,+,+);
``n`` is the sky direction; dT/T(n) = Theta_ab n^a n^b = -Sigma^T_ab n^a n^b.
Time variable N = ln a (a = 1 today). Shear rate s_ab = sigma_ab / H is
dimensionless. All equations are per STF component: the system is linear with
scalar coefficients, so every STF5 component evolves with the same kernels.

Equation register (also in R54 THEORY/L1 and LOCAL_AGENT_CONTRACT.json):

R54-EQ-01  d Theta/dN = -s - kappa [ (9/10) Theta + (sqrt6/10) Ecal ]
R54-EQ-02  d Ecal /dN =      - kappa [ (sqrt6/10) Theta + (4/10) Ecal ]
           kappa(N) = n_e sigma_T c / H = d tau / d ln(1+z),  tau(N) = int_N^0 kappa dN'
           (Hu & White 1997 total-angular-momentum hierarchy at k = 0, ell = 2;
            P = (Theta_2 - sqrt6 E_2)/10.)
R54-EQ-03  K_T(tau) = (6 e^{-tau} + e^{-3 tau/10}) / 7
           K_E(tau) = (sqrt6/7) (e^{-3 tau/10} - e^{-tau})
R54-EQ-04  Sigma_T = -Theta(N=0) = int K_T(tau(N)) s(N) dN
           Sigma_E = +Ecal(N=0)  = int K_E(tau(N)) s(N) dN
           HEALPix sign: a^E_2m carries the same STF tensor sign as a^T_2m
           (a^T_2m <-> -T0 n.Sigma_T.n, a^E_2m <-> -T0 n.Sigma_E.n).
R54-EQ-05  ds/dN = -(3 + dlnH/dN) s + (8/5) [ Omega_gamma(N) Theta + Omega_nu(N) Ncal ]
           d Ncal/dN = -s                       (massless collisionless neutrinos)
           from sigma_dot + 3 H sigma = 8 pi G pi, pi = (8/15) rho Theta.
R54-EQ-06  massive collisionless species at k = 0, first order: with the accumulated shear beta_ij = int s_ij dN = -Ncal_ij
           the distribution is f0(a p (1 + beta_ij n^i n^j)) and
           pi_ij = -(2/15) beta_ij Kcal,   Kcal = 4 pi int dp f0(p) p^4 (4 p^2 + 5 m^2)/E^3   (Kcal = 4 rho for m = 0)
           W(mu) = Kcal/(4 rho_massless) = int dx x^4 (4x^2 + 5mu^2)/(x^2 + mu^2)^(3/2) f(x) / [4 int dx x^3 f(x)],
           f = 1/(e^x + 1), mu = m a/T_nu0;  W(0) = 1, W -> (5/(4 mu)) I_4/I_3 for mu >> 1.
           The neutrino term of R54-EQ-05 becomes Omega_nu^massless(N) <W>(N) Ncal.
"""
from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Callable

import numpy as np
from scipy import integrate
from scipy.interpolate import PchipInterpolator

SQRT6 = math.sqrt(6.0)
#: Thomson collision matrix acting on (Theta, Ecal); eigenvalues 1 and 3/10.
THOMSON_M = np.array([[0.9, SQRT6 / 10.0], [SQRT6 / 10.0, 0.4]])

STRESS_NONE = "perfect_fluid"
STRESS_PHOTON = "photon_stress"
STRESS_PHOTON_NEUTRINO = "photon_neutrino_stress"
_STRESS_MODES = (STRESS_NONE, STRESS_PHOTON, STRESS_PHOTON_NEUTRINO)


def thomson_propagator(tau: float) -> np.ndarray:
    """exp(-M tau) in closed form: e^{-tau} v1 v1^T/7 + e^{-3 tau/10} v2 v2^T/7.

    v1 = (sqrt6, 1) (eigenvalue 1), v2 = (1, -sqrt6) (eigenvalue 3/10).
    """
    if not (math.isfinite(tau) and tau >= 0.0):
        raise ValueError("optical depth must be finite and non-negative")
    e1, e2 = math.exp(-tau), math.exp(-0.3 * tau)
    return np.array(
        [[(6.0 * e1 + e2) / 7.0, SQRT6 * (e1 - e2) / 7.0], [SQRT6 * (e1 - e2) / 7.0, (e1 + 6.0 * e2) / 7.0]]
    )


def thomson_kernels(tau: np.ndarray | float) -> tuple[np.ndarray, np.ndarray]:
    """(K_T, K_E) of R54-EQ-03 for optical depth ``tau`` between the epoch and today."""
    t = np.asarray(tau, float)
    if not np.isfinite(t).all() or (t < 0).any():
        raise ValueError("optical depth must be finite and non-negative")
    e1, e2 = np.exp(-t), np.exp(-0.3 * t)
    return (6.0 * e1 + e2) / 7.0, SQRT6 * (e2 - e1) / 7.0


@dataclass(frozen=True)
class FlatBackground:
    """Flat LCDM + massless radiation. Densities are today's fractions of critical."""

    omega_m: float
    omega_gamma: float
    omega_nu: float

    def __post_init__(self) -> None:
        if min(self.omega_m, self.omega_gamma, self.omega_nu) < 0 or self.omega_lambda <= 0:
            raise ValueError("invalid flat background")

    @property
    def omega_lambda(self) -> float:
        return 1.0 - self.omega_m - self.omega_gamma - self.omega_nu

    def e2(self, n: float) -> float:
        a = math.exp(n)
        return (self.omega_gamma + self.omega_nu) * a**-4 + self.omega_m * a**-3 + self.omega_lambda

    def dlnh_dn(self, n: float) -> float:
        a = math.exp(n)
        return -0.5 * (4.0 * (self.omega_gamma + self.omega_nu) * a**-4 + 3.0 * self.omega_m * a**-3) / self.e2(n)

    def frac_gamma(self, n: float) -> float:
        return self.omega_gamma * math.exp(-4.0 * n) / self.e2(n)

    def frac_nu(self, n: float) -> float:
        return self.omega_nu * math.exp(-4.0 * n) / self.e2(n)


def planck18_background(h: float = 0.6736, omega_m: float = 0.3153, t_cmb_k: float = 2.72548,
                        n_eff: float = 3.044) -> FlatBackground:
    """Background matching R51/R52 (Planck 2018 VI), neutrinos treated as massless radiation."""
    og = 2.4728e-5 * (t_cmb_k / 2.7255) ** 4 / h**2
    return FlatBackground(omega_m=omega_m, omega_gamma=og, omega_nu=og * 0.22710731766 * n_eff)


class OpticalDepthHistory:
    """Thomson optical depth tau(z) from today, tabulated on increasing z (z[0] = 0).

    Above the table the plasma is taken fully ionized with constant x_e, so
    kappa scales as (1+z)^3 / H(z); ``e2_of_n`` supplies the background for that
    extrapolation.
    """

    def __init__(self, z: np.ndarray, tau: np.ndarray, e2_of_n: Callable[[float], float]):
        z, tau = np.asarray(z, float), np.asarray(tau, float)
        if z.ndim != 1 or z.shape != tau.shape or z.size < 16:
            raise ValueError("z, tau: equal-length 1-D tables with >= 16 points required")
        if z[0] != 0.0 or tau[0] != 0.0 or (np.diff(z) <= 0).any() or (np.diff(tau) < 0).any():
            raise ValueError("tables must start at z=0, tau=0 and be monotone")
        self._x = np.log1p(z)
        self._tau_tab_max = float(tau[-1])
        # monotone C1 interpolant: kappa is its exact derivative, so the kernel
        # form (R54-EQ-04) and the ODE form (R54-EQ-01/02) see one history
        self._pchip = PchipInterpolator(self._x, tau, extrapolate=False)
        self._dpchip = self._pchip.derivative()
        self._kappa_max = float(self._dpchip(self._x[-1]))
        self._e2 = e2_of_n
        self.z_max = float(z[-1])

    def tau(self, n: float) -> float:
        x = -n
        if x < 0.0:
            raise ValueError("N must be <= 0")
        if x <= self._x[-1]:
            return float(self._pchip(x))
        # analytic continuation: integrate kappa above the table
        val, _ = integrate.quad(lambda xx: self.kappa(-xx), self._x[-1], x, epsrel=1e-10, limit=200)
        return float(self._tau_tab_max + val)

    def kappa(self, n: float) -> float:
        """kappa = d tau / d ln(1+z) >= 0 at N = ln a."""
        x = -n
        if x < 0.0:
            raise ValueError("N must be <= 0")
        if x <= self._x[-1]:
            return float(max(self._dpchip(x), 0.0))
        xm = self._x[-1]
        return float(self._kappa_max * math.exp(3.0 * (x - xm)) * math.sqrt(self._e2(-xm) / self._e2(-x)))


def perfect_fluid_shear(bg: FlatBackground, n: np.ndarray | float) -> np.ndarray:
    """s(N)/s(0) for sigma a^3 = const (no anisotropic stress): e^{-3N}/E(N)."""
    nn = np.atleast_1d(np.asarray(n, float))
    return np.array([math.exp(-3.0 * x) / math.sqrt(bg.e2(x)) for x in nn])


def history_functionals(s_of_n: Callable[[float], float], hist: OpticalDepthHistory,
                        n_start: float, n_end: float = 0.0, n_panels: int = 3000) -> dict[str, float]:
    """Sigma_T, Sigma_E of R54-EQ-04 for a prescribed shear history s(N) on [n_start, n_end]."""
    if not n_start < n_end <= 0.0:
        raise ValueError("require n_start < n_end <= 0")

    # deterministic composite Gauss-Legendre in N (panels resolve recombination)
    xg, wg = np.polynomial.legendre.leggauss(6)
    edges = np.linspace(n_start, n_end, n_panels + 1)
    half = 0.5 * np.diff(edges)
    mid = 0.5 * (edges[1:] + edges[:-1])
    st = se = 0.0
    for h, m in zip(half, mid):
        for x, w in zip(xg, wg):
            n = m + h * x
            kt, ke = thomson_kernels(hist.tau(n))
            sv = s_of_n(n)
            st += w * h * float(kt) * sv
            se += w * h * float(ke) * sv
    if not (math.isfinite(st) and math.isfinite(se)):
        raise ArithmeticError("history functional not finite")
    return {"Sigma_T": st, "Sigma_E": se, "n_panels": n_panels}


def solve_type1_history(
    bg: FlatBackground,
    hist: OpticalDepthHistory,
    stress: str,
    z_init: float,
    s_init: float = 1.0,
    ncal_init: float = 0.0,
    z_tight: float = 5.0e4,
    neutrino_stress_scale: Callable[[float], float] | None = None,
    rtol: float = 1e-9,
    atol: float = 1e-14,
    n_eval: np.ndarray | None = None,
) -> dict:
    """Integrate R54-EQ-01/02/05 from z_init to today.

    State y = (s, Theta, Ecal, Ncal). For z > z_tight photons are tightly coupled
    and Theta = Ecal = 0 is imposed exactly (kappa > 1e4 there), which removes
    the stiff transient. ``neutrino_stress_scale(N)`` multiplies the neutrino
    stress (default 1: massless); it exists only for the mass-sensitivity test.
    Returns today's (s, Sigma_T, Sigma_E, Ncal) and, if ``n_eval`` is given, the
    state on those epochs (``n``, ``y`` with rows s, Theta, Ecal, Ncal).
    """
    if stress not in _STRESS_MODES:
        raise ValueError(f"stress must be one of {_STRESS_MODES}")
    if z_init <= 0:
        raise ValueError("z_init must be positive")
    use_g = stress in (STRESS_PHOTON, STRESS_PHOTON_NEUTRINO)
    use_nu = stress == STRESS_PHOTON_NEUTRINO
    scale = neutrino_stress_scale or (lambda _n: 1.0)

    def rhs(n: float, y: np.ndarray, tight: bool) -> list[float]:
        s, th, ec, nc = y
        src = 0.0
        if use_g and not tight:
            src += bg.frac_gamma(n) * th
        if use_nu:
            src += scale(n) * bg.frac_nu(n) * nc
        ds = -(3.0 + bg.dlnh_dn(n)) * s + 1.6 * src
        if tight:
            return [ds, 0.0, 0.0, -s]
        k = hist.kappa(n)
        return [ds, -s - k * (0.9 * th + SQRT6 / 10.0 * ec), -k * (SQRT6 / 10.0 * th + 0.4 * ec), -s]

    n0 = -math.log1p(z_init)
    n_t = -math.log1p(z_tight)
    segments = [(n0, n_t, True), (n_t, 0.0, False)] if n0 < n_t else [(n0, 0.0, False)]
    y = np.array([s_init, 0.0, 0.0, ncal_init], float)
    out_n: list[np.ndarray] = []
    out_y: list[np.ndarray] = []
    for a, b, tight in segments:
        sol = integrate.solve_ivp(lambda n, yy, tt=tight: rhs(n, yy, tt), (a, b), y,
                                  method="DOP853" if tight else "Radau", rtol=rtol, atol=atol, dense_output=n_eval is not None)
        if not sol.success:
            raise ArithmeticError(f"history ODE failed: {sol.message}")
        if n_eval is not None:
            sel = np.asarray(n_eval, float)
            sel = sel[(sel >= a) & (sel <= b)] if not out_n else sel[(sel > a) & (sel <= b)]
            if sel.size:
                out_n.append(sel)
                out_y.append(sol.sol(sel))
        y = sol.y[:, -1]
    out: dict = {"stress": stress, "s_today": float(y[0]), "Sigma_T": float(-y[1]), "Sigma_E": float(y[2]),
                 "Ncal_today": float(y[3])}
    if out_n:
        out["n"] = np.concatenate(out_n)
        out["y"] = np.concatenate(out_y, axis=1)
    return out


K_B_EV_PER_K = 8.617333262e-5


def massive_stress_weight(mu: np.ndarray | float) -> np.ndarray:
    """W(mu) of R54-EQ-06: anisotropic stress of a collisionless Fermi-Dirac species of mass m relative to the
    massless value for the same accumulated shear; mu = m / T_nu at the epoch considered."""
    mu = np.atleast_1d(np.asarray(mu, float))
    if (mu < 0).any() or not np.isfinite(mu).all():
        raise ValueError("mu must be finite and non-negative")
    x, w = np.polynomial.laguerre.laggauss(100)            # int_0^inf e^-x g(x) dx
    fermi = 1.0 / (1.0 + np.exp(-x))                         # e^-x * fermi = 1/(e^x + 1)
    den = 4.0 * np.sum(w * x**3 * fermi)
    xx, mm = x[None, :], mu[:, None]
    num = np.sum(w[None, :] * fermi[None, :] * xx**4 * (4.0 * xx * xx + 5.0 * mm * mm) / (xx * xx + mm * mm) ** 1.5, axis=1)
    return num / den


def neutrino_stress_scale(masses_ev: tuple[float, ...], t_cmb_k: float = 2.72548) -> Callable[[float], float]:
    """N -> mean over species of W(m_i a / T_nu0): the factor that multiplies the massless neutrino stress in
    ``solve_type1_history`` (equal-temperature species; R54-EQ-06)."""
    masses = np.asarray(masses_ev, float)
    if masses.ndim != 1 or masses.size == 0 or (masses < 0).any():
        raise ValueError("masses must be a non-empty tuple of non-negative values in eV")
    t_nu0 = (4.0 / 11.0) ** (1.0 / 3.0) * t_cmb_k * K_B_EV_PER_K
    grid = np.linspace(-26.0, 0.5, 2400)
    table = np.mean([massive_stress_weight(m * np.exp(grid) / t_nu0) for m in masses], axis=0)
    interp = PchipInterpolator(grid, table)
    return lambda n: float(interp(min(max(n, grid[0]), grid[-1])))


def e_to_t_ratio(result: dict) -> float:
    """r_E = Sigma_E / Sigma_T; raises if the temperature functional vanishes."""
    st = float(result["Sigma_T"])
    if st == 0.0:
        raise ZeroDivisionError("Sigma_T = 0: ratio undefined")
    return float(result["Sigma_E"]) / st
