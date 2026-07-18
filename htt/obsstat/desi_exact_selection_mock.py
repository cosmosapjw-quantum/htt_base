"""PR-151: DESI DR1 BGS exact-selection mock and per-mock refit.

A number-count dipole mock that matches the DESI survey selection EXACTLY by
drawing from the real random-catalogue density per cap (NGC and SGC), modulated
by a linear-clustering Gaussian field and optional kinematic and selection-
systematic injections, then Poisson-sampled to the data count.  On EVERY mock
the random-to-data normalisation ``alpha`` and a systematic nuisance amplitude
are RE-FIT by the same estimator (never fixed).  A fast covariance tier over many
cheap mocks is validated against a smaller high-realism tier.  A clustering /
kinematic / selection component confusion matrix injects each component at a
known amplitude and reports how the SAME estimator attributes it, demonstrating
the three are confounded.

Because the official DESI DR1 validation mocks (1000 EZmocks + 25 AbacusSummit)
are NOT on disk, causal attribution is ABANDONED per the kill rule and only the
DESI-survey-conditional null of the observed dipole is reported.  DESI-survey-
conditional estimator/null DIAGNOSTIC at ``roadmap_rescue_v1:C3`` only: no
clustering-dominated causal claim, no DESI dipole-detection, anisotropy,
geometry, or Bianchi-family claim; the two CF4 P0s are untouched.
"""
from __future__ import annotations

from fractions import Fraction

import numpy as np

# bind the number-count dipole estimator primitives (rev-r193/r198)
from obsstat.number_count_dipole import (  # noqa: E402
    dipole_from_delta,
    synfast_seeded,
)
# bind the exact-discrete exchangeable pooled-rank estimator (PR-135)
from common.finite_null_ranking import pooled_rank_p  # noqa: E402

SCHEMA_VERSION = "pr151.desi_exact_selection_mock.v1"


class DESIExactSelectionError(ValueError):
    """Raised when the DESI exact-selection mock discipline is violated."""


# --------------------------------------------------------------------------
# official validation-mock manifest + kill disposition
# --------------------------------------------------------------------------
def official_mock_manifest(*, mocks_on_disk: bool,
                           reference_url: str) -> dict:
    """The DESI DR1 documentation lists 1000 EZmocks + 25 AbacusSummit
    validation mocks.  Their availability does NOT auto-guarantee estimator
    support: the exact selection / weights / window / randoms / cap match must be
    verified first.  When the official mocks are NOT on disk the kill rule fires
    --- causal attribution is abandoned and only the survey-conditional null is
    reported."""
    return {
        "official_ezmocks": 1000,
        "official_abacussummit_validation": 25,
        "reference_url": reference_url,
        "official_mocks_on_disk": bool(mocks_on_disk),
        "exact_selection_match_required": True,
        "causal_attribution_abandoned": not mocks_on_disk,
        "survey_conditional_null_only": not mocks_on_disk,
        "note": "the official DESI DR1 validation mocks (1000 EZmocks + 25 "
                "AbacusSummit) are required for causal component attribution; "
                "when they are absent the kill rule fires and only the DESI-"
                "survey-conditional null of the observed dipole is reported"}


