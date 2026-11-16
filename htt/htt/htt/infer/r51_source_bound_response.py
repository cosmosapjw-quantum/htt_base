"""R51 source-bound responses, normalized laws and response-term quarantine.

Scope (R51, claim ceiling C0):

* Equation-labelled forward operators that are checked against an exact
  reference limit in ``tests/r51``.
* A registry classifying every response coefficient used by the R49 joint
  likelihood and the linearized transfer as SOURCE_BOUND, CONDITIONAL
  (derived under stated assumptions) or WORKING_MODEL (phenomenological,
  excluded from physical inference).
* One normalized Gaussian law in which mean and covariance may depend on the
  same modes, a finite-Monte-Carlo (Sellentin & Heavens 2016) law, and a
  data-block identity registry that blocks independent re-use of one dataset.

No native Bianchi Boltzmann transfer is implemented here (AGENTS.md boundary 1).

Conventions: metric (-,+,+,+), c retained; ``n`` is the sky direction from the
observer to the source; the photon propagates along ``-n``.
"""
from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Any

import numpy as np
from scipy import integrate
from scipy.linalg import expm
from scipy.special import gammaln
from scipy.stats import chi2 as chi2_dist
from scipy.stats import f as f_dist

# -----------------------------------------------------------------------------
# Response-term registry
# -----------------------------------------------------------------------------

T_CMB_K_SSOT: float = 2.72548  # docs/SSOT_POLICY.md

SOURCE_BOUND = "SOURCE_BOUND"
CONDITIONAL = "CONDITIONAL_DERIVED"
WORKING_MODEL = "WORKING_MODEL_EXCLUDED_FROM_PHYSICAL_INFERENCE"

