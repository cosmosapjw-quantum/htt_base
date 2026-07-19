#!/usr/bin/env python3
"""PR-152 heavy producer: ACT DR6 lensing release-simulation cross-fit card.

Loads the REAL ACT DR6 reconstructed convergence (data + 400 Monte-Carlo sims,
downgraded to the L=2..10 low-multipole band) and computes the observation-
inclusive leave-one-out mean-field rank, a legacy simulation-only sensitivity,
the exact algebraic finite-rank ceiling, the
stochastic-vs-fixed-template injection-law distinction, and the authenticated
inventory + upstream raw-QE availability decision, writing
docs/generated/act_raw_qe_card.json.

Run ONCE (reads ~60 GB of sim convergence alm); PR-152's runner reads this card
(the ACT pattern). Public raw-QE inputs/software are recorded as a separate,
large, not-yet-executed reconstruction. Deterministic; --check.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
from pathlib import Path

import numpy as np

REPO = Path(__file__).resolve().parents[1]
for root in (REPO, REPO / "htt", REPO / "htt" / "src"):
    if str(root) not in sys.path:
        sys.path.insert(0, str(root))

from obsstat.act_raw_qe_gate import (               # noqa: E402
    act_dr6_lensing_inventory,
    algebraic_finite_rank_ceiling,
    injection_law_distinction,
    leave_one_sim_crossfit_mean_field,
    observation_inclusive_crossfit_mean_field,
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
PUBLIC_RAW_QE_SOURCES = {
    "act_dr6_maps": "https://act.princeton.edu/act-dr6-data-products",
    "so_lenspipe": "https://github.com/simonsobs/so-lenspipe",
    "falafel": "https://github.com/simonsobs/falafel",
    "tempura": "https://github.com/simonsobs/tempura",
    "pixell": "https://github.com/simonsobs/pixell",
}
CARD_SCHEMA = "htt.act_raw_qe_card.v2"
INPUT_MANIFEST_SCHEMA = "htt.act.release_input_manifest.v2"
CACHE_SCHEMA = "htt.act.lowl_cache.v2"


def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        while block := fh.read(16 << 20):
            h.update(block)
    return "sha256:" + h.hexdigest()


def _canonical_sha256(payload: dict) -> str:
    raw = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
    return "sha256:" + hashlib.sha256(raw).hexdigest()


def _display_path(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(REPO.resolve()))
    except ValueError:
        return str(path.resolve())


def _file_record(path: Path) -> dict:
    if not path.is_file():
        raise FileNotFoundError(path)
    return {
        "path": _display_path(path),
        "size_bytes": path.stat().st_size,
        "sha256": _sha256(path),
    }


def build_input_manifest(sims: list[Path]) -> dict:
    """Full-content, ordered ACT input identity used to key the low-L cache."""
    if len(sims) != MAX_SIMS:
        raise ValueError(f"expected exactly {MAX_SIMS} simulations, got {len(sims)}")
    simulation_records = []
    for index, path in enumerate(sims, start=1):
        simulation_records.append(_file_record(path))
        if index % 25 == 0 or index == len(sims):
            print(f"authenticated ACT simulation inputs {index}/{len(sims)}",
                  flush=True)
    payload = {
        "schema": INPUT_MANIFEST_SCHEMA,
        "data_alm": _file_record(DATA_ALM),
        "ordered_simulation_alms": simulation_records,
        "config": {
            "ell_min": ELL_MIN,
            "ell_max": ELL_MAX,
            "mode_weights": "m0=1,m_positive=2",
            "expected_simulation_count": MAX_SIMS,
            "seed": SEED,
        },
        "producer": _file_record(Path(__file__).resolve()),
    }
    payload["manifest_sha256"] = _canonical_sha256(payload)
    return payload


def cache_path_for_manifest(input_manifest: dict) -> Path:
    digest = input_manifest["manifest_sha256"].removeprefix("sha256:")
    return REPO / "workdir" / f"act_lowl_cache_{digest}.npz"


def cache_is_bound(cache: Path, *, manifest_sha256: str,
                   expected_simulations: int) -> bool:
    """Return true only for a structurally complete cache with the exact key."""
    if not cache.is_file():
        return False
    try:
        with np.load(cache, allow_pickle=False) as z:
            required = {"schema", "input_manifest_sha256", "data_low",
                        "sim_low", "wm"}
            if not required.issubset(z.files):
                return False
            if str(z["schema"].item()) != CACHE_SCHEMA:
                return False
            if str(z["input_manifest_sha256"].item()) != manifest_sha256:
                return False
            data_low = z["data_low"]
            sim_low = z["sim_low"]
            wm = z["wm"]
            return bool(
                sim_low.ndim == 2
                and sim_low.shape[0] == expected_simulations
                and data_low.shape == sim_low.shape[1:]
                and wm.shape == data_low.shape
                and np.all(np.isfinite(data_low))
                and np.all(np.isfinite(sim_low))
                and np.all(np.isfinite(wm))
            )
    except (OSError, ValueError, KeyError):
        return False


def _write_cache(cache: Path, *, manifest_sha256: str,
                 data_low: np.ndarray, sim_low: np.ndarray,
                 wm: np.ndarray) -> None:
    cache.parent.mkdir(parents=True, exist_ok=True)
    tmp = cache.with_suffix(".tmp.npz")
    np.savez(
        tmp,
        schema=np.asarray(CACHE_SCHEMA),
        input_manifest_sha256=np.asarray(manifest_sha256),
        data_low=data_low,
        sim_low=sim_low,
        wm=wm,
    )
    tmp.replace(cache)


def _generation_environment() -> dict:
    import healpy as hp

    head = subprocess.run(
        ["git", "rev-parse", "HEAD"], cwd=REPO, capture_output=True,
        text=True, check=True).stdout.strip()
    dirty = bool(subprocess.run(
        ["git", "status", "--porcelain", "--untracked-files=no"],
        cwd=REPO, capture_output=True, text=True, check=True).stdout.strip())
    return {
        "python": sys.version.split()[0],
        "numpy": np.__version__,
        "healpy": hp.__version__,
        "git_commit": head,
        "worktree_state": "dirty" if dirty else "clean",
    }


def _stable_generation_environment(input_manifest_sha256: str) -> dict:
    """Preserve the recorded generation state across later deterministic checks."""
    if OUT.is_file():
        try:
            old = json.loads(OUT.read_text(encoding="utf-8"))
            provenance = old.get("input_provenance") or {}
            if provenance.get("input_manifest_sha256") == input_manifest_sha256:
                environment = provenance.get("generation_environment")
                if isinstance(environment, dict):
                    return environment
        except (OSError, ValueError, TypeError):
            pass
    return _generation_environment()


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


def measure() -> dict:
    import healpy as hp

    sims = sorted(SIMS_DIR.glob("kappa_alm_sim_*_baseline_*.fits"))
    required_products = [DATA_ALM, N0_CURVE, KAPPA_FILTER,
                         LIKE / "like_corrs" /
                         "N1der_KK_lmin600_lmax3000_full.txt",
                         LIKE / "clkk_bandpowers_act.txt"]
    if (not all(path.is_file() for path in required_products)
            or len(sims) != MAX_SIMS):
        return {"schema": CARD_SCHEMA,
                "status": "BLOCKED_MISSING_ACT_LENSING_RELEASE"}

    # Hash every byte of the ordered data+400-simulation inputs before cache
    # selection. A same-count replacement, a non-head mutation, a band change,
    # or a producer change therefore chooses a different cache. Old caches are
    # retained for audit; they are never silently repurposed.
    input_manifest = build_input_manifest(sims)
    cache = cache_path_for_manifest(input_manifest)
    cache_ok = cache_is_bound(
        cache,
        manifest_sha256=input_manifest["manifest_sha256"],
        expected_simulations=MAX_SIMS,
    )
    if cache_ok:
        with np.load(cache, allow_pickle=False) as z:
            data_low = np.array(z["data_low"], copy=True)
            sim_low = np.array(z["sim_low"], copy=True)
            wm = np.array(z["wm"], copy=True)
    else:
        data = _load_alm(DATA_ALM)
        lmax = int(hp.Alm.getlmax(len(data)))
        if lmax < ELL_MAX:
            raise ValueError(f"data alm lmax={lmax} is below {ELL_MAX}")
        idx, ms = _lowl(lmax)
        wm = np.where(ms == 0, 1.0, 2.0)
        data_low = data[idx]
        sim_low = np.empty((len(sims), idx.size), dtype=complex)
        for k, s in enumerate(sims):
            sim_alm = _load_alm(s)
            if int(hp.Alm.getlmax(len(sim_alm))) != lmax:
                raise ValueError(f"simulation alm lmax mismatch: {s}")
            sim_low[k] = sim_alm[idx]
            if (k + 1) % 25 == 0 or k + 1 == len(sims):
                print(f"loaded ACT low-L modes {k + 1}/{len(sims)}",
                      flush=True)
        _write_cache(
            cache,
            manifest_sha256=input_manifest["manifest_sha256"],
            data_low=data_low,
            sim_low=sim_low,
            wm=wm,
        )
        if not cache_is_bound(
                cache,
                manifest_sha256=input_manifest["manifest_sha256"],
                expected_simulations=MAX_SIMS):
            raise RuntimeError("new ACT low-L cache failed binding validation")

    crossfit = observation_inclusive_crossfit_mean_field(sim_low, data_low, wm)
    legacy_sensitivity = leave_one_sim_crossfit_mean_field(sim_low, data_low, wm)
    rank = algebraic_finite_rank_ceiling(
        n_sims=len(sims), ell_min=ELL_MIN, ell_max=ELL_MAX)
    injection = injection_law_distinction(
        crossfit["simulation_band_powers"], injection_amplitude=0.10,
        seed=SEED)

    present = {
        "kappa_alm_data": _sha256(DATA_ALM),
        "n0_curve": _sha256(N0_CURVE),
        "kappa_filter_response": _sha256(KAPPA_FILTER),
        "n1_derivative_kk": _sha256(LIKE / "like_corrs"
                                    / "N1der_KK_lmin600_lmax3000_full.txt"),
        "clkk_bandpowers": _sha256(LIKE / "clkk_bandpowers_act.txt"),
        "n_reconstructed_sims": len(sims),
        "ordered_simulation_manifest_sha256":
            input_manifest["manifest_sha256"],
    }
    inventory = act_dr6_lensing_inventory(
        present=present, raw_qe_inputs_on_disk=False,
        validated_ell_range=VALIDATED_ELL, reference_url=REF_URL,
        public_raw_qe_sources=PUBLIC_RAW_QE_SOURCES)
    decision = upstream_availability_decision(inventory)

    crossfit_card = dict(crossfit)
    crossfit_card.update({
        "analysis_ell_range": [ELL_MIN, ELL_MAX],
        "release_validated_ell_range": list(VALIDATED_ELL),
        "inside_release_validated_range": False,
        "validation_boundary":
            "exploratory_outside_release_spectrum_validation_range",
    })
    legacy_card = {k: v for k, v in legacy_sensitivity.items()
                   if k != "crossfit_sim_band_powers"}
    return {
        "schema": CARD_SCHEMA,
        "status": "RELEASE_SIMULATION_CONDITIONAL_RESULT",
        "config": {"ell_min": ELL_MIN, "ell_max": ELL_MAX,
                   "n_sims": len(sims), "seed": SEED},
        "input_provenance": {
            "input_manifest": input_manifest,
            "input_manifest_sha256": input_manifest["manifest_sha256"],
            "cache_path": _display_path(cache),
            "cache_sha256": _sha256(cache),
            "cache_schema": CACHE_SCHEMA,
            "cache_binding_verified": True,
            "generating_command": "venv/bin/python scripts/act_raw_qe_card.py",
            "generation_environment": _stable_generation_environment(
                input_manifest["manifest_sha256"]),
        },
        "inventory": inventory,
        "availability_decision": decision,
        "crossfit_mean_field": crossfit_card,
        "legacy_simulation_only_sensitivity": legacy_card,
        "rank_ceiling": rank,
        "injection_law": injection,
    }


def main(argv=None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args(argv)
    payload = measure()
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
          f"crossfit_p={cf.get('observation_inclusive_crossfit_pooled_rank_p')} "
          f"decision={payload.get('availability_decision', {}).get('decision')}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
