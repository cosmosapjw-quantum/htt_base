#!/usr/bin/env python3
"""PR-177 heavy producer for the ACT DR6 strict-in-band feature card.

The extraction phase reads the authenticated baseline data and 400 release
reconstructions exactly one at a time.  It never rehashes those 64.15 GB of
raw payloads: PR-152's byte-authenticated ordered records are the authority.
The aggregate/check phases use only content-addressed per-unit feature caches.

Run the real extraction at low priority::

    ionice -c 3 nice -n 15 env OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 \
      MKL_NUM_THREADS=1 MPLCONFIGDIR=/tmp/mpl-pr177 \
      venv/bin/python -B scripts/act_inband_modulation_card.py --phase all
"""
from __future__ import annotations

import argparse
import fcntl
import hashlib
import json
import os
import platform
import subprocess
import sys
import time
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Mapping

import numpy as np
import yaml


REPO = Path(__file__).resolve().parents[1]
for root in (REPO, REPO / "htt"):
    if str(root) not in sys.path:
        sys.path.insert(0, str(root))

from obsstat.act_inband_modulation import (  # noqa: E402
    ActInbandModulationError,
    build_mask_design,
    canonical_sha256,
    extract_alm_features,
    raw_records_only_root,
    semantic_digest,
    strict_integer_support,
)


SPEC_PATH = REPO / "docs/research_program/long_horizon_rescue/pr177_spec.yaml"
MODULE_PATH = REPO / "htt/obsstat/act_inband_modulation.py"
SCRIPT_PATH = Path(__file__).resolve()
OUT = REPO / "docs/generated/pr177_act_inband_feature_card.json"
DEEP_REPLAY_OUT = REPO / "docs/generated/pr177_deep_replay_receipt.json"
CACHE_BASE = REPO / "workdir/pr177_act_dr6_inband"
CARD_SCHEMA = "htt.pr177.act_inband_feature_card.v1"
CACHE_SCHEMA = "htt.pr177.act_inband_unit_feature.v1"
EXTRACTION_SCHEMA = "htt.pr177.extraction_resource_receipt.v2"
DEEP_REPLAY_SCHEMA = "htt.pr177.deep_replay_receipt.v1"


