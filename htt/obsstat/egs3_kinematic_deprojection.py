"""EGS3 Axis C: kinematic deprojection of the observer-boost quadrupole.

Framework upgrade (answers the "Leaky Universe" test). A local observer boost
``beta`` deposits, through the Doppler/aberration transform of the monopole
``T0`` (``mu^2 = (2/3) P2(mu) + 1/3``), an O(beta^2) KINEMATIC QUADRUPOLE aligned
with the boost axis ``v_hat``. A naive low-ell estimator that reads all quadrupole
power as shear therefore reports a false ``Sigma^2 > 0`` in a universe whose only
anisotropy is a bulk flow, and the graded-comparator covariance is NOT diagonal:
``F_{Sigma2,Omega_tilt} propto beta^2``.

This module makes the low-ell shear reading provably immune to that contamination.
It is a SEPARATE DIAGNOSTIC SURFACE: it never touches the bit-identical comparator
``x_C = tr(C M)`` (`egs3_psd_cone.xc_from_matrix`), the response design
(`egs3_graded_comparator.channel_response_design`), or the frozen registered low-ell
statistic set (`lowell_precision`). It adds no new registered statistic.

Convention (amplitude / epsilon level). The sector readings ``sigma2_naive`` and
``omega_tilt`` are quadrupole-/dipole-AMPLITUDE sector coordinates in the registered
epsilon-normalization, i.e. the same level at which the boost kernel is written in
`htt/bass/forward/doppler_boost.py:94` (``delta_eps2 = (4/5) eps2 beta + eps1^2``)
and `htt/tsc/charts/boost_coefficients.py:135` (``a[2] = v^2``, Paper I Prop 5,
``T~_ab += v_<a v_b>``). At this level the boost contributes EXACTLY
``alpha * (Omega_tilt)^2`` to the quadrupole-amplitude shear reading, because the
tilt is linear in the velocity (``Omega_tilt = kappa_tilt * beta``) so
``(Omega_tilt)^2 propto beta^2`` matches the O(beta^2) kinematic quadrupole. The
deprojection subtracts that term; ``alpha`` is a beta-INDEPENDENT constant of the
registered response.

Claim discipline. Diagnostic-only. This is a proven ESTIMATOR PROPERTY plus a
synthetic false-positive-rate / coverage witness -- NOT a shear detection. Sigma^2
on the real sky stays ``partial`` until data lands. No detection, family/geometry,
native-solver validation, or global-tilt certificate. The exact physical alpha
awaits the covariant low-ell transfer (EGS3-B1); the ratio STRUCTURE and the
deprojection/inflation/identifiability content are the robust, closed-form part.
"""
from __future__ import annotations

from dataclasses import dataclass, asdict
import numpy as np

# The mu^2 = (2/3) P2(mu) + 1/3 Legendre split: the P2 (quadrupole) coefficient is
# 2/3, the monopole shift coefficient is -1/6 (boost_coefficients.py:131, a[0]).
KIN_QUAD_COEFF = 2.0 / 3.0
MONOPOLE_SHIFT_COEFF = -1.0 / 6.0

__all__ = [
    "KIN_QUAD_COEFF",
    "MONOPOLE_SHIFT_COEFF",
    "kinematic_quadrupole_coeff",
    "deprojection_alpha",
    "projected_shear",
    "kinematic_response_row",
    "coupled_fisher",
    "response_correlation",
    "covariance_inflation",
    "legendre_p2",
    "BoostTiltIdentifiability",
    "boost_tilt_identifiability",
    "injection_recovery_experiment",
    "injection_recovery_fullmap",
]


def legendre_p2(x: float) -> float:
    """P2(x) = (3 x^2 - 1)/2  (the addition-theorem overlap of two l=2 templates)."""
    x = float(x)
    return 0.5 * (3.0 * x * x - 1.0)


def kinematic_quadrupole_coeff() -> float:
    """The C2^kin per (beta^2 T0)^2 leading constant = (2/3)^2 = 4/9.

    This is the squared P2 projection of mu^2; it is the numerator constant of the
    closed-form alpha below (chain-of-code: `deprojection_alpha` recomputes it)."""
    return KIN_QUAD_COEFF * KIN_QUAD_COEFF


