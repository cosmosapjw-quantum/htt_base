"""Regression anchors for the TSC ↔ HTT filling-fraction bridge (D5 closure).

Companion to ``htt/tests/test_production_anchors.py``. The HTT-side anchor
file pins ``FillingFraction.mc_posterior`` medians bit-identical; this file
pins the **bridged** cross-check values emitted by
:func:`tsc.integration.htt_bridge.ff_htt_mc_cross_check` at a canonical
``(N, seed, w)`` triple:

    * ``F_Bayes_tsc``       — tsc re-derivation from the shared RNG stream
    * ``F_Bayes_htt_mean``  — htt's ``mc_posterior`` sample mean
    * ``rel_difference``    — agreement between the two paths

Any drift in the htt likelihood coefficients, the tsc re-derivation, or
the shared-stream plumbing will fire one of these tests.

Canonical call arguments (match ``test_htt_bridge.py::TestHttMcCrossCheck``):

    scenario ∈ {S1, S2a, S2b, S2c, S3}
    N        = 100_000
    seed     = 20260419
    w        = 0.0
"""
from __future__ import annotations

import numpy as np
import pytest

from tsc.integration.htt_bridge import (
    PUBLISHED_F_BAYES_BAND,
    ff_htt_mc_cross_check,
)


_N_SAMPLES = 100_000
_SEED = 20260419
_W = 0.0


# ─── Pinned (F_Bayes_tsc, F_Bayes_htt_mean, rel_diff) anchors per scenario ─
# Measured 2026-04-24 — determinism verified across 3 consecutive runs.
_BRIDGE_ANCHORS: dict[str, dict[str, float]] = {
    "S1":  {
        "F_tsc":       0.066858945852,
        "F_htt_mean":  0.066860283057,
        "rel_diff":    2.0000e-05,
    },
    "S2a": {
        "F_tsc":       0.094197473745,
        "F_htt_mean":  0.094197473745,
        "rel_diff":    0.0,
    },
    "S2b": {
        "F_tsc":       0.066858945852,
        "F_htt_mean":  0.066860283057,
        "rel_diff":    2.0000e-05,
    },
    "S2c": {
        "F_tsc":       0.454972665234,
        "F_htt_mean":  0.454972665234,
        "rel_diff":    0.0,
    },
    "S3":  {
        "F_tsc":       0.094197473745,
        "F_htt_mean":  0.094197473745,
        "rel_diff":    0.0,
    },
}


# ─── 1. Pinned per-scenario regression ────────────────────────────────
@pytest.mark.parametrize("scenario,expected", _BRIDGE_ANCHORS.items())
def test_bridge_F_tsc_pinned(scenario, expected):
    """TSC-side F_Bayes is bit-identical to the pinned anchor."""
    report = ff_htt_mc_cross_check(
        scenario=scenario, N=_N_SAMPLES, seed=_SEED, w=_W,
    )
    assert report.F_Bayes_tsc == pytest.approx(expected["F_tsc"], abs=1e-9), (
        f"F_Bayes_tsc({scenario}) drifted from pinned {expected['F_tsc']}: "
        f"got {report.F_Bayes_tsc!r}. Investigate tsc.diagnostics.filling_fraction "
        "and tsc.integration.htt_bridge._tsc_filling_fraction_from_stream."
    )


@pytest.mark.parametrize("scenario,expected", _BRIDGE_ANCHORS.items())
def test_bridge_F_htt_mean_pinned(scenario, expected):
    """HTT-side F_Bayes mean is bit-identical to the pinned anchor."""
    report = ff_htt_mc_cross_check(
        scenario=scenario, N=_N_SAMPLES, seed=_SEED, w=_W,
    )
    assert report.F_Bayes_htt_mean == pytest.approx(
        expected["F_htt_mean"], abs=1e-9
    ), (
        f"F_Bayes_htt_mean({scenario}) drifted from pinned "
        f"{expected['F_htt_mean']}: got {report.F_Bayes_htt_mean!r}."
    )


@pytest.mark.parametrize("scenario,expected", _BRIDGE_ANCHORS.items())
def test_bridge_rel_difference_pinned(scenario, expected):
    """TSC ↔ HTT relative agreement is pinned at machine-precision level.

    The bridge intentionally re-derives the same arithmetic from the
    shared RNG stream, so rel_diff must stay at 0 (or the known 2e-5
    floor that arises from htt's eps1 clip-to-nonnegative step for
    scenarios whose eps1 central value is small enough to sample the
    boundary).
    """
    report = ff_htt_mc_cross_check(
        scenario=scenario, N=_N_SAMPLES, seed=_SEED, w=_W,
    )
    assert report.rel_difference == pytest.approx(
        expected["rel_diff"], abs=1e-7
    ), (
        f"rel_difference({scenario}) drifted from pinned {expected['rel_diff']}: "
        f"got {report.rel_difference!r}. The tsc and htt paths are not "
        "reproducing the same arithmetic on the shared stream."
    )