def _sha(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        while block := handle.read(1 << 20):
            digest.update(block)
    return digest.hexdigest()


def _json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ActInbandModulationError(f"{path} must contain a JSON object")
    return value


def _spec() -> dict[str, Any]:
    value = yaml.safe_load(SPEC_PATH.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ActInbandModulationError("PR-177 spec must be a mapping")
    return value


def _normalize_hash(value: object) -> str:
    text = str(value)
    if text.startswith("sha256:"):
        text = text[7:]
    if len(text) != 64 or any(char not in "0123456789abcdef" for char in text):
        raise ActInbandModulationError(f"invalid SHA-256 value {value!r}")
    return text


def _canonical_without_self_hash(payload: Mapping[str, object], field: str) -> str:
    material = dict(payload)
    material.pop(field, None)
    return canonical_sha256(material)


def _find_acquisition_record(manifest: Mapping[str, object], path: Path) -> dict[str, Any]:
    rows = manifest.get("local_files")
    if not isinstance(rows, list):
        raise ActInbandModulationError("ACT acquisition manifest has no local_files list")
    resolved = path.resolve()
    matches = [
        row
        for row in rows
        if isinstance(row, dict) and Path(str(row.get("path"))).resolve() == resolved
    ]
    if len(matches) != 1:
        raise ActInbandModulationError(f"expected one acquisition record for {path}")
    return dict(matches[0])


def _verify_record(record: Mapping[str, object], expected: Mapping[str, object], label: str) -> None:
    if int(record.get("size_bytes", -1)) != int(expected["size_bytes"]):
        raise ActInbandModulationError(f"{label} authority size mismatch")
    if _normalize_hash(record.get("sha256")) != _normalize_hash(expected["sha256"]):
        raise ActInbandModulationError(f"{label} authority hash mismatch")


def authenticate_sources(spec: Mapping[str, Any]) -> dict[str, Any]:
    """Authenticate small authorities and stat, but never hash, raw payloads."""

    authorities = spec["source_authorities"]
    manifest_path = REPO / authorities["pr152_artifact_manifest"]["path"]
    card_path = REPO / authorities["pr152_release_card"]["path"]
    acquisition_path = REPO / authorities["acquisition_manifest"]["path"]
    readme_path = REPO / authorities["release_readme"]["path"]
    expected_small = {
        manifest_path: authorities["pr152_artifact_manifest"]["sha256"],
        card_path: authorities["pr152_release_card"]["sha256"],
        acquisition_path: authorities["acquisition_manifest"]["sha256"],
        readme_path: authorities["release_readme"]["sha256"],
    }
    actual_small: dict[str, str] = {}
    for path, expected in expected_small.items():
        actual = _sha(path)
        if actual != _normalize_hash(expected):
            raise ActInbandModulationError(f"small authority hash mismatch: {path}")
        actual_small[str(path.relative_to(REPO))] = actual

    pr152_manifest = _json(manifest_path)
    pr152_card = _json(card_path)
    manifest_pins = {
        str(row.get("path")): _normalize_hash(row.get("sha256"))
        for row in pr152_manifest.get("input_hashes", [])
        if isinstance(row, dict) and row.get("path") and row.get("sha256")
    }
    if manifest_pins.get(str(card_path.relative_to(REPO))) != actual_small[
        str(card_path.relative_to(REPO))
    ]:
        raise ActInbandModulationError("PR-152 manifest does not pin the release card")
    embedded = pr152_card.get("input_provenance", {}).get("input_manifest")
    if not isinstance(embedded, dict):
        raise ActInbandModulationError("PR-152 embedded input manifest missing")
    embedded_hash = _normalize_hash(embedded.get("manifest_sha256"))
    if _canonical_without_self_hash(embedded, "manifest_sha256") != embedded_hash:
        raise ActInbandModulationError("PR-152 embedded manifest self-hash mismatch")
    expected_embedded = _normalize_hash(
        authorities["pr152_release_card"]["embedded_ordered_manifest_sha256"]
    )
    if embedded_hash != expected_embedded:
        raise ActInbandModulationError("PR-152 embedded manifest identity drift")
    if manifest_pins.get("embedded:ordered_act_release_input_manifest") != embedded_hash:
        raise ActInbandModulationError("PR-152 outer/embedded manifest cross-pin failed")
    raw_root = raw_records_only_root(embedded)
    if raw_root != _normalize_hash(
        authorities["pr152_release_card"]["raw_records_only_sha256"]
    ):
        raise ActInbandModulationError("PR-177 raw-record-only root mismatch")

    bundle = spec["selected_release_bundle"]
    acquisition = _json(acquisition_path)
    for key in ("observed_alm", "mask", "release_filter_context"):
        expected = bundle[key]
        record = _find_acquisition_record(acquisition, REPO / expected["path"])
        _verify_record(record, expected, key)

    data_record = dict(embedded["data_alm"])
    _verify_record(data_record, bundle["observed_alm"], "observed alm")
    sim_records = [dict(row) for row in embedded["ordered_simulation_alms"]]
    if len(sim_records) != 400:
        raise ActInbandModulationError("exactly 400 simulation records required")
    expected_names = [
        f"kappa_alm_sim_act_dr6_lensing_v1_baseline_{index:04d}.fits"
        for index in range(1, 401)
    ]
    names = [Path(str(row["path"])).name for row in sim_records]
    if names != expected_names or len(set(names)) != 400:
        raise ActInbandModulationError("ordered baseline simulation identities drifted")
    raw_records = [data_record, *sim_records]
    for record in raw_records:
        path = REPO / str(record["path"]) if not Path(str(record["path"])).is_absolute() else Path(str(record["path"]))
        if not path.is_file() or path.stat().st_size != int(record["size_bytes"]):
            raise ActInbandModulationError(f"raw payload stat check failed: {path}")
    for key in ("mask", "release_filter_context"):
        expected = bundle[key]
        path = REPO / expected["path"]
        if not path.is_file() or path.stat().st_size != int(expected["size_bytes"]):
            raise ActInbandModulationError(f"release context stat check failed: {path}")

    units = [
        {
            "unit_id": "data",
            "unit_kind": "observed",
            "record": data_record,
        }
    ]
    units.extend(
        {
            "unit_id": f"sim-{index:04d}",
            "unit_kind": "release_simulation",
            "record": record,
        }
        for index, record in enumerate(sim_records, start=1)
    )
    return {
        "small_authority_hashes": actual_small,
        "embedded_ordered_manifest_sha256": embedded_hash,
        "raw_records_only_sha256": raw_root,
        "raw_payload_count": len(raw_records),
        "raw_payload_bytes": sum(int(row["size_bytes"]) for row in raw_records),
        "raw_payload_hashing_performed_by_pr177": False,
        "raw_payload_stat_checks_performed": len(raw_records),
        "mask_and_filter_stat_checks_performed": 2,
        "units": units,
    }


def _priority_receipt() -> dict[str, Any]:
    nice = os.getpriority(os.PRIO_PROCESS, 0)
    completed = subprocess.run(
        ["ionice", "-p", str(os.getpid())],
        capture_output=True,
        text=True,
        check=False,
    )
    text = (completed.stdout + completed.stderr).strip()
    return {
        "pid": os.getpid(),
        "effective_nice": int(nice),
        "ionice_query": text,
        "ionice_idle": completed.returncode == 0 and "idle" in text.lower(),
        "thread_environment": {
            key: os.environ.get(key)
            for key in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS")
        },
    }


def _resource_receipt() -> dict[str, Any]:
    probe = subprocess.run(
        [sys.executable, str(REPO / "scripts/codex_harness/pr151_progress.py"), "--compact"],
        cwd=REPO,
        capture_output=True,
        text=True,
        check=False,
    )
    if probe.returncode != 0:
        raise ActInbandModulationError("PR-151 fast progress probe failed")
    progress = json.loads(probe.stdout)
    log = progress["transfer_state"]["log"]
    disk = progress["disk"]
    priority = _priority_receipt()
    receipt: dict[str, Any] = {
        "pr151_sample_id": progress["activity"]["sample_id"],
        "pr151_effective_writer_state": progress["activity"]["effective_writer_state"],
        "pr151_log_age_seconds": float(log["age_seconds"]),
        "pr151_log_fresh_under_1800_seconds": float(log["age_seconds"]) < 1800.0,
        "free_gib": float(disk["free_gib"]),
        "free_gib_at_least_300": float(disk["free_gib"]) >= 300.0,
        "priority": priority,
        "single_sequential_reader": True,
        "raw_workers": 1,
    }
    receipt["eligible"] = not resource_receipt_errors(receipt, require_eligible_field=False)
    receipt["semantic_digest"] = semantic_digest(receipt)
    if resource_receipt_errors(receipt):
        raise ActInbandModulationError(f"PR-177 resource policy failed: {receipt}")
    return receipt


def resource_receipt_errors(
    receipt: Mapping[str, Any], *, require_eligible_field: bool = True
) -> list[str]:
    """Re-derive extraction eligibility from primitive resource fields."""

    errors: list[str] = []
    try:
        age = float(receipt["pr151_log_age_seconds"])
        free = float(receipt["free_gib"])
        priority = receipt["priority"]
        threads = priority["thread_environment"]
        effective_nice = int(priority["effective_nice"])
    except (KeyError, TypeError, ValueError):
        return ["resource receipt primitives are incomplete"]
    conditions = {
        "PR-151 writer is not running": receipt.get("pr151_effective_writer_state") == "running",
        "PR-151 log is not fresh": np.isfinite(age) and 0.0 <= age < 1800.0,
        "PR-151 freshness flag drift": receipt.get("pr151_log_fresh_under_1800_seconds") is True,
        "free space is below 300 GiB": np.isfinite(free) and free >= 300.0,
        "free-space flag drift": receipt.get("free_gib_at_least_300") is True,
        "effective nice is below 15": effective_nice >= 15,
        "ionice is not idle": priority.get("ionice_idle") is True,
        "thread caps are not exactly one": isinstance(threads, Mapping)
        and dict(threads)
        == {"OMP_NUM_THREADS": "1", "OPENBLAS_NUM_THREADS": "1", "MKL_NUM_THREADS": "1"},
        "reader is not declared sequential": receipt.get("single_sequential_reader") is True,
        "raw worker count is not one": receipt.get("raw_workers") == 1,
    }
    errors.extend(message for message, passed in conditions.items() if not passed)
    if require_eligible_field and receipt.get("eligible") != (not errors):
        errors.append("eligible flag does not equal re-derived resource state")
    if "semantic_digest" in receipt and receipt.get("semantic_digest") != semantic_digest(receipt):
        errors.append("resource receipt digest mismatch")
    return errors


def extraction_runtime_identity() -> dict[str, Any]:
    """Return the numerical runtime identity bound into every cache key."""

    import healpy as hp

    return {
        "python": platform.python_version(),
        "numpy": np.__version__,
        "healpy": hp.__version__,
        "harmonic_backend": "healpy.sphtfunc.alm2map(libsharp)",
        "platform": platform.platform(),
        "thread_environment": {
            key: os.environ.get(key)
            for key in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS")
        },
    }


def _local_hashes() -> dict[str, str]:
    return {
        str(path.relative_to(REPO)): _sha(path)
        for path in (SPEC_PATH, MODULE_PATH, SCRIPT_PATH)
    }


def build_cache_identity(spec: Mapping[str, Any], source: Mapping[str, Any]) -> dict[str, Any]:
    local = _local_hashes()
    identity = {
        "schema": CACHE_SCHEMA,
        "config_hash": local[str(SPEC_PATH.relative_to(REPO))],
        "module_hash": local[str(MODULE_PATH.relative_to(REPO))],
        "producer_hash": local[str(SCRIPT_PATH.relative_to(REPO))],
        "raw_records_only_sha256": source["raw_records_only_sha256"],
        "mask_sha256": _normalize_hash(spec["selected_release_bundle"]["mask"]["sha256"]),
        "integer_support": list(strict_integer_support()),
        "nside": int(spec["estimator"]["pixelization"]["nside"]),
        "mask_threshold": float(spec["estimator"]["pixelization"]["mask_threshold"]),
        "raw_workers": 1,
        "runtime_identity": extraction_runtime_identity(),
    }
    identity["cache_key"] = canonical_sha256(identity)
    return identity


def _cache_root(identity: Mapping[str, Any]) -> Path:
    return CACHE_BASE / str(identity["cache_key"])


def _atomic_json(path: Path, payload: Mapping[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    temporary.replace(path)


def _unit_cache_path(root: Path, unit_id: str) -> Path:
    return root / "units" / f"{unit_id}.json"


@contextmanager
def extraction_lock(root: Path):
    """Hold the cache-key-specific single-writer lock for every raw read."""

    root.mkdir(parents=True, exist_ok=True)
    path = root / ".extract.lock"
    with path.open("a+", encoding="utf-8") as handle:
        try:
            fcntl.flock(handle.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError as exc:
            raise ActInbandModulationError("another PR-177 raw extractor holds the lock") from exc
        try:
            yield
        finally:
            fcntl.flock(handle.fileno(), fcntl.LOCK_UN)


def unit_cache_errors(
    payload: Mapping[str, Any],
    *,
    identity: Mapping[str, Any],
    unit: Mapping[str, Any],
) -> list[str]:
    """Validate a unit cache against the frozen identity and exact source row."""

    errors: list[str] = []
    expected_pipeline = {
        "integer_min": 41,
        "integer_max": 762,
        "nside": int(identity["nside"]),
        "mask_threshold": float(identity["mask_threshold"]),
        "feature_callable": "obsstat.act_inband_modulation.extract_alm_features",
        "runtime_identity": identity["runtime_identity"],
    }
    checks = {
        "unit cache schema mismatch": payload.get("schema") == CACHE_SCHEMA,
        "unit cache key mismatch": payload.get("cache_key") == identity["cache_key"],
        "unit id mismatch": payload.get("unit_id") == unit["unit_id"],
        "unit kind mismatch": payload.get("unit_kind") == unit["unit_kind"],
        "unit source record mismatch": payload.get("source_record") == unit["record"],
        "unit pipeline receipt mismatch": payload.get("identical_pipeline_receipt") == expected_pipeline,
        "unit cache raw-rehash flag drift": payload.get("raw_payload_rehashed_by_pr177") is False,
        "unit cache semantic digest mismatch": payload.get("semantic_digest") == semantic_digest(payload),
    }
    errors.extend(message for message, passed in checks.items() if not passed)
    feature = payload.get("feature")
    if not isinstance(feature, Mapping):
        return [*errors, "unit feature is missing"]
    try:
        raw = np.asarray(feature["q_raw"], dtype=float)
        controlled = np.asarray(feature["q_controlled"], dtype=float)
        change = float(feature["mask_change"])
        mean_variance = float(feature["mean_core_variance"])
        raw_condition = float(feature["raw_design_condition_number"])
        controlled_condition = float(feature["controlled_design_condition_number"])
    except (KeyError, TypeError, ValueError):
        return [*errors, "unit feature primitives are malformed"]
    if raw.shape != (5,) or controlled.shape != (5,) or not np.all(np.isfinite(raw)) or not np.all(np.isfinite(controlled)):
        errors.append("unit quadrupole vectors are malformed")
    expected_change = float(np.sum((raw - controlled) ** 2))
    if not np.isfinite(change) or change < 0.0 or not np.isclose(change, expected_change, rtol=0.0, atol=1.0e-24):
        errors.append("unit mask-change primitive is inconsistent")
    if not np.isfinite(mean_variance) or mean_variance <= 0.0:
        errors.append("unit mean variance is not finite and positive")
    if (
        not np.isfinite(raw_condition)
        or not np.isfinite(controlled_condition)
        or raw_condition > 1.0e8
        or controlled_condition > 1.0e8
    ):
        errors.append("unit design receipt failed")
    return errors


def _valid_unit_cache(
    path: Path,
    *,
    identity: Mapping[str, Any],
    unit: Mapping[str, Any],
) -> bool:
    if not path.is_file():
        return False
    try:
        payload = _json(path)
        return not unit_cache_errors(payload, identity=identity, unit=unit)
    except (OSError, ValueError, KeyError, TypeError):
        return False


def _load_design(spec: Mapping[str, Any]):
    import healpy as hp

    mask_row = spec["selected_release_bundle"]["mask"]
    mask = hp.read_map(str(REPO / mask_row["path"]), dtype=np.float32)
    nside = int(spec["estimator"]["pixelization"]["nside"])
    downgraded = hp.ud_grade(mask, nside, order_in="RING", order_out="RING", power=0)
    design = build_mask_design(
        downgraded,
        nside=nside,
        threshold=float(spec["estimator"]["pixelization"]["mask_threshold"]),
        maximum_condition_number=float(spec["scoring"]["covariance_gate"]["maximum_condition_number"]),
    )
    expected = spec["estimator"]["pixelization"]["pre_result_mask_receipt"]
    if int(expected["core_pixels"]) != design.core_pixels.size:
        raise ActInbandModulationError("frozen mask-core count drifted")
    return design


def _resource_history_errors(
    resource: Mapping[str, Any], identity: Mapping[str, Any]
) -> list[str]:
    errors: list[str] = []
    if resource.get("schema") != EXTRACTION_SCHEMA:
        errors.append("resource history schema mismatch")
    if resource.get("cache_key") != identity["cache_key"]:
        errors.append("resource history cache key mismatch")
    if resource.get("semantic_digest") != semantic_digest(resource):
        errors.append("resource history semantic digest mismatch")
    invocations = resource.get("invocations")
    if not isinstance(invocations, list) or not invocations:
        errors.append("resource history has no invocations")
    else:
        for index, receipt in enumerate(invocations):
            if not isinstance(receipt, Mapping):
                errors.append(f"resource invocation {index} is malformed")
            else:
                errors.extend(
                    f"resource invocation {index}: {message}"
                    for message in resource_receipt_errors(receipt)
                )
        if resource.get("latest_receipt_digest") != invocations[-1].get("semantic_digest"):
            errors.append("latest resource receipt digest mismatch")
    return errors


def _append_fresh_resource_receipt(
    path: Path, identity: Mapping[str, Any]
) -> dict[str, Any]:
    if path.is_file():
        resource = _json(path)
        errors = _resource_history_errors(resource, identity)
        if errors:
            raise ActInbandModulationError("; ".join(errors))
        invocations = list(resource["invocations"])
    else:
        invocations = []
    fresh = _resource_receipt()
    invocations.append(fresh)
    updated: dict[str, Any] = {
        "schema": EXTRACTION_SCHEMA,
        "cache_key": identity["cache_key"],
        "invocations": invocations,
        "latest_receipt_digest": fresh["semantic_digest"],
    }
    updated["semantic_digest"] = semantic_digest(updated)
    _atomic_json(path, updated)
    return updated


def extract(spec: Mapping[str, Any], source: Mapping[str, Any], identity: Mapping[str, Any]) -> None:
    """Extract or resume under a fresh live resource gate and one writer lock."""

    root = _cache_root(identity)
    with extraction_lock(root):
        _extract_locked(spec, source, identity, root)


def _extract_locked(
    spec: Mapping[str, Any],
    source: Mapping[str, Any],
    identity: Mapping[str, Any],
    root: Path,
) -> None:
    import healpy as hp

    resource_path = root / "extraction_resource_receipt.json"
    _append_fresh_resource_receipt(resource_path, identity)
    last_probe = time.monotonic()
    design = _load_design(spec)
    design_path = root / "mask_design_receipt.json"
    design_receipt: dict[str, Any] = {
        "schema": "htt.pr177.mask_design_receipt.v1",
        "cache_key": identity["cache_key"],
        "mask_sha256": _normalize_hash(spec["selected_release_bundle"]["mask"]["sha256"]),
        "design": design.receipt(),
    }
    design_receipt["semantic_digest"] = semantic_digest(design_receipt)
    if design_path.is_file():
        if _json(design_path) != design_receipt:
            raise ActInbandModulationError("cached mask design receipt drifted")
    else:
        _atomic_json(design_path, design_receipt)
    integer_min = int(spec["estimator"]["analysis_multipoles"]["integer_min"])
    integer_max = int(spec["estimator"]["analysis_multipoles"]["integer_max"])
    for position, unit in enumerate(source["units"], start=1):
        if time.monotonic() - last_probe >= 1800.0:
            _append_fresh_resource_receipt(resource_path, identity)
            last_probe = time.monotonic()
        cache_path = _unit_cache_path(root, str(unit["unit_id"]))
        if _valid_unit_cache(cache_path, identity=identity, unit=unit):
            continue
        raw_path = Path(str(unit["record"]["path"]))
        if not raw_path.is_absolute():
            raw_path = REPO / raw_path
        alm = np.asarray(hp.read_alm(str(raw_path)), dtype=np.complex128)
        feature = extract_alm_features(
            alm,
            design,
            integer_min=integer_min,
            integer_max=integer_max,
        )
        payload: dict[str, Any] = {
            "schema": CACHE_SCHEMA,
            "cache_key": identity["cache_key"],
            "unit_id": unit["unit_id"],
            "unit_kind": unit["unit_kind"],
            "source_record": unit["record"],
            "feature": feature,
            "identical_pipeline_receipt": {
                "integer_min": integer_min,
                "integer_max": integer_max,
                "nside": design.nside,
                "mask_threshold": design.threshold,
                "feature_callable": "obsstat.act_inband_modulation.extract_alm_features",
                "runtime_identity": identity["runtime_identity"],
            },
            "raw_payload_rehashed_by_pr177": False,
        }
        payload["semantic_digest"] = semantic_digest(payload)
        errors = unit_cache_errors(payload, identity=identity, unit=unit)
        if errors:
            raise ActInbandModulationError("new unit cache failed validation: " + "; ".join(errors))
        _atomic_json(cache_path, payload)
        del alm
        if position % 10 == 0 or position == len(source["units"]):
            print(f"PR-177 extracted authenticated unit {position}/{len(source['units'])}", flush=True)


def _load_complete_cache(
    source: Mapping[str, Any], identity: Mapping[str, Any]
) -> tuple[list[dict[str, Any]], dict[str, Any], dict[str, Any]]:
    root = _cache_root(identity)
    resource = _json(root / "extraction_resource_receipt.json")
    resource_errors = _resource_history_errors(resource, identity)
    if resource_errors:
        raise ActInbandModulationError("; ".join(resource_errors))
    design = _json(root / "mask_design_receipt.json")
    if (
        design.get("schema") != "htt.pr177.mask_design_receipt.v1"
        or design.get("cache_key") != identity["cache_key"]
        or design.get("semantic_digest") != semantic_digest(design)
    ):
        raise ActInbandModulationError("mask design receipt is invalid")
    records: list[dict[str, Any]] = []
    expected_paths: set[Path] = set()
    for unit in source["units"]:
        path = _unit_cache_path(root, str(unit["unit_id"]))
        expected_paths.add(path.resolve())
        if not _valid_unit_cache(path, identity=identity, unit=unit):
            raise ActInbandModulationError(f"missing or stale unit cache {unit['unit_id']}")
        records.append(_json(path))
    actual_paths = {path.resolve() for path in (root / "units").glob("*.json")}
    if actual_paths != expected_paths:
        raise ActInbandModulationError("unit cache contains missing or extra records")
    return records, resource, design


def build_card(
    spec: Mapping[str, Any], source: Mapping[str, Any], identity: Mapping[str, Any]
) -> dict[str, Any]:
    records, resource, design = _load_complete_cache(source, identity)
    local = _local_hashes()
    head = str(spec["baseline_commit"])
    units = [
        {
            "unit_id": row["unit_id"],
            "unit_kind": row["unit_kind"],
            "source_sha256": _normalize_hash(row["source_record"]["sha256"]),
            "source_size_bytes": int(row["source_record"]["size_bytes"]),
            "feature": row["feature"],
            "unit_cache_semantic_digest": row["semantic_digest"],
        }
        for row in records
    ]
    content_receipt = canonical_sha256(
        {
            "local": local,
            "source_authorities": source["small_authority_hashes"],
            "raw_records_only_sha256": source["raw_records_only_sha256"],
            "mask_sha256": spec["selected_release_bundle"]["mask"]["sha256"],
            "unit_cache_digests": [row["semantic_digest"] for row in records],
        }
    )
    card: dict[str, Any] = {
        "schema": CARD_SCHEMA,
        "process_execution_status": "PASS_COMPLETE_401_UNIT_EXTRACTION",
        "scientific_result": None,
        "scientific_status": "NOT_EVALUATED_FEATURE_EXTRACTION_ONLY",
        "owner": "OBSSTAT",
        "implementation_scope": ["obsstat"],
        "claim_tier": "conditional",
        "claim_level": {"scheme": "roadmap_rescue_v1", "level": "C3"},
        "scientific_artifact_mode": "standard_internal",
        "public_use": False,
        "transfer_source": "none",
        "config_hash": local[str(SPEC_PATH.relative_to(REPO))],
        "input_hashes": {
            **local,
            **source["small_authority_hashes"],
            "embedded:pr152_ordered_manifest": source["embedded_ordered_manifest_sha256"],
            "embedded:pr177_raw_records_only_root": source["raw_records_only_sha256"],
            "raw:observed_alm": _normalize_hash(spec["selected_release_bundle"]["observed_alm"]["sha256"]),
            "raw:ordered_400_simulation_root": source["raw_records_only_sha256"],
            "raw:release_mask": _normalize_hash(spec["selected_release_bundle"]["mask"]["sha256"]),
            "raw:release_filter_context": _normalize_hash(spec["selected_release_bundle"]["release_filter_context"]["sha256"]),
        },
        "input_authentication": {
            key: value for key, value in source.items() if key != "units"
        },
        "cache_identity": dict(identity),
        "extraction_resource_receipt": resource,
        "analysis_support": {
            "inequality": "40 < L < 763",
            "integer_min": 41,
            "integer_max": 762,
            "integer_count": 722,
            "endpoints_40_and_763_included": False,
            "coordinate_frame": "Equatorial",
        },
        "mask_design": design["design"],
        "unit_count": len(units),
        "observed_unit_count": sum(row["unit_kind"] == "observed" for row in units),
        "release_simulation_count": sum(row["unit_kind"] == "release_simulation" for row in units),
        "units": units,
        "identical_pipeline": True,
        "raw_workers": 1,
        "sequential_reader": True,
        "raw_payload_rehashed_by_pr177": False,
        "sky_support_status": "released_baseline_reconstructed_kappa_equatorial_mask_core_not_independently_reprocessed",
        "mask_status": "authenticated_release_mask_MK_ge_0p99_core_with_MK_squared_registered_nuisance",
        "covariance_status": "not_evaluated_feature_extraction_only",
        "null_mock_status": "exactly_400_authenticated_release_reconstructed_simulations_features_extracted",
        "generating_command": (
            "ionice -c 3 nice -n 15 env OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 "
            "MKL_NUM_THREADS=1 MPLCONFIGDIR=/tmp/mpl-pr177 venv/bin/python -B "
            "scripts/act_inband_modulation_card.py --phase all"
        ),
        "git_commit": head,
        "worktree_content_receipt": content_receipt,
        "worktree_state": f"{head}+content-sha256:{content_receipt}",
        "runtime_environment": identity["runtime_identity"],
        "caveats": [
            "Feature extraction is process evidence, not a scientific terminal result.",
            "The released reconstructed kappa is not a local raw-QE or RDN0 rerun.",
            "Raw payload hashes are inherited from PR-152 and the ACT acquisition manifest; PR-177 performs only path/size checks.",
            "The mask control is bounded and cannot rule out all reconstruction, filter, foreground, noise, or mask effects.",
            "No detection, cosmological anisotropy, transfer, geometry, or family claim is authorized.",
        ],
    }
    card["semantic_digest"] = semantic_digest(card)
    return card


def _card_text(card: Mapping[str, object]) -> str:
    return json.dumps(card, indent=2, sort_keys=True) + "\n"


def serialized_payload_sha256(payload: Mapping[str, object]) -> str:
    """Hash the canonical tracked JSON rendering used by this producer."""

    return hashlib.sha256(_card_text(payload).encode("utf-8")).hexdigest()


def deep_replay(
    spec: Mapping[str, Any], source: Mapping[str, Any], identity: Mapping[str, Any]
) -> dict[str, Any]:
    """Re-extract all 401 features from raw authority and compare without hashing."""

    import healpy as hp

    expected_card = build_card(spec, source, identity)
    if not OUT.is_file() or OUT.read_text(encoding="utf-8") != _card_text(expected_card):
        raise ActInbandModulationError("deep replay requires the current feature card")
    root = _cache_root(identity)
    with extraction_lock(root):
        resource_receipts = [_resource_receipt()]
        last_probe = time.monotonic()
        design = _load_design(spec)
        integer_min = int(spec["estimator"]["analysis_multipoles"]["integer_min"])
        integer_max = int(spec["estimator"]["analysis_multipoles"]["integer_max"])
        mismatches: list[str] = []
        for position, unit in enumerate(source["units"], start=1):
            if time.monotonic() - last_probe >= 1800.0:
                resource_receipts.append(_resource_receipt())
                last_probe = time.monotonic()
            raw_path = Path(str(unit["record"]["path"]))
            if not raw_path.is_absolute():
                raw_path = REPO / raw_path
            alm = np.asarray(hp.read_alm(str(raw_path)), dtype=np.complex128)
            replayed = extract_alm_features(
                alm,
                design,
                integer_min=integer_min,
                integer_max=integer_max,
            )
            cache = _json(_unit_cache_path(root, str(unit["unit_id"])))
            if unit_cache_errors(cache, identity=identity, unit=unit):
                mismatches.append(f"{unit['unit_id']}:cache_envelope")
            if replayed != cache.get("feature"):
                mismatches.append(f"{unit['unit_id']}:raw_feature_replay")
            if replayed != expected_card["units"][position - 1]["feature"]:
                mismatches.append(f"{unit['unit_id']}:feature_card")
            del alm
            if position % 25 == 0 or position == len(source["units"]):
                print(
                    f"PR-177 deep-replayed authenticated unit {position}/{len(source['units'])}",
                    flush=True,
                )
        if mismatches:
            raise ActInbandModulationError(
                "deep replay feature mismatch: " + ", ".join(mismatches[:10])
            )
    receipt: dict[str, Any] = {
        "schema": DEEP_REPLAY_SCHEMA,
        "process_execution_status": "PASS_AUTHORITATIVE_401_UNIT_FEATURE_REPLAY",
        "scientific_result": None,
        "scientific_status": "NOT_EVALUATED_PROVENANCE_REPLAY_ONLY",
        "owner": "OBSSTAT",
        "implementation_scope": ["obsstat"],
        "claim_tier": "conditional",
        "claim_level": {"scheme": "roadmap_rescue_v1", "level": "C3"},
        "scientific_artifact_mode": "standard_internal",
        "public_use": False,
        "transfer_source": "none",
        "config_hash": expected_card["config_hash"],
        "input_hashes": {
            **expected_card["input_hashes"],
            str(OUT.relative_to(REPO)): serialized_payload_sha256(expected_card),
        },
        "analysis_support": expected_card["analysis_support"],
        "cache_key": identity["cache_key"],
        "cache_identity": dict(identity),
        "feature_card_path": str(OUT.relative_to(REPO)),
        "feature_card_sha256": serialized_payload_sha256(expected_card),
        "feature_card_semantic_digest": expected_card["semantic_digest"],
        "raw_records_only_sha256": source["raw_records_only_sha256"],
        "raw_units_opened": 401,
        "raw_payloads_hashed": 0,
        "raw_payload_stat_checks": source["raw_payload_stat_checks_performed"],
        "feature_units_replayed": 401,
        "feature_mismatch_count": 0,
        "features_match_raw_authority": True,
        "single_sequential_reader": True,
        "resource_receipts": resource_receipts,
        "runtime_identity": identity["runtime_identity"],
        "sky_support_status": expected_card["sky_support_status"],
        "mask_status": expected_card["mask_status"],
        "covariance_status": "not_evaluated_provenance_replay_only",
        "null_mock_status": "exactly_400_authenticated_release_reconstructions_replayed_without_scoring",
        "generating_command": (
            "ionice -c 3 nice -n 15 env OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 "
            "MKL_NUM_THREADS=1 MPLCONFIGDIR=/tmp/mpl-pr177 PYTHONPATH=htt "
            "venv/bin/python -B scripts/act_inband_modulation_card.py --phase deep-check"
        ),
        "git_commit": expected_card["git_commit"],
        "worktree_state": expected_card["worktree_state"],
        "caveats": [
            "This receipt proves a same-runtime feature replay against authenticated raw paths; it is not physical validation.",
            "Raw bytes were not rehashed; byte authority remains inherited from PR-152.",
            "The replay does not reproduce the ACT raw-QE reconstruction or authorize a detection claim.",
        ],
        "interpretation": "derived_feature_provenance_replay_not_physical_validation",
    }
    receipt["semantic_digest"] = semantic_digest(receipt)
    _atomic_json(DEEP_REPLAY_OUT, receipt)
    return receipt


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--phase", choices=("extract", "aggregate", "all", "check", "deep-check"), default="all"
    )
    parser.add_argument("--workers", type=int, default=1)
    args = parser.parse_args(argv)
    if args.workers != 1:
        raise SystemExit("PR-177 refuses raw worker counts other than one")
    spec = _spec()
    support = strict_integer_support()
    if support[0] != 41 or support[-1] != 762 or len(support) != 722:
        raise ActInbandModulationError("strict integer support drifted")
    source = authenticate_sources(spec)
    identity = build_cache_identity(spec, source)
    if args.phase in ("extract", "all"):
        extract(spec, source, identity)
    if args.phase in ("aggregate", "all", "check"):
        card = build_card(spec, source, identity)
        expected = _card_text(card)
        if args.phase == "check":
            if not OUT.is_file() or OUT.read_text(encoding="utf-8") != expected:
                print("stale PR-177 feature card")
                return 1
            print(json.dumps({"ok": True, "raw_payloads_opened": 0, "raw_payloads_hashed": 0, "unit_count": card["unit_count"]}, sort_keys=True))
            return 0
        OUT.parent.mkdir(parents=True, exist_ok=True)
        OUT.write_text(expected, encoding="utf-8")
        print(f"wrote {OUT.relative_to(REPO)} with {card['unit_count']} authenticated unit features")
    if args.phase == "deep-check":
        receipt = deep_replay(spec, source, identity)
        print(
            json.dumps(
                {
                    "ok": True,
                    "feature_units_replayed": receipt["feature_units_replayed"],
                    "raw_payloads_hashed": receipt["raw_payloads_hashed"],
                    "features_match_raw_authority": receipt["features_match_raw_authority"],
                },
                sort_keys=True,
            )
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
