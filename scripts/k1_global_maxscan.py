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

Long-run (docs/research_program/K1_E2E_DOWNLOAD_GUIDE.md), two modes, each a
SEPARATE artifact so the canonical GRF result is untouched:

  * Route A FULL E2E (the exit gate; needs the ~1 TB FFP10 download) --
    ``--cmb-mc-dir <cmb> --noise-mc-dir <noise> [--method] [--max-sims N]``: the
    PLA-available ensemble of REAL component-separated CMB MC + REAL instrument-noise
    MC, paired BY PARSED MC id (noise[cmb_id mod n_noise]) so the known missing CMB
    realization 00970 (999 usable of a nominal 1000) does not misalign the pairing;
    carries signal + noise/systematics + the cleaning transfer. This is the null whose
    exit gate flips K1 measured_partial -> measured and closes
    BLOCKED_MISSING_PR4_E2E_ACCESS. Writes docs/generated/k1_global_maxscan_e2e_full.json.
  * Route 4 noise-only (lighter, ~40 GB) -- ``--noise-mc-dir <noise>`` alone: a
    local LambdaCDM signal added to each real noise MC. An UPGRADE of, not a
    replacement for, the full null (no residual foregrounds/systematics, no matched
    signal), so K1 stays measured_partial. Writes
    docs/generated/k1_global_maxscan_e2e_noise.json.

