#!/usr/bin/env python3
"""K1 (partial discharge): global look-elsewhere-corrected max-scan p-value of
the real Planck low-ell morphology.

The existing pipeline (`make_lowell_morphology_real_map.py`, REV-R102) computes
six registered low-ell anomaly statistics on the real Planck SMICA / Commander
NSIDE=16 map and their *per-statistic* p-values against an isotropic LambdaCDM
null. This script adds the missing **global** layer: it stacks the six statistics
into the OBSSTAT frozen max-scan (`htt/obsstat/lowell_global_calibration.py:
calibrate_max_scan`) and returns the single look-elsewhere-corrected global rank
p-value, with the dependence among statistics preserved by the per-simulation
maximum transformed score.

Scope / honest residual: the null here is an **isotropic LambdaCDM GRF ensemble**,
not the Planck FFP10 / NPIPE end-to-end simulations. So this discharges the
*look-elsewhere correction* on the real map (a genuine global statistic), but the
E2E-systematics calibration of `BLOCKED_MISSING_PR4_E2E_ACCESS` stays open:
swapping the GRF null for matched component-separated E2E summaries (same
map/mask/beam/statistic pipeline) requires the public FFP10/NPIPE sim ensemble,
which the Planck Legacy Archive serves only through its interactive query portal
(not a plain-URL download). cobaya was checked as an alternative source: its
``planck_2018_lowl.TT`` install delivers the Blackwell-Rao C_ell-level low-ell
TT likelihood (cov 249x249, mu, change-of-variable tables), not a map/a_lm
ensemble -- and the morphology statistics here depend on a_lm phases, so a
C_ell-only product cannot generate the matched null. No Bianchi family,
geometry, or native-solver claim.

Outputs: docs/generated/k1_global_maxscan.json. Deterministic (seeded); --check.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import sys

import numpy as np

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "scripts"))

import make_lowell_morphology_real_map as rm  # noqa: E402
from obsstat.lowell_global_calibration import calibrate_max_scan  # noqa: E402

OUT_JSON = REPO_ROOT / "docs/generated/k1_global_maxscan.json"
N_NULL = 2000
# max-scan tail direction per statistic: anomaly "lower"->minimise, "upper"->maximise.
_DIR = {"lower": "low", "upper": "high"}


def _sha256_file(path: Path) -> str:
    return "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest()


def _observed_and_null(map_path: Path, pix_vectors, cmb_apex, cl):
    keys = list(rm.TAILS)
    real_map = rm._load_real_map(map_path)
    real = rm.compute_map_statistics(real_map, pix_vectors, cmb_apex)
    observed = np.array([float(real[k]) for k in keys])
    nulls = rm._build_null_distribution(cl, pix_vectors, cmb_apex, N_NULL)
    null_matrix = np.column_stack([nulls[k] for k in keys])
    return keys, observed, null_matrix


def build_report() -> dict:
    pix_vectors = np.asarray(rm.hp.pix2vec(rm.NSIDE, np.arange(rm.hp.nside2npix(rm.NSIDE)))).T
    obs_defaults = json.loads(rm.OBS_DEFAULTS.read_text())
    cmb = obs_defaults["dipole_observations"]["cmb_planck_2018"]
    cmb_apex = np.asarray(rm.lb_to_unitvec(np.array(cmb["l_deg"]), np.array(cmb["b_deg"])), dtype=float).reshape(3)
    cl = rm._fiducial_cl(rm.LMAX)

    keys, observed, null_matrix = _observed_and_null(rm.SMICA_MAP, pix_vectors, cmb_apex, cl)
    directions = [_DIR[rm.TAILS[k]] for k in keys]
    smica = calibrate_max_scan(observed, null_matrix, directions)

    # Commander cross-check (independent component-separation method).
    _, obs_c, null_c = _observed_and_null(rm.COMMANDER_MAP, pix_vectors, cmb_apex, cl)
    commander = calibrate_max_scan(obs_c, null_c, directions)

    config = {"nside": rm.NSIDE, "lmax": rm.LMAX, "ell_min": rm.ELL_MIN,
              "n_null": N_NULL, "seed": rm.SEED, "statistics": keys,
              "directions": directions, "null_model": "isotropic_lambdacdm_grf"}
    config_hash = "sha256:" + hashlib.sha256(json.dumps(config, sort_keys=True).encode()).hexdigest()
    return {
        "schema": "htt.k1.global_maxscan.v1",
        "owner": "OBSSTAT",
        "claim_tier": "diagnostic_only",
        "blocker_partial": "BLOCKED_MISSING_PR4_E2E_ACCESS",
        "blocker_partial_note": "global look-elsewhere correction discharged on the real map under an isotropic LambdaCDM null; the FFP10/NPIPE E2E-systematics null remains blocked (PLA serves sims via an interactive query portal, not a plain-URL download)",
        "transfer_source": "none",
        "family_identification": False,
        "native_solver_result": False,
        "maps": {
            "smica": {"path": rm.SMICA_MAP.name, "input_hash": _sha256_file(rm.SMICA_MAP)},
            "commander": {"path": rm.COMMANDER_MAP.name, "input_hash": _sha256_file(rm.COMMANDER_MAP)},
            "product": "Planck PR3 component-separated CMB, NSIDE=16 low-ell temperature",
        },
        "statistics": keys,
        "config": config,
        "config_hash": config_hash,
        "smica": {
            "local_p": {k: float(p) for k, p in zip(keys, smica.local_p)},
            "global_p": float(smica.global_p),
            "observed_max_score": float(smica.observed_max_score),
        },
        "commander": {
            "local_p": {k: float(p) for k, p in zip(keys, commander.local_p)},
            "global_p": float(commander.global_p),
        },
        "headline": "global look-elsewhere-corrected low-ell morphology p-value on the real Planck map under an isotropic LambdaCDM null",
        "caveats": [
            "null is isotropic LambdaCDM GRF, not FFP10/NPIPE end-to-end (no instrument noise/systematics/residual foregrounds)",
            "look-elsewhere correction over the six registered statistics is real; the E2E-systematics calibration is not",
            "model-independent low-ell descriptor; no Bianchi family, geometry, anisotropy-evidence, or native-solver claim",
        ],
        "claim_boundary": "OBSSTAT global look-elsewhere diagnostic under an idealised null; not an E2E-calibrated detection",
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args(argv)
    payload = build_report()
    text = json.dumps(payload, indent=2, sort_keys=True) + "\n"
    if args.check:
        if not OUT_JSON.is_file() or OUT_JSON.read_text() != text:
            print("stale k1_global_maxscan.json; rerun scripts/k1_global_maxscan.py")
            return 1
        print("k1_global_maxscan.json up to date")
        return 0
    OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    OUT_JSON.write_text(text)
    print(f"wrote {OUT_JSON.relative_to(REPO_ROOT)}")
    print(f"   SMICA global p = {payload['smica']['global_p']:.4f} ; "
          f"Commander global p = {payload['commander']['global_p']:.4f}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