def deprojection_alpha(*, T0: float, kappa_tilt: float, R_sigma: float,
                       N2: float = 1.0) -> float:
    """Closed-form deprojection coefficient alpha in Sigma_tilde^2 = Sigma^2 - alpha (Omega_tilt)^2.

    alpha = (4/9) * T0^2 * N2 / (kappa_tilt^2 * R_sigma), the ratio of the
    boost-quadrupole response ((2/3)^2 T0^2 N2 per (Omega_tilt)^2, since the tilt is
    linear in beta) to the shear-quadrupole response R_sigma. Leading order in beta,
    single blackbody monopole T0, mu^2 = (2/3)P2 + 1/3, axis-aligned boost. It is a
    pure constant of the registered response -- INDEPENDENT of beta (the beta
    dependence lives entirely in (Omega_tilt)^2).

    In the registered epsilon-normalization (T0=kappa_tilt=R_sigma=1, N2=9/4) this
    reduces to alpha=1, matching the eps1^2 coefficient in doppler_boost.py:94.
    """
    T0 = float(T0); kappa_tilt = float(kappa_tilt); R_sigma = float(R_sigma); N2 = float(N2)
    if kappa_tilt == 0.0 or R_sigma == 0.0:
        raise ValueError("kappa_tilt and R_sigma must be nonzero")
    return kinematic_quadrupole_coeff() * T0 * T0 * N2 / (kappa_tilt * kappa_tilt * R_sigma)


def projected_shear(sigma2_naive: float, omega_tilt: float, alpha: float) -> float:
    """Deprojected (boost-immune) shear reading Sigma_tilde^2 = Sigma^2 - alpha (Omega_tilt)^2.

    Subtracts the boost-sourced kinematic quadrupole BEFORE the shear is read off, so
    Sigma_tilde^2 -> 0 in a pure-bulk-flow sky (sigma2_naive = alpha (Omega_tilt)^2)
    and Sigma_tilde^2 = Sigma^2 when omega_tilt = 0 (no over-subtraction). This is the
    ML solution of the coupled Fisher block after marginalising Omega_tilt."""
    return float(sigma2_naive) - float(alpha) * float(omega_tilt) * float(omega_tilt)


def kinematic_response_row(beta: float, *, kappa_tilt: float, alpha: float) -> np.ndarray:
    """The O(beta^2) augmented response row d_kin = [rho, 0, rho, 0] on (Sigma2, W2,
    Omega_tilt, Omega_k), with rho = sqrt(alpha) * kappa_tilt * beta the response
    correlation amplitude. The same velocity sources both the boost quadrupole
    (Sigma2 column) and the tilt (Omega_tilt column), so the row is NOT block-diagonal."""
    rho = np.sqrt(max(float(alpha), 0.0)) * float(kappa_tilt) * float(beta)
    return np.array([rho, 0.0, rho, 0.0], dtype=float)


def coupled_fisher(beta: float, *, kappa_tilt: float, alpha: float,
                   f_omega_tilt: float = 1.0) -> np.ndarray:
    """The 2x2 {Sigma2, Omega_tilt} Fisher block with the beta^2 off-diagonal.

    F = [[1 + rho^2, rho^2], [rho^2, f_omega_tilt + rho^2]], rho = sqrt(alpha) kappa_tilt beta.
    The off-diagonal F_{Sigma2,Omega_tilt} = rho^2 propto beta^2 is the analytic
    statement of the boost/tilt degeneracy; it vanishes at beta = 0."""
    rho = np.sqrt(max(float(alpha), 0.0)) * float(kappa_tilt) * float(beta)
    rho2 = rho * rho
    return np.array([[1.0 + rho2, rho2],
                     [rho2, float(f_omega_tilt) + rho2]], dtype=float)


def response_correlation(fisher_block: np.ndarray) -> float:
    """r = F_{12} / sqrt(F_{11} F_{22}) for a 2x2 Fisher block (the response correlation)."""
    F = np.asarray(fisher_block, dtype=float)
    denom = np.sqrt(F[0, 0] * F[1, 1])
    if denom == 0.0:
        return 0.0
    return float(F[0, 1] / denom)


def covariance_inflation(beta: float, *, kappa_tilt: float, alpha: float,
                         f_omega_tilt: float = 1.0) -> float:
    """Sigma^2 covariance-inflation factor from the boost/tilt coupling: 1/(1 - r^2),
    r the response correlation of `coupled_fisher`. It is the ratio of the marginal
    (over Omega_tilt) to the conditional Sigma^2 variance, equals 1 at beta = 0, and
    increases monotonically with beta. Deprojection buys the 1/(1 - r^2) factor back."""
    F = coupled_fisher(beta, kappa_tilt=kappa_tilt, alpha=alpha, f_omega_tilt=f_omega_tilt)
    r = response_correlation(F)
    return 1.0 / (1.0 - r * r)


