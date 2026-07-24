#!/usr/bin/env python3
"""Heavy PR-204 producer for strict-band post-reconstruction injections.

The ignored unit cache makes the 400-unit single-reader run resumable.  The
tracked calibration card contains the bounded paired features needed for
deterministic response and coverage recomputation; it does not contain raw
ACT data.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
import time
from pathlib import Path
from typing import Any, Mapping

import numpy as np
import yaml

REPO = Path(__file__).resolve().parents[1]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

from obsstat.act_inband_injection import (  # noqa: E402
    analyze_injection_records,
    full_sky_real_y2_templates,
    injected_unit_features,
    injection_assignment,
)
from obsstat.act_inband_modulation import (  # noqa: E402
    ActInbandModulationError,
    canonical_sha256,
)
from scripts.act_inband_modulation_card import (  # noqa: E402
    _load_design,
    _resource_receipt,
    authenticate_sources,
    extraction_lock,
    extraction_runtime_identity,
    resource_receipt_errors,
)

SPEC = REPO / "docs/research_program/strengthening/pr204_spec.yaml"
PR177_SPEC = REPO / "docs/research_program/long_horizon_rescue/pr177_spec.yaml"
PR177_FEATURE_CARD = REPO / "docs/generated/pr177_act_inband_feature_card.json"
MODULE = REPO / "htt/obsstat/act_inband_injection.py"
OUT = REPO / "docs/generated/pr204_injection_calibration.json"
CACHE_BASE = REPO / "workdir/pr204_act_inband_injection"
CACHE_SCHEMA = "htt.pr204.injection_unit.v1"
CARD_SCHEMA = "htt.pr204.injection_calibration.v1"


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


def _yaml(path: Path) -> dict[str, Any]:
    value = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ActInbandModulationError(f"{path} must contain a YAML mapping")
    return value


def _atomic_json(path: Path, payload: Mapping[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(
        json.dumps(payload, indent=1, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    temporary.replace(path)


def _identity(spec: Mapping[str, Any], source: Mapping[str, Any]) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "schema": CACHE_SCHEMA,
        "spec_sha256": _sha(SPEC),
        "module_sha256": _sha(MODULE),
        "producer_sha256": _sha(Path(__file__).resolve()),
        "pr177_feature_card_sha256": _sha(PR177_FEATURE_CARD),
        "raw_records_only_sha256": source["raw_records_only_sha256"],
        "support": [41, 762],
        "nside": int(spec["harmonic_contract"]["nside"]),
        "amplitude_magnitude": float(
            spec["injection_contract"]["amplitude_magnitude"]
        ),
        "runtime": extraction_runtime_identity(),
    }
    payload["cache_key"] = canonical_sha256(payload)
    return payload


def _assignment_dict(simulation_id: int) -> dict[str, object]:
    assignment = injection_assignment(simulation_id)
    return {
        "axis_index": assignment.axis_index,
        "axis_name": assignment.axis_name,
        "within_axis_index": assignment.within_axis_index,
        "amplitude": assignment.amplitude,
        "split": assignment.split,
    }


def _semantic_digest(payload: Mapping[str, object]) -> str:
    material = dict(payload)
    material.pop("semantic_digest", None)
    return canonical_sha256(material)


def _unit_errors(
    payload: Mapping[str, Any],
    *,
    identity: Mapping[str, Any],
    simulation_id: int,
    source_record: Mapping[str, Any],
) -> list[str]:
    errors = []
    expected_assignment = _assignment_dict(simulation_id)
    checks = {
        "unit schema mismatch": payload.get("schema") == CACHE_SCHEMA,
        "cache key mismatch": payload.get("cache_key") == identity["cache_key"],
        "simulation id mismatch": payload.get("simulation_id") == simulation_id,
        "source record mismatch": payload.get("source_record") == source_record,
        "assignment mismatch": payload.get("assignment") == expected_assignment,
        "raw rehash flag mismatch": payload.get("raw_payload_rehashed") is False,
        "semantic digest mismatch": payload.get("semantic_digest")
        == _semantic_digest(payload),
    }
    errors.extend(message for message, passed in checks.items() if not passed)
    try:
        baseline = payload["baseline"]
        injected = payload["injected"]
        for feature in (baseline, injected):
            for key in ("q_raw", "q_controlled"):
                values = np.asarray(feature[key], dtype=float)
                if values.shape != (5,) or not np.all(np.isfinite(values)):
                    errors.append(f"{key} is malformed")
        support = payload["hard_reprojected_integer_support"]
        if support != [41, 762]:
            errors.append("hard support mismatch")
        if payload.get("map2alm_iterations") != 0:
            errors.append("map2alm iteration contract mismatch")
        if payload.get("pixel_weights") is not False:
            errors.append("pixel-weight contract mismatch")
        if float(payload["minimum_variance_factor"]) <= 0.0:
            errors.append("variance factor is not positive")
    except (KeyError, TypeError, ValueError):
        errors.append("unit feature payload is incomplete")
    return errors


def _unit_path(root: Path, simulation_id: int) -> Path:
    return root / "units" / f"sim-{simulation_id:04d}.json"


def _baseline_features() -> dict[str, dict[str, Any]]:
    card = _json(PR177_FEATURE_CARD)
    if _sha(PR177_FEATURE_CARD) != _yaml(SPEC)["source_authorities"][
        "pr177_feature_card"
    ]["sha256"]:
        raise ActInbandModulationError("PR-177 feature-card authority drift")
    return {
        str(row["unit_id"]): dict(row["feature"])
        for row in card["units"]
        if row["unit_kind"] == "release_simulation"
    }


def _assert_baseline_match(
    recomputed: Mapping[str, object],
    cached: Mapping[str, object],
    tolerance: float,
) -> None:
    for field in (
        "q_raw",
        "q_controlled",
        "mask_change",
        "mean_core_variance",
        "raw_design_condition_number",
        "controlled_design_condition_number",
    ):
        left = np.asarray(recomputed[field], dtype=float)
        right = np.asarray(cached[field], dtype=float)
        if left.shape != right.shape or not np.allclose(
            left,
            right,
            rtol=0.0,
            atol=tolerance,
        ):
            raise ActInbandModulationError(
                f"paired PR-177 baseline feature drifted: {field}"
            )


def _append_resource_receipt(root: Path) -> None:
    path = root / "resource_receipts.json"
    payload = _json(path) if path.is_file() else {
        "schema": "htt.pr204.resource_receipts.v1",
        "receipts": [],
    }
    receipts = list(payload["receipts"])
    for index, receipt in enumerate(receipts):
        if not isinstance(receipt, Mapping):
            raise ActInbandModulationError(
                f"resource receipt {index} is malformed"
            )
        errors = resource_receipt_errors(receipt)
        if errors:
            raise ActInbandModulationError(
                f"resource receipt {index}: {'; '.join(errors)}"
            )
    if payload.get("semantic_digest") not in (
        None,
        _semantic_digest(payload),
    ):
        raise ActInbandModulationError("resource receipt history digest mismatch")
    receipts.append(_resource_receipt())
    payload["receipts"] = receipts
    payload["semantic_digest"] = _semantic_digest(payload)
    _atomic_json(path, payload)


def extract() -> dict[str, object]:
    import healpy as hp

    spec = _yaml(SPEC)
    pr177_spec = _yaml(PR177_SPEC)
    source = authenticate_sources(pr177_spec)
    identity = _identity(spec, source)
    root = CACHE_BASE / str(identity["cache_key"])
    baseline = _baseline_features()
    tolerance = float(
        spec["injection_contract"]["paired_baseline_gate"][
            "cached_feature_match_absolute_tolerance"
        ]
    )
    simulations = [row for row in source["units"] if row["unit_kind"] == "release_simulation"]
    if len(simulations) != 400:
        raise ActInbandModulationError("exactly 400 release simulations required")
    with extraction_lock(root):
        _append_resource_receipt(root)
        design = _load_design(pr177_spec)
        templates = full_sky_real_y2_templates(design.nside)
        last_resource_probe = time.monotonic()
        for position, unit in enumerate(simulations, start=1):
            simulation_id = int(str(unit["unit_id"]).split("-")[-1])
            path = _unit_path(root, simulation_id)
            if path.is_file():
                existing = _json(path)
                if not _unit_errors(
                    existing,
                    identity=identity,
                    simulation_id=simulation_id,
                    source_record=unit["record"],
                ):
                    continue
            if time.monotonic() - last_resource_probe >= 1800.0:
                _append_resource_receipt(root)
                last_resource_probe = time.monotonic()
            raw_path = Path(str(unit["record"]["path"]))
            if not raw_path.is_absolute():
                raw_path = REPO / raw_path
            full_alm = np.asarray(hp.read_alm(str(raw_path)), dtype=np.complex128)
            assignment = injection_assignment(simulation_id)
            features = injected_unit_features(
                full_alm,
                design,
                templates[assignment.axis_index],
                assignment.amplitude,
                map2alm_iterations=int(
                    spec["injection_contract"]["transform"]["map2alm_iterations"]
                ),
            )
            _assert_baseline_match(
                features["baseline"],
                baseline[str(unit["unit_id"])],
                tolerance,
            )
            payload: dict[str, Any] = {
                "schema": CACHE_SCHEMA,
                "cache_key": identity["cache_key"],
                "simulation_id": simulation_id,
                "source_record": unit["record"],
                "assignment": _assignment_dict(simulation_id),
                **features,
                "raw_payload_rehashed": False,
            }
            payload["semantic_digest"] = _semantic_digest(payload)
            errors = _unit_errors(
                payload,
                identity=identity,
                simulation_id=simulation_id,
                source_record=unit["record"],
            )
            if errors:
                raise ActInbandModulationError("; ".join(errors))
            _atomic_json(path, payload)
            if position % 10 == 0 or position == 400:
                print(f"PR-204 injected release simulation {position}/400", flush=True)
        _append_resource_receipt(root)
    return identity


def build_card() -> dict[str, Any]:
    spec = _yaml(SPEC)
    pr177_spec = _yaml(PR177_SPEC)
    source = authenticate_sources(pr177_spec)
    identity = _identity(spec, source)
    root = CACHE_BASE / str(identity["cache_key"])
    simulations = [row for row in source["units"] if row["unit_kind"] == "release_simulation"]
    records = []
    for unit in simulations:
        simulation_id = int(str(unit["unit_id"]).split("-")[-1])
        path = _unit_path(root, simulation_id)
        if not path.is_file():
            raise ActInbandModulationError(f"missing injection unit {simulation_id}")
        payload = _json(path)
        errors = _unit_errors(
            payload,
            identity=identity,
            simulation_id=simulation_id,
            source_record=unit["record"],
        )
        if errors:
            raise ActInbandModulationError("; ".join(errors))
        records.append(
            {
                key: payload[key]
                for key in (
                    "simulation_id",
                    "assignment",
                    "baseline",
                    "injected",
                    "minimum_variance_factor",
                    "hard_reprojected_integer_support",
                    "map2alm_iterations",
                    "pixel_weights",
                    "semantic_digest",
                )
            }
        )
    analysis = analyze_injection_records(records)
    resources = _json(root / "resource_receipts.json")
    card: dict[str, Any] = {
        "schema": CARD_SCHEMA,
        "process_execution_status": "PASS_COMPLETE_400_PAIRED_INJECTIONS",
        "owner": "OBSSTAT",
        "implementation_scope": ["obsstat"],
        "claim_tier": "exploratory",
        "claim_level": {"scheme": "roadmap_rescue_v1", "level": "C1"},
        "scientific_artifact_mode": "standard_internal",
        "public_use": False,
        "transfer_source": "none",
        "readiness_state": "EVIDENCE_READY",
        "independence_gate": "OPEN",
        "scientific_result": None,
        "spec_sha256": _sha(SPEC),
        "input_hashes": {
            "docs/generated/pr177_act_inband_feature_card.json": _sha(
                PR177_FEATURE_CARD
            ),
            "docs/generated/pr177_deep_replay_receipt.json": _sha(
                REPO / "docs/generated/pr177_deep_replay_receipt.json"
            ),
            "docs/generated/pr177_result_card.json": _sha(
                REPO / "docs/generated/pr177_result_card.json"
            ),
            "docs/generated/pr152_inventory.json": _sha(
                REPO / "docs/generated/pr152_inventory.json"
            ),
            "docs/generated/pr152_availability_decision.json": _sha(
                REPO / "docs/generated/pr152_availability_decision.json"
            ),
            "htt/obsstat/act_inband_injection.py": _sha(MODULE),
            "scripts/act_inband_injection_card.py": _sha(Path(__file__).resolve()),
        },
        "cache_identity": identity,
        "analysis_support": {
            "inequality": "40 < L < 763",
            "integer_min": 41,
            "integer_max": 762,
            "endpoints_included": False,
            "coordinate_frame": "Equatorial",
        },
        "injection_stage": "post_reconstruction_strict_band_hard_reprojected",
        "raw_qe_reproduction": False,
        "unit_count": len(records),
        "records": records,
        "analysis": analysis,
        "resource_receipt_digests": [
            row["semantic_digest"] for row in resources["receipts"]
        ],
        "raw_payload_rehashed": False,
        "network_access": False,
        "sky_support_status": (
            "released_baseline_reconstructed_kappa_equatorial_MK_ge_0p99_core"
        ),
        "mask_status": (
            "authenticated_release_mask_with_raw_and_MK_squared_controlled_fits"
        ),
        "covariance_status": (
            "paired_release_simulation_response_and_split_empirical_coverage"
        ),
        "null_mock_status": (
            "exactly_400_authenticated_release_reconstructions"
        ),
        "caveats": [
            "The injection begins after the ACT quadratic estimator.",
            "The response is conditional on the selected released baseline reconstruction ensemble.",
            "This does not validate raw-QE filtering, RDN0, sky transfer, detection, isotropy, cosmological anisotropy, geometry, or family identification.",
        ],
        "generating_command": (
            "env OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 "
            "nice -n 15 ionice -c 3 venv/bin/python -B "
            "scripts/act_inband_injection_card.py --phase all"
        ),
    }
    card["semantic_digest"] = _semantic_digest(card)
    return card


def _validate_card(card: Mapping[str, Any]) -> None:
    spec = _yaml(SPEC)
    if card.get("schema") != CARD_SCHEMA:
        raise ActInbandModulationError("calibration card schema mismatch")
    if card.get("spec_sha256") != _sha(SPEC):
        raise ActInbandModulationError("calibration card spec drift")
    metadata_checks = {
        "calibration card claim tier drift": card.get("claim_tier")
        == "exploratory",
        "calibration card readiness drift": card.get("readiness_state")
        == "EVIDENCE_READY",
        "calibration card independence drift": card.get("independence_gate")
        == "OPEN",
        "calibration card public-use drift": card.get("public_use") is False,
        "calibration card promoted a scientific result": card.get(
            "scientific_result"
        )
        is None,
        "calibration card raw-QE drift": card.get("raw_qe_reproduction")
        is False,
        "calibration card stage drift": card.get("injection_stage")
        == "post_reconstruction_strict_band_hard_reprojected",
        "calibration card raw rehash drift": card.get("raw_payload_rehashed")
        is False,
        "calibration card network drift": card.get("network_access") is False,
    }
    failed = [
        message for message, passed in metadata_checks.items() if not passed
    ]
    if failed:
        raise ActInbandModulationError("; ".join(failed))
    for key, expected in spec["source_authorities"].items():
        if isinstance(expected, Mapping) and "path" in expected and "sha256" in expected:
            path = REPO / str(expected["path"])
            if _sha(path) != str(expected["sha256"]):
                raise ActInbandModulationError(f"source authority drift: {key}")
    records = card.get("records")
    if not isinstance(records, list) or len(records) != 400:
        raise ActInbandModulationError("calibration card must contain 400 records")
    recomputed = analyze_injection_records(records)
    if recomputed != card.get("analysis"):
        raise ActInbandModulationError("calibration analysis drift")
    expected_input_hashes = {
        "docs/generated/pr177_act_inband_feature_card.json": _sha(
            PR177_FEATURE_CARD
        ),
        "docs/generated/pr177_deep_replay_receipt.json": _sha(
            REPO / "docs/generated/pr177_deep_replay_receipt.json"
        ),
        "docs/generated/pr177_result_card.json": _sha(
            REPO / "docs/generated/pr177_result_card.json"
        ),
        "docs/generated/pr152_inventory.json": _sha(
            REPO / "docs/generated/pr152_inventory.json"
        ),
        "docs/generated/pr152_availability_decision.json": _sha(
            REPO / "docs/generated/pr152_availability_decision.json"
        ),
        "htt/obsstat/act_inband_injection.py": _sha(MODULE),
        "scripts/act_inband_injection_card.py": _sha(
            Path(__file__).resolve()
        ),
    }
    if card.get("input_hashes") != expected_input_hashes:
        raise ActInbandModulationError("calibration input-hash map drift")
    source = authenticate_sources(_yaml(PR177_SPEC))
    identity = _identity(spec, source)
    if card.get("cache_identity") != identity:
        raise ActInbandModulationError("calibration cache identity drift")
    root = CACHE_BASE / str(identity["cache_key"])
    resources = _json(root / "resource_receipts.json")
    resource_rows = resources.get("receipts")
    if not isinstance(resource_rows, list) or len(resource_rows) < 2:
        raise ActInbandModulationError("resource receipt history is incomplete")
    for index, receipt in enumerate(resource_rows):
        if not isinstance(receipt, Mapping):
            raise ActInbandModulationError(
                f"resource receipt {index} is malformed"
            )
        errors = resource_receipt_errors(receipt)
        if errors:
            raise ActInbandModulationError(
                f"resource receipt {index}: {'; '.join(errors)}"
            )
    if resources.get("semantic_digest") != _semantic_digest(resources):
        raise ActInbandModulationError("resource receipt history digest mismatch")
    if card.get("resource_receipt_digests") != [
        row["semantic_digest"] for row in resource_rows
    ]:
        raise ActInbandModulationError("resource receipt binding drift")
    source_records = {
        row["unit_id"]: row["record"] for row in source["units"]
    }
    for record in records:
        simulation_id = int(record["simulation_id"])
        cached = _json(_unit_path(root, simulation_id))
        expected_record = source_records[f"sim-{simulation_id:04d}"]
        errors = _unit_errors(
            cached,
            identity=identity,
            simulation_id=simulation_id,
            source_record=expected_record,
        )
        if errors:
            raise ActInbandModulationError("; ".join(errors))
        selected = {
            key: cached[key]
            for key in (
                "simulation_id",
                "assignment",
                "baseline",
                "injected",
                "minimum_variance_factor",
                "hard_reprojected_integer_support",
                "map2alm_iterations",
                "pixel_weights",
                "semantic_digest",
            )
        }
        if selected != record:
            raise ActInbandModulationError(
                f"tracked/cache unit mismatch: {simulation_id}"
            )
    if card.get("semantic_digest") != _semantic_digest(card):
        raise ActInbandModulationError("calibration card semantic digest mismatch")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--phase",
        choices=("extract", "aggregate", "check", "all"),
        required=True,
    )
    args = parser.parse_args(argv)
    if args.phase in {"extract", "all"}:
        extract()
    if args.phase in {"aggregate", "all"}:
        card = build_card()
        _atomic_json(OUT, card)
        print(f"wrote {OUT.name}")
    if args.phase == "check":
        _validate_card(_json(OUT))
        print(json.dumps({"ok": True, "read_only": True}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