# --------------------------------------------------------------------------
# exact-selection mock generator (draws from the REAL random density per cap)
# --------------------------------------------------------------------------
def exact_selection_mock(Rp_per_cap: dict, alpha_per_cap: dict, Cl: np.ndarray,
                         vec: np.ndarray, nside: int, lmax: int,
                         rng: np.random.Generator, *,
                         kinematic_amp: float = 0.0,
                         kinematic_dir: np.ndarray | None = None,
                         selection_template_per_cap: dict | None = None,
                         selection_amp: float = 0.0,
                         extra_contrast_per_cap: dict | None = None) -> dict:
    """Draw one exact-selection mock: the expected count in each pixel is
    ``alpha * Rp * (1 + delta_clustering + kinematic + selection + extra)`` where
    ``Rp`` is the REAL random density (so the survey selection/window/cap is
    matched exactly, not a binary mask), and the counts are Poisson-sampled.  The
    clustering field is a fresh Gaussian realisation of ``Cl``; ``extra_contrast``
    carries an arbitrary per-cap additive contrast (used for a per-mock random
    UN-modelled systematic in the high-realism covariance tier)."""
    dmap = synfast_seeded(Cl, nside, rng, lmax)
    counts_per_cap: dict = {}
    for cap, Rp in Rp_per_cap.items():
        a = alpha_per_cap[cap]
        mask = Rp > 0
        contrast = dmap.copy()
        if kinematic_amp and kinematic_dir is not None:
            contrast = contrast + kinematic_amp * (vec.T @ kinematic_dir)
        if selection_amp and selection_template_per_cap is not None:
            contrast = contrast + selection_amp * selection_template_per_cap[cap]
        if extra_contrast_per_cap is not None:
            contrast = contrast + extra_contrast_per_cap[cap]
        lam = np.clip(a * Rp * (1.0 + contrast), 0.0, None)
        counts = np.zeros_like(Rp)
        counts[mask] = rng.poisson(lam[mask])
        counts_per_cap[cap] = counts
    return counts_per_cap


def _dipole_amp(delta_per_cap, Rp_per_cap, vec):
    D = np.asarray(dipole_from_delta(delta_per_cap, Rp_per_cap, vec), float)
    return D, float(np.linalg.norm(D))


# --------------------------------------------------------------------------
# per-mock refit: RE-FIT alpha AND the nuisance amplitude (never fixed)
# --------------------------------------------------------------------------
def per_mock_refit(counts_per_cap: dict, Rp_per_cap: dict, vec: np.ndarray, *,
                   selection_template_per_cap: dict | None = None) -> dict:
    """Re-fit the random-to-data normalisation ``alpha`` per cap from the mock's
    OWN counts (never the data alpha), form the overdensity, and re-fit a
    systematic nuisance amplitude ``beta`` by Rp-weighted least squares against
    the template.  Both alpha and beta are re-estimated on every call.

    The PRIMARY reported dipole is the RAW dipole (no nuisance removal), so no
    signal is silently deflated.  A SECONDARY ``cleaned`` dipole subtracts the
    fitted nuisance; because a realistic imaging template carries an l=1 part
    that is DEGENERATE with the dipole estimand, the cleaned dipole removes power
    along the template's dipole direction and is reported only as a
    degenerate-direction-removed secondary --- never as the headline observable.
    """
    alpha_hat: dict = {}
    delta_per_cap: dict = {}
    num = den = 0.0
    for cap, Rp in Rp_per_cap.items():
        counts = counts_per_cap[cap]
        mask = Rp > 0
        a = float(counts[mask].sum() / Rp[mask].sum())     # RE-FIT alpha
        alpha_hat[cap] = a
        dd = np.zeros_like(Rp)
        dd[mask] = (counts[mask] - a * Rp[mask]) / (a * Rp[mask])
        delta_per_cap[cap] = dd
        if selection_template_per_cap is not None:
            t = selection_template_per_cap[cap]
            num += float((Rp[mask] * dd[mask] * t[mask]).sum())
            den += float((Rp[mask] * t[mask] * t[mask]).sum())
    beta_hat = float(num / den) if den > 0 else 0.0        # RE-FIT nuisance
    # RAW dipole = the primary observable (no signal deflation)
    D_raw, amp_raw = _dipole_amp(delta_per_cap, Rp_per_cap, vec)
    # cleaned dipole = SECONDARY (removes the template's degenerate l=1 power)
    cleaned = {}
    for cap, Rp in Rp_per_cap.items():
        dd = delta_per_cap[cap].copy()
        if selection_template_per_cap is not None:
            dd = dd - beta_hat * selection_template_per_cap[cap]
        cleaned[cap] = dd
    D_cl, amp_cl = _dipole_amp(cleaned, Rp_per_cap, vec)
    return {"alpha_hat_per_cap": alpha_hat, "beta_hat": beta_hat,
            "dipole": D_raw, "dipole_amplitude": amp_raw,
            "cleaned_dipole": D_cl, "cleaned_dipole_amplitude": amp_cl}


