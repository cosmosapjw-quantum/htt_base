"""v10 B1: even-L diagonal BiPoSH exchangeable ranks under the E2E null.

Diagnostic consistency analysis ONLY, conditional on the PR-150 compact
cache (999 SMICA-processed FFP10 CMB MC + 300 noise MC + observed SMICA
+ common mask, nside 64), the masked-pseudo-alm convention, and this
statistic set. The odd-L diagonal BiPoSH A^{LM}_{ll} vanishes
identically for ANY alm (exchange symmetry, Book-Kamionkowski-Souradeep
2012; independently re-proven in-repo), so odd L carries no trials and
the feature space is quotiented to even L. Never a detection, isotropy,
anisotropy, transfer, geometry, or Bianchi-family statement.
"""

from __future__ import annotations

import hashlib
import json
import math
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

import healpy as hp
import numpy as np

CACHE_PATH = Path(
    "/mnt/sn850x2t/htt_base_e2e/k1_e2e_reduced_pr150/k1_ffp10_reduced_smica.npz"
)
CACHE_SHA256 = "86b792c821b3e641c76c83d96523148c65e9d30a439d7c850acc808c1bc5fadb"

LMAX = 24
ELL_MIN = 2
ELL_MAX = 10
EVEN_L = (2, 4)
ODD_L_CHECK = 3
ALPHA = 0.05


@dataclass(frozen=True)
class EvenLConfig:
    lmax: int = LMAX
    ell_min: int = ELL_MIN
    ell_max: int = ELL_MAX
    even_l: tuple[int, ...] = EVEN_L
    alpha: float = ALPHA

    def config_hash(self) -> str:
        payload = json.dumps(
            {
                "lmax": self.lmax,
                "ells": [self.ell_min, self.ell_max],
                "even_l": list(self.even_l),
                "odd_l_check": ODD_L_CHECK,
                "alpha": self.alpha,
                "cache_sha256": CACHE_SHA256,
                "feature_transform": "log_invariant_power",
                "boost_band_convention": "pr180_dipole_frame_couplings",
            },
            sort_keys=True,
        )
        return hashlib.sha256(payload.encode()).hexdigest()


def verify_cache() -> dict:
    digest = hashlib.sha256(CACHE_PATH.read_bytes()).hexdigest()
    if digest != CACHE_SHA256:
        raise SystemExit("compact cache hash mismatch — BLOCKED_INTEGRITY_FAILURE")
    return {"path": str(CACHE_PATH), "sha256": digest}


@lru_cache(maxsize=None)
def _cg_table(ell: int, big_l: int) -> tuple[np.ndarray, np.ndarray]:
    """Clebsch-Gordan table C^{L M}_{l m1 l m2} for the diagonal pair.

    Returns (indices, coefficients): indices[k] = (m1, m2, M) with
    m2 = M - m1, coefficients[k] exact-sympy evaluated to float.
    """
    from sympy.physics.quantum.cg import CG

    rows = []
    vals = []
    for big_m in range(-big_l, big_l + 1):
        for m1 in range(-ell, ell + 1):
            m2 = big_m - m1
            if abs(m2) > ell:
                continue
            coeff = float(CG(ell, m1, ell, m2, big_l, big_m).doit())
            if coeff != 0.0:
                rows.append((m1, m2, big_m))
                vals.append(coeff)
    return np.asarray(rows, dtype=np.int64), np.asarray(vals)


def _full_alm_row(alm: np.ndarray, lmax: int, ell: int) -> np.ndarray:
    """Signed-m coefficient row a_{ell, m} for m = -ell..ell (reality)."""
    row = np.zeros(2 * ell + 1, dtype=np.complex128)
    for m in range(0, ell + 1):
        val = alm[hp.Alm.getidx(lmax, ell, m)]
        row[ell + m] = val
        if m > 0:
            row[ell - m] = (-1) ** m * np.conj(val)
    return row


def diagonal_biposh_power(
    alm: np.ndarray, lmax: int, ell: int, big_l: int
) -> float:
    """Rotationally invariant S_{ell,L} = sum_M |A^{LM}_{ll}|^2."""
    idx, coeff = _cg_table(ell, big_l)
    row = _full_alm_row(alm, lmax, ell)
    a1 = row[ell + idx[:, 0]]
    a2 = row[ell + idx[:, 1]]
    terms = coeff * a1 * a2
    power = 0.0
    for big_m in range(-big_l, big_l + 1):
        sel = idx[:, 2] == big_m
        power += float(np.abs(np.sum(terms[sel])) ** 2)
    return power