#: Every response term used by R49 forward models. ``location`` is the R49
#: commit 36bd9030 source location. Working-model terms keep their numbers only
#: for reproducing historical receipts; they carry no physical name.
RESPONSE_TERM_REGISTRY: tuple[dict[str, Any], ...] = (
    {
        "id": "CMB_T_TYPE_I_INTEGRATED_SHEAR",
        "location": "bass/transport/general_bianchi_transfer.py:_evaluate_linearized_near_flrw_sky (type-I boundary)",
        "equation": "dT/T(n) = -n^a n^b Sigma_ab, Sigma_ab = int_{t_*}^{t_0} sigma_ab dt (first order)",
        "exact_reference": "T(n) = T_bar / sqrt(n^T exp(2 Sigma) n) for Bianchi I with fixed shear eigenframe",
        "source": "Collins & Hawking 1973 MNRAS 162 307; Barrow, Juszkiewicz & Sonoda 1985 MNRAS 213 917",
        "status": SOURCE_BOUND,
        "parameter_semantics": "Sigma_ab: dimensionless line-of-sight integrated shear (last scattering -> observer); NOT sigma/H0 today",
    },
    {
        "id": "SHEAR_HISTORY_OPERATOR_TYPE_I",
        "location": "new in R51 (bianchi_i_shear_history_integral)",
        "equation": "Sigma_ab = I_hist (sigma_ab/H)_0, I_hist = int_{a_*}^{1} a^-4 / E(a) da",
        "source": "sigma a^3 = const for Bianchi I perfect fluids without anisotropic stress (Ellis & MacCallum 1969)",
        "status": CONDITIONAL,
        "assumptions": [
            "no anisotropic stress (free-streaming neutrinos damp shear and violate this)",
            "near-FLRW LCDM expansion E(a); shear back-reaction neglected",
            "fixed shear eigenframe (type I)",
        ],
        "systematics": "67% of I_hist comes from z>500 where radiation (24% of density at z_*) and free-streaming "
                       "neutrino anisotropic stress act; the neutrino-damped history is not computed, so any sigma/H0 "
                       "value derived through I_hist is conditional and carries an unquantified systematic",
    },
    {
        "id": "CMB_TYPE_I_POLARIZATION_GAIN_0p18",
        "location": "general_bianchi_transfer.py:TiltedTransferParameters.polarization_to_shear_gain=0.18",
        "equation": "Pi_emit = 0.18 sigma_N + 0.5 Q_kin(v_rel)",
        "source": None,
        "status": WORKING_MODEL,
        "reason": "Thomson quadrupole requires visibility-weighted transfer; coefficient unsourced",
    },
    {
        "id": "CMB_FINITE_CURVATURE_FOCUS_TWIST",
        "location": "general_bianchi_transfer.py:932-1021 (0.25/0.35 floors, tanh(0.6 x), 0.6+0.4nz, 1+0.3(...))",
        "equation": None,
        "source": None,
        "status": WORKING_MODEL,
        "reason": "focusing/twist profiles and floors not derived from V/VII_h/VII_0/IX geodesics",
    },
    {
        "id": "CMB_COVARIANCE_EXCESS_1e-8",
        "location": "r49_general_bianchi_likelihood.py:_predict_cmb_vector",
        "equation": "C_ll += 1e-8 (T_CMB uK)^2 |sigma|^2 on covariance modes",
        "source": None,
        "status": WORKING_MODEL,
    },
    {
        "id": "CMB_SIGMA_AS_TODAY_SHEAR",
        "location": "r49_general_bianchi_likelihood.py:_predict_cmb_vector (sigma_N=state.sigma_matrix)",
        "equation": "uses (sigma/H)_0 as Sigma_ab, i.e. history operator := 1",
        "source": None,
        "status": WORKING_MODEL,
        "reason": "epoch conflation; physical Bianchi-I history operator I_hist = 3.93e4 (Planck18, conditional) (see SHEAR_HISTORY_OPERATOR_TYPE_I)",
    },
    {
        "id": "CMB_EMISSION_AND_OBSERVER_KINEMATIC_ELL_GE_2",
        "location": "general_bianchi_transfer.py emission Doppler (v_rad - v_matter) and _apply_observer_boost_on_sky_grid",
        "equation": "T_obs = T/[gamma (1 - beta.n)] (exact Lorentz); ell>=2 at O(beta^2, beta Sigma)",
        "source": "exact Lorentz transformation of a Planck spectrum (e.g. Challinor & van Leeuwen 2002)",
        "status": SOURCE_BOUND,
        "r51_usage": "EXCLUDED from the R51 source-bound CMB evaluation (velocities set to 0) until the "
                     "kinematic-quadrupole removal contract of map and MC is bound",
    },
    {
        "id": "COUNT_DIPOLE_KINEMATIC",
        "location": "r49_general_bianchi_likelihood.py:logp_by_probe (c_eb * beta_MO)",
        "equation": "d = [2 + x(1+alpha)] beta_obs_src, beta_obs_src = beta_MO if sources comove with matter",
        "source": "Ellis & Baldwin 1984 MNRAS 206 377",
        "status": SOURCE_BOUND,
        "assumptions": ["no intrinsic clustering/evolution dipole beyond declared covariance", "x, alpha measured per survey"],
    },
    {
        "id": "COUNT_DIPOLE_0p1_A",
        "location": "r49_general_bianchi_likelihood.py:792 (0.1*A_A)",
        "equation": None, "source": None, "status": WORKING_MODEL,
    },
    {
        "id": "GAIA_E1_H0_BETA_PLUS_A",
        "location": "r49_general_bianchi_likelihood.py:802",
        "equation": "E1 = H0 (beta_MO + A_A) [uas/yr]",
        "source": None,
        "status": WORKING_MODEL,
        "reason": "constant velocity gives static aberration, no drift; drift dipole is observer acceleration a_obs/c (galactic + cosmological), a nuisance here",
    },
    {
        "id": "GAIA_B1_VORTICITY",
        "location": "r49_general_bianchi_likelihood.py:804",
        "equation": "B1 = H0 omega + frame spin", "source": None, "status": WORKING_MODEL,
        "reason": "fully degenerate with marginalized frame spin; omega not identified",
    },
    {
        "id": "GAIA_E2_DIRECT_SHEAR_PLUS_0p25_Q",
        "location": "r49_general_bianchi_likelihood.py:806",
        "equation": "E2 = H0 sigma + 0.25 H0 Q(beta_MO)",
        "source": None,
        "status": WORKING_MODEL,
        "reason": "E2 measures endpoint-history A_PM=2c(B_o-B_s)/D-dot B_o (R50), not sigma/H0; velocity term unsourced",
    },
    {
        "id": "PANTHEON_0p5_A_AND_ORDER_Z_SHEAR",
        "location": "r49_general_bianchi_likelihood.py:836-838",
        "equation": "delta mu = -(5/ln10)[n.(beta_MO - v_m + 0.5 A)/z - 0.5 z n.sigma.n]",
        "source": None,
        "status": WORKING_MODEL,
        "reason": "first-order Heinesen 2021 term is (n.a - sigma_nn)/H at O(z^0); z_HD already boost-corrected upstream",
    },
    {
        "id": "CF4_0p1_Z_A",
        "location": "r49_general_bianchi_likelihood.py:850",
        "equation": None, "source": None, "status": WORKING_MODEL,
    },
    {
        "id": "DESI_DIRECTIONAL_QUAD_AS_SHEAR",
        "location": "scripts/r49/run_r49_cmb_and_multiprobe_lanes.py:796 (contrast*0.02); likelihood:870",
        "equation": "sigma5 := 0.02 * (NGC-SGC contrast), padded 4 unobserved directions",
        "source": None,
        "status": WORKING_MODEL,
    },
    {
        "id": "DESI_BAO_ISOTROPIC",
        "location": "r49_general_bianchi_likelihood.py:856-868",
        "equation": "D_M/r_d, D_H/r_d, D_V/r_d in FLRW background psi",
        "source": "DESI DR2 BAO release definitions",
        "status": SOURCE_BOUND,
    },
)

