#!/usr/bin/env python3
"""PR-151 heavy producer: DESI DR1 BGS exact-selection mock card.

Loads the REAL DESI DR1 BGS_ANY randoms + data (NGC + SGC, downgraded to
NSIDE=64), builds the exact-selection mock ensemble (drawn from the real random
density per cap), re-fits alpha + a nuisance amplitude on every mock, and writes
the fast/high-realism two-tier covariance, the clustering/kinematic/selection
component confusion matrix, and the DESI-survey-conditional pooled-rank null of
the observed dipole to docs/generated/desi_exact_selection_card.json.

Run ONCE (loads ~2.3 GB of randoms); PR-151's runner reads this card (the ACT
pattern) and never re-runs the heavy read.  Because the official DESI validation
mocks are absent, causal attribution is abandoned and only the survey-conditional
null is reported.  Deterministic; --check verifies the card is current.
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import sys
from pathlib import Path

import numpy as np

REPO = Path(__file__).resolve().parents[1]
for root in (REPO, REPO / "htt", REPO / "htt" / "src"):
    if str(root) not in sys.path:
        sys.path.insert(0, str(root))

from htt.obsstat import number_count_dipole as ncd            # noqa: E402
from obsstat.desi_exact_selection_mock import (               # noqa: E402
    component_confusion_matrix,
    exact_selection_mock,
    official_mock_manifest,
    per_mock_refit,
    survey_conditional_null,
    two_tier_covariance,
)

OUT = REPO / "docs/generated/desi_exact_selection_card.json"
COMPACT = REPO / "workdir/compact_products/desi"
NSIDE = 64
LMAX = 8
BIAS = 1.5
FAST_TIER = 200
HIGH_REALISM_TIER = 40
NULL_MOCKS = 200
SEED = 20260725
REF_URL = "https://data.desi.lbl.gov/doc/releases/dr1/"


class InvalidatedHistoricalProducerError(RuntimeError):
    """PR-151 producer cannot run before a separately validated successor exists."""


def _load_desi_measure():
    spec = importlib.util.spec_from_file_location(
        "desi_dip", REPO / "scripts/desi_dipole_measure.py")
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def _selection_template(vec, mask):
    """A realistic declination-dependent imaging-depth systematic: a mix of an
    N-S (l=1) gradient AND an l=2 quadrupole in the survey polar (z) direction,
    mean-subtracted over the cap footprint.  Its l=1 part is DEGENERATE with the
    number-count dipole estimand (that degeneracy IS the confounding), so the
    per-mock refit reports the RAW dipole as primary and the nuisance-cleaned
    dipole only as a disclosed secondary."""
    z = vec[2]
    t = np.zeros(vec.shape[1])
    t[mask] = z[mask] + 0.5 * (3.0 * z[mask] ** 2 - 1.0) / 2.0
    if mask.any():
        t[mask] = t[mask] - t[mask].mean()
    return t


def _unmodeled_template(vec, mask):
    """A per-mock UN-modelled imaging systematic for the high-realism covariance
    tier: an l=2 quadrupole in the x direction, NOT spanned by the polar (z)
    fit template, so the estimator does not remove it and it genuinely inflates
    the high-realism covariance."""
    x = vec[0]
    t = np.zeros(vec.shape[1])
    t[mask] = (3.0 * x[mask] ** 2 - 1.0) / 2.0
    if mask.any():
        t[mask] = t[mask] - t[mask].mean()
    return t


def _round(obj, n=6):
    if isinstance(obj, float):
        return round(obj, n)
    if isinstance(obj, dict):
        return {k: _round(v, n) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_round(v, n) for v in obj]
    return obj


def measure() -> dict:
    raise InvalidatedHistoricalProducerError(
        "PR-151 historical producer is invalidated; successor formalism and independent validation are required"
    )
    import healpy as hp

    desi = _load_desi_measure()
    npix = hp.nside2npix(NSIDE)
    vec = np.asarray(hp.pix2vec(NSIDE, np.arange(npix)))       # (3, npix)
    caps = {}
    for cap in ("NGC", "SGC"):
        c = desi._load_cap(cap)
        if c is not None:
            caps[cap] = c
    if not caps:
        return {"schema": "htt.desi_exact_selection_card.v1",
                "status": "BLOCKED_MISSING_DESI_RANDOMS"}

    Rp = {c: caps[c]["Rp"] for c in caps}
    alpha_data = {c: caps[c]["alpha"] for c in caps}
    n_data = {c: caps[c]["n_data"] for c in caps}
    # source-derived cap ratio (NOT hard-coded)
    cap_ratio = float(n_data["NGC"] / n_data["SGC"]) if "SGC" in n_data else None
    sel_tpl = {c: _selection_template(vec, Rp[c] > 0) for c in caps}
    unm_tpl = {c: _unmodeled_template(vec, Rp[c] > 0) for c in caps}

    # observed dipole via the SAME per-mock refit estimator on the real counts;
    # the RAW dipole is the primary observable (no signal deflation), the
    # nuisance-cleaned dipole is a disclosed degenerate-direction-removed secondary
    obs = per_mock_refit({c: caps[c]["Dp"] for c in caps}, Rp, vec,
                         selection_template_per_cap=sel_tpl)

    # clustering C_ell from the data dN/dz at the fiducial bias
    zall = []
    for cap in ("NGC", "SGC"):
        f = COMPACT / f"BGS_ANY_{cap}_clustering_extended.npz"
        if f.exists():
            zall.append(np.asarray(np.load(f)["z"], float))
    z = np.concatenate(zall)
    z = z[(z > 0.01) & (z < 0.5)]
    zc = np.linspace(0.02, 0.5, 40)
    dz = zc[1] - zc[0]
    phi, _ = np.histogram(z, bins=np.r_[zc - dz / 2, zc[-1] + dz / 2])
    phi = phi.astype(float)
    from htt.obsstat.velocity_power import fiducial
    cos = fiducial()
    Cl, _ = ncd.angular_power_projection(phi, zc, cos["pk"], cos["om"],
                                         cos["h"], BIAS, LMAX)

    # survey-conditional null mock amplitudes (exact selection, per-mock refit)
    rng = np.random.default_rng(SEED)
    null_amps = []
    for _ in range(NULL_MOCKS):
        counts = exact_selection_mock(Rp, alpha_data, Cl, vec, NSIDE, LMAX, rng,
                                      selection_template_per_cap=sel_tpl,
                                      selection_amp=0.0)
        null_amps.append(per_mock_refit(
            counts, Rp, vec, selection_template_per_cap=sel_tpl)[
                "dipole_amplitude"])
    scn = survey_conditional_null(obs["dipole_amplitude"], null_amps)

    two_tier = two_tier_covariance(
        Rp, alpha_data, Cl, vec, NSIDE, LMAX, fast_tier_mocks=FAST_TIER,
        high_realism_tier_mocks=HIGH_REALISM_TIER, seed=SEED,
        selection_template_per_cap=sel_tpl,
        unmodeled_systematic_template_per_cap=unm_tpl, systematic_sigma=0.02)

    kin_dir = np.array([1.0, 0.0, 0.0])
    confusion = component_confusion_matrix(
        Rp, alpha_data, Cl, vec, NSIDE, LMAX, injection_amplitude=0.02,
        kinematic_dir=kin_dir, selection_template_per_cap=sel_tpl, seed=SEED)

    manifest = official_mock_manifest(mocks_on_disk=False, reference_url=REF_URL)

    return {
        "schema": "htt.desi_exact_selection_card.v1",
        "status": "SURVEY_CONDITIONAL_NULL",
        "config": {"nside": NSIDE, "lmax": LMAX, "bias": BIAS,
                   "fast_tier": FAST_TIER, "high_realism_tier": HIGH_REALISM_TIER,
                   "null_mocks": NULL_MOCKS, "seed": SEED},
        "caps": {c: {"n_data": n_data[c], "alpha": alpha_data[c]} for c in caps},
        "source_derived_cap_ratio_ngc_over_sgc": cap_ratio,
        "observed": {"dipole_amplitude": obs["dipole_amplitude"],
                     "cleaned_dipole_amplitude": obs["cleaned_dipole_amplitude"],
                     "alpha_hat_per_cap": obs["alpha_hat_per_cap"],
                     "beta_hat": obs["beta_hat"],
                     "primary_is_raw_dipole": True,
                     "cleaned_note": "the nuisance-cleaned amplitude removes the "
                     "l=1 power degenerate with the imaging template and is a "
                     "disclosed secondary, NOT the headline observable"},
        "survey_conditional_null": scn,
        "two_tier_covariance": two_tier,
        "component_confusion": confusion,
        "official_mock_manifest": manifest,
    }


def main(argv=None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args(argv)
    payload = _round(measure())
    text = json.dumps(payload, indent=2, sort_keys=True) + "\n"
    if args.check:
        if not OUT.is_file() or OUT.read_text() != text:
            print("stale desi_exact_selection_card.json")
            return 1
        print("desi_exact_selection_card.json up to date")
        return 0
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(text)
    print(f"wrote {OUT.relative_to(REPO)}  status={payload.get('status')} "
          f"obs_amp={payload.get('observed', {}).get('dipole_amplitude')} "
          f"scn_p={payload.get('survey_conditional_null', {}).get('survey_conditional_pooled_rank_p')}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
