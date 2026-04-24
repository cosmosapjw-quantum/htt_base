"""Regression tests for the three CLAUDE.md §5 production anchors.

Anchors (as of 2026-04-24, bit-identical across repeated runs with fixed
seeds / n_points):

    ln B(FLRW_tilt vs FLRW)  = 26.3966094015
    <beta>_FLRW_tilt         = 1.3597868670e-03
    median F_Bayes (S3)      = 0.0904143077

CLAUDE.md §5 records the semantic form of the same anchors as

    ln B(FLRW_tilt)          = +26.40
    beta                     = 1.360e-3
    F_Bayes                  = 0.093 ± 0.025

These tests pin the computed values at tight tolerance so any accidental
drift in the underlying likelihood / MC machinery is caught, and also
cross-check that the computed values remain consistent with the
semantic anchors in CLAUDE.md §5.
"""
from __future__ import annotations

import numpy as np
import pytest

from htt.core.evidence_models import (
    ALL_MODELS,
    FLRW,
    FLRW_tilt,
)
from htt.core.analysis_extended import FillingFraction


# ─── Pinned regression values (bit-identical, fixed seeds / grid) ──────
_LN_B_FLRW_TILT        = 26.3966094015
_BETA_MEAN_FLRW_TILT   = 1.3597868670e-03
_F_MEDIAN_S3           = 0.0904143077
_QUAD_N_POINTS         = 10_000
_MC_N                  = 200_000
_MC_SEED               = 42


# ─── 1. Pinned regression anchors ─────────────────────────────────────
def test_anchor_lnB_flrw_tilt_vs_flrw_pinned():
    """ln B(FLRW_tilt vs FLRW) is bit-identical to the pinned value."""
    lnZ_flrw_tilt = FLRW_tilt().log_evidence_quadrature(
        n_points=_QUAD_N_POINTS
    )["lnZ"]
    lnZ_flrw = FLRW().log_evidence()
    lnB = lnZ_flrw_tilt - lnZ_flrw
    assert lnB == pytest.approx(_LN_B_FLRW_TILT, rel=0, abs=1e-9), (
        f"lnB drifted from pinned {_LN_B_FLRW_TILT}: got {lnB!r}. "
        "If this drift is intentional, update the pinned value and the "
        "matching CLAUDE.md §5 anchor together."
    )


def test_anchor_beta_mean_flrw_tilt_pinned():
    """Posterior <beta> under FLRW_tilt is bit-identical to the pinned value."""
    beta_mean = FLRW_tilt().log_evidence_quadrature(
        n_points=_QUAD_N_POINTS
    )["beta_mean"]
    assert beta_mean == pytest.approx(
        _BETA_MEAN_FLRW_TILT, rel=0, abs=1e-12
    ), (
        f"<beta> drifted from pinned {_BETA_MEAN_FLRW_TILT}: got {beta_mean!r}."
    )


def test_anchor_filling_fraction_S3_pinned():
    """Median F_Bayes at scenario S3 is bit-identical to the pinned value."""
    ff = FillingFraction()
    _, med, _q16, _q84, _q025, _q975 = ff.mc_posterior(
        scenario="S3", N=_MC_N, seed=_MC_SEED
    )
    assert med == pytest.approx(_F_MEDIAN_S3, rel=0, abs=1e-9), (
        f"F_Bayes(S3) median drifted from pinned {_F_MEDIAN_S3}: got {med!r}."
    )


# ─── 2. CLAUDE.md §5 semantic anchors (loose-tolerance cross-check) ───
def test_semantic_anchor_lnB_matches_claude_md():
    """ln B(FLRW_tilt) ≈ +26.40 (CLAUDE.md §5)."""
    lnZ_ft = FLRW_tilt().log_evidence_quadrature(n_points=_QUAD_N_POINTS)["lnZ"]
    lnB = lnZ_ft - FLRW().log_evidence()
    assert lnB == pytest.approx(26.40, abs=0.10)


def test_semantic_anchor_beta_matches_claude_md():
    """<beta> ≈ 1.360e-3 (CLAUDE.md §5)."""
    beta_mean = FLRW_tilt().log_evidence_quadrature(
        n_points=_QUAD_N_POINTS
    )["beta_mean"]
    assert beta_mean == pytest.approx(1.360e-3, rel=5e-3)


def test_semantic_anchor_F_bayes_matches_claude_md():
    """F_Bayes ≈ 0.093 ± 0.025 (CLAUDE.md §5; the 1σ band is indicative).

    We cross-check the *median* lands inside a window of width 3σ around the
    CLAUDE.md central value — strict enough to catch gross drift but loose
    enough to absorb Monte Carlo boundary effects.
    """
    _, med, _, _, _, _ = FillingFraction().mc_posterior(
        scenario="S3", N=_MC_N, seed=_MC_SEED
    )
    assert med == pytest.approx(0.093, abs=3 * 0.025)


# ─── 3. 15-model reachability smoke test ──────────────────────────────
_SMOKE_SEED = 0
_SMOKE_TRIES = 20


def _smoke_params_reach_finite(model, rng, tries):
    """Return True if some (u,theta) draw yields a finite log_likelihood."""
    if model.ndim == 0:
        return np.isfinite(model.log_likelihood())
    for _ in range(tries):
        u = rng.random(model.ndim)
        theta = model.prior_transform(u)
        ll = model.log_likelihood(theta)
        if np.isfinite(ll):
            return True
    return False


@pytest.mark.parametrize("model_name", list(ALL_MODELS.keys()))
def test_all_15_models_admit_finite_log_likelihood(model_name):
    """Every registered Bianchi model must expose at least one parameter
    draw with finite log_likelihood under the default channel set.

    Protects against silent breakage of prior_transform / predicted_observables
    wiring (e.g. a MES ceiling regression that makes a whole model -inf).
    """
    rng = np.random.default_rng(_SMOKE_SEED)
    model = ALL_MODELS[model_name]()
    assert _smoke_params_reach_finite(model, rng, _SMOKE_TRIES), (
        f"{model_name}: no finite log_likelihood in {_SMOKE_TRIES} prior draws "
        "(seed 0). Check prior_transform, predicted_observables, and the "
        "MES hard ceiling in _core_logL."
    )


# ─── 4. Cross-scenario sanity on FillingFraction ──────────────────────
_FILLING_SCENARIOS_PINNED = {
    # Pinned median values at N=_MC_N, seed=_MC_SEED (2026-04-24).
    "S1":  0.0631,
    "S2a": 0.0904,
    "S2b": 0.0631,
    "S2c": 0.4512,
    "S3":  0.0904,
}


@pytest.mark.parametrize("scenario,expected", _FILLING_SCENARIOS_PINNED.items())
def test_filling_fraction_scenario_median_pinned(scenario, expected):
    """Median F_Bayes per scenario is stable at 4-decimal precision."""
    _, med, _, _, _, _ = FillingFraction().mc_posterior(
        scenario=scenario, N=_MC_N, seed=_MC_SEED
    )
    assert med == pytest.approx(expected, abs=5e-5)
