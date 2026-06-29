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

Long-run (route 4 of docs/research_program/K1_E2E_DOWNLOAD_GUIDE.md): once the
~300 per-method *noise-only* sims are downloaded, ``--noise-mc-dir <dir>
[--method smica|commander] [--max-noise-sims N]`` upgrades the pure-GRF null to a
NOISE-AUGMENTED null (a local LambdaCDM signal added to each REAL instrument-noise
sim), carrying the real low-ell instrument-noise covariance for that method. This
writes a SEPARATE artifact (docs/generated/k1_global_maxscan_e2e_noise.json) so the
canonical GRF result is untouched. It is an UPGRADE of, not a replacement for, the
blocked full E2E null (no residual foregrounds/systematics, no matched signal), so
K1 stays measured_partial. Ready to run the moment the noise sims land.

Outputs: docs/generated/k1_global_maxscan.json (GRF null; default) and, in
long-run mode, docs/generated/k1_global_maxscan_e2e_noise.json. Deterministic
(seeded); --check verifies the canonical GRF artifact.
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
# E2E noise-augmented null (route 4 of K1_E2E_DOWNLOAD_GUIDE): a SEPARATE artifact,
# so the canonical GRF-null k1_global_maxscan.json (and its contract) is untouched.
OUT_E2E_JSON = REPO_ROOT / "docs/generated/k1_global_maxscan_e2e_noise.json"
N_NULL = 2000
DEFAULT_MAX_NOISE_SIMS = 300
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


def _observed_only(map_path: Path, pix_vectors, cmb_apex):
    """Observed statistics on the real map (no GRF null built)."""
    keys = list(rm.TAILS)
    real = rm.compute_map_statistics(rm._load_real_map(map_path), pix_vectors, cmb_apex)
    return keys, np.array([float(real[k]) for k in keys])


def _list_noise_sims(noise_mc_dir: Path) -> list[Path]:
    """Sorted noise-only sim files (FITS for the real download, NPZ for fixtures)."""
    files: list[Path] = []
    for pat in ("*.fits", "*.fits.gz", "*.npz"):
        files.extend(sorted(noise_mc_dir.glob(pat)))
    return files


def _load_noise_sim_map(path: Path) -> np.ndarray:
    """Load one NOISE-ONLY sim, downgrade-on-read to NSIDE=16 low-ell, return in uK.

    Handles the two real formats: the raw Planck FFP10/NPIPE noise sims
    (``dx12_v3_<method>_noise_mc_*.fits``, full-resolution K_CMB -> ud_grade to
    NSIDE=16 + uK rescale) and the compact NSIDE=16 ``.npz`` fixtures used by the
    in-repo regression test (same ``{I, unit}`` layout as the real downgraded maps).
    """
    if path.suffix == ".npz":
        return rm._load_real_map(path)
    # FITS: full-resolution noise map. Read, downgrade to NSIDE=16, rescale K->uK.
    m = np.asarray(rm.hp.read_map(path, verbose=False), dtype=float)
    if rm.hp.npix2nside(m.size) != rm.NSIDE:
        m = rm.hp.ud_grade(m, nside_out=rm.NSIDE)
    if float(np.nanstd(m)) < 1.0e-2:          # stored in K_CMB -> uK
        m = m * 1.0e6
    return m


def _e2e_noise_null(noise_mc_dir: Path, max_sims: int, pix_vectors, cmb_apex,
                    cl, seed: int):
    """Route-4 E2E-noise null: for each real instrument-noise sim, add a fresh,
    deterministic local LambdaCDM GRF signal realisation and compute the six
    registered statistics on the signal+noise map. This upgrades the pure-GRF null
    to one that carries the real low-ell instrument-noise covariance (per method),
    while needing only the ~300 noise sims (not the full signal+noise set).

    Returns (null_matrix [S x P], provenance list). Honest residual: this is still
    NOT the full FFP10/NPIPE E2E (no residual foregrounds / systematics / matched
    signal), so K1 stays measured_partial; the null label records exactly this."""
    keys = list(rm.TAILS)
    files = _list_noise_sims(noise_mc_dir)[:max_sims]
    rows: list[list[float]] = []
    provenance: list[dict] = []
    for i, f in enumerate(files):
        noise = _load_noise_sim_map(f)
        np.random.seed(seed + i)              # synfast uses the global RNG; per-sim seed
        signal = rm.hp.synfast(cl, nside=rm.NSIDE, lmax=rm.LMAX, pixwin=False)
        stats = rm.compute_map_statistics(signal + noise, pix_vectors, cmb_apex)
        rows.append([float(stats[k]) for k in keys])
        provenance.append({"file": f.name, "input_hash": _sha256_file(f)})
    if not rows:
        raise FileNotFoundError(
            f"no noise-only sims (*.fits/*.npz) found in {noise_mc_dir}")
    return np.asarray(rows, dtype=float), provenance


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


_METHOD_MAP = {"smica": rm.SMICA_MAP, "commander": rm.COMMANDER_MAP}