def _alm_of_map(pixel_map: np.ndarray, mask: np.ndarray,
                config: EvenLConfig) -> np.ndarray:
    return hp.map2alm(pixel_map * mask, lmax=config.lmax, iter=3)


def feature_from_alm(alm: np.ndarray, config: EvenLConfig) -> np.ndarray:
    """Even-L diagonal BiPoSH invariant LOG-powers.

    The raw powers S_{ell,L} are quartic in the alm and heavy-tailed, so
    the ensemble covariance of the raw vector is ill-conditioned; the
    log transform (S is positive almost surely) conditions the
    Mahalanobis scoring without changing the exchangeable-rank validity.
    """
    out = []
    for big_l in config.even_l:
        for ell in range(config.ell_min, config.ell_max + 1):
            out.append(
                math.log(diagonal_biposh_power(alm, config.lmax, ell, big_l))
            )
    return np.asarray(out)


# PR-180 boost-feature convention (dipole-frame (ell, ell+1) couplings),
# recomputed here ONLY to provide the ensemble scatter band for the v10
# replot; the sealed PR-180 card remains the authority for the result.
BOOST_DIPOLE_L_DEG = 264.021
BOOST_DIPOLE_B_DEG = 48.253


def boost_feature_from_alm(alm: np.ndarray, config: EvenLConfig) -> np.ndarray:
    rot = hp.Rotator(
        rot=[BOOST_DIPOLE_L_DEG, BOOST_DIPOLE_B_DEG, 0.0], inv=True
    )
    alm_r = rot.rotate_alm(alm.copy(), lmax=config.lmax)
    out = np.zeros(10 - 2 + 1)
    for idx, ell in enumerate(range(2, 10 + 1)):
        total = 0.0
        for m in range(0, ell + 1):
            a1 = alm_r[hp.Alm.getidx(config.lmax, ell, m)]
            a2 = alm_r[hp.Alm.getidx(config.lmax, ell + 1, m)]
            weight = 1.0 if m == 0 else 2.0
            total += weight * float(np.real(np.conj(a1) * a2))
        out[idx] = total / (2.0 * ell + 1.0)
    return out


def odd_l_structural_zero_ratio(
    alm: np.ndarray, config: EvenLConfig
) -> float:
    """max_ell S_{ell,3} / S_{ell,2}: identically zero up to float error.

    The zero is an alm-independent exchange-symmetry identity, so it
    holds for masked pseudo-alm exactly as for full-sky alm.
    """
    worst = 0.0
    for ell in range(config.ell_min, config.ell_max + 1):
        odd = diagonal_biposh_power(alm, config.lmax, ell, ODD_L_CHECK)
        even = diagonal_biposh_power(alm, config.lmax, ell, 2)
        if even > 0.0:
            worst = max(worst, odd / even)
    return worst