Outputs: docs/generated/k1_global_maxscan.json (GRF null; default), plus the E2E
artifact for the long-run mode used. Deterministic (seeded); --check verifies the
canonical GRF artifact.
"""
from __future__ import annotations

import os
# Single-thread the SHT/BLAS backends BEFORE numpy/healpy import: N worker processes
# each running 1 thread saturates the cores without oversubscription, and -- critically
# -- it keeps libsharp's threadpool from being created, so the parallel pool never hits
# the fork-after-OpenMP deadlock. (The pool also uses the 'spawn' context for safety.)
for _v in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS"):
    os.environ.setdefault(_v, "1")

import argparse
from concurrent.futures import ProcessPoolExecutor
import hashlib
import json
import multiprocessing as mp
from pathlib import Path
import re
import sys

import numpy as np

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "scripts"))
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

import make_lowell_morphology_real_map as rm  # noqa: E402
from obsstat.lowell_global_calibration import calibrate_max_scan  # noqa: E402
from htt.obsstat.lowell_precision import (  # noqa: E402
    DEFAULT_LMAX,
    DEFAULT_PROC_NSIDE,
    PrecisionConfig,
    downgrade_mask,
    precision_map_statistics,
)

# Full-resolution observed maps + common temperature mask (for the v2 precision path:
# observed must be processed identically to the sims, so it comes from the full-res
# map, not the NSIDE=16 .npz used by the v1 ell<=8 path).
_PLANCK = REPO_ROOT / "workdir/raw/planck_data"
FULLRES_OBS = {"smica": _PLANCK / "COM_CMB_IQU-smica_2048_R3.00_full.fits",
               "commander": _PLANCK / "COM_CMB_IQU-commander_2048_R3.00_full.fits"}
MASK_HI = _PLANCK / "COM_Mask_CMB-common-Mask-Int_2048_R3.00.fits"

OUT_JSON = REPO_ROOT / "docs/generated/k1_global_maxscan.json"
# E2E nulls (K1_E2E_DOWNLOAD_GUIDE): SEPARATE artifacts, so the canonical GRF-null
# k1_global_maxscan.json (and its contract) is untouched.
#   route 4 (noise-only + local LambdaCDM signal)  -> OUT_E2E_JSON
#   Route A full (real CMB MC + real noise MC, E2E) -> OUT_E2E_FULL_JSON
OUT_E2E_JSON = REPO_ROOT / "docs/generated/k1_global_maxscan_e2e_noise.json"
OUT_E2E_FULL_JSON = REPO_ROOT / "docs/generated/k1_global_maxscan_e2e_full.json"
N_NULL = 2000
DEFAULT_MAX_NOISE_SIMS = 300
DEFAULT_MAX_FULL_SIMS = 300   # Planck-2018 anomaly standard; raise to 1000 with full FFP10
# Nominal FFP10 SMICA library sizes and the registered missing/corrupt CMB realization.
# The library nominally has 1000 CMB MC (ids 00000..00999) + 300 noise MC (00000..00299);
# CMB realization 00970 is a known missing/corrupt file on the PLA -> 999 usable CMB MC.
FFP10_SMICA_NOMINAL_CMB = 1000
FFP10_SMICA_NOMINAL_NOISE = 300
KNOWN_MISSING_FFP10_SMICA_CMB = (970,)
PLA_CONFIRMATION = "pending"   # set to "confirmed_absent" once ESA/PLA confirms 00970
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


def _list_sims(sim_dir: Path) -> list[Path]:
    """Sorted sim files (FITS for the real download, NPZ for fixtures)."""
    files: list[Path] = []
    for pat in ("*.fits", "*.fits.gz", "*.npz"):
        files.extend(sorted(sim_dir.glob(pat)))
    return files


# back-compat alias (rev-r135 name)
_list_noise_sims = _list_sims

_MC_ID = re.compile(r"_mc_(\d{5})(?:_raw)?\.(?:fits(?:\.gz)?|npz)$")


def _parse_mc_id(path: Path) -> int:
    """Parse the 5-digit Monte-Carlo id from a sim filename
    (``dx12_v3_<method>_<cmb|noise>_mc_00970_raw.fits[.gz]`` or the ``.npz`` fixture
    ``..._mc_00970.npz``). Raising on an unparseable name is a deliberate kill switch."""
    m = _MC_ID.search(path.name)
    if not m:
        raise ValueError(f"cannot parse MC id from {path.name}")
    return int(m.group(1))


def _pair_cmb_noise_by_id(cmb_dir: Path, noise_dir: Path, max_sims: int):
    """Pair each available CMB MC with a noise MC BY PARSED id --- NOT by list
    position. The Planck FFP10 SMICA library has a known missing/corrupt CMB
    realization (00970), so positional pairing (``noise[i mod n]``) would silently
    misalign every CMB after the gap; id-based pairing (``noise[cmb_id mod n_noise]``)
    is robust to arbitrary gaps. Returns (cmb_paths_used, pairs, n_noise) where each
    pair is (cmb_path, cmb_id, noise_path, noise_id)."""
    cmb_paths = sorted(_list_sims(cmb_dir), key=_parse_mc_id)[:max_sims]
    noise_paths = _list_sims(noise_dir)
    if not cmb_paths:
        raise FileNotFoundError(f"no CMB sims (*.fits/*.npz) found in {cmb_dir}")
    if not noise_paths:
        raise FileNotFoundError(f"no noise sims (*.fits/*.npz) found in {noise_dir}")
    noise_by_id = {_parse_mc_id(p): p for p in noise_paths}
    n_noise = len(noise_by_id)
    pairs = []
    for cmb_path in cmb_paths:
        cmb_id = _parse_mc_id(cmb_path)
        noise_id = cmb_id % n_noise
        if noise_id not in noise_by_id:               # gap in the noise set -> stop
            raise KeyError(f"noise MC id {noise_id:05d} (for CMB {cmb_id:05d}) is absent "
                           f"in {noise_dir}")
        pairs.append((cmb_path, cmb_id, noise_by_id[noise_id], noise_id))
    return cmb_paths, pairs, n_noise


def _load_sim_map(path: Path, nside: int = rm.NSIDE) -> np.ndarray:
    """Load one simulation map (CMB MC or noise MC), downgrade-on-read to ``nside``
    (default NSIDE=16), return in uK.

    Handles the two real formats: the raw Planck FFP10/NPIPE sims
    (``dx12_v3_<method>_{cmb,noise}_mc_*.fits``, full-resolution K_CMB -> ud_grade
    + uK rescale) and the compact ``.npz`` fixtures used by the in-repo regression
    test (same ``{I, unit}`` layout as the real downgraded maps).
    """
    if path.suffix == ".npz":
        m = rm._load_real_map(path)
    else:
        m = np.asarray(rm.hp.read_map(path), dtype=float)  # field=0 (I); silent by default
        if float(np.nanstd(m)) < 1.0e-2:      # stored in K_CMB -> uK
            m = m * 1.0e6
    if rm.hp.npix2nside(m.size) != nside:
        m = rm.hp.ud_grade(m, nside_out=nside)
    return m


# back-compat alias (rev-r135 name)
_load_noise_sim_map = _load_sim_map


def _e2e_full_null(cmb_mc_dir: Path, noise_mc_dir: Path, max_sims: int,
                   pix_vectors, cmb_apex):
    """Route-A FULL E2E null (the strongest, what flips K1 measured_partial->measured):
    for each available REAL component-separated CMB MC, add a REAL instrument-noise MC
    (paired BY PARSED id, ``noise[cmb_id mod n_noise]`` -- robust to the known missing
    CMB realization 00970) and compute the six registered statistics on the CMB+noise
    map. Matched FFP10/NPIPE E2E ensemble: real signal + real noise/systematics + (via
    the maps) the component-separation transfer -- no local-LambdaCDM stand-in.

    Returns (null_matrix [S x P], provenance list)."""
    keys = list(rm.TAILS)
    _cmb, pairs, _n = _pair_cmb_noise_by_id(cmb_mc_dir, noise_mc_dir, max_sims)
    rows: list[list[float]] = []
    provenance: list[dict] = []
    for cf, cmb_id, nf, noise_id in pairs:
        signal = _load_sim_map(cf)
        noise = _load_sim_map(nf)
        stats = rm.compute_map_statistics(signal + noise, pix_vectors, cmb_apex)
        rows.append([float(stats[k]) for k in keys])
        provenance.append({"cmb_file": cf.name, "cmb_id": cmb_id, "cmb_hash": _sha256_file(cf),
                           "noise_file": nf.name, "noise_id": noise_id, "noise_hash": _sha256_file(nf)})
    return np.asarray(rows, dtype=float), provenance


# --------------------------------------------------------------------------- #
# v2 PRECISION path (proc-NSIDE + ell_max + mask, optionally parallel --jobs).
# Workers are module-level + state passed via an initializer so they are picklable
# for ProcessPoolExecutor. The v1 ell<=8 path above is untouched.
# --------------------------------------------------------------------------- #
_W: dict = {}


def _winit(cfg, keep_mask, cmb_apex, noise_cache, cl, seed):
    # threads already pinned to 1 at module import (before healpy); just stash state
    _W.update(cfg=cfg, keep=keep_mask, apex=np.asarray(cmb_apex, float),
              noise=noise_cache, cl=cl, seed=seed,
              pix=np.asarray(rm.hp.pix2vec(cfg.proc_nside,
                             np.arange(rm.hp.nside2npix(cfg.proc_nside)))).T,
              keys=list(rm.TAILS))


def _w_full(task):
    cmb_id, cmb_path, noise_id = task           # id-based pairing (robust to gaps)
    cfg = _W["cfg"]
    sig = _load_sim_map(Path(cmb_path), cfg.proc_nside)
    noise = _W["noise"][noise_id]               # id-keyed cache dict
    stats = precision_map_statistics(sig + noise, _W["apex"], cfg, _W["keep"], _W["pix"])
    return cmb_id, [float(stats[k]) for k in _W["keys"]]


def _w_noise(task):
    i, noise_path = task
    cfg = _W["cfg"]
    noise = _load_sim_map(Path(noise_path), cfg.proc_nside)
    np.random.seed(_W["seed"] + i)                       # synfast uses the global RNG
    sig = rm.hp.synfast(_W["cl"], nside=cfg.proc_nside, lmax=cfg.lmax, pixwin=False)
    stats = precision_map_statistics(sig + noise, _W["apex"], cfg, _W["keep"], _W["pix"])
    return i, [float(stats[k]) for k in _W["keys"]]


def _load_noise_one(args):
    path, nside = args
    return _load_sim_map(Path(path), nside)


def _map_parallel(worker, tasks, init_args, jobs):
    """Run worker over tasks, serial (jobs<=1) or via ProcessPoolExecutor. Returns
    rows ordered by task index. Serial path sets the same worker globals so results
    are identical to the parallel path."""
    if jobs <= 1:
        _winit(*init_args)
        out = [worker(t) for t in tasks]
    else:
        ctx = mp.get_context("spawn")     # spawn: avoids fork-after-OpenMP deadlock
        with ProcessPoolExecutor(max_workers=jobs, mp_context=ctx,
                                 initializer=_winit, initargs=init_args) as ex:
            chunk = max(1, len(tasks) // (jobs * 4) or 1)
            out = list(ex.map(worker, tasks, chunksize=chunk))
    out.sort(key=lambda r: r[0])
    return np.asarray([r[1] for r in out], dtype=float)


def _keep_mask(cfg: PrecisionConfig):
    if not cfg.masked:
        return None
    if not MASK_HI.is_file():
        raise FileNotFoundError(f"common mask not found at {MASK_HI}")
    mask_hi = np.asarray(rm.hp.read_map(MASK_HI), dtype=float)
    return downgrade_mask(mask_hi, cfg.proc_nside)


def _observed_precision(method: str, cfg: PrecisionConfig, keep_mask, cmb_apex):
    """Observed 6-vector under the v2 config, from the FULL-RES observed map
    processed identically to the sims (downgrade -> mask+inpaint -> lmax)."""
    obs_path = FULLRES_OBS[method]
    if not obs_path.is_file():
        raise FileNotFoundError(f"full-resolution observed map not found at {obs_path}")
    obs = _load_sim_map(obs_path, cfg.proc_nside)
    keys = list(rm.TAILS)
    stats = precision_map_statistics(obs, cmb_apex, cfg, keep_mask)
    return keys, np.array([float(stats[k]) for k in keys])


def _e2e_full_null_precision(cmb_mc_dir, noise_mc_dir, max_sims, cfg, keep_mask,
                             cmb_apex, jobs):
    _cmb, pairs, _n = _pair_cmb_noise_by_id(cmb_mc_dir, noise_mc_dir, max_sims)
    noise_files = _list_sims(noise_mc_dir)
    # pre-downgrade each unique noise sim ONCE, keyed BY id (not position), so the
    # id-based pairing survives any gap in the CMB set (missing 00970).
    if jobs <= 1:
        noise_cache = {_parse_mc_id(f): _load_sim_map(f, cfg.proc_nside) for f in noise_files}
    else:
        ctx = mp.get_context("spawn")
        with ProcessPoolExecutor(max_workers=jobs, mp_context=ctx) as ex:
            downgraded = list(ex.map(
                _load_noise_one, [(str(f), cfg.proc_nside) for f in noise_files]))
        noise_cache = {_parse_mc_id(f): m for f, m in zip(noise_files, downgraded)}
    tasks = [(cmb_id, str(cf), noise_id) for cf, cmb_id, _nf, noise_id in pairs]
    rows = _map_parallel(_w_full, tasks,
                         (cfg, keep_mask, cmb_apex, noise_cache, None, rm.SEED), jobs)
    provenance = [{"cmb_file": cf.name, "cmb_id": cmb_id, "cmb_hash": _sha256_file(cf),
                   "noise_file": nf.name, "noise_id": noise_id, "noise_hash": _sha256_file(nf)}
                  for cf, cmb_id, nf, noise_id in pairs]
    return rows, provenance


def _e2e_noise_null_precision(noise_mc_dir, max_sims, cfg, keep_mask, cmb_apex, cl, jobs):
    noise_files = _list_sims(noise_mc_dir)[:max_sims]
    if not noise_files:
        raise FileNotFoundError(f"no noise sims (*.fits/*.npz) found in {noise_mc_dir}")
    tasks = [(i, str(nf)) for i, nf in enumerate(noise_files)]
    rows = _map_parallel(_w_noise, tasks,
                         (cfg, keep_mask, cmb_apex, None, cl, rm.SEED), jobs)
    provenance = [{"file": nf.name, "input_hash": _sha256_file(nf)} for nf in noise_files]
    return rows, provenance


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
                           max_noise_sims: int = DEFAULT_MAX_NOISE_SIMS,
                           precision: PrecisionConfig | None = None,
                           jobs: int = 1) -> dict:
    """Route-4 long-run: the global max-scan against an E2E-NOISE-augmented null
    (real instrument-noise sims + local LambdaCDM signal). Method-matched: the null
    built from <method> noise sims is compared to the <method> observed map. With
    ``precision`` set, uses the v2 statistic set (proc-NSIDE/ell_max/mask, observed
    from the full-res map); ``jobs>1`` fans the sims over processes. Writes
    a SEPARATE artifact so the canonical GRF result is untouched. K1 stays
    measured_partial -- this carries real noise covariance but not residual
    foregrounds/systematics, so it is an upgrade of, not a replacement for, the
    blocked full E2E null."""
    if method not in _METHOD_MAP:
        raise ValueError(f"method must be one of {sorted(_METHOD_MAP)}")
    map_path = _METHOD_MAP[method]
    obs_defaults = json.loads(rm.OBS_DEFAULTS.read_text())
    cmb = obs_defaults["dipole_observations"]["cmb_planck_2018"]
    cmb_apex = np.asarray(rm.lb_to_unitvec(np.array(cmb["l_deg"]), np.array(cmb["b_deg"])), dtype=float).reshape(3)
    directions = [_DIR[rm.TAILS[k]] for k in list(rm.TAILS)]

    if precision is not None:
        keep_mask = _keep_mask(precision)
        cl = rm._fiducial_cl(precision.lmax)
        keys, observed = _observed_precision(method, precision, keep_mask, cmb_apex)
        e2e_null, provenance = _e2e_noise_null_precision(
            noise_mc_dir, max_noise_sims, precision, keep_mask, cmb_apex, cl, jobs)
        obs_map_path = FULLRES_OBS[method]
        config = {**precision.as_dict(), "method": method, "n_noise_sims": len(provenance),
                  "seed": rm.SEED, "statistics": keys, "directions": directions, "jobs": jobs,
                  "null_model": "lambdacdm_signal_plus_real_instrument_noise_v2_precision"}
    else:
        pix_vectors = np.asarray(rm.hp.pix2vec(rm.NSIDE, np.arange(rm.hp.nside2npix(rm.NSIDE)))).T
        cl = rm._fiducial_cl(rm.LMAX)
        keys, observed = _observed_only(map_path, pix_vectors, cmb_apex)
        e2e_null, provenance = _e2e_noise_null(noise_mc_dir, max_noise_sims,
                                               pix_vectors, cmb_apex, cl, rm.SEED)
        obs_map_path = map_path
        config = {"nside": rm.NSIDE, "lmax": rm.LMAX, "ell_min": rm.ELL_MIN,
                  "method": method, "n_noise_sims": len(provenance), "seed": rm.SEED,
                  "statistics": keys, "directions": directions,
                  "null_model": "lambdacdm_signal_plus_real_instrument_noise"}
    res = calibrate_max_scan(observed, e2e_null, directions)
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
        "map": {"path": obs_map_path.name, "input_hash": _sha256_file(obs_map_path)},
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


def build_e2e_full_report(cmb_mc_dir: Path, noise_mc_dir: Path, method: str = "smica",
                          max_sims: int = DEFAULT_MAX_FULL_SIMS,
                          precision: PrecisionConfig | None = None,
                          jobs: int = 1) -> dict:
    """Route-A FULL E2E long-run: the global max-scan against the PLA-available FFP10
    SMICA end-to-end ensemble -- REAL component-separated CMB MC + REAL instrument-noise
    MC (paired by parsed MC id, robust to the known missing CMB realization 00970 ->
    999 usable CMB MC). This is the strongest null and the one whose exit gate
    flips K1 measured_partial -> measured and closes BLOCKED_MISSING_PR4_E2E_ACCESS:
    it carries the real signal realisation, the real noise/systematics, and (through
    the component-separated maps) the cleaning transfer. Method-matched; writes a
    SEPARATE artifact so the canonical GRF result is untouched. With ``precision``
    set, uses the v2 statistic set (proc-NSIDE/ell_max/mask, observed from the full-res
    map); ``jobs>1`` fans the sims over processes.

    NOTE: flipping the egs_results_table K1 row to `measured` is a deliberate manual
    step after this run (re-point the row + provenance), per the guide's exit gate."""
    if method not in _METHOD_MAP:
        raise ValueError(f"method must be one of {sorted(_METHOD_MAP)}")
    map_path = _METHOD_MAP[method]
    obs_defaults = json.loads(rm.OBS_DEFAULTS.read_text())
    cmb = obs_defaults["dipole_observations"]["cmb_planck_2018"]
    cmb_apex = np.asarray(rm.lb_to_unitvec(np.array(cmb["l_deg"]), np.array(cmb["b_deg"])), dtype=float).reshape(3)
    directions = [_DIR[rm.TAILS[k]] for k in list(rm.TAILS)]

    if precision is not None:
        keep_mask = _keep_mask(precision)
        keys, observed = _observed_precision(method, precision, keep_mask, cmb_apex)
        e2e_null, provenance = _e2e_full_null_precision(
            cmb_mc_dir, noise_mc_dir, max_sims, precision, keep_mask, cmb_apex, jobs)
        obs_map_path = FULLRES_OBS[method]
        config = {**precision.as_dict(), "method": method, "n_sims": len(provenance),
                  "seed": rm.SEED, "statistics": keys, "directions": directions, "jobs": jobs,
                  "null_model": "ffp10_cmb_plus_noise_e2e_v2_precision"}
    else:
        pix_vectors = np.asarray(rm.hp.pix2vec(rm.NSIDE, np.arange(rm.hp.nside2npix(rm.NSIDE)))).T
        keys, observed = _observed_only(map_path, pix_vectors, cmb_apex)
        e2e_null, provenance = _e2e_full_null(cmb_mc_dir, noise_mc_dir, max_sims,
                                              pix_vectors, cmb_apex)
        obs_map_path = map_path
        config = {"nside": rm.NSIDE, "lmax": rm.LMAX, "ell_min": rm.ELL_MIN,
                  "method": method, "n_sims": len(provenance), "seed": rm.SEED,
                  "statistics": keys, "directions": directions,
                  "null_model": "ffp10_cmb_plus_noise_e2e"}
    res = calibrate_max_scan(observed, e2e_null, directions)
    config_hash = "sha256:" + hashlib.sha256(json.dumps(config, sort_keys=True).encode()).hexdigest()
    # availability accounting: what was actually usable vs the nominal library, and any
    # gaps in the CMB id range on disk (00970 is the registered known missing realization)
    present_ids = sorted(p["cmb_id"] for p in provenance)
    observed_gaps = (sorted(set(range(present_ids[0], present_ids[-1] + 1)) - set(present_ids))
                     if present_ids else [])
    n_noise_used = len({p["noise_id"] for p in provenance})
    return {
        "schema": "htt.k1.global_maxscan_e2e_full.v1",
        "owner": "OBSSTAT",
        "claim_tier": "diagnostic_only",
        "blocker_closes": "BLOCKED_MISSING_PR4_E2E_ACCESS",
        "blocker_note": "PLA-available FFP10 SMICA E2E null: real component-separated CMB MC + real instrument-noise MC for this method, paired by parsed MC id (robust to the known missing CMB realization 00970). This is the exit-gate null; once run on the PLA-available ensemble, flip the egs_results_table K1 row measured_partial -> measured through the generator with this provenance",
        "transfer_source": "ffp10_component_separation",
        "family_identification": False,
        "native_solver_result": False,
        "method": method,
        "map": {"path": obs_map_path.name, "input_hash": _sha256_file(obs_map_path)},
        "e2e_sims": {"cmb_dir": str(cmb_mc_dir), "noise_dir": str(noise_mc_dir),
                     "n_cmb_used": len(provenance), "n_noise_used": n_noise_used,
                     "max_requested": max_sims,
                     "nominal_cmb": FFP10_SMICA_NOMINAL_CMB, "nominal_noise": FFP10_SMICA_NOMINAL_NOISE,
                     "known_missing_cmb_ids": list(KNOWN_MISSING_FFP10_SMICA_CMB),
                     "observed_cmb_id_gaps": observed_gaps,
                     "pla_confirmation": PLA_CONFIRMATION,
                     "pairing": "cmb_mc[id] + noise_mc[id mod n_noise]  (id-parsed, gap-robust)",
                     "files": provenance},
        "statistics": keys,
        "config": config,
        "config_hash": config_hash,
        "result": {
            "local_p": {k: float(p) for k, p in zip(keys, res.local_p)},
            "global_p": float(res.global_p),
            "observed_max_score": float(res.observed_max_score),
        },
        "headline": f"K1 global look-elsewhere-corrected low-ell morphology p ({method}) under the PLA-available FFP10 SMICA CMB+noise E2E null ({len(provenance)} used CMB MC + {n_noise_used} noise MC)",
        "caveats": [
            "null = REAL component-separated CMB MC + REAL instrument-noise MC (PLA-available E2E); carries noise/systematics + the cleaning transfer",
            "CMB set is the PLA-available subset, NOT all 1000: known missing/corrupt realization 00970 (ESA/PLA " + PLA_CONFIRMATION + "); sims paired by parsed MC id so the gap does not misalign the pairing",
            "method-matched: built from this method's sims only; compare methods side by side, do not average",
            "look-elsewhere correction over the six registered statistics; max-scan frozen",
            "model-independent low-ell descriptor; no Bianchi family, geometry, anisotropy-evidence, or native-solver claim",
        ],
        "claim_boundary": "OBSSTAT global look-elsewhere diagnostic under the PLA-available E2E ensemble; this is the exit-gate null, not a family/geometry/native-solver claim",
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true",
                        help="verify the canonical GRF artifact is up to date")
    parser.add_argument("--noise-mc-dir", type=Path, default=None,
                        help="real noise-only sims dir (*.fits / *.npz). Alone -> route-4 "
                             "noise+local-LambdaCDM null; with --cmb-mc-dir -> full E2E null")
    parser.add_argument("--cmb-mc-dir", type=Path, default=None,
                        help="real component-separated CMB MC dir (*.fits / *.npz). With "
                             "--noise-mc-dir -> Route-A FULL CMB+noise E2E null (exit gate)")
    parser.add_argument("--method", choices=sorted(_METHOD_MAP), default="smica",
                        help="component-separation method matched to the sims (default: smica)")
    parser.add_argument("--max-noise-sims", type=int, default=DEFAULT_MAX_NOISE_SIMS,
                        help=f"cap on noise sims (route-4 mode; default: {DEFAULT_MAX_NOISE_SIMS})")
    parser.add_argument("--max-sims", type=int, default=DEFAULT_MAX_FULL_SIMS,
                        help=f"cap on CMB sims (full E2E mode; default: {DEFAULT_MAX_FULL_SIMS}; "
                             "raise to 1000 to use the whole PLA-available set, i.e. 999 usable CMB MC)")
    parser.add_argument("--jobs", type=int, default=1,
                        help="parallel worker processes for the E2E sim loop (default 1)")
    parser.add_argument("--precision", action="store_true",
                        help="v2 precision statistic set: proc-NSIDE + ell_max + galactic "
                             "mask (re-registered; observed taken from the full-res map)")
    parser.add_argument("--proc-nside", type=int, default=DEFAULT_PROC_NSIDE,
                        help=f"processing NSIDE for --precision (default {DEFAULT_PROC_NSIDE}; "
                             "64 is the ell<=8 ceiling, higher only helps with --lmax)")
    parser.add_argument("--lmax", type=int, default=DEFAULT_LMAX,
                        help=f"max multipole for the ell-summed stats under --precision "
                             f"(default {DEFAULT_LMAX}; Q-O alignment stays ell=2,3)")
    parser.add_argument("--no-mask", action="store_true",
                        help="under --precision, skip the galactic mask + inpainting (full-sky)")
    args = parser.parse_args(argv)

    precision = None
    if args.precision:
        precision = PrecisionConfig(proc_nside=args.proc_nside, lmax=args.lmax,
                                    masked=not args.no_mask)

    if args.cmb_mc_dir is not None:
        # Route-A FULL E2E: real CMB MC + real noise MC (needs both dirs)
        if args.noise_mc_dir is None:
            parser.error("--cmb-mc-dir requires --noise-mc-dir (full E2E null = CMB + noise)")
        payload = build_e2e_full_report(args.cmb_mc_dir, args.noise_mc_dir,
                                        args.method, args.max_sims, precision, args.jobs)
        text = json.dumps(payload, indent=2, sort_keys=True) + "\n"
        OUT_E2E_FULL_JSON.parent.mkdir(parents=True, exist_ok=True)
        OUT_E2E_FULL_JSON.write_text(text)
        print(f"wrote {OUT_E2E_FULL_JSON.relative_to(REPO_ROOT)}")
        print(f"   {args.method} FULL E2E global p = {payload['result']['global_p']:.4f} "
              f"({payload['e2e_sims']['n_cmb_used']} usable CMB MC + {payload['e2e_sims']['n_noise_used']} noise MC; "
              f"statistic_set={payload['config'].get('statistic_set', 'v1')}, jobs={args.jobs})")
        return 0

    if args.noise_mc_dir is not None:
        payload = build_e2e_noise_report(args.noise_mc_dir, args.method,
                                         args.max_noise_sims, precision, args.jobs)
        text = json.dumps(payload, indent=2, sort_keys=True) + "\n"
        OUT_E2E_JSON.parent.mkdir(parents=True, exist_ok=True)
        OUT_E2E_JSON.write_text(text)
        print(f"wrote {OUT_E2E_JSON.relative_to(REPO_ROOT)}")
        print(f"   {args.method} E2E-noise global p = {payload['result']['global_p']:.4f} "
              f"({payload['noise_sims']['n_used']} noise sims; "
              f"statistic_set={payload['config'].get('statistic_set', 'v1')}, jobs={args.jobs})")
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
