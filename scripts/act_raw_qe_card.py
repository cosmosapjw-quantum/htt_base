#!/usr/bin/env python3
"""PR-152 heavy producer: ACT DR6 lensing release-simulation cross-fit card.

Loads the REAL ACT DR6 reconstructed convergence (data + 400 Monte-Carlo sims,
downgraded to the L=2..10 low-multipole band) and computes the leave-one-
simulation cross-fit mean field diagnostic, the exact finite rank, the
stochastic-vs-fixed-template injection-law distinction, and the authenticated
inventory + upstream raw-QE availability decision, writing
docs/generated/act_raw_qe_card.json.

Run ONCE (reads ~60 GB of sim convergence alm); PR-152's runner reads this card
(the ACT pattern).  Because the raw-QE inputs are absent, only the
release-simulation cross-fit diagnostic is closed.  Deterministic; --check.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

import numpy as np

REPO = Path(__file__).resolve().parents[1]
for root in (REPO, REPO / "htt", REPO / "htt" / "src"):
    if str(root) not in sys.path:
        sys.path.insert(0, str(root))

from obsstat.act_raw_qe_gate import (               # noqa: E402
    act_dr6_lensing_inventory,
    exact_finite_rank,
    injection_law_distinction,
    leave_one_sim_crossfit_mean_field,
    upstream_availability_decision,
)

OUT = REPO / "docs/generated/act_raw_qe_card.json"
ACT = REPO / "workdir/raw/act_dr6_lensing/dr6_lensing_release/maps/baseline"
DATA_ALM = ACT / "kappa_alm_data_act_dr6_lensing_v1_baseline.fits"
N0_CURVE = ACT / "N_L_kk_act_dr6_lensing_v1_baseline.txt"
KAPPA_FILTER = ACT / "kappa_filter_act_dr6_lensing_v1_baseline.txt"
LIKE = REPO / "workdir/raw/act_dr6_lensing/ACT_dr6_likelihood_v1.2/v1.2"
SIMS_DIR = Path("/mnt/sn850x2t/htt_base_e2e/act_dr6_lensing_sims")
ELL_MIN, ELL_MAX = 2, 10
MAX_SIMS = 400
SEED = 20260726
VALIDATED_ELL = (40, 763)          # DR6 validated lensing power-spectrum range
REF_URL = "https://act.princeton.edu/act-dr6-data-products"


def _sha_head(path: Path, nbytes: int = 1 << 20) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        h.update(fh.read(nbytes))
    return "sha256head:" + h.hexdigest()


def _load_alm(path):
    import healpy as hp
    return np.asarray(hp.read_alm(str(path)), dtype=complex)


def _lowl(lmax):
    import healpy as hp
    idx, ms = [], []
    for ell in range(ELL_MIN, ELL_MAX + 1):
        for m in range(0, ell + 1):
            idx.append(hp.Alm.getidx(lmax, ell, m))
            ms.append(m)
    return np.array(idx), np.array(ms)


def _round(obj, n=6):
    if isinstance(obj, float):
        return round(obj, n)
    if isinstance(obj, dict):
        return {k: _round(v, n) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_round(v, n) for v in obj]
    return obj


def measure() -> dict:
    import healpy as hp

    sims = sorted(SIMS_DIR.glob("kappa_alm_sim_*_baseline_*.fits"))[:MAX_SIMS]
    if not DATA_ALM.is_file() or not sims:
        return {"schema": "htt.act_raw_qe_card.v1",
                "status": "BLOCKED_MISSING_ACT_LENSING_RELEASE"}
    # cache the extracted low-multipole modes so the crossfit/injection can be
    # re-derived without re-reading ~60 GB of sim alm (the heavy step is the read)
    cache = REPO / "workdir" / "act_lowl_cache.npz"
    cache.parent.mkdir(parents=True, exist_ok=True)
    if cache.is_file():
        z = np.load(cache)
        data_low, sim_low, wm = z["data_low"], z["sim_low"], z["wm"]
        if sim_low.shape[0] != len(sims):
            cache.unlink()
    if not cache.is_file():
        data = _load_alm(DATA_ALM)
        lmax = int(hp.Alm.getlmax(len(data)))
        idx, ms = _lowl(lmax)
        wm = np.where(ms == 0, 1.0, 2.0)
        data_low = data[idx]
        sim_low = np.empty((len(sims), idx.size), dtype=complex)
        for k, s in enumerate(sims):
            sim_low[k] = _load_alm(s)[idx]
        np.savez(cache, data_low=data_low, sim_low=sim_low, wm=wm)

    crossfit = leave_one_sim_crossfit_mean_field(sim_low, data_low, wm)
    rank = exact_finite_rank(n_sims=len(sims), ell_min=ELL_MIN, ell_max=ELL_MAX)
    injection = injection_law_distinction(
        crossfit["crossfit_sim_band_powers"], injection_amplitude=0.10,
        seed=SEED)

    present = {
        "kappa_alm_data": _sha_head(DATA_ALM),
        "n0_curve": _sha_head(N0_CURVE),
        "kappa_filter_response": _sha_head(KAPPA_FILTER),
        "n1_derivative_kk": _sha_head(LIKE / "like_corrs"
                                      / "N1der_KK_lmin600_lmax3000_full.txt"),
        "clkk_bandpowers": _sha_head(LIKE / "clkk_bandpowers_act.txt"),
        "n_reconstructed_sims": len(sims),
    }
    inventory = act_dr6_lensing_inventory(
        present=present, raw_qe_inputs_on_disk=False,
        validated_ell_range=VALIDATED_ELL, reference_url=REF_URL)
    decision = upstream_availability_decision(inventory)

    # drop the bulky per-sim band-power list from the card (keep the summary)
    crossfit_card = {k: v for k, v in crossfit.items()
                     if k != "crossfit_sim_band_powers"}
    return {
        "schema": "htt.act_raw_qe_card.v1",
        "status": "RELEASE_SIMULATION_CROSSFIT",
        "config": {"ell_min": ELL_MIN, "ell_max": ELL_MAX,
                   "n_sims": len(sims), "seed": SEED},
        "inventory": inventory,
        "availability_decision": decision,
        "crossfit_mean_field": crossfit_card,
        "exact_rank": rank,
        "injection_law": injection,
    }


def main(argv=None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args(argv)
    payload = _round(measure())
    text = json.dumps(payload, indent=2, sort_keys=True) + "\n"
    if args.check:
        if not OUT.is_file() or OUT.read_text() != text:
            print("stale act_raw_qe_card.json")
            return 1
        print("act_raw_qe_card.json up to date")
        return 0
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(text)
    cf = payload.get("crossfit_mean_field", {})
    print(f"wrote {OUT.relative_to(REPO)}  status={payload.get('status')} "
          f"crossfit_p={cf.get('crossfit_pooled_rank_p')} "
          f"self_mf_bias={cf.get('self_mean_field_bias_ratio_naive_over_crossfit')} "
          f"decision={payload.get('availability_decision', {}).get('decision')}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