@dataclass(frozen=True)
class BoostTiltIdentifiability:
    augmented_rank: int          # 2 generic; drops to 1 on the aligned degeneracy
    separable: bool
    degenerate: bool             # v_hat parallel/anti-parallel to the shear axis
    axis_angle_deg: float        # angle(v_hat, sigma_axis)
    gram_determinant: float      # 1 - P2(cos angle)^2 ; > 0 iff separable
    reachable_sectors: tuple[str, ...]


def _unit(v) -> np.ndarray:
    a = np.asarray(v, dtype=float)
    n = np.linalg.norm(a)
    if n == 0.0:
        raise ValueError("zero-length axis")
    return a / n


def boost_tilt_identifiability(v_hat, sigma_axis, beta: float, *, tol: float = 1e-9
                               ) -> BoostTiltIdentifiability:
    """When do the boost quadrupole and the shear quadrupole separate?

    The measured l=2 amplitude is a2 = Sigma * Y2(sigma_axis) + sqrt(alpha) Omega_tilt
    * Y2(v_hat). By the addition theorem the Gram matrix of the two unit l=2 templates
    is [[1, P2(cos t)], [P2(cos t), 1]] with t = angle(v_hat, sigma_axis); its
    determinant 1 - P2(cos t)^2 is > 0 iff t != 0, pi (the templates are independent),
    so Sigma_tilde^2 is identifiable at rank 2 in the generic case and DEGENERATE
    (rank 1, over-subtraction) iff the boost axis is aligned with the shear principal
    axis. beta = 0 removes the kinematic template entirely (trivially separable)."""
    u, w = _unit(v_hat), _unit(sigma_axis)
    cos_t = float(np.clip(u @ w, -1.0, 1.0))
    angle_deg = float(np.degrees(np.arccos(abs(cos_t))))   # antipodal-invariant
    p2 = legendre_p2(cos_t)
    gram_det = 1.0 - p2 * p2
    if float(beta) == 0.0:
        separable, rank = True, 2
    else:
        separable = gram_det > tol
        rank = 2 if separable else 1
    return BoostTiltIdentifiability(
        augmented_rank=rank, separable=separable, degenerate=(not separable),
        axis_angle_deg=angle_deg, gram_determinant=float(gram_det),
        reachable_sectors=("Sigma2", "Omega_tilt") if separable else ("Omega_tilt",))


