"""Regression tests for active non-CF4 evidence and derived diagnostics.

The historical likelihood anchors included quarantined channel c.  They are
preserved only in ``legacy/cf4_p0`` and are not valid production expectations
for the active default. These tests enforce a fail-closed implicit likelihood,
explicit non-CF4 method selection, and the remaining independent
filling-fraction anchors. They do not compute a replacement evidence or
posterior headline.
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
from htt.core.cf4_observational_input import (
    ACTIVE_DEFAULT_CHANNELS,
    CF4InputQuarantined,
)


# ─── Pinned regression values (bit-identical, fixed seeds / grid) ──────
_F_MEDIAN_S3           = 0.0904143077
_MC_N                  = 200_000
_MC_SEED               = 42


# ─── 1. Pinned regression anchors ─────────────────────────────────────
@pytest.mark.parametrize("model_type", [FLRW, FLRW_tilt])
def test_implicit_evidence_likelihood_fails_closed(model_type):
    """The historical implicit default cannot silently drop channel c."""
    with pytest.raises(CF4InputQuarantined, match="implicit/default likelihood"):
        model_type()


def test_anchor_filling_fraction_S3_pinned():
    """Median F_Bayes at scenario S3 is bit-identical to the pinned value."""
    ff = FillingFraction()
    _, med, _q16, _q84, _q025, _q975 = ff.mc_posterior(
        scenario="S3", N=_MC_N, seed=_MC_SEED
    )
    assert med == pytest.approx(_F_MEDIAN_S3, rel=0, abs=1e-9), (
        f"F_Bayes(S3) median drifted from pinned {_F_MEDIAN_S3}: got {med!r}."
    )


# ─── 2. Active non-CF4 semantic checks ────────────────────────────────
def test_explicit_non_cf4_method_channel_set_is_canonical():
    """Independent method checks must opt into the c-free channel set."""
    assert FLRW_tilt(channels=ACTIVE_DEFAULT_CHANNELS).channels == "abdefh"
    assert FLRW(channels=ACTIVE_DEFAULT_CHANNELS).channels == "abdefh"


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
    draw with finite log_likelihood under an explicit c-free method channel set.

    Protects against silent breakage of prior_transform / predicted_observables
    wiring (e.g. a MES ceiling regression that makes a whole model -inf).
    """
    rng = np.random.default_rng(_SMOKE_SEED)
    model = ALL_MODELS[model_name](channels=ACTIVE_DEFAULT_CHANNELS)
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