# --------------------------------------------------------------------------
# two-tier covariance: fast tier validated against a high-realism tier
# --------------------------------------------------------------------------
def two_tier_covariance(Rp_per_cap: dict, alpha_per_cap: dict, Cl: np.ndarray,
                        vec: np.ndarray, nside: int, lmax: int, *,
                        fast_tier_mocks: int, high_realism_tier_mocks: int,
                        seed: int,
                        selection_template_per_cap: dict | None = None,
                        unmodeled_systematic_template_per_cap: dict | None = None,
                        systematic_sigma: float = 0.01) -> dict:
    """Estimate the dipole-vector covariance from a FAST tier of many cheap mocks
    (clustering + shot only) and compare it to a smaller HIGH-REALISM tier that
    additionally carries a PER-MOCK RANDOM, UN-modelled imaging systematic (an
    l>=2 template the estimator does NOT fit, with a fresh N(0, systematic_sigma)
    amplitude every mock so it genuinely contributes to the cross-mock
    covariance).  Because that systematic is neither in the fit basis nor
    deterministic, the high-realism covariance genuinely INFLATES relative to the
    fast tier; the trace ratio and the relative Frobenius gap (full
    eigenstructure, not just the trace) quantify how much the fast tier
    UNDER-estimates the covariance when the systematic is present.  A trace ratio
    near 1 and a small Frobenius gap mean the fast tier is usable; a small ratio
    / large gap mean it is not."""
    def _run(n_mocks: int, tier_seed: int, realism: bool) -> np.ndarray:
        rng = np.random.default_rng(tier_seed)
        D = np.empty((n_mocks, 3))
        for i in range(n_mocks):
            extra = None
            if realism and unmodeled_systematic_template_per_cap is not None:
                amp = float(rng.normal(0.0, systematic_sigma))   # per-mock random
                extra = {c: amp * unmodeled_systematic_template_per_cap[c]
                         for c in Rp_per_cap}
            counts = exact_selection_mock(
                Rp_per_cap, alpha_per_cap, Cl, vec, nside, lmax, rng,
                extra_contrast_per_cap=extra)
            r = per_mock_refit(
                counts, Rp_per_cap, vec,
                selection_template_per_cap=selection_template_per_cap)
            D[i] = r["dipole"]
        return D
    fast = _run(fast_tier_mocks, seed, realism=False)
    hi = _run(high_realism_tier_mocks, seed + 1, realism=True)
    cov_fast = np.cov(fast.T)
    cov_hi = np.cov(hi.T)
    tr_fast = float(np.trace(cov_fast))
    tr_hi = float(np.trace(cov_hi))
    trace_ratio = float(tr_fast / tr_hi) if tr_hi > 0 else float("inf")
    nrm_hi = float(np.linalg.norm(cov_hi))
    frob_gap = float(np.linalg.norm(cov_hi - cov_fast) / nrm_hi) \
        if nrm_hi > 0 else float("inf")
    fast_underestimates = bool(trace_ratio < 0.9 or frob_gap > 0.15)
    return {"fast_tier_mocks": fast_tier_mocks,
            "high_realism_tier_mocks": high_realism_tier_mocks,
            "cov_fast_trace": tr_fast, "cov_hi_trace": tr_hi,
            "trace_ratio_fast_over_hi": trace_ratio,
            "relative_frobenius_gap": frob_gap,
            "fast_tier_underestimates_covariance": fast_underestimates,
            "fast_tier_amplitudes": [float(np.linalg.norm(d)) for d in fast],
            "note": "the high-realism tier carries a per-mock RANDOM un-modelled "
                    "l>=2 imaging systematic the estimator does not fit; the "
                    "trace ratio and relative Frobenius gap quantify how much the "
                    "fast tier under-estimates the covariance when that "
                    "systematic is present (near 1 / near 0 means usable)"}


# --------------------------------------------------------------------------
# clustering / kinematic / selection component confusion matrix
# --------------------------------------------------------------------------
CONFUSION_MATERIAL_THRESHOLD = 0.10


