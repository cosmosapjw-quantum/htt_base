"""PR-151 contract tests: DESI DR1 BGS exact-selection mock + per-mock refit.

The estimator mechanics (exact-selection draw, per-mock alpha/nuisance refit,
two-tier covariance, component confusion), the guards, the manifest kill
disposition and captions run everywhere on a small synthetic exact-selection
footprint; the tests that read the built artifacts skip when the heavy
real-DESI card is absent.
"""
from __future__ import annotations

import json
import subprocess
import sys
import warnings
from pathlib import Path

import numpy as np
import pytest

warnings.filterwarnings("ignore")

import healpy as hp

from obsstat.desi_exact_selection_mock import (
    DESIExactSelectionError,
    component_confusion_matrix,
    exact_selection_mock,
    generate_caption,
    lint_caption,
    official_mock_manifest,
    per_mock_refit,
    refuse_attribution_without_official_mocks,
    refuse_bianchi_from_desi,
    refuse_desi_detection,
    refuse_fixed_alpha,
    refuse_generic_grf_attribution,
    refuse_hard_coded_cap_ratio,
    survey_conditional_null,
    two_tier_covariance,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
GEN = REPO_ROOT / "docs/generated"
CARD = GEN / "desi_exact_selection_card.json"
needs_card = pytest.mark.skipif(
    not CARD.is_file(), reason="real DESI exact-selection card absent")


def _synthetic_footprint(nside=16, lmax=8):
    npix = hp.nside2npix(nside)
    vec = np.asarray(hp.pix2vec(nside, np.arange(npix)))
    Rp = {}
    for cap, sgn in (("NGC", 1), ("SGC", -1)):
        dens = np.clip(50 * (1 + 0.3 * sgn * vec[2]), 1, None)
        m = (sgn * vec[2] > -0.1)
        d = np.zeros(npix)
        d[m] = dens[m]
        Rp[cap] = d
    alpha = {c: 0.8 for c in Rp}
    z, x = vec[2], vec[0]
    # fit template: l=1 + l=2 in the polar direction (l=1 part is degenerate)
    sel = {c: (Rp[c] > 0) * (z + 0.5 * (3 * z ** 2 - 1) / 2) for c in Rp}
    # un-modelled l=2 systematic in the x direction (NOT in the fit basis)
    unm = {c: (Rp[c] > 0) * (3 * x ** 2 - 1) / 2 for c in Rp}
    Cl = np.zeros(lmax + 1)
    Cl[1:] = 1e-3 / np.arange(1, lmax + 1) ** 2.0
    return vec, Rp, alpha, sel, unm, Cl, nside, lmax


def test_exact_selection_mock_respects_the_real_selection() -> None:
    vec, Rp, alpha, sel, unm, Cl, nside, lmax = _synthetic_footprint()
    rng = np.random.default_rng(3)
    counts = exact_selection_mock(Rp, alpha, Cl, vec, nside, lmax, rng)
    for cap in Rp:
        off = Rp[cap] <= 0
        # exact selection: no galaxies drawn outside the random footprint
        assert np.all(counts[cap][off] == 0)
        # and some drawn inside it
        assert counts[cap][Rp[cap] > 0].sum() > 0


def test_per_mock_refit_refits_alpha_and_nuisance() -> None:
    vec, Rp, alpha, sel, unm, Cl, nside, lmax = _synthetic_footprint()
    r1 = per_mock_refit(
        exact_selection_mock(Rp, alpha, Cl, vec, nside, lmax,
                             np.random.default_rng(1)),
        Rp, vec, selection_template_per_cap=sel)
    r2 = per_mock_refit(
        exact_selection_mock(Rp, alpha, Cl, vec, nside, lmax,
                             np.random.default_rng(2)),
        Rp, vec, selection_template_per_cap=sel)
    # alpha is re-fit per cap and recovers the input normalisation ~0.8
    for cap in Rp:
        assert abs(r1["alpha_hat_per_cap"][cap] - 0.8) < 0.05
    # two different mocks give DIFFERENT re-fit alpha (not a fixed constant)
    assert (r1["alpha_hat_per_cap"]["NGC"]
            != r2["alpha_hat_per_cap"]["NGC"])
    assert "beta_hat" in r1 and r1["dipole"].shape == (3,)
    # the RAW dipole is the primary observable; the cleaned dipole is a separate
    # (secondary) quantity -- the raw is NOT silently deflated by the nuisance
    assert "cleaned_dipole_amplitude" in r1
    assert r1["dipole_amplitude"] == pytest.approx(
        float(np.linalg.norm(r1["dipole"])))


def test_component_confusion_is_confounded() -> None:
    vec, Rp, alpha, sel, unm, Cl, nside, lmax = _synthetic_footprint()
    cm = component_confusion_matrix(
        Rp, alpha, Cl, vec, nside, lmax, injection_amplitude=0.05,
        kinematic_dir=np.array([1.0, 0.0, 0.0]),
        selection_template_per_cap=sel, seed=7)
    assert cm["components_confounded"]
    # confounding is MATERIAL, not a ">0" tautology: the off-diagonal leakage is
    # a material fraction of the diagonal response
    assert cm["selection_into_dipole_relative"] >= cm["material_threshold"]
    assert cm["kinematic_into_nuisance_relative"] >= cm["material_threshold"]
    # a below-threshold leakage would NOT be called confounded
    assert cm["material_threshold"] > 0.0


def test_two_tier_covariance_reports_agreement() -> None:
    vec, Rp, alpha, sel, unm, Cl, nside, lmax = _synthetic_footprint()
    tt = two_tier_covariance(
        Rp, alpha, Cl, vec, nside, lmax, fast_tier_mocks=40,
        high_realism_tier_mocks=20, seed=5, selection_template_per_cap=sel,
        unmodeled_systematic_template_per_cap=unm, systematic_sigma=0.02)
    assert tt["cov_fast_trace"] > 0 and tt["cov_hi_trace"] > 0
    assert np.isfinite(tt["trace_ratio_fast_over_hi"])
    assert "relative_frobenius_gap" in tt
    assert len(tt["fast_tier_amplitudes"]) == 40
    # the un-modelled l>=2 systematic inflates the high-realism covariance, so
    # the fast tier genuinely under-estimates it (a real, non-vacuous test)
    assert tt["fast_tier_underestimates_covariance"]


def test_survey_conditional_null_is_two_sided_and_carries_no_attribution() -> None:
    scn = survey_conditional_null(0.01, [0.02, 0.03, 0.015, 0.05, 0.008])
    assert 0.0 < scn["survey_conditional_pooled_rank_p"] <= 1.0
    assert 0.0 <= scn["observed_percentile_in_null"] <= 1.0
    assert scn["two_sided_position"] in ("bulk", "deficit", "excess")
    assert scn["causal_attribution"] == "abandoned_official_mocks_absent"
    # a DEFICIT (below the null bulk) is flagged, not hidden by a one-sided p
    deficit = survey_conditional_null(0.001, [0.02, 0.03, 0.04, 0.05, 0.06])
    assert deficit["two_sided_position"] == "deficit"
    assert not deficit["consistent_with_survey_conditional_null"]


def test_official_manifest_kill_disposition() -> None:
    absent = official_mock_manifest(mocks_on_disk=False, reference_url="x")
    assert absent["causal_attribution_abandoned"]
    assert absent["survey_conditional_null_only"]
    assert absent["official_ezmocks"] == 1000
    present = official_mock_manifest(mocks_on_disk=True, reference_url="x")
    assert not present["causal_attribution_abandoned"]


def test_guards_reject_forbidden_moves() -> None:
    with pytest.raises(DESIExactSelectionError, match="source-derived"):
        refuse_hard_coded_cap_ratio("hard_coded")
    with pytest.raises(DESIExactSelectionError, match="re-fit per realisation"):
        refuse_fixed_alpha(False)
    with pytest.raises(DESIExactSelectionError, match="generic Gaussian"):
        refuse_generic_grf_attribution("clustering_dominated_causal")
    with pytest.raises(DESIExactSelectionError, match="official DESI"):
        refuse_attribution_without_official_mocks(False, "causal_attribution")
    with pytest.raises(DESIExactSelectionError, match="dipole-detection"):
        refuse_desi_detection("desi_dipole_detection")
    with pytest.raises(DESIExactSelectionError, match="Bianchi-family"):
        refuse_bianchi_from_desi("bianchi_family")
    # admissible inputs do NOT raise
    refuse_fixed_alpha(True)
    refuse_attribution_without_official_mocks(True, "causal_attribution")


def test_caption_lint_blocks_a_detection_phrase() -> None:
    with pytest.raises(DESIExactSelectionError, match="forbidden caption"):
        lint_caption("this is a DESI dipole detection of anisotropy")


# --------------------------------------------------------------------------
# built artifacts from the real DESI card (data-gated)
# --------------------------------------------------------------------------
@needs_card
def test_runner_check_and_real_artifacts() -> None:
    result = subprocess.run(
        [sys.executable,
         str(REPO_ROOT / "scripts/codex_harness/run_pr151_desi_exact_selection.py"),
         "--check"], cwd=REPO_ROOT, capture_output=True, text=True, check=False)
    assert result.returncode == 0, result.stdout + result.stderr
    refit = json.loads((GEN / "pr151_per_mock_refit.json")
                       .read_text(encoding="utf-8"))
    # the cap ratio is a source-derived float (NGC/SGC), never hard-coded
    assert refit["alpha_and_nuisance_refit_per_mock"]
    assert refit["source_derived_cap_ratio_ngc_over_sgc"] > 1.0
    conf = json.loads((GEN / "pr151_component_confusion.json")
                      .read_text(encoding="utf-8"))
    assert conf["components_confounded"]
    null = json.loads((GEN / "pr151_survey_conditional_null.json")
                      .read_text(encoding="utf-8"))
    assert null["causal_attribution"] == "abandoned_official_mocks_absent"
    man = json.loads((GEN / "pr151_mock_manifest.json")
                     .read_text(encoding="utf-8"))
    assert man["causal_attribution_abandoned"]
    report = json.loads((GEN / "pr151_mutation_report.json")
                        .read_text(encoding="utf-8"))
    assert report["surviving_mutation_count"] == 0
    assert len(report["mutations"]) == 6