#: Probes whose R49 response survives in a physical (source-bound) likelihood.
SOURCE_BOUND_PROBES = ("CMB", "Quaia", "NVSS", "RACS", "DESI")
#: Probes with no source-bound response to the R49 theta in R51; deferred to R52.
DEFERRED_PROBES = {
    "Gaia": "E1/B1 are nuisance (observer acceleration, frame spin); E2 needs the R50 endpoint-history operator (R52)",
    "PantheonPlus": "requires low-z Heinesen jet with remainder and z_HD correction binding (R52/L5)",
    "CF4": "grouped distance/selection likelihood and tilt/boost separation (R52)",
}


def registry_status(term_id: str) -> str:
    for row in RESPONSE_TERM_REGISTRY:
        if row["id"] == term_id:
            return row["status"]
    raise KeyError(term_id)


class WorkingModelResponseError(ValueError):
    """A physical (source-bound) evaluation reached a working-model response."""


# -----------------------------------------------------------------------------
# Source-bound forward operators
# -----------------------------------------------------------------------------


def _sym(a: np.ndarray) -> np.ndarray:
    a = np.asarray(a, float)
    if a.shape != (3, 3) or not np.isfinite(a).all():
        raise ValueError("finite 3x3 tensor required")
    return 0.5 * (a + a.T)


def integrated_shear_isw_temperature(n_hat: np.ndarray, sigma_int: np.ndarray) -> np.ndarray:
    """First-order Bianchi-I temperature dT/T(n) = -n^a n^b Sigma_ab (dimensionless)."""
    s = _sym(sigma_int)
    return -np.einsum("...i,ij,...j->...", np.asarray(n_hat, float), s, np.asarray(n_hat, float))