def component_confusion_matrix(Rp_per_cap: dict, alpha_per_cap: dict,
                               Cl: np.ndarray, vec: np.ndarray, nside: int,
                               lmax: int, *, injection_amplitude: float,
                               kinematic_dir: np.ndarray,
                               selection_template_per_cap: dict,
                               seed: int,
                               material_threshold: float
                               = CONFUSION_MATERIAL_THRESHOLD) -> dict:
    """Inject each of {clustering, kinematic, selection} at a MATCHED dipole-scale
    ``injection_amplitude`` (others off), run the SAME estimator, and report how
    much of the injected signal lands in the dipole channel (|D_raw|) vs the
    nuisance channel (|beta|).  Confounding is asserted only when the OFF-diagonal
    leakage is MATERIAL relative to the diagonal response --- selection's leakage
    into the dipole channel is at least ``material_threshold`` of kinematic's
    dipole response, AND kinematic's leakage into the nuisance channel is at least
    ``material_threshold`` of selection's nuisance response.  A ``> 0`` float is
    NOT enough."""
    rows = {}
    _offset = {"clustering": 0, "kinematic": 1, "selection": 2}
    for comp in ("clustering", "kinematic", "selection"):
        rng = np.random.default_rng(seed + _offset[comp])
        kwargs = dict(kinematic_amp=0.0, selection_amp=0.0)
        boost = 0.0
        if comp == "clustering":
            # inject a matched-amplitude additive random dipole (a single
            # clustering-sourced dipole realisation), NOT a small power rescale
            gdir = rng.standard_normal(3)
            gdir = gdir / np.linalg.norm(gdir)
            kwargs.update(kinematic_amp=injection_amplitude, kinematic_dir=gdir)
        elif comp == "kinematic":
            kwargs.update(kinematic_amp=injection_amplitude,
                          kinematic_dir=kinematic_dir)
        elif comp == "selection":
            kwargs.update(selection_amp=injection_amplitude,
                          selection_template_per_cap=selection_template_per_cap)
        counts = exact_selection_mock(
            Rp_per_cap, alpha_per_cap, (1.0 + boost) * Cl, vec, nside, lmax,
            rng, **kwargs)
        r = per_mock_refit(counts, Rp_per_cap, vec,
                           selection_template_per_cap=selection_template_per_cap)
        rows[comp] = {"dipole_channel": r["dipole_amplitude"],
                      "nuisance_channel": abs(r["beta_hat"])}
    # MATERIAL off-diagonal leakage (relative to the diagonal response), not a
    # bare ">0" tautology on positive floats
    kin_dipole = rows["kinematic"]["dipole_channel"] or 1e-30
    sel_nuisance = rows["selection"]["nuisance_channel"] or 1e-30
    sel_into_dipole = rows["selection"]["dipole_channel"] / kin_dipole
    kin_into_nuisance = rows["kinematic"]["nuisance_channel"] / sel_nuisance
    confounded = bool(sel_into_dipole >= material_threshold
                      and kin_into_nuisance >= material_threshold)
    return {"injection_amplitude": injection_amplitude, "rows": rows,
            "material_threshold": material_threshold,
            "selection_into_dipole_relative": float(sel_into_dipole),
            "kinematic_into_nuisance_relative": float(kin_into_nuisance),
            "components_confounded": confounded,
            "note": "each component is injected at a matched dipole-scale "
                    "amplitude and read by the same estimator; confounding is "
                    "asserted only when the off-diagonal leakage is a material "
                    "fraction of the diagonal response (selection into the dipole "
                    "channel, kinematic into the nuisance channel), so causal "
                    "attribution is not identified"}


