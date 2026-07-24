"""PR-180: exact zero-parameter boost-BiPoSH residual excitation vector.

Consistency estimator ONLY, conditional on the PR-150 compact cache,
common mask, masked-pseudo-alm convention, and the BOOSTED FFP10
ensemble (the FFP10 CMB MC include Doppler boosting — Planck 2018 III —
so the null already carries the boost; the fixed template is subtracted
identically from observed and simulations, and the informative centring
is the simulation mean). Never a detection, independence, isotropy,
transfer, geometry, or Bianchi-family statement; the kernel is never
fitted and the residual is never a geometric estimand.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path

import healpy as hp
import numpy as np

CACHE_PATH = Path(
    "/mnt/sn850x2t/htt_base_e2e/k1_e2e_reduced_pr150/k1_ffp10_reduced_smica.npz"
)
CACHE_SHA256 = "86b792c821b3e641c76c83d96523148c65e9d30a439d7c850acc808c1bc5fadb"

BETA = 1.23357e-3
DIPOLE_L_DEG = 264.021
DIPOLE_B_DEG = 48.253
DIPOLE_FRAME_ROTATION = "healpy_zyx_dipole_to_z_v2"
LMAX = 24
ELL_MIN = 2
ELL_MAX_FEATURE = 10  # F_ell for ell = 2..10 (couples to ell+1 <= 11)
N_TEMPLATE_SIMS = 128
ALPHA = 0.05


@dataclass(frozen=True)
class BoostBiposhConfig:
    beta: float = BETA
    lmax: int = LMAX
    ell_min: int = ELL_MIN
    ell_max_feature: int = ELL_MAX_FEATURE
    n_template_sims: int = N_TEMPLATE_SIMS
    alpha: float = ALPHA

    def config_hash(self) -> str:
        payload = json.dumps(
            {
                "beta": self.beta,
                "dipole": [DIPOLE_L_DEG, DIPOLE_B_DEG],
                "dipole_frame_rotation": DIPOLE_FRAME_ROTATION,
                "lmax": self.lmax,
                "ells": [self.ell_min, self.ell_max_feature],
                "n_template_sims": self.n_template_sims,
                "alpha": self.alpha,
                "cache_sha256": CACHE_SHA256,
            },
            sort_keys=True,
        )
        return hashlib.sha256(payload.encode()).hexdigest()


def verify_cache() -> dict:
    digest = hashlib.sha256(CACHE_PATH.read_bytes()).hexdigest()
    if digest != CACHE_SHA256:
        raise SystemExit("compact cache hash mismatch — BLOCKED_INTEGRITY_FAILURE")
    return {"path": str(CACHE_PATH), "sha256": digest}


def _rotator() -> hp.Rotator:
    """Active rotation carrying the solar-dipole axis to the z-axis."""
    # In healpy's ZYX convention the second angle is minus colatitude,
    # not Galactic latitude.
    return hp.Rotator(
        rot=[DIPOLE_L_DEG, DIPOLE_B_DEG - 90.0, 0.0],
        inv=False,
        eulertype="ZYX",
    )


def feature_from_map(
    pixel_map: np.ndarray,
    mask: np.ndarray | None,
    config: BoostBiposhConfig,
) -> np.ndarray:
    """Masked pseudo-alm -> dipole-frame -> F_ell couplings (ell, ell+1)."""
    work = pixel_map if mask is None else pixel_map * mask
    alm = hp.map2alm(work, lmax=config.lmax, iter=3)
    alm = _rotator().rotate_alm(alm, lmax=config.lmax)
    out = np.zeros(config.ell_max_feature - config.ell_min + 1)
    for idx, ell in enumerate(range(config.ell_min, config.ell_max_feature + 1)):
        total = 0.0
        for m in range(0, ell + 1):
            a1 = alm[hp.Alm.getidx(config.lmax, ell, m)]
            a2 = alm[hp.Alm.getidx(config.lmax, ell + 1, m)]
            weight = 1.0 if m == 0 else 2.0  # negative-m via reality
            total += weight * float(np.real(np.conj(a1) * a2))
        out[idx] = total / (2.0 * ell + 1.0)
    return out


class ExactBoostOperator:
    """Zero-parameter pixel-space boost of a band-limited nside-64 map.

    T'(n) = T(n_ab) / (gamma (1 - beta . n)) with T evaluated by EXACT
    spherical-harmonic synthesis at the aberrated directions. The
    operator is the definition of the boost; no coupling-coefficient
    formula is transcribed.
    """

    def __init__(self, nside: int = 64, lmax: int = LMAX, beta: float = BETA):
        self.nside = nside
        self.lmax = lmax
        self.beta = beta
        npix = hp.nside2npix(nside)
        theta, phi = hp.pix2ang(nside, np.arange(npix))
        n_hat = np.stack(
            [
                np.sin(theta) * np.cos(phi),
                np.sin(theta) * np.sin(phi),
                np.cos(theta),
            ],
            axis=1,
        )
        b_vec = hp.rotator.dir2vec(DIPOLE_L_DEG, DIPOLE_B_DEG, lonlat=True)
        beta_vec = beta * np.asarray(b_vec)
        gamma = 1.0 / np.sqrt(1.0 - beta**2)
        b_hat = beta_vec / beta
        mu = n_hat @ b_hat
        # Consistent exact pair for the LINE-OF-SIGHT direction n (from
        # observer toward the sky) of a photon observed at n: the
        # CMB-frame line of sight is
        #   n_cmb_par = (mu - beta) / (1 - beta mu) * b_hat
        #   n_cmb_perp = n_perp / (gamma (1 - beta mu))
        # and the thermodynamic temperature transforms with the SAME
        # (1 - beta mu) Doppler pairing:
        #   T_obs(n) = T_cmb(n_cmb) / (gamma (1 - beta mu)).
        par_coeff = (mu - beta) / (1.0 - beta * mu)
        perp = n_hat - mu[:, None] * b_hat[None, :]
        n_ab = (
            par_coeff[:, None] * b_hat[None, :]
            + perp / (gamma * (1.0 - beta * mu))[:, None]
        )
        n_ab /= np.linalg.norm(n_ab, axis=1, keepdims=True)
        self.doppler = 1.0 / (gamma * (1.0 - beta * mu))
        theta_ab = np.arccos(np.clip(n_ab[:, 2], -1.0, 1.0))
        phi_ab = np.mod(np.arctan2(n_ab[:, 1], n_ab[:, 0]), 2.0 * np.pi)
        self._theta_ab = theta_ab
        self._phi_ab = phi_ab
        self._synth_rows: np.ndarray | None = None

    def _synthesis_matrix(self) -> np.ndarray:
        if self._synth_rows is None:
            lmax = self.lmax
            n_alm = hp.Alm.getsize(lmax)
            from scipy.special import sph_harm_y

            rows = np.zeros((self._theta_ab.size, n_alm), dtype=np.complex128)
            for ell in range(lmax + 1):
                for m in range(0, ell + 1):
                    idx = hp.Alm.getidx(lmax, ell, m)
                    rows[:, idx] = sph_harm_y(
                        ell, m, self._theta_ab, self._phi_ab
                    )
            self._synth_rows = rows
        return self._synth_rows

    def __call__(self, pixel_map: np.ndarray) -> np.ndarray:
        alm = hp.map2alm(pixel_map, lmax=self.lmax, iter=3)
        rows = self._synthesis_matrix()
        lmax = self.lmax
        values = np.zeros(self._theta_ab.size)
        m0 = np.array(
            [hp.Alm.getidx(lmax, ell, 0) for ell in range(lmax + 1)]
        )
        contrib = rows @ alm
        # add the negative-m contribution via reality: 2 Re(sum_{m>0}),
        # m=0 counted once — rows@alm counts each m>=0 once, so:
        m0_part = rows[:, m0] @ alm[m0]
        values = 2.0 * np.real(contrib) - np.real(m0_part)
        return values * self.doppler


def run_estimator(config: BoostBiposhConfig | None = None) -> dict:
    config = config or BoostBiposhConfig()
    cache_receipt = verify_cache()
    cache = np.load(CACHE_PATH)
    mask = np.asarray(cache["common_mask"], dtype=np.float64)
    observed = np.asarray(cache["observed_map"], dtype=np.float64)
    cmb = cache["cmb_maps"]
    noise = cache["noise_maps"]
    n_sims = cmb.shape[0]

    # Features for every simulation (cmb_i + noise_(i mod 300)) and observed.
    features = np.zeros((n_sims, config.ell_max_feature - config.ell_min + 1))
    for i in range(n_sims):
        total_map = np.asarray(cmb[i], dtype=np.float64) + np.asarray(
            noise[i % noise.shape[0]], dtype=np.float64
        )
        features[i] = feature_from_map(total_map, mask, config)
    f_obs = feature_from_map(observed, mask, config)

    # Operator template via TWO-POINT RICHARDSON at an amplified boost:
    # with h = K * beta (K = 20) and f(x) the feature increment of the
    # exact boost at velocity x, the linear-in-beta template is
    #   T = beta * (4 f(h) - f(2h)) / (2 h)
    # which cancels the quadratic term exactly and lifts the increment
    # ~K x above the synthesis/quadrature numeric floor (the raw
    # per-unit-beta increment at K = 1 sits at that floor; disclosed).
    K = 20.0
    h = K * config.beta
    operator_h = ExactBoostOperator(lmax=config.lmax, beta=h)
    operator_2h = ExactBoostOperator(lmax=config.lmax, beta=2.0 * h)
    deltas = []
    ratio_samples = []
    for i in range(config.n_template_sims):
        base = np.asarray(cmb[i], dtype=np.float64)
        f_base = feature_from_map(base, mask, config)
        f_h = feature_from_map(operator_h(base), mask, config) - f_base
        f_2h = feature_from_map(operator_2h(base), mask, config) - f_base
        deltas.append(config.beta * (4.0 * f_h - f_2h) / (2.0 * h))
        if i < 8:
            dom = int(np.argmax(np.abs(f_h)))
            ratio_samples.append(float(f_2h[dom] / f_h[dom]))
    template = np.mean(np.asarray(deltas), axis=0)
    template_se = np.std(np.asarray(deltas), axis=0, ddof=1) / np.sqrt(
        len(deltas)
    )

    # Linearity gate on the amplified increments (measurable above the
    # numeric floor): f(2h)/f(h) must be ~2 with an O(h) quadratic
    # allowance.
    linearity_ratio = float(np.mean(ratio_samples))
    linearity_ok = abs(linearity_ratio - 2.0) <= 0.2

    # Ensemble boost-content measurement (full sky, cmb-only, reported).
    fullsky_features = np.zeros_like(features[: config.n_template_sims])
    for i in range(config.n_template_sims):
        fullsky_features[i] = feature_from_map(
            np.asarray(cmb[i], dtype=np.float64), None, config
        )
    fullsky_mean = np.mean(fullsky_features, axis=0)
    fullsky_se = np.std(fullsky_features, axis=0, ddof=1) / np.sqrt(
        config.n_template_sims
    )

    # Identical-treatment template subtraction (rank-invariant, disclosed)
    features_t = features - template[None, :]
    f_obs_t = f_obs - template

    # Scores: Hartlap-corrected Mahalanobis with leave-one-out centring.
    n_dim = features.shape[1]
    hartlap = (n_sims - n_dim - 2) / (n_sims - 1)
    scores = np.zeros(n_sims)
    total_sum = features_t.sum(axis=0)
    for i in range(n_sims):
        rest = np.delete(features_t, i, axis=0)
        centre = (total_sum - features_t[i]) / (n_sims - 1)
        cov = np.cov(rest, rowvar=False)
        resid = features_t[i] - centre
        scores[i] = hartlap * float(resid @ np.linalg.solve(cov, resid))
    centre_all = features_t.mean(axis=0)
    cov_all = np.cov(features_t, rowvar=False)
    resid_obs = f_obs_t - centre_all
    score_obs = hartlap * float(resid_obs @ np.linalg.solve(cov_all, resid_obs))

    b_count = int(np.sum(scores >= score_obs))
    rank_p = (1 + b_count) / (n_sims + 1)
    grid_step = 1.0 / (n_sims + 1)
    if abs(rank_p - config.alpha) <= grid_step:
        terminal = "NUMERICALLY_UNRESOLVED_AT_CURRENT_MC_BUDGET"
    elif rank_p > config.alpha:
        terminal = "CONSISTENT_WITH_PURE_BOOST_WITHIN_THIS_PIPELINE"
    else:
        terminal = "NOT_EXPLAINED_BY_THE_FIXED_BOOST_TEMPLATE_WITHIN_THIS_PIPELINE"
    if not linearity_ok:
        terminal = "BLOCKED_INTEGRITY_FAILURE"

    return {
        "schema": "htt.pr180.boost_biposh_residual.v1",
        "config_hash": config.config_hash(),
        "cache": cache_receipt,
        "n_sims": int(n_sims),
        "feature_ells": list(range(config.ell_min, config.ell_max_feature + 1)),
        "observed_feature": f_obs.tolist(),
        "sim_feature_mean": features.mean(axis=0).tolist(),
        "template_operator_derived": template.tolist(),
        "template_mc_se": template_se.tolist(),
        "template_construction": (
            "two-point Richardson at amplified boost h = 20*beta and 2h; "
            "quadratic term cancelled exactly; per-unit-beta increment at "
            "K=1 sits at the synthesis/quadrature numeric floor (disclosed)"
        ),
        "linearity_ratio_f2h_over_fh": linearity_ratio,
        "linearity_ok": bool(linearity_ok),
        "fullsky_cmb_mean_feature": fullsky_mean.tolist(),
        "fullsky_cmb_mean_se": fullsky_se.tolist(),
        "ensemble_boost_content_note": (
            "full-sky CMB-only simulation-mean feature vs the operator "
            "template measures the FFP10 ensemble's effective boost "
            "content; REPORTED with MC error, not gated (marginal power)"
        ),
        "identical_treatment_note": (
            "the fixed template is subtracted from observed and every "
            "simulation identically; the subtraction cancels in the "
            "centred residual and is rank-invariant (disclosed)"
        ),
        "observed_score": score_obs,
        "rank_exceedances": b_count,
        "rank_p": rank_p,
        "finite_resolution_floor": grid_step,
        "alpha": config.alpha,
        "terminal": terminal,
        "interpretation": (
            "Consistency result only, conditional on this cache, mask, "
            "pseudo-alm convention, boosted FFP10 ensemble, and pipeline; "
            "never a boost confirmation, independence claim, detection, "
            "isotropy/anisotropy statement, transfer validation, geometry "
            "or Bianchi-family result; kernel never fitted."
        ),
    }


if __name__ == "__main__":
    print(json.dumps(run_estimator(), sort_keys=True))