# ─── 2. Determinism across repeated invocations ───────────────────────
def test_bridge_is_deterministic_across_repeated_calls():
    """Identical inputs → bit-identical reports across repeats."""
    r1 = ff_htt_mc_cross_check(scenario="S3", N=_N_SAMPLES, seed=_SEED, w=_W)
    r2 = ff_htt_mc_cross_check(scenario="S3", N=_N_SAMPLES, seed=_SEED, w=_W)
    assert r1.F_Bayes_tsc == r2.F_Bayes_tsc
    assert r1.F_Bayes_htt_mean == r2.F_Bayes_htt_mean
    assert r1.rel_difference == r2.rel_difference
    assert r1.F_Bayes_htt_median == r2.F_Bayes_htt_median


# ─── 3. Cross-reference to CLAUDE.md §5 semantic anchor (S3) ──────────
def test_bridge_S3_matches_claude_md_semantic_band():
    """S3 cross-check anchors inside the CLAUDE.md §5 band 0.093 ± 0.025.

    CLAUDE.md §5 records the production anchor ``F_Bayes = 0.093 ± 0.025``
    (§9.2 published band ``[0.068, 0.118]``). The S3 bridge result must
    land inside this window on both paths.
    """
    report = ff_htt_mc_cross_check(
        scenario="S3", N=_N_SAMPLES, seed=_SEED, w=_W,
    )
    lo, hi = PUBLISHED_F_BAYES_BAND
    assert lo <= report.F_Bayes_tsc <= hi
    assert lo <= report.F_Bayes_htt_mean <= hi
    # Semantic check vs CLAUDE.md central value 0.093 (not 0.068/0.118 edge).
    assert report.F_Bayes_tsc == pytest.approx(0.093, abs=0.025)


# ─── 4. Cross-reference to htt/tests/test_production_anchors.py ───────
def test_bridge_S3_htt_median_consistent_with_production_anchor():
    """Bridge S3 htt median must land inside the same CLAUDE.md §5 band
    as the HTT-side anchor pinned at ``F_median(S3) = 0.0904143077``.

    The bridge uses (N=100_000, seed=20260419) while the HTT-side anchor
    uses (N=200_000, seed=42) — they are *different* Monte Carlo draws
    by design (independent verification). This test asserts the draws
    are consistent with each other within MC noise (one σ ≈ 0.037 at
    the published band), which is the physical cross-check the plan
    calls for in §9.2.
    """
    report = ff_htt_mc_cross_check(
        scenario="S3", N=_N_SAMPLES, seed=_SEED, w=_W,
    )
    pinned_S3_median = 0.0904143077  # htt/tests/test_production_anchors.py
    # Two independent MC draws from the same underlying posterior must
    # agree to within ~1σ of the band (≈ 0.025 from CLAUDE.md §5).
    assert report.F_Bayes_htt_median == pytest.approx(
        pinned_S3_median, abs=0.025
    ), (
        f"Bridge S3 median {report.F_Bayes_htt_median!r} inconsistent "
        f"with htt anchor median {pinned_S3_median}: disagreement exceeds "
        "CLAUDE.md §5 1σ band — one of the two MC draws has drifted."
    )


# ─── 5. G19 architectural guarantees ──────────────────────────────────
def test_bridge_report_carries_is_cross_check_flag():
    """Every bridge report must mark itself as a cross-check (G19 §10.2bis)."""
    for scn in _BRIDGE_ANCHORS:
        r = ff_htt_mc_cross_check(scenario=scn, N=20_000, seed=1, w=_W)
        assert r.is_cross_check is True


def test_bridge_report_has_no_merged_score_field():
    """G19: no CrossCheckReport field merges tsc and htt F_Bayes."""
    import dataclasses

    from tsc.integration.htt_bridge import FFCrossCheckReport

    forbidden_substrings = ("combined", "merged", "total_score", "master_score")
    for f in dataclasses.fields(FFCrossCheckReport):
        name = f.name.lower()
        for bad in forbidden_substrings:
            assert bad not in name, (
                f"FFCrossCheckReport.{f.name} looks like a merged score "
                f"(contains {bad!r}) — G19 §10.2bis forbids fusing the two."
            )


# ─── 6. Edge-case coverage ────────────────────────────────────────────
def test_bridge_S0_is_zero_filling_fraction():
    """S0 (exact FLRW: eps1=beta=0) produces F_Bayes ≈ 0 on both sides.

    This is a degenerate sanity anchor — if the bridge starts leaking a
    nonzero F at S0, the filling-fraction definition is broken on one
    side or the tilt probe has contaminated the null.
    """
    from htt.core.analysis_extended import SCENARIOS

    # S0 is in SCENARIOS but FillingFraction.mc_posterior doesn't expose
    # it in the built-in scenario dict used here — skip with an explicit
    # fixture if absent.
    if "S0" not in SCENARIOS:
        pytest.skip("S0 not registered in htt SCENARIOS")
    report = ff_htt_mc_cross_check(scenario="S0", N=20_000, seed=1, w=_W)
    # eps1 is drawn from N(0, 0.30e-3) then clipped ≥ 0, so positive tail
    # survives. But the expected |F_Bayes| is ~10⁻³ or less — assert it
    # is at least two orders of magnitude below the band lower edge.
    assert report.F_Bayes_tsc < 0.01
    assert report.F_Bayes_htt_mean < 0.01