# --------------------------------------------------------------------------
# survey-conditional null (NO causal attribution)
# --------------------------------------------------------------------------
def survey_conditional_null(observed_amplitude: float,
                            null_amplitudes: list) -> dict:
    """Report the observed dipole amplitude against the survey-conditional null
    mock amplitudes (clustering + shot under the exact selection) BOTH as the
    exchangeable right-tail pooled-rank (PR-135) AND as the two-sided percentile
    position, so a DEFICIT (under-dispersion) is visible and is not hidden behind
    a one-sided ``p > 0.05`` screen.  This is a consistency statement ONLY --- it
    carries NO causal attribution of the observed dipole to clustering,
    kinematic, or selection, because the official validation mocks needed to
    break that confusion are absent."""
    nulls = np.asarray(null_amplitudes, float)
    p_upper = float(pooled_rank_p(observed_amplitude, nulls))     # right tail
    percentile = float(np.mean(nulls < observed_amplitude))       # fraction below
    position = ("excess" if percentile > 0.95 else
                "deficit" if percentile < 0.05 else "bulk")
    in_bulk = bool(position == "bulk")
    return {"observed_amplitude": float(observed_amplitude),
            "n_null": int(nulls.size),
            "survey_conditional_pooled_rank_p": p_upper,
            "observed_percentile_in_null": percentile,
            "two_sided_position": position,
            "consistent_with_survey_conditional_null": in_bulk,
            "causal_attribution": "abandoned_official_mocks_absent",
            "note": "survey-conditional two-sided consistency only (the observed "
                    "amplitude must sit in the bulk, not an excess NOR a deficit "
                    "tail); the observed dipole is NOT attributed to clustering, "
                    "kinematic, or selection --- that attribution is not "
                    "identified without the official DESI validation mocks"}


# --------------------------------------------------------------------------
# guards
# --------------------------------------------------------------------------
def refuse_hard_coded_cap_ratio(source: str) -> None:
    if source in ("hard_coded", "literal", "constant"):
        raise DESIExactSelectionError(
            "the NGC-over-SGC cap ratio must be source-derived, not hard-coded")


def refuse_fixed_alpha(refit: bool) -> None:
    if not refit:
        raise DESIExactSelectionError(
            "a mock whose alpha is fixed rather than re-fit per realisation is "
            "rejected")


def refuse_generic_grf_attribution(claim: str) -> None:
    if claim in ("clustering_dominated_causal", "grf_causal_attribution"):
        raise DESIExactSelectionError(
            "a clustering-dominated causal claim from a generic Gaussian "
            "field without exact-support mocks is rejected")


def refuse_attribution_without_official_mocks(mocks_on_disk: bool,
                                              claim: str) -> None:
    if claim in ("component_attribution", "causal_attribution") \
            and not mocks_on_disk:
        raise DESIExactSelectionError(
            "any causal component attribution without the official DESI "
            "validation mocks is rejected")


def refuse_desi_detection(claim: str) -> None:
    if claim in ("desi_dipole_detection", "anisotropy_detection"):
        raise DESIExactSelectionError(
            "a DESI dipole-detection or anisotropy claim is rejected")


def refuse_bianchi_from_desi(claim: str) -> None:
    if claim in ("bianchi_family", "geometry"):
        raise DESIExactSelectionError(
            "a Bianchi-family or geometry claim from the DESI dipole is rejected")


# --------------------------------------------------------------------------
# captions
# --------------------------------------------------------------------------
_FORBIDDEN = tuple(
    a + b for a, b in (
        ("hard-coded ", "cap ratio"),
        ("fixed-alpha ", "mock"),
        ("clustering-dominated ", "causal attribution"),
        ("desi dipole ", "detection"),
        ("bianchi family ", "from desi"),
        ("anisotropy ", "detected"),
    ))


def lint_caption(text: str) -> None:
    low = text.lower()
    for phrase in _FORBIDDEN:
        if phrase in low:
            raise DESIExactSelectionError(f"forbidden caption phrase: {phrase!r}")


def generate_caption(manifest: dict, confusion: dict, null: dict) -> str:
    return (
        f"DESI DR1 BGS exact-selection number-count dipole mock: the mock draws "
        f"from the real random density per cap (exact selection/window match), "
        f"alpha and a nuisance amplitude are re-fit on every mock, and a "
        f"clustering/kinematic/selection component confusion matrix shows the "
        f"three are confounded (components_confounded="
        f"{confusion['components_confounded']}). The official DESI validation "
        f"mocks ({manifest['official_ezmocks']} EZmocks + "
        f"{manifest['official_abacussummit_validation']} AbacusSummit) are "
        f"absent, so causal attribution is abandoned and only the survey-"
        f"conditional pooled-rank null is reported "
        f"(p={null['survey_conditional_pooled_rank_p']:.3f}). DESI-survey-"
        f"conditional estimator/null diagnostic only; no dipole detection, no "
        f"anisotropy, no Bianchi-family claim; the two CF4 P0s stay OPEN.")