def run_estimator(config: EvenLConfig | None = None) -> dict:
    config = config or EvenLConfig()
    cache_receipt = verify_cache()
    cache = np.load(CACHE_PATH)
    mask = np.asarray(cache["common_mask"], dtype=np.float64)
    observed = np.asarray(cache["observed_map"], dtype=np.float64)
    cmb = cache["cmb_maps"]
    noise = cache["noise_maps"]
    n_sims = cmb.shape[0]
    n_dim = len(config.even_l) * (config.ell_max - config.ell_min + 1)

    features = np.zeros((n_sims, n_dim))
    boost_features = np.zeros((n_sims, 9))
    for i in range(n_sims):
        total_map = np.asarray(cmb[i], dtype=np.float64) + np.asarray(
            noise[i % noise.shape[0]], dtype=np.float64
        )
        alm = _alm_of_map(total_map, mask, config)
        features[i] = feature_from_alm(alm, config)
        boost_features[i] = boost_feature_from_alm(alm, config)
    alm_obs = _alm_of_map(observed, mask, config)
    f_obs = feature_from_alm(alm_obs, config)
    boost_obs = boost_feature_from_alm(alm_obs, config)
    zero_ratio = odd_l_structural_zero_ratio(alm_obs, config)

    # Hartlap-corrected Mahalanobis with leave-one-out centring (pooled),
    # plus per-L block sub-ranks (secondary, disclosed). The quadratic
    # form uses an eigenvalue-floored pseudo-inverse (floor 1e-9 of the
    # top eigenvalue) so near-singular ensemble covariances can never
    # produce indefinite scores; the floor is applied identically to
    # simulations and observation (rank validity preserved).
    def _psd_quad(cov: np.ndarray, resid: np.ndarray) -> float:
        w, v = np.linalg.eigh(cov)
        w = np.clip(w, w.max() * 1e-9, None)
        proj = v.T @ resid
        return float(np.sum(proj**2 / w))

    def _ranks(block: slice) -> dict:
        sub = features[:, block]
        sub_obs = f_obs[block]
        d = sub.shape[1]
        hartlap = (n_sims - d - 2) / (n_sims - 1)
        scores = np.zeros(n_sims)
        total_sum = sub.sum(axis=0)
        for i in range(n_sims):
            rest = np.delete(sub, i, axis=0)
            centre = (total_sum - sub[i]) / (n_sims - 1)
            cov = np.cov(rest, rowvar=False)
            resid = sub[i] - centre
            scores[i] = hartlap * _psd_quad(cov, resid)
        centre_all = sub.mean(axis=0)
        cov_all = np.cov(sub, rowvar=False)
        resid_obs = sub_obs - centre_all
        score_obs = hartlap * _psd_quad(cov_all, resid_obs)
        b_count = int(np.sum(scores >= score_obs))
        return {
            "observed_score": score_obs,
            "rank_exceedances": b_count,
            "rank_p": (1 + b_count) / (n_sims + 1),
            "sim_scores_hist_edges_scores": scores.tolist(),
        }

    pooled = _ranks(slice(0, n_dim))
    per_l = {}
    n_ell = config.ell_max - config.ell_min + 1
    for j, big_l in enumerate(config.even_l):
        per_l[f"L{big_l}"] = {
            k: v
            for k, v in _ranks(slice(j * n_ell, (j + 1) * n_ell)).items()
            if k != "sim_scores_hist_edges_scores"
        }

    grid_step = 1.0 / (n_sims + 1)
    rank_p = pooled["rank_p"]
    if abs(rank_p - config.alpha) <= grid_step:
        terminal = "NUMERICALLY_UNRESOLVED_AT_CURRENT_MC_BUDGET"
    elif rank_p > config.alpha:
        terminal = "EVENL_CONSISTENT_WITH_E2E_NULL_WITHIN_THIS_PIPELINE"
    else:
        terminal = "EVENL_FEATURE_OUTSIDE_NULL_AT_ALPHA_WITHIN_THIS_PIPELINE"
    if zero_ratio > 1e-10:
        terminal = "BLOCKED_INTEGRITY_FAILURE"

    return {
        "schema": "htt.v10.k1_evenl_biposh_rank.v1",
        "config_hash": config.config_hash(),
        "cache": cache_receipt,
        "n_sims": int(n_sims),
        "n_dim": int(n_dim),
        "feature_layout": [
            f"S_ell{ell}_L{big_l}"
            for big_l in config.even_l
            for ell in range(config.ell_min, config.ell_max + 1)
        ],
        "observed_feature": f_obs.tolist(),
        "sim_feature_mean": features.mean(axis=0).tolist(),
        "odd_l_structural_zero_max_ratio": zero_ratio,
        "odd_l_note": (
            "the odd-L diagonal A^{LM}_{ll} vanishes for ANY alm "
            "(exchange symmetry; known result, independently re-proven); "
            "measured max S_{ell,3}/S_{ell,2} on the observed masked map "
            "certifies the implementation at float precision"
        ),
        "boost_feature_band": {
            "convention": "pr180_dipole_frame_couplings_replot_support",
            "ells": list(range(2, 11)),
            "observed": boost_obs.tolist(),
            "sim_p16": np.percentile(boost_features, 16, axis=0).tolist(),
            "sim_p84": np.percentile(boost_features, 84, axis=0).tolist(),
            "sim_mean": boost_features.mean(axis=0).tolist(),
            "note": (
                "ensemble scatter band recomputed in the sealed PR-180 "
                "feature convention solely so the report figure can show "
                "the null spread; the sealed PR-180 card remains the "
                "authority for the residual result"
            ),
        },
        "pooled": {
            k: v
            for k, v in pooled.items()
            if k != "sim_scores_hist_edges_scores"
        },
        "sim_scores": pooled["sim_scores_hist_edges_scores"],
        "per_L_secondary": per_l,
        "finite_resolution_floor": grid_step,
        "alpha": config.alpha,
        "terminal": terminal,
        "interpretation": (
            "Diagnostic consistency analysis only, conditional on this "
            "cache, mask, pseudo-alm convention, statistic set, and the "
            "SMICA-processed FFP10 E2E null; never a detection, isotropy, "
            "anisotropy, transfer, geometry, or Bianchi-family statement."
        ),
    }


if __name__ == "__main__":
    print(json.dumps(run_estimator(), sort_keys=True))