def bianchi_i_exact_temperature_contrast(n_hat: np.ndarray, sigma_int: np.ndarray) -> np.ndarray:
    """Exact Bianchi-I contrast T(n)/[T_* a_*/a_0] - 1 = (n^T e^{2 Sigma} n)^{-1/2} - 1.

    Derivation: comoving momenta p_i are conserved (Killing vectors d_i); with
    a_i = a e^{beta_i} and Delta beta_i = int sigma_i dt in the fixed shear
    eigenframe, E_*/E_0 = (a_0/a_*) sqrt(sum_i n_i^2 e^{2 Delta beta_i}).
    Sigma must be trace-free for (a_*/a_0) to be the volume scale factor ratio.
    """
    s = _sym(sigma_int)
    if abs(np.trace(s)) > 1e-12 * max(1.0, np.abs(s).max()):
        raise ValueError("integrated shear must be trace-free")
    m = expm(2.0 * s)
    n = np.asarray(n_hat, float)
    return np.einsum("...i,ij,...j->...", n, m, n) ** -0.5 - 1.0


def radiation_density_parameter(h: float, t_cmb_k: float = 2.72548, n_eff: float = 3.044) -> float:
    """Omega_r = Omega_gamma (1 + 7/8 (4/11)^{4/3} N_eff), Omega_gamma h^2 = 2.4728e-5 (T/2.7255)^4."""
    og = 2.4728e-5 * (t_cmb_k / 2.7255) ** 4 / h**2
    return og * (1.0 + 0.22710731766 * n_eff)


def bianchi_i_shear_history_integral(
    omega_m: float,
    omega_r: float,
    omega_lambda: float,
    z_star: float,
    omega_k: float = 0.0,
) -> float:
    """I_hist = H0 int_{t_*}^{t_0} sigma(t)/sigma_0 dt = int_{a_*}^1 a^{-4}/E(a) da.

    Valid only under sigma a^3 = const (no anisotropic stress) on a near-FLRW
    background. Integrated in ln a for conditioning.
    """
    if z_star <= 0 or min(omega_m, omega_r) < 0:
        raise ValueError("invalid background")

    def integrand(lna: float) -> float:
        a = math.exp(lna)
        e2 = omega_r * a**-4 + omega_m * a**-3 + omega_k * a**-2 + omega_lambda
        if e2 <= 0:
            raise ValueError("non-positive E^2")
        return a**-3 / math.sqrt(e2)

    val, err = integrate.quad(integrand, -math.log1p(z_star), 0.0, epsabs=0.0, epsrel=1e-11, limit=400)
    if not math.isfinite(val) or err > 1e-8 * abs(val):
        raise ArithmeticError(f"history integral not converged: {val} +- {err}")
    return float(val)


# -----------------------------------------------------------------------------
# Laws
# -----------------------------------------------------------------------------


def _cholesky_spd(c: np.ndarray, name: str = "covariance") -> np.ndarray:
    c = np.asarray(c, float)
    if c.ndim != 2 or c.shape[0] != c.shape[1] or not np.isfinite(c).all():
        raise ValueError(f"{name}: finite square matrix required")
    if not np.allclose(c, c.T, rtol=1e-12, atol=0.0):
        raise ValueError(f"{name}: must be symmetric (no silent symmetrization)")
    try:
        return np.linalg.cholesky(c)
    except np.linalg.LinAlgError as exc:
        raise ValueError(f"{name}: not positive definite; no jitter/pseudoinverse applied") from exc


def gaussian_loglike(residual: np.ndarray, cov: np.ndarray) -> float:
    """Normalized log N(r; 0, C). Mean and covariance may depend on the same modes."""
    r = np.asarray(residual, float)
    L = _cholesky_spd(cov)
    w = np.linalg.solve(L, r)
    return float(-0.5 * (w @ w + 2.0 * np.log(np.diag(L)).sum() + r.size * math.log(2.0 * math.pi)))