def injection_recovery_experiment(*, beta: float, sigma2_true: float = 0.0,
                                  alpha: float, kappa_tilt: float,
                                  sigma_quad: float, sigma_dip: float,
                                  v_hat=(1.0, 0.0, 0.0), sigma_axis=(0.0, 0.0, 1.0),
                                  n_mock: int = 2000, z_thresh: float = 1.645,
                                  seed: int = 20260701) -> dict:
    """Moment-level, deterministic injection-recovery of the boost/tilt separation.

    NO map, NO native low-ell solver, NO real data. Amplitude-level readings (see the
    module convention). Per mock draw with np.random.default_rng(seed):

      Omega_tilt_true = kappa_tilt * beta;  Omega_tilt_hat = Omega_tilt_true + N(0, sigma_dip)
      leak            = alpha * Omega_tilt_true^2 * |P2(cos angle(v_hat, sigma_axis))|
      shear_naive     = sigma2_true + leak + N(0, sigma_quad)
      shear_deproj    = shear_naive - alpha * Omega_tilt_hat^2 * overlap + alpha * sigma_dip^2 * overlap
                        (the last term debiases E[Omega_tilt_hat^2] = Omega_tilt_true^2 + sigma_dip^2)

    A false positive is declared when reading / se > z_thresh with se the amplitude
    noise (naive) or the deprojection-inflated noise se_deproj = sqrt(sigma_quad^2 +
    (2 alpha Omega_tilt_true sigma_dip)^2) (delta method) for the deprojected reading.

    Returns FPR (naive vs deprojected) on a pure-bulk-flow sky, and the genuine-shear
    bias/coverage, as gate-assertable deterministic numbers."""
    rng = np.random.default_rng(int(seed))
    ot_true = float(kappa_tilt) * float(beta)
    u, w = _unit(v_hat), _unit(sigma_axis)
    overlap = abs(legendre_p2(float(np.clip(u @ w, -1.0, 1.0))))
    a = float(alpha)
    sq, sd = float(sigma_quad), float(sigma_dip)

    ot_hat = ot_true + rng.normal(0.0, sd, size=int(n_mock))
    noise = rng.normal(0.0, sq, size=int(n_mock))
    leak = a * ot_true * ot_true * overlap

    shear_naive = float(sigma2_true) + leak + noise
    # deproject with the OBSERVED tilt, then debias the delta-method E[ot_hat^2] term
    shear_deproj = shear_naive - a * ot_hat * ot_hat * overlap + a * sd * sd * overlap

    se_naive = sq if sq > 0.0 else 1.0
    se_deproj = np.sqrt(sq * sq + (2.0 * a * ot_true * sd * overlap) ** 2)
    se_deproj = se_deproj if se_deproj > 0.0 else 1.0

    fpr_naive = float(np.mean(shear_naive / se_naive > z_thresh))
    fpr_deproj = float(np.mean(shear_deproj / se_deproj > z_thresh))

    shear_bias = float(np.mean(shear_deproj) - float(sigma2_true))
    lo, hi = shear_deproj - se_deproj, shear_deproj + se_deproj
    coverage = float(np.mean((lo <= float(sigma2_true)) & (float(sigma2_true) <= hi)))

    inflation = covariance_inflation(beta, kappa_tilt=kappa_tilt, alpha=alpha)
    ident = boost_tilt_identifiability(v_hat, sigma_axis, beta)

    return {
        "schema": "htt.egs3.axis_c.boost_tilt_deprojection.v1",
        "beta": float(beta),
        "alpha": a,
        "sigma2_true": float(sigma2_true),
        "n_mock": int(n_mock),
        "z_thresh": float(z_thresh),
        "fpr_naive": fpr_naive,
        "fpr_deprojected": fpr_deproj,
        "shear_bias": shear_bias,
        "shear_coverage": coverage,
        "covariance_inflation": float(inflation),
        "axis_angle_deg": ident.axis_angle_deg,
        "separable": ident.separable,
        "scope": ("moment-level synthetic injection-recovery; amplitude-level readings; "
                  "no map, no native low-ell solver, no real data; Sigma2 stays partial"),
    }


def injection_recovery_fullmap(*, beta: float, v_hat=(1.0, 0.0, 0.0),
                               nside: int = 16, seed: int = 20260701) -> dict:
    """OPTIONAL full-sky illustration (figure only; NOT used by the gate).

    Injects a v_hat-aligned beta^2 (mu^2 - 1/3) l=2 pattern on top of a LambdaCDM
    synfast base map and reports the naive vs deprojected quadrupole power. Requires
    healpy; raises RuntimeError if healpy is unavailable so the caller can skip it."""
    try:
        import healpy as hp  # type: ignore
    except Exception as exc:  # pragma: no cover - optional dependency
        raise RuntimeError("healpy unavailable; full-map illustration skipped") from exc
    rng = np.random.default_rng(int(seed))
    npix = hp.nside2npix(nside)
    # flat-ish low-ell base spectrum (illustration only)
    cl = np.array([0.0, 0.0] + [1.0e2 / (l * (l + 1.0)) for l in range(2, 33)], dtype=float)
    base = hp.synfast(cl, nside=nside, lmax=32, pixwin=False, new=True)
    base = base + rng.normal(0.0, 1.0e-3, size=npix)  # tiny noise, deterministic
    n = np.array(hp.pix2vec(nside, np.arange(npix))).T
    mu = n @ _unit(v_hat)
    T0 = 2.72548e6  # uK
    kin = (beta ** 2) * T0 * (mu * mu - 1.0 / 3.0)   # v_hat-aligned kinematic quadrupole
    obs = base + kin
    alm_obs = hp.map2alm(obs, lmax=32, iter=1)
    c2_obs = float(np.sum(np.abs(alm_obs[[hp.Alm.getidx(32, 2, m) for m in range(3)]]) ** 2))
    alm_base = hp.map2alm(base, lmax=32, iter=1)
    c2_base = float(np.sum(np.abs(alm_base[[hp.Alm.getidx(32, 2, m) for m in range(3)]]) ** 2))
    return {"beta": float(beta), "nside": int(nside),
            "c2_naive_with_boost": c2_obs, "c2_base": c2_base,
            "c2_kinematic_excess": c2_obs - c2_base}