def build_e2e_noise_report(noise_mc_dir: Path, method: str = "smica",
                           max_noise_sims: int = DEFAULT_MAX_NOISE_SIMS) -> dict:
    """Route-4 long-run: the global max-scan against an E2E-NOISE-augmented null
    (real instrument-noise sims + local LambdaCDM signal). Method-matched: the null
    built from <method> noise sims is compared to the <method> observed map. Writes
    a SEPARATE artifact so the canonical GRF result is untouched. K1 stays
    measured_partial -- this carries real noise covariance but not residual
    foregrounds/systematics, so it is an upgrade of, not a replacement for, the
    blocked full E2E null."""
    if method not in _METHOD_MAP:
        raise ValueError(f"method must be one of {sorted(_METHOD_MAP)}")
    map_path = _METHOD_MAP[method]
    pix_vectors = np.asarray(rm.hp.pix2vec(rm.NSIDE, np.arange(rm.hp.nside2npix(rm.NSIDE)))).T
    obs_defaults = json.loads(rm.OBS_DEFAULTS.read_text())
    cmb = obs_defaults["dipole_observations"]["cmb_planck_2018"]
    cmb_apex = np.asarray(rm.lb_to_unitvec(np.array(cmb["l_deg"]), np.array(cmb["b_deg"])), dtype=float).reshape(3)
    cl = rm._fiducial_cl(rm.LMAX)

    keys, observed = _observed_only(map_path, pix_vectors, cmb_apex)
    directions = [_DIR[rm.TAILS[k]] for k in keys]
    e2e_null, provenance = _e2e_noise_null(noise_mc_dir, max_noise_sims,
                                           pix_vectors, cmb_apex, cl, rm.SEED)
    res = calibrate_max_scan(observed, e2e_null, directions)

    config = {"nside": rm.NSIDE, "lmax": rm.LMAX, "ell_min": rm.ELL_MIN,
              "method": method, "n_noise_sims": len(provenance), "seed": rm.SEED,
              "statistics": keys, "directions": directions,
              "null_model": "lambdacdm_signal_plus_real_instrument_noise"}
    config_hash = "sha256:" + hashlib.sha256(json.dumps(config, sort_keys=True).encode()).hexdigest()
    return {
        "schema": "htt.k1.global_maxscan_e2e_noise.v1",
        "owner": "OBSSTAT",
        "claim_tier": "diagnostic_only",
        "blocker_partial": "BLOCKED_MISSING_PR4_E2E_ACCESS",
        "blocker_partial_note": "noise-augmented null carries the real low-ell instrument-noise covariance for this method + a local LambdaCDM signal; it does NOT carry residual foregrounds/systematics or the matched FFP10/NPIPE signal, so the full E2E-systematics null stays partially open and K1 remains measured_partial",
        "transfer_source": "none",
        "family_identification": False,
        "native_solver_result": False,
        "method": method,
        "map": {"path": map_path.name, "input_hash": _sha256_file(map_path)},
        "noise_sims": {"dir": str(noise_mc_dir), "n_used": len(provenance),
                       "max_requested": max_noise_sims, "files": provenance},
        "statistics": keys,
        "config": config,
        "config_hash": config_hash,
        "result": {
            "local_p": {k: float(p) for k, p in zip(keys, res.local_p)},
            "global_p": float(res.global_p),
            "observed_max_score": float(res.observed_max_score),
        },
        "headline": f"K1 global look-elsewhere-corrected low-ell morphology p ({method}) under a LambdaCDM-signal + real-instrument-noise null",
        "caveats": [
            "null = local LambdaCDM GRF signal + REAL per-method instrument-noise sims (upgrade over pure GRF); still NOT the full FFP10/NPIPE E2E (no residual foregrounds/systematics, no matched signal)",
            "method-matched: the null is built from this method's noise sims only; compare methods side by side, do not average",
            "K1 stays measured_partial; this narrows but does not close BLOCKED_MISSING_PR4_E2E_ACCESS",
            "model-independent low-ell descriptor; no Bianchi family, geometry, anisotropy-evidence, or native-solver claim",
        ],
        "claim_boundary": "OBSSTAT global look-elsewhere diagnostic under a noise-augmented null; an upgrade of the GRF null, not a full E2E-calibrated detection",
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true",
                        help="verify the canonical GRF artifact is up to date")
    parser.add_argument("--noise-mc-dir", type=Path, default=None,
                        help="run the long-run E2E-noise mode against real noise-only sims "
                             "in this directory (*.fits / *.npz); writes a separate artifact")
    parser.add_argument("--method", choices=sorted(_METHOD_MAP), default="smica",
                        help="component-separation method matched to the noise sims (default: smica)")
    parser.add_argument("--max-noise-sims", type=int, default=DEFAULT_MAX_NOISE_SIMS,
                        help=f"cap on noise sims to use (default: {DEFAULT_MAX_NOISE_SIMS})")
    args = parser.parse_args(argv)

    if args.noise_mc_dir is not None:
        payload = build_e2e_noise_report(args.noise_mc_dir, args.method, args.max_noise_sims)
        text = json.dumps(payload, indent=2, sort_keys=True) + "\n"
        OUT_E2E_JSON.parent.mkdir(parents=True, exist_ok=True)
        OUT_E2E_JSON.write_text(text)
        print(f"wrote {OUT_E2E_JSON.relative_to(REPO_ROOT)}")
        print(f"   {args.method} E2E-noise global p = {payload['result']['global_p']:.4f} "
              f"({payload['noise_sims']['n_used']} noise sims)")
        return 0

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
