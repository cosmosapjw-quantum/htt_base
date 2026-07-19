#!/usr/bin/env python3
"""PR-150 compact-cache and future PR3 deletion gate.

The gate has two deliberately separate decisions:

``cache_reproducibility_green``
    The exact registered PR-150 input inventory was reduced directly to
    pre-mask NSIDE=64 float64 maps; all 999 CMB and 300 noise arrays reproduce
    raw-to-64 bit for bit; the independent cache copy is authenticated; and a
    full compact replay reproduces the retained 999x6 precision statistic matrix
    and result artifact.

``mechanically_deletion_eligible``
    The cache decision is green *and* a separate authenticated PR4 replacement
    inventory has been reopened and fully rehashed.

``safe_to_delete_raw``
    Always false in this validator: explicit human storage-swap authorization
    belongs to the later deletion workflow, not to a data-readiness receipt.
    This script never deletes anything.

Sampling is diagnostic only and can never authorize raw deletion.  A nonzero
tolerance is diagnostic only; the deletion-bearing map comparison is exact
``numpy.array_equal`` with byte hashes.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import platform
import sys

import numpy as np

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "scripts"))
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

import k1_global_maxscan as k1  # noqa: E402
import make_lowell_morphology_real_map as rm  # noqa: E402
from obsstat.lowell_global_calibration import calibrate_max_scan  # noqa: E402

GEN = REPO_ROOT / "docs/generated"
EXPECTED_CMB_IDS = set(range(1000)) - {970}
EXPECTED_NOISE_IDS = set(range(300))
# The registered full PR-150 run used ell_max=30. The reducer's cached ell<=8
# alm array is auxiliary; the retained NSIDE64 map is the authoritative replay
# input and supports the exact registered ell_max=30 statistic path.
PR150_CONFIG = k1.PrecisionConfig(proc_nside=64, lmax=30, masked=True)
PR4_READY_SCHEMA = "htt.planck.pr4_replacement_ready_receipt.v1"
PR4_OBSERVED_MAP_ID = "COM_CMB_IQU-sevem_2048_R4.00.fits"


def _display_path(path: Path) -> str:
    """Render relative CLI paths safely after resolving them against cwd."""
    resolved = path.resolve()
    try:
        return str(resolved.relative_to(REPO_ROOT))
    except ValueError:
        return str(resolved)


def _sha256_path(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        while block := handle.read(16 << 20):
            digest.update(block)
    return "sha256:" + digest.hexdigest()


def _canonical_hash(payload: object) -> str:
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
    return "sha256:" + hashlib.sha256(encoded).hexdigest()


def _verify_pr4_file_record(row: object, *, base: Path, role: str,
                            identity_field: str | None = None) -> tuple[dict | None, list[str]]:
    """Verify one replacement file against path, size, and full content hash."""
    errors: list[str] = []
    if not isinstance(row, dict):
        return None, [f"{role}:record_not_object"]
    path_text = row.get("path")
    size = row.get("size_bytes")
    expected_hash = row.get("sha256")
    identity = row.get(identity_field) if identity_field else None
    if not isinstance(path_text, str) or not path_text.strip():
        errors.append(f"{role}:path_missing")
    if not isinstance(size, int) or isinstance(size, bool) or size <= 0:
        errors.append(f"{role}:size_bytes_invalid")
    if (not isinstance(expected_hash, str) or
            not expected_hash.startswith("sha256:") or
            len(expected_hash.removeprefix("sha256:")) != 64 or
            any(char not in "0123456789abcdef"
                for char in expected_hash.removeprefix("sha256:"))):
        errors.append(f"{role}:sha256_invalid")
    if identity_field and (not isinstance(identity, str) or not identity.strip()):
        errors.append(f"{role}:{identity_field}_missing")
    if errors:
        return None, errors
    path = Path(path_text)
    if not path.is_absolute():
        path = base / path
    path = path.resolve()
    if not path.is_file():
        return None, [f"{role}:file_absent"]
    actual_size = path.stat().st_size
    if actual_size != size:
        errors.append(f"{role}:size_mismatch")
    actual_hash = _sha256_path(path)
    if actual_hash != expected_hash:
        errors.append(f"{role}:hash_mismatch")
    normalized = {
        "role": role,
        "path": str(path),
        "size_bytes": actual_size,
        "sha256": actual_hash,
    }
    if identity_field:
        normalized[identity_field] = identity
    return normalized, errors


def _array_hash(array: np.ndarray) -> str:
    return "sha256:" + hashlib.sha256(np.ascontiguousarray(array)).hexdigest()


def _apex() -> np.ndarray:
    obs_defaults = json.loads(rm.OBS_DEFAULTS.read_text())
    cmb = obs_defaults["dipole_observations"]["cmb_planck_2018"]
    return np.asarray(rm.lb_to_unitvec(np.array(cmb["l_deg"]),
                                       np.array(cmb["b_deg"])), float).reshape(3)


def _selected_indices(n: int, sample: int, do_all: bool) -> list[int]:
    if do_all:
        return list(range(n))
    step = max(1, n // max(1, sample))
    return list(range(n))[::step][:sample]


def _inventory(ids: np.ndarray, expected: set[int]) -> dict:
    values = [int(value) for value in ids]
    present = set(values)
    return {
        "count": len(values), "unique_count": len(present),
        "missing": sorted(expected - present), "extra": sorted(present - expected),
        "duplicate_count": len(values) - len(present),
        "exact": len(values) == len(expected) and present == expected,
    }


def _replay_precision(cache, ids: dict[str, np.ndarray]) -> dict:
    cfg = PR150_CONFIG
    mask = np.asarray(cache["common_mask"], dtype=np.float64)
    keep = k1.downgrade_mask(mask, cfg.proc_nside)
    apex = _apex()
    keys = list(rm.TAILS)
    directions = [k1._DIR[rm.TAILS[key]] for key in keys]
    observed_stats = k1.precision_map_statistics(
        np.asarray(cache["observed_map"], dtype=np.float64), apex, cfg, keep)
    observed = np.asarray([observed_stats[key] for key in keys], dtype=np.float64)

    cmb_index = {int(mc_id): i for i, mc_id in enumerate(ids["cmb"])}
    noise_index = {int(mc_id): i for i, mc_id in enumerate(ids["noise"])}
    rows = []
    pair_rows = []
    for cmb_id in sorted(cmb_index):
        noise_id = cmb_id % len(EXPECTED_NOISE_IDS)
        if noise_id not in noise_index:
            raise ValueError(f"noise id {noise_id:05d} absent from compact cache")
        combined = (np.asarray(cache["cmb_maps"][cmb_index[cmb_id]], dtype=np.float64)
                    + np.asarray(cache["noise_maps"][noise_index[noise_id]],
                                 dtype=np.float64))
        stats = k1.precision_map_statistics(combined, apex, cfg, keep)
        row = [float(stats[key]) for key in keys]
        rows.append(row)
        pair_rows.append({"cmb_id": cmb_id, "noise_id": noise_id,
                          "statistics": {key: value for key, value in zip(keys, row)}})
    matrix = np.asarray(rows, dtype=np.float64)
    calibrated = calibrate_max_scan(observed, matrix, directions)
    score_rows = [
        {"cmb_id": pair["cmb_id"], "noise_id": pair["noise_id"],
         "max_score": float(score),
         "exceeds_observed": bool(score >= calibrated.observed_max_score)}
        for pair, score in zip(pair_rows, calibrated.simulation_max_scores)
    ]
    return {
        "keys": keys, "directions": directions,
        "observed": observed, "matrix": matrix,
        "pair_rows": pair_rows, "score_rows": score_rows,
        "global_p": float(calibrated.global_p),
        "local_p": {key: float(value)
                    for key, value in zip(keys, calibrated.local_p)},
        "observed_max_score": float(calibrated.observed_max_score),
        "keep_mask_hash": _array_hash(keep),
    }


def _artifact_match(path: Path | None, replay: dict | None) -> dict:
    if path is None or replay is None:
        return {"provided": False, "exact": False,
                "reason": "full compact replay result artifact not supplied"}
    payload = json.loads(path.read_text(encoding="utf-8"))
    result = payload.get("result", {})
    artifact_rows = result.get("simulation_statistics")
    artifact_observed = result.get("observed_statistics")
    if not isinstance(artifact_rows, list) or not isinstance(artifact_observed, dict):
        return {"provided": True, "exact": False,
                "reason": "artifact lacks the retained 999x6/observed precision receipt"}
    by_id = {int(row["cmb_id"]): row for row in artifact_rows}
    expected_ids = [row["cmb_id"] for row in replay["pair_rows"]]
    rows_exact = set(by_id) == set(expected_ids)
    if rows_exact:
        for expected in replay["pair_rows"]:
            actual = by_id[expected["cmb_id"]]
            if (int(actual["noise_id"]) != expected["noise_id"] or
                    any(float(actual["statistics"][key]) != expected["statistics"][key]
                        for key in replay["keys"])):
                rows_exact = False
                break
    observed_exact = all(float(artifact_observed[key]) == value
                         for key, value in zip(replay["keys"], replay["observed"]))
    scores = result.get("simulation_max_scores", [])
    scores_exact = scores == replay["score_rows"]
    ranks_exact = (
        float(result.get("global_p", np.nan)) == replay["global_p"] and
        float(result.get("observed_max_score", np.nan)) == replay["observed_max_score"] and
        all(float(result.get("local_p", {}).get(key, np.nan)) == value
            for key, value in replay["local_p"].items())
    )
    exact = bool(rows_exact and observed_exact and scores_exact and ranks_exact)
    return {
        "provided": True, "path": str(path), "input_hash": k1._sha256_file(path),
        "simulation_statistics_exact": rows_exact,
        "observed_statistics_exact": observed_exact,
        "simulation_scores_exact": scores_exact,
        "rank_products_exact": ranks_exact, "exact": exact,
    }


def _pr4_ready(path: Path | None) -> dict:
    if path is None:
        return {"provided": False, "ready": False,
                "reason": "PR4 access is externally blocked; no replacement-ready receipt",
                "required_schema": PR4_READY_SCHEMA}
    path = path.resolve()
    payload = json.loads(path.read_text(encoding="utf-8"))
    errors: list[str] = []
    required_scalars = {
        "schema": PR4_READY_SCHEMA,
        "status": "PR4_REPLACEMENT_READY",
        "access_status": "available",
        "analysis_status": "ready",
        "replacement_scope": "PR4_NPIPE_SEVEM_ANALYSIS_INPUTS",
    }
    for field, expected in required_scalars.items():
        if payload.get(field) != expected:
            errors.append(f"{field}_invalid")
    if payload.get("input_checksums_verified") is not True:
        errors.append("input_checksums_verified_not_asserted")
    if payload.get("download_plan_size_probed") is not True:
        errors.append("download_plan_size_not_probed")
    if not isinstance(payload.get("source_authority"), str) or not payload[
            "source_authority"].strip():
        errors.append("source_authority_missing")
    if not isinstance(payload.get("generating_command"), str) or not payload[
            "generating_command"].strip():
        errors.append("generating_command_missing")

    observed, observed_errors = _verify_pr4_file_record(
        payload.get("observed_map"), base=path.parent, role="observed_map",
        identity_field="map_id")
    errors.extend(observed_errors)
    if observed is not None and observed.get("map_id") != PR4_OBSERVED_MAP_ID:
        errors.append("observed_map_id_invalid")

    inventory = payload.get("simulation_inventory")
    simulation_records: list[dict] = []
    simulation_ids: list[str] = []
    if not isinstance(inventory, dict):
        errors.append("simulation_inventory_not_object")
        inventory = {}
    files = inventory.get("files")
    if not isinstance(files, list) or not files:
        errors.append("simulation_files_missing")
        files = []
    for index, row in enumerate(files):
        record, record_errors = _verify_pr4_file_record(
            row, base=path.parent, role=f"simulation[{index}]",
            identity_field="simulation_id")
        errors.extend(record_errors)
        if record is not None:
            simulation_records.append(record)
            simulation_ids.append(record["simulation_id"])
    if len(set(simulation_ids)) != len(simulation_ids):
        errors.append("simulation_ids_not_unique")
    nominal = inventory.get("nominal_count")
    usable = inventory.get("usable_count")
    excluded = inventory.get("excluded_ids")
    if (not isinstance(nominal, int) or isinstance(nominal, bool) or nominal <= 0):
        errors.append("nominal_count_invalid")
    if usable != len(simulation_records) or not simulation_records:
        errors.append("usable_count_mismatch")
    if (not isinstance(excluded, list) or
            any(not isinstance(value, str) or not value for value in excluded) or
            len(set(excluded)) != len(excluded)):
        errors.append("excluded_ids_invalid")
        excluded = []
    if isinstance(nominal, int) and nominal != len(simulation_records) + len(excluded):
        errors.append("nominal_inventory_arithmetic_mismatch")
    if set(excluded) & set(simulation_ids):
        errors.append("excluded_ids_present_in_files")

    noise_fix, noise_errors = _verify_pr4_file_record(
        payload.get("noise_fix"), base=path.parent, role="noise_fix")
    errors.extend(noise_errors)
    verified_records = ([observed] if observed is not None else []) + \
        simulation_records + ([noise_fix] if noise_fix is not None else [])
    total_size = sum(record["size_bytes"] for record in verified_records)
    if payload.get("total_size_bytes") != total_size or not verified_records:
        errors.append("total_size_bytes_mismatch")
    inventory_payload = {
        "observed_map": observed,
        "simulations": sorted(simulation_records,
                              key=lambda row: row["simulation_id"]),
        "excluded_ids": sorted(excluded),
        "noise_fix": noise_fix,
    }
    inventory_hash = _canonical_hash(inventory_payload)
    if payload.get("verified_inventory_sha256") != inventory_hash:
        errors.append("verified_inventory_sha256_mismatch")
    ready = not errors
    return {
        "provided": True,
        "ready": ready,
        "path": str(path),
        "input_hash": _sha256_path(path),
        "required_schema": PR4_READY_SCHEMA,
        "required_status": "PR4_REPLACEMENT_READY",
        "verified_file_count": len(verified_records),
        "verified_total_size_bytes": total_size,
        "verified_inventory_sha256": inventory_hash,
        "errors": errors,
    }


def _deletion_decision(*, cache_green: bool, pr4_ready: bool) -> dict:
    """Separate mechanical replacement readiness from human authorization."""
    mechanically_eligible = bool(cache_green and pr4_ready)
    return {
        "mechanically_deletion_eligible": mechanically_eligible,
        "explicit_storage_swap_authorization_provided": False,
        "safe_to_delete_raw": False,
    }


def run(manifest: Path, dirs: dict[str, Path | None], sample: int, do_all: bool,
        tol: float = 0.0, *, result_artifact: Path | None = None,
        pr4_ready_receipt: Path | None = None) -> dict:
    manifest = manifest.resolve()
    man = json.loads(manifest.read_text(encoding="utf-8"))
    cache_path = Path(man["tier2_cache"]["path"])
    if not cache_path.is_file():
        raise FileNotFoundError(f"compact cache not found: {cache_path}")
    cache_hash_ok = k1._sha256_file(cache_path) == man["tier2_cache"]["cache_hash"]
    if not cache_hash_ok:
        raise ValueError("combined compact-cache hash mismatch")
    cache = np.load(cache_path)
    reduce_nside = int(man["config"]["reduce_nside"])
    ids = {label: np.asarray(cache[f"{label}_ids"], dtype=int)
           for label in ("cmb", "noise") if f"{label}_ids" in cache}
    require_pr150 = bool(man["config"].get("require_pr150_inventory"))
    inventory = {
        "cmb": _inventory(ids.get("cmb", np.asarray([], dtype=int)), EXPECTED_CMB_IDS),
        "noise": _inventory(ids.get("noise", np.asarray([], dtype=int)), EXPECTED_NOISE_IDS),
    }
    inventory_exact = inventory["cmb"]["exact"] and inventory["noise"]["exact"]

    checks = []
    raw_hash_ok = True
    map_exact = True
    full_map_count = 0
    expected_map_count = sum(len(values) for values in ids.values())
    for label in ("cmb", "noise"):
        if label not in ids:
            continue
        directory = dirs.get(label)
        if directory is None:
            map_exact = raw_hash_ok = False
            checks.append({"label": label, "status": "RAW_DIRECTORY_ABSENT"})
            continue
        provenance = {int(row["mc_id"]): row
                      for row in man["parts"][label]["input_hashes"]}
        order = _selected_indices(len(ids[label]), sample, do_all)
        for i in order:
            mc_id = int(ids[label][i])
            row = provenance.get(mc_id)
            if row is None:
                raw_hash_ok = map_exact = False
                checks.append({"label": label, "mc_id": mc_id,
                               "status": "PROVENANCE_ABSENT"})
                continue
            raw = directory / row["file"]
            if not raw.is_file():
                raw_hash_ok = map_exact = False
                checks.append({"label": label, "mc_id": mc_id,
                               "status": "RAW_ABSENT"})
                continue
            hash_ok = k1._sha256_file(raw) == row["input_hash"]
            direct = k1._load_sim_map(raw, reduce_nside)
            cached = np.asarray(cache[f"{label}_maps"][i], dtype=np.float64)
            exact = bool(np.array_equal(direct, cached))
            raw_hash_ok &= hash_ok
            map_exact &= exact
            full_map_count += 1
            checks.append({
                "label": label, "mc_id": mc_id,
                "raw_hash_ok": hash_ok, "map_array_equal": exact,
                "raw_array_hash": _array_hash(direct),
                "cache_array_hash": _array_hash(cached),
                "max_abs_map_diff": float(np.max(np.abs(direct - cached))),
                "status": "OK" if hash_ok and exact else "MISMATCH",
            })

    full_map_replay = bool(do_all and full_map_count == expected_map_count)
    replay_file_exact = True
    for label, section in man.get("replay_directories", {}).items():
        expected_rows = {int(row["mc_id"]): row for row in section["files"]}
        for i, mc_id in enumerate(ids[label]):
            row = expected_rows.get(int(mc_id))
            if row is None or not Path(row["path"]).is_file():
                replay_file_exact = False
                continue
            replay_map = rm._load_real_map(Path(row["path"]))
            replay_file_exact &= bool(
                k1._sha256_file(Path(row["path"])) == row["file_hash"] and
                np.array_equal(replay_map, cache[f"{label}_maps"][i]))

    backup = man.get("independent_backup")
    backup_exact = bool(
        backup and Path(backup["path"]).is_file() and
        k1._sha256_file(Path(backup["path"])) == man["tier2_cache"]["cache_hash"] and
        int(Path(backup["path"]).stat().st_dev) != int(cache_path.stat().st_dev)
    )

    observed_exact = mask_exact = False
    if man.get("observed_and_mask") and "observed_map" in cache and "common_mask" in cache:
        obs = man["observed_and_mask"]
        observed_direct = k1._load_sim_map(Path(obs["observed_source"]), reduce_nside)
        mask_hi = np.asarray(rm.hp.read_map(Path(obs["mask_source"])), dtype=np.float64)
        mask_direct = (rm.hp.ud_grade(mask_hi, nside_out=reduce_nside)
                       if rm.hp.npix2nside(mask_hi.size) != reduce_nside
                       else mask_hi)
        observed_exact = bool(np.array_equal(observed_direct, cache["observed_map"]))
        mask_exact = bool(np.array_equal(mask_direct, cache["common_mask"]))

    precision_replay = None
    precision_receipt = None
    if require_pr150 and inventory_exact and replay_file_exact and observed_exact and mask_exact:
        precision_replay = _replay_precision(cache, ids)
        precision_receipt = {
            "config": PR150_CONFIG.as_dict(),
            "statistics": precision_replay["keys"],
            "directions": precision_replay["directions"],
            "observed_statistics": {key: float(value) for key, value in
                                    zip(precision_replay["keys"],
                                        precision_replay["observed"])},
            "simulation_statistics": precision_replay["pair_rows"],
            "simulation_statistics_array_hash": _array_hash(precision_replay["matrix"]),
            "simulation_max_scores": precision_replay["score_rows"],
            "global_p": precision_replay["global_p"],
            "local_p": precision_replay["local_p"],
            "observed_max_score": precision_replay["observed_max_score"],
            "keep_mask_hash": precision_replay["keep_mask_hash"],
        }
    artifact = _artifact_match(result_artifact, precision_replay)
    pr4 = _pr4_ready(pr4_ready_receipt)

    mechanical_green = bool(
        cache_hash_ok and full_map_replay and raw_hash_ok and map_exact and
        replay_file_exact and (inventory_exact if require_pr150 else True)
    )
    cache_green = bool(
        mechanical_green and require_pr150 and observed_exact and mask_exact and
        backup_exact and artifact["exact"] and tol == 0.0
    )
    deletion = _deletion_decision(
        cache_green=cache_green, pr4_ready=bool(pr4["ready"]))
    mechanically_eligible = deletion["mechanically_deletion_eligible"]
    return {
        "schema": "htt.k1.e2e_cache_gate.v2",
        "owner": "OBSSTAT", "claim_tier": "conditional",
        "manifest": str(manifest), "manifest_hash": k1._sha256_file(manifest),
        "cache_path": str(cache_path), "cache_hash": man["tier2_cache"]["cache_hash"],
        "config": PR150_CONFIG.as_dict(), "reduce_nside": reduce_nside,
        "mode": "all" if do_all else f"sample={sample}",
        "user_tolerance": tol,
        "deletion_authority_requires_exact_zero_tolerance": True,
        "inventory": inventory, "require_pr150_inventory": require_pr150,
        "n_checked": len([row for row in checks if "mc_id" in row]),
        "expected_map_count": expected_map_count,
        "full_map_replay": full_map_replay, "raw_hash_ok": raw_hash_ok,
        "direct_raw_to_cache_array_equal": map_exact,
        "replay_files_exact": replay_file_exact,
        "observed_map_exact": observed_exact, "common_mask_exact": mask_exact,
        "independent_backup_exact_and_distinct_device": backup_exact,
        "result_artifact_replay": artifact,
        "precision_receipt": precision_receipt,
        "cache_reproducibility_green": cache_green,
        "pr4_replacement_ready": pr4,
        **deletion,
        "raw_retention_decision": (
            "ELIGIBLE_PENDING_EXPLICIT_AUTHORIZATION: compact and authenticated PR4 replacement inventories pass, but this validator cannot authorize or perform deletion"
            if mechanically_eligible else
            "RETAIN_RAW_PR3: compact reproduction may be green, but mechanical eligibility still requires an authenticated PR4 replacement inventory"
        ),
        "checks": checks,
        "runtime": {"python": platform.python_version(),
                    "numpy": np.__version__, "healpy": rm.hp.__version__},
        "family_identification": False, "native_solver_result": False,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--cmb-mc-dir", type=Path, required=True)
    parser.add_argument("--noise-mc-dir", type=Path, required=True)
    parser.add_argument("--sample", type=int, default=24)
    parser.add_argument("--all", action="store_true")
    parser.add_argument("--tol", type=float, default=0.0,
                        help="diagnostic tolerance label only; nonzero can never authorize deletion")
    parser.add_argument("--result-artifact", type=Path, default=None)
    parser.add_argument("--pr4-ready-receipt", type=Path, default=None)
    parser.add_argument("--out", type=Path, default=None)
    args = parser.parse_args(argv)
    payload = run(
        args.manifest, {"cmb": args.cmb_mc_dir, "noise": args.noise_mc_dir},
        args.sample, args.all, args.tol,
        result_artifact=args.result_artifact,
        pr4_ready_receipt=args.pr4_ready_receipt,
    )
    out = args.out or (GEN / (args.manifest.stem.replace(
        "k1_e2e_reduced_manifest", "k1_e2e_cache_gate") + ".json"))
    out.parent.mkdir(parents=True, exist_ok=True)
    temp = out.with_suffix(out.suffix + ".tmp")
    temp.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")
    temp.replace(out)
    print(f"wrote {_display_path(out)}")
    print(f"   checked={payload['n_checked']}/{payload['expected_map_count']} "
          f"cache_green={payload['cache_reproducibility_green']} "
          f"pr4_ready={payload['pr4_replacement_ready']['ready']} "
          f"safe_to_delete_raw={payload['safe_to_delete_raw']}")
    # A valid compact pack is success even while raw retention remains required.
    return 0 if payload["cache_reproducibility_green"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