def finite_mc_t_loglike(residual: np.ndarray, sample_cov: np.ndarray, n_sims: int) -> float:
    """Sellentin & Heavens (2016, MNRAS 456 L132) law for S estimated from N iid Gaussian sims.

    logL = lgamma(N/2) - lgamma((N-p)/2) - p/2 log(pi (N-1)) - 1/2 logdet S
           - N/2 log(1 + Q/(N-1)),  Q = r^T S^{-1} r.
    Valid only for iid Gaussian realizations of the same observable process,
    S with N-1 degrees of freedom, N > p.
    """
    r = np.asarray(residual, float)
    p, n = r.size, int(n_sims)
    if n <= p:
        raise ValueError(f"finite-MC law requires N > p (N={n}, p={p})")
    L = _cholesky_spd(sample_cov, "sample covariance")
    w = np.linalg.solve(L, r)
    q = float(w @ w)
    return float(
        gammaln(n / 2.0) - gammaln((n - p) / 2.0) - 0.5 * p * math.log(math.pi * (n - 1))
        - np.log(np.diag(L)).sum() - 0.5 * n * math.log1p(q / (n - 1))
    )


def heldout_pit(x: np.ndarray, train: np.ndarray) -> dict[str, float]:
    """Predictive PIT of a held-out realization x under train-sample S and mean.

    finite-MC (Hotelling): T2 = (x-xbar)^T S^-1 (x-xbar)/(1+1/N),
      T2 (N-p)/(p (N-1)) ~ F(p, N-p) exactly for iid Gaussian.
    plug-in Gaussian: chi2_p of (x-xbar)^T S^-1 (x-xbar).
    """
    tr = np.asarray(train, float)
    n, p = tr.shape
    if n <= p:
        raise ValueError("N > p required")
    xbar = tr.mean(axis=0)
    S = np.cov(tr.T, ddof=1)
    L = _cholesky_spd(S, "train covariance")
    w = np.linalg.solve(L, np.asarray(x, float) - xbar)
    q = float(w @ w)
    t2 = q / (1.0 + 1.0 / n)
    return {
        "q": q,
        "pit_finite_mc": float(f_dist.cdf(t2 * (n - p) / (p * (n - 1)), p, n - p)),
        "pit_plugin_gaussian": float(chi2_dist.cdf(q, p)),
    }


# -----------------------------------------------------------------------------
# Signed carriers
# -----------------------------------------------------------------------------


def signed_linear_carrier(design: np.ndarray, data: np.ndarray, cov: np.ndarray) -> dict[str, np.ndarray | float]:
    """Return (F, t, Q0) for r(theta) = d - J theta under covariance C.

    Q(theta) = Q0 - 2 theta.t + theta.F.theta. (F,t) gives all Gaussian
    likelihood ratios; the finite-MC law additionally needs the scalar Q0.
    """
    J, d = np.asarray(design, float), np.asarray(data, float)
    L = _cholesky_spd(cov)
    Jw, dw = np.linalg.solve(L, J), np.linalg.solve(L, d)
    F = Jw.T @ Jw
    return {"F": 0.5 * (F + F.T), "t": Jw.T @ dw, "Q0": float(dw @ dw)}


def carrier_quadratic(carrier: dict[str, Any], theta: np.ndarray) -> float:
    th = np.asarray(theta, float)
    return float(carrier["Q0"] - 2.0 * th @ carrier["t"] + th @ carrier["F"] @ th)


# -----------------------------------------------------------------------------
# Data-block identity
# -----------------------------------------------------------------------------


class DuplicateDataBlockError(ValueError):
    """The same data block entered two independent likelihood factors."""


@dataclass
class DataBlockRegistry:
    """Unique-provenance guard: one data block may feed only one likelihood factor."""

    owners: dict[str, str] = field(default_factory=dict)

    def register(self, block_id: str, factor: str) -> None:
        if not block_id:
            raise ValueError(f"factor {factor!r}: empty data-block identity")
        prev = self.owners.get(block_id)
        if prev is not None and prev != factor:
            raise DuplicateDataBlockError(
                f"data block {block_id!r} already enters factor {prev!r}; refusing independent factor {factor!r}"
            )
        self.owners[block_id] = factor
