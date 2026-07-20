#!/usr/bin/env python3
"""Build and verify the PR-177 ACT strict-in-band result pack."""
from __future__ import annotations

import argparse
import copy
import hashlib
import json
import sys
from pathlib import Path
from typing import Any, Callable, Mapping

import numpy as np
import yaml


REPO = Path(__file__).resolve().parents[2]
for root in (REPO, REPO / "htt"):
    if str(root) not in sys.path:
        sys.path.insert(0, str(root))

from obsstat.act_inband_modulation import (  # noqa: E402
    ALLOWED_SCIENTIFIC_RESULTS,
    BLOCKED,
    ActInbandModulationError,
    canonical_sha256,
    delete_simulation_rank_replicates,
    full_statistics,
    rank_resolution_certificate,
    semantic_digest,
    terminal_result,
)
from scripts.act_inband_modulation_card import (  # noqa: E402
    DEEP_REPLAY_SCHEMA,
    authenticate_sources,
    build_cache_identity,
    resource_receipt_errors,
    serialized_payload_sha256,
    unit_cache_errors,
)


SPEC_PATH = REPO / "docs/research_program/long_horizon_rescue/pr177_spec.yaml"
MODULE_PATH = REPO / "htt/obsstat/act_inband_modulation.py"
HEAVY_PATH = REPO / "scripts/act_inband_modulation_card.py"
SCRIPT_PATH = Path(__file__).resolve()
FEATURE_PATH = REPO / "docs/generated/pr177_act_inband_feature_card.json"
DEEP_REPLAY_PATH = REPO / "docs/generated/pr177_deep_replay_receipt.json"
OUTPUTS = {
    "authority": REPO / "docs/generated/pr177_input_authority_receipt.json",
    "result": REPO / "docs/generated/pr177_act_modulation_result.json",
    "mask": REPO / "docs/generated/pr177_mask_control.json",
    "mc": REPO / "docs/generated/pr177_mc_resolution.json",
    "mutation": REPO / "docs/generated/pr177_mutation_report.json",
    "card": REPO / "docs/generated/pr177_result_card.json",
    "manifest": REPO / "docs/generated/pr177_artifact_manifest.json",
}

EXPECTED_SUPPORT = {
    "inequality": "40 < L < 763",
    "integer_min": 41,
    "integer_max": 762,
    "integer_count": 722,
    "endpoints_40_and_763_included": False,
    "coordinate_frame": "Equatorial",
}


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


def source_authority_errors(
    spec: Mapping[str, Any], source: Mapping[str, Any]
) -> list[str]:
    """Bind a reconstructed source bundle back to every frozen PR-177 pin."""

    authorities = spec["source_authorities"]
    expected_small = {
        str(authorities[name]["path"]): _normalize_hash(authorities[name]["sha256"])
        for name in (
            "pr152_artifact_manifest",
            "pr152_release_card",
            "acquisition_manifest",
            "release_readme",
        )
    }
    checks = {
        "frozen small-authority hash set mismatch": source.get("small_authority_hashes")
        == expected_small,
        "frozen embedded manifest pin mismatch": source.get(
            "embedded_ordered_manifest_sha256"
        )
        == _normalize_hash(
            authorities["pr152_release_card"]["embedded_ordered_manifest_sha256"]
        ),
        "frozen raw-record root mismatch": source.get("raw_records_only_sha256")
        == _normalize_hash(
            authorities["pr152_release_card"]["raw_records_only_sha256"]
        ),
        "raw authority count mismatch": source.get("raw_payload_count") == 401,
        "raw authority stat-check count mismatch": source.get(
            "raw_payload_stat_checks_performed"
        )
        == 401,
        "release-context stat-check count mismatch": source.get(
            "mask_and_filter_stat_checks_performed"
        )
        == 2,
        "source authority claims raw hashing": source.get(
            "raw_payload_hashing_performed_by_pr177"
        )
        is False,
    }
    errors = [message for message, passed in checks.items() if not passed]
    units = source.get("units")
    expected_ids = ["data", *[f"sim-{index:04d}" for index in range(1, 401)]]
    if not isinstance(units, list) or len(units) != 401:
        errors.append("source authority unit inventory mismatch")
    elif [row.get("unit_id") for row in units if isinstance(row, Mapping)] != expected_ids:
        errors.append("source authority unit order mismatch")
    return errors


def _expected_units_from_pr152(
    spec: Mapping[str, Any],
) -> tuple[list[dict[str, Any]], str, dict[str, Any]]:
    source = authenticate_sources(spec)
    errors = source_authority_errors(spec, source)
    if errors:
        raise ActInbandModulationError("; ".join(errors))
    records = [dict(row["record"]) for row in source["units"]]
    return records, str(source["raw_records_only_sha256"]), source


def persisted_resource_receipt_errors(receipt: Mapping[str, Any]) -> list[str]:
    """Require the digest field on every persisted resource receipt."""

    errors = resource_receipt_errors(receipt)
    if receipt.get("semantic_digest") != semantic_digest(receipt):
        message = "persisted resource receipt digest missing or invalid"
        if message not in errors:
            errors.append(message)
    return errors


def _cache_unit(card: Mapping[str, Any], unit_id: str) -> dict[str, Any]:
    cache_key = str(card["cache_identity"]["cache_key"])
    path = REPO / "workdir/pr177_act_dr6_inband" / cache_key / "units" / f"{unit_id}.json"
    return _json(path)


def _deep_replay_errors(
    card: Mapping[str, Any],
    expected_identity: Mapping[str, Any],
    *,
    receipt: Mapping[str, Any] | None = None,
) -> list[str]:
    errors: list[str] = []
    if receipt is None:
        try:
            receipt = _json(DEEP_REPLAY_PATH)
        except (OSError, ValueError) as exc:
            return [f"authoritative deep replay receipt unavailable: {exc}"]
    checks = {
        "deep replay schema mismatch": receipt.get("schema") == DEEP_REPLAY_SCHEMA,
        "deep replay process status mismatch": receipt.get("process_execution_status")
        == "PASS_AUTHORITATIVE_401_UNIT_FEATURE_REPLAY",
        "deep replay scientific status mismatch": receipt.get("scientific_status")
        == "NOT_EVALUATED_PROVENANCE_REPLAY_ONLY",
        "deep replay semantic digest mismatch": receipt.get("semantic_digest") == semantic_digest(receipt),
        "deep replay cache identity mismatch": receipt.get("cache_identity") == expected_identity,
        "deep replay cache key mismatch": receipt.get("cache_key") == expected_identity["cache_key"],
        "deep replay feature-card hash mismatch": receipt.get("feature_card_sha256")
        == serialized_payload_sha256(card),
        "deep replay feature-card semantic digest mismatch": receipt.get("feature_card_semantic_digest")
        == card.get("semantic_digest"),
        "deep replay feature-card path mismatch": receipt.get("feature_card_path")
        == str(FEATURE_PATH.relative_to(REPO)),
        "deep replay config hash mismatch": receipt.get("config_hash")
        == expected_identity["config_hash"],
        "deep replay complete input binding mismatch": receipt.get("input_hashes")
        == {
            **dict(card.get("input_hashes", {})),
            str(FEATURE_PATH.relative_to(REPO)): serialized_payload_sha256(card),
        },
        "deep replay raw root mismatch": receipt.get("raw_records_only_sha256")
        == expected_identity["raw_records_only_sha256"],
        "deep replay raw-unit count mismatch": receipt.get("raw_units_opened") == 401,
        "deep replay raw stat-check count mismatch": receipt.get(
            "raw_payload_stat_checks"
        )
        == 401,
        "deep replay performed raw hashing": receipt.get("raw_payloads_hashed") == 0,
        "deep replay feature count mismatch": receipt.get("feature_units_replayed") == 401,
        "deep replay reports feature mismatch": receipt.get("feature_mismatch_count") == 0
        and receipt.get("features_match_raw_authority") is True,
        "deep replay was not sequential": receipt.get("single_sequential_reader") is True,
        "deep replay runtime identity mismatch": receipt.get("runtime_identity")
        == expected_identity["runtime_identity"],
        "deep replay strict support mismatch": receipt.get("analysis_support")
        == EXPECTED_SUPPORT,
        "deep replay claim metadata mismatch": receipt.get("owner") == "OBSSTAT"
        and receipt.get("claim_tier") == "conditional"
        and receipt.get("public_use") is False
        and receipt.get("transfer_source") == "none"
        and receipt.get("scientific_result") is None,
    }
    errors.extend(message for message, passed in checks.items() if not passed)
    resource_receipts = receipt.get("resource_receipts")
    if not isinstance(resource_receipts, list) or not resource_receipts:
        errors.append("deep replay resource receipts missing")
    else:
        for index, resource in enumerate(resource_receipts):
            if not isinstance(resource, Mapping):
                errors.append(f"deep replay resource receipt {index} malformed")
            else:
                errors.extend(
                    f"deep replay resource receipt {index}: {message}"
                    for message in persisted_resource_receipt_errors(resource)
                )
    return errors


def validate_feature_card(
    card: Mapping[str, Any],
    spec: Mapping[str, Any],
    *,
    cache_loader: Callable[[Mapping[str, Any], str], dict[str, Any]] = _cache_unit,
    deep_replay_receipt: Mapping[str, Any] | None = None,
) -> list[str]:
    """Validate the feature card against frozen sources and cache primitives."""

    errors: list[str] = []
    if card.get("schema") != "htt.pr177.act_inband_feature_card.v1":
        errors.append("feature-card schema mismatch")
    if card.get("semantic_digest") != semantic_digest(card):
        errors.append("feature-card semantic digest mismatch")
    if card.get("process_execution_status") != "PASS_COMPLETE_401_UNIT_EXTRACTION":
        errors.append("feature extraction process status is not complete")
    if card.get("scientific_result") is not None or card.get("scientific_status") != "NOT_EVALUATED_FEATURE_EXTRACTION_ONLY":
        errors.append("feature extraction card promoted a scientific result")
    expected_local = {
        str(path.relative_to(REPO)): _sha(path)
        for path in (SPEC_PATH, MODULE_PATH, HEAVY_PATH)
    }
    if card.get("config_hash") != expected_local[str(SPEC_PATH.relative_to(REPO))]:
        errors.append("feature-card config hash drift")
    input_hashes = card.get("input_hashes")
    if not isinstance(input_hashes, Mapping):
        errors.append("feature-card input hashes missing")
        input_hashes = {}
    for path, digest in expected_local.items():
        if input_hashes.get(path) != digest:
            errors.append(f"feature-card local hash drift: {path}")
    support = card.get("analysis_support")
    if not isinstance(support, Mapping) or dict(support) != EXPECTED_SUPPORT:
        errors.append("strict integer support receipt mismatch")
    if (
        card.get("owner") != "OBSSTAT"
        or card.get("claim_tier") != "conditional"
        or card.get("public_use") is not False
        or card.get("transfer_source") != "none"
    ):
        errors.append("feature-card claim metadata drift")
    if card.get("raw_payload_rehashed_by_pr177") is not False:
        errors.append("feature-card claims PR-177 raw rehashing")
    authentication = card.get("input_authentication")
    if not isinstance(authentication, Mapping):
        errors.append("input authentication receipt missing")
        authentication = {}
    try:
        source_records, raw_root, source_authority = _expected_units_from_pr152(spec)
    except (OSError, ValueError, KeyError, TypeError) as exc:
        errors.append(f"PR-152 authority reconstruction failed: {exc}")
        source_records, raw_root, source_authority = [], "", {}
    if authentication.get("raw_records_only_sha256") != raw_root:
        errors.append("raw-record authority root mismatch")
    expected_authentication = {
        key: value for key, value in source_authority.items() if key != "units"
    }
    if authentication != expected_authentication:
        errors.append("feature-card source authentication differs from frozen reconstruction")
    expected_input_hashes = {
        **expected_local,
        **dict(source_authority.get("small_authority_hashes", {})),
        "embedded:pr152_ordered_manifest": source_authority.get(
            "embedded_ordered_manifest_sha256"
        ),
        "embedded:pr177_raw_records_only_root": raw_root,
        "raw:observed_alm": _normalize_hash(
            spec["selected_release_bundle"]["observed_alm"]["sha256"]
        ),
        "raw:ordered_400_simulation_root": raw_root,
        "raw:release_mask": _normalize_hash(
            spec["selected_release_bundle"]["mask"]["sha256"]
        ),
        "raw:release_filter_context": _normalize_hash(
            spec["selected_release_bundle"]["release_filter_context"]["sha256"]
        ),
    }
    if input_hashes != expected_input_hashes:
        errors.append("feature-card complete input-hash map differs from frozen reconstruction")
    try:
        expected_identity = build_cache_identity(
            spec, {"raw_records_only_sha256": raw_root}
        )
    except (OSError, ValueError, KeyError, TypeError) as exc:
        errors.append(f"cache identity reconstruction failed: {exc}")
        expected_identity = {}
    if card.get("cache_identity") != expected_identity:
        errors.append("cache identity does not match frozen reconstruction")
    if expected_identity:
        material = dict(expected_identity)
        declared_key = material.pop("cache_key", None)
        if declared_key != canonical_sha256(material):
            errors.append("cache identity canonical key mismatch")
    units = card.get("units")
    if not isinstance(units, list) or len(units) != 401:
        errors.append("feature card must retain exactly 401 units")
        units = []
    expected_ids = ["data", *[f"sim-{index:04d}" for index in range(1, 401)]]
    actual_ids = [str(row.get("unit_id")) for row in units if isinstance(row, Mapping)]
    if actual_ids != expected_ids:
        errors.append("feature unit order or identity drift")
    if card.get("unit_count") != 401 or card.get("observed_unit_count") != 1 or card.get("release_simulation_count") != 400:
        errors.append("feature unit summary counts drift")
    if card.get("identical_pipeline") is not True or card.get("raw_workers") != 1 or card.get("sequential_reader") is not True:
        errors.append("identical/sequential pipeline receipt failed")
    resource_history = card.get("extraction_resource_receipt")
    if not isinstance(resource_history, Mapping):
        errors.append("extraction resource history missing")
    else:
        if resource_history.get("semantic_digest") != semantic_digest(resource_history):
            errors.append("extraction resource history digest mismatch")
        if expected_identity and resource_history.get("cache_key") != expected_identity["cache_key"]:
            errors.append("extraction resource history cache key mismatch")
        invocations = resource_history.get("invocations")
        if not isinstance(invocations, list) or not invocations:
            errors.append("extraction resource invocations missing")
        else:
            for index, resource in enumerate(invocations):
                if not isinstance(resource, Mapping):
                    errors.append(f"extraction resource invocation {index} malformed")
                else:
                    errors.extend(
                        f"extraction resource invocation {index}: {message}"
                        for message in persisted_resource_receipt_errors(resource)
                    )
            if resource_history.get("latest_receipt_digest") != invocations[-1].get("semantic_digest"):
                errors.append("extraction latest resource digest mismatch")
    mask_design = card.get("mask_design")
    expected_core = spec["estimator"]["pixelization"]["pre_result_mask_receipt"]["core_pixels"]
    if not isinstance(mask_design, Mapping) or mask_design.get("core_pixel_count") != expected_core:
        errors.append("mask-design core receipt mismatch")

    for index, row in enumerate(units):
        if not isinstance(row, Mapping):
            errors.append(f"unit {index} is not a mapping")
            continue
        feature = row.get("feature")
        if not isinstance(feature, Mapping):
            errors.append(f"unit {index} feature missing")
            continue
        try:
            q_raw = np.asarray(feature["q_raw"], dtype=float)
            q_controlled = np.asarray(feature["q_controlled"], dtype=float)
            mask_change = float(feature["mask_change"])
        except (KeyError, TypeError, ValueError):
            errors.append(f"unit {index} feature malformed")
            continue
        if q_raw.shape != (5,) or q_controlled.shape != (5,) or not np.all(np.isfinite(q_raw)) or not np.all(np.isfinite(q_controlled)):
            errors.append(f"unit {index} quadrupole malformed")
        expected_change = float(np.sum((q_raw - q_controlled) ** 2))
        if not np.isfinite(mask_change) or not np.isclose(mask_change, expected_change, rtol=0.0, atol=1.0e-24):
            errors.append(f"unit {index} mask-change arithmetic mismatch")
        if index < len(source_records):
            source = source_records[index]
            if _normalize_hash(row.get("source_sha256")) != _normalize_hash(source["sha256"]):
                errors.append(f"unit {index} source hash mismatch")
            if int(row.get("source_size_bytes", -1)) != int(source["size_bytes"]):
                errors.append(f"unit {index} source size mismatch")
        try:
            cache = cache_loader(card, str(row["unit_id"]))
            if expected_identity and index < len(source_records):
                cache_errors = unit_cache_errors(
                    cache,
                    identity=expected_identity,
                    unit={
                        "unit_id": expected_ids[index],
                        "unit_kind": "observed" if index == 0 else "release_simulation",
                        "record": source_records[index],
                    },
                )
                errors.extend(f"unit {index} cache: {message}" for message in cache_errors)
            if row.get("unit_cache_semantic_digest") != cache.get("semantic_digest"):
                errors.append(f"unit {index} cache binding mismatch")
            if feature != cache.get("feature"):
                errors.append(f"unit {index} feature/cache mismatch")
        except (OSError, ValueError, KeyError, TypeError) as exc:
            errors.append(f"unit {index} cache validation failed: {exc}")
    if expected_identity:
        errors.extend(
            _deep_replay_errors(
                card,
                expected_identity,
                receipt=deep_replay_receipt,
            )
        )
    return errors


def _common_metadata(spec: Mapping[str, Any], feature_card: Mapping[str, Any]) -> dict[str, Any]:
    local = {
        str(path.relative_to(REPO)): _sha(path)
        for path in (
            SPEC_PATH,
            MODULE_PATH,
            HEAVY_PATH,
            SCRIPT_PATH,
            FEATURE_PATH,
            DEEP_REPLAY_PATH,
        )
    }
    content_receipt = canonical_sha256(
        {"local": local, "feature_semantic_digest": feature_card["semantic_digest"]}
    )
    baseline = str(spec["baseline_commit"])
    return {
        "owner": "OBSSTAT",
        "implementation_scope": ["obsstat"],
        "claim_tier": "conditional",
        "claim_level": {"scheme": "roadmap_rescue_v1", "level": "C3"},
        "scientific_artifact_mode": "standard_internal",
        "public_use": False,
        "transfer_source": "none",
        "config_hash": local[str(SPEC_PATH.relative_to(REPO))],
        "input_hashes": local,
        "sky_support_status": "released_baseline_reconstructed_kappa_equatorial_MK_ge_0p99_core_not_independently_reprocessed",
        "mask_status": "authenticated_release_mask_with_MK_squared_registered_nuisance_control",
        "covariance_status": "observation_inclusive_5d_leave_one_out_empirical_covariance_exactly_400_release_simulations",
        "null_mock_status": "exactly_400_authenticated_release_reconstructed_simulations_conditional_exchangeability",
        "generating_command": (
            "env OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 "
            "MPLCONFIGDIR=/tmp/mpl-pr177 PYTHONPATH=htt venv/bin/python -B "
            "scripts/codex_harness/run_pr177_act_dr6_inband_modulation.py --write"
        ),
        "git_commit": baseline,
        "worktree_content_receipt": content_receipt,
        "worktree_state": f"{baseline}+content-sha256:{content_receipt}",
        "runtime_environment": feature_card["runtime_environment"],
        "caveats": [
            "The ranks are conditional on the selected ACT DR6 baseline released reconstruction and exactly 400 released reconstructions.",
            "Joint exchangeability is an explicit conditional assumption, not release validation.",
            "The registered M_K-squared control is bounded and cannot rule out all mask, filter, reconstruction, foreground, or noise effects.",
            "This is not raw-QE reproduction, a detection, cosmological-anisotropy attribution, transfer validation, geometry identification, or family identification.",
            "Numerical-resolution intervals describe the finite release-rank functional, not physical uncertainty or external coverage.",
        ],
    }


def _certificate(full: Mapping[str, Any], deletes: list[dict[str, Any]], key: str) -> dict[str, Any]:
    return rank_resolution_certificate(
        full_rank=float(full["rank"]),
        delete_ranks=[float(row[key]) for row in deletes],
    )


def _science_payloads(spec: Mapping[str, Any], feature_card: Mapping[str, Any]) -> dict[str, dict[str, Any]]:
    units = feature_card["units"]
    q_raw = [row["feature"]["q_raw"] for row in units]
    q_controlled = [row["feature"]["q_controlled"] for row in units]
    mask_change = [row["feature"]["mask_change"] for row in units]
    maximum_condition = float(spec["scoring"]["covariance_gate"]["maximum_condition_number"])
    full = full_statistics(
        q_raw,
        q_controlled,
        mask_change,
        maximum_condition_number=maximum_condition,
    )
    delete = delete_simulation_rank_replicates(
        q_raw,
        q_controlled,
        mask_change,
        maximum_condition_number=maximum_condition,
    )
    rows = delete["replicates"]
    certificates = {
        "raw": _certificate(full["raw"], rows, "raw_rank"),
        "controlled": _certificate(full["controlled"], rows, "controlled_rank"),
        "mask_change": _certificate(full["mask_change"], rows, "mask_change_rank"),
    }
    terminal = terminal_result(
        controlled=certificates["controlled"],
        raw=certificates["raw"],
        mask_change=certificates["mask_change"],
        eligibility_passed=True,
    )
    metadata = _common_metadata(spec, feature_card)
    authority = {
        "schema": "htt.pr177.input_authority_receipt.v1",
        **metadata,
        "process_execution_status": "PASS",
        "scientific_result": None,
        "source_authentication": feature_card["input_authentication"],
        "analysis_support": feature_card["analysis_support"],
        "mask_design": feature_card["mask_design"],
        "feature_card_sha256": _sha(FEATURE_PATH),
        "raw_payload_rehashed_by_pr177": False,
    }
    authority["semantic_digest"] = semantic_digest(authority)
    result = {
        "schema": "htt.pr177.act_modulation_result.v1",
        **metadata,
        "process_execution_status": "PASS_REPRODUCIBLE_RESULT",
        **terminal,
        "analysis_support": feature_card["analysis_support"],
        "estimand": "single_5d_quadrupolar_fractional_variance_modulation",
        "full_statistics": full,
        "resolution_certificates": certificates,
        "lineage_status": delete["lineage_status"],
        "release_simulation_count": 400,
        "raw_qe_reproduced": False,
        "physical_interpretation": "not_evaluated",
    }
    result["semantic_digest"] = semantic_digest(result)
    mask = {
        "schema": "htt.pr177.mask_control.v1",
        **metadata,
        "process_execution_status": "PASS",
        "scientific_result": terminal["scientific_result"],
        "scientific_status": terminal["scientific_status"],
        "analysis_support": feature_card["analysis_support"],
        "mask_nuisance": "M_K_squared_centered_on_M_K_ge_0p99_core",
        "raw_rank": full["raw"],
        "controlled_rank": full["controlled"],
        "mask_change_rank": full["mask_change"],
        "raw_resolution": certificates["raw"],
        "controlled_resolution": certificates["controlled"],
        "mask_change_resolution": certificates["mask_change"],
        "candidate_survives_registered_mask_control": terminal["scientific_result"] == ALLOWED_SCIENTIFIC_RESULTS[0],
        "control_scope": "bounded_reproduced_or_not_reproduced_by_this_control_no_causal_attribution",
    }
    mask["semantic_digest"] = semantic_digest(mask)
    mc = {
        "schema": "htt.pr177.mc_resolution.v1",
        **metadata,
        "process_execution_status": "PASS_COMPLETE_DELETE_SIMULATION_RECOMPUTATION",
        "scientific_result": terminal["scientific_result"],
        "scientific_status": terminal["scientific_status"],
        "analysis_support": feature_card["analysis_support"],
        "replicate_lineage": {key: value for key, value in delete.items() if key != "replicates"},
        "delete_replicates": rows,
        "certificates": certificates,
        "finite_rank_support_full": 1.0 / 401.0,
        "finite_rank_support_delete": 1.0 / 400.0,
        "iid_binomial_interval_used": False,
        "gaussian_sigma_emitted": False,
        "physical_interpretation": "not_evaluated",
    }
    mc["semantic_digest"] = semantic_digest(mc)
    card = {
        "schema": "htt.pr177.result_card.v1",
        **metadata,
        "process_execution_status": "PASS_REPRODUCIBLE_RESULT",
        **terminal,
        "headline": terminal["scientific_result"],
        "analysis_support": feature_card["analysis_support"],
        "support": "strict 40 < L < 763 (integer 41..762)",
        "observed_and_release_simulation_pipeline_identical": True,
        "release_simulation_count": 400,
        "rank_summary": {
            key: {
                "rank": full[key]["rank"],
                "rank_fraction": full[key]["rank_fraction"],
                "guard_interval": certificates[key]["guard_interval"],
                "relation_to_alpha": certificates[key]["relation_to_alpha"],
            }
            for key in ("raw", "controlled", "mask_change")
        },
        "mask_control_scope": "registered_MK_squared_sensitivity_only",
        "raw_qe_reproduction": False,
        "detection_claim": False,
        "family_identification": False,
    }
    card["semantic_digest"] = semantic_digest(card)
    return {"authority": authority, "result": result, "mask": mask, "mc": mc, "card": card}


def _reseal(payload: dict[str, Any]) -> None:
    payload["semantic_digest"] = semantic_digest(payload)


def _mutate_latest_resource(
    card: dict[str, Any], updates: Mapping[str, Any]
) -> None:
    history = card["extraction_resource_receipt"]
    latest = history["invocations"][-1]
    latest.update(updates)
    latest["semantic_digest"] = semantic_digest(latest)
    history["latest_receipt_digest"] = latest["semantic_digest"]
    history["semantic_digest"] = semantic_digest(history)


def result_support_errors(
    payloads: Mapping[str, Mapping[str, Any]],
    expected_support: Mapping[str, Any],
) -> list[str]:
    """Require one exact support object on every result-bearing artifact."""

    errors: list[str] = []
    for name, payload in payloads.items():
        if payload.get("scientific_result") is not None and payload.get(
            "analysis_support"
        ) != expected_support:
            errors.append(f"{name} result artifact strict support mismatch")
    return errors


def build_mutation_report(
    card: Mapping[str, Any],
    spec: Mapping[str, Any],
    metadata: Mapping[str, Any],
    science_outputs: Mapping[str, Mapping[str, Any]],
) -> dict[str, Any]:
    mutations: list[tuple[str, Any]] = [
        ("include_L40", lambda value: value["analysis_support"].update({"integer_min": 40, "endpoints_40_and_763_included": True})),
        ("drop_sim_0400", lambda value: value["units"].pop()),
        ("duplicate_sim_identity", lambda value: value["units"][2].update({"unit_id": "sim-0001"})),
        ("replace_source_hash", lambda value: value["units"][1].update({"source_sha256": "0" * 64})),
        ("mutate_q_raw", lambda value: value["units"][0]["feature"]["q_raw"].__setitem__(0, value["units"][0]["feature"]["q_raw"][0] + 1.0)),
        ("forge_mask_change", lambda value: value["units"][0]["feature"].update({"mask_change": 0.0})),
        ("change_config_hash", lambda value: value.update({"config_hash": "0" * 64})),
        ("change_raw_root", lambda value: value["input_authentication"].update({"raw_records_only_sha256": "0" * 64})),
        (
            "change_feature_pr152_input_hash",
            lambda value: value["input_hashes"].update(
                {
                    str(spec["source_authorities"]["pr152_release_card"]["path"]): "0"
                    * 64
                }
            ),
        ),
        ("change_cache_identity_raw_root", lambda value: value["cache_identity"].update({"raw_records_only_sha256": "0" * 64})),
        ("change_cache_runtime", lambda value: value["cache_identity"]["runtime_identity"].update({"healpy": "forged"})),
        ("forge_cache_key", lambda value: value["cache_identity"].update({"cache_key": "0" * 64})),
        ("promote_feature_to_candidate", lambda value: value.update({"scientific_result": ALLOWED_SCIENTIFIC_RESULTS[0]})),
        ("claim_raw_rehash", lambda value: value.update({"raw_payload_rehashed_by_pr177": True})),
        ("public_use_promotion", lambda value: value.update({"public_use": True})),
        ("transfer_promotion", lambda value: value.update({"transfer_source": "native"})),
        (
            "low_disk_resealed_resource",
            lambda value: _mutate_latest_resource(
                value,
                {
                    "free_gib": 299.0,
                    "free_gib_at_least_300": False,
                    "eligible": False,
                },
            ),
        ),
        (
            "stale_log_resealed_resource",
            lambda value: _mutate_latest_resource(
                value,
                {
                    "pr151_log_age_seconds": 1800.0,
                    "pr151_log_fresh_under_1800_seconds": False,
                    "eligible": False,
                },
            ),
        ),
        ("forge_resource_eligible", lambda value: value["extraction_resource_receipt"]["invocations"][-1].update({"eligible": False})),
        ("replace_cache_digest", lambda value: value["units"][0].update({"unit_cache_semantic_digest": "0" * 64})),
    ]
    rows: list[dict[str, Any]] = []
    for mutation_id, mutate in mutations:
        candidate = copy.deepcopy(card)
        mutate(candidate)
        _reseal(candidate)
        errors = validate_feature_card(candidate, spec)
        rows.append(
            {
                "mutation_id": mutation_id,
                "executed": True,
                "killed": bool(errors),
                "first_error": errors[0] if errors else None,
            }
        )

    coordinated_card = copy.deepcopy(card)
    forged_cache = copy.deepcopy(_cache_unit(card, "data"))
    forged_feature = copy.deepcopy(coordinated_card["units"][0]["feature"])
    forged_feature["q_raw"][0] += 1.0e-6
    raw = np.asarray(forged_feature["q_raw"], dtype=float)
    controlled = np.asarray(forged_feature["q_controlled"], dtype=float)
    forged_feature["mask_change"] = float(np.sum((raw - controlled) ** 2))
    forged_cache["feature"] = forged_feature
    _reseal(forged_cache)
    coordinated_card["units"][0]["feature"] = copy.deepcopy(forged_feature)
    coordinated_card["units"][0]["unit_cache_semantic_digest"] = forged_cache[
        "semantic_digest"
    ]
    _reseal(coordinated_card)

    def coordinated_loader(value: Mapping[str, Any], unit_id: str) -> dict[str, Any]:
        if unit_id == "data":
            return copy.deepcopy(forged_cache)
        return _cache_unit(value, unit_id)

    coordinated_errors = validate_feature_card(
        coordinated_card,
        spec,
        cache_loader=coordinated_loader,
    )
    rows.append(
        {
            "mutation_id": "coordinated_card_and_cache_feature_reseal",
            "executed": True,
            "killed": bool(coordinated_errors),
            "first_error": coordinated_errors[0] if coordinated_errors else None,
            "required_independent_falsifier": "authoritative_deep_replay_receipt",
        }
    )

    support_probes: list[tuple[str, str, dict[str, Any], Any]] = [
        (
            "drop_mask_analysis_support",
            "mask",
            copy.deepcopy(science_outputs["mask"]),
            lambda value: value.pop("analysis_support", None),
        ),
        (
            "drift_mc_analysis_support",
            "mc",
            copy.deepcopy(science_outputs["mc"]),
            lambda value: value["analysis_support"].update({"integer_min": 40}),
        ),
        (
            "drop_manifest_analysis_support",
            "manifest",
            {
                "scientific_result": science_outputs["card"]["scientific_result"],
                "analysis_support": copy.deepcopy(EXPECTED_SUPPORT),
            },
            lambda value: value.pop("analysis_support", None),
        ),
    ]
    for mutation_id, name, candidate, mutate in support_probes:
        mutate(candidate)
        errors = result_support_errors({name: candidate}, EXPECTED_SUPPORT)
        rows.append(
            {
                "mutation_id": mutation_id,
                "executed": True,
                "killed": bool(errors),
                "first_error": errors[0] if errors else None,
            }
        )

    source = authenticate_sources(spec)
    source_probes: list[tuple[str, Any]] = [
        (
            "change_frozen_source_raw_root",
            lambda value: value.update({"raw_records_only_sha256": "0" * 64}),
        ),
        (
            "change_frozen_small_authority_hash",
            lambda value: value["small_authority_hashes"].update(
                {str(spec["source_authorities"]["pr152_release_card"]["path"]): "0" * 64}
            ),
        ),
    ]
    for mutation_id, mutate in source_probes:
        candidate = copy.deepcopy(source)
        mutate(candidate)
        errors = source_authority_errors(spec, candidate)
        rows.append(
            {
                "mutation_id": mutation_id,
                "executed": True,
                "killed": bool(errors),
                "first_error": errors[0] if errors else None,
            }
        )

    deep_probes: list[tuple[str, Any]] = [
        (
            "deep_replay_failed_process_status",
            lambda value: value.update({"process_execution_status": "FAIL"}),
        ),
        (
            "deep_replay_zero_raw_stat_checks",
            lambda value: value.update({"raw_payload_stat_checks": 0}),
        ),
        (
            "deep_replay_missing_resource_digest",
            lambda value: value["resource_receipts"][0].pop(
                "semantic_digest", None
            ),
        ),
        (
            "deep_replay_changed_pr152_input_hash",
            lambda value: value["input_hashes"].update(
                {
                    str(spec["source_authorities"]["pr152_release_card"]["path"]): "0"
                    * 64
                }
            ),
        ),
    ]
    deep = _json(DEEP_REPLAY_PATH)
    for mutation_id, mutate in deep_probes:
        candidate = copy.deepcopy(deep)
        mutate(candidate)
        _reseal(candidate)
        errors = validate_feature_card(
            card,
            spec,
            deep_replay_receipt=candidate,
        )
        rows.append(
            {
                "mutation_id": mutation_id,
                "executed": True,
                "killed": bool(errors),
                "first_error": errors[0] if errors else None,
            }
        )
    report: dict[str, Any] = {
        "schema": "htt.pr177.mutation_report.v1",
        **metadata,
        "process_execution_status": "PASS" if all(row["killed"] for row in rows) else "FAIL",
        "scientific_result": None,
        "registered_count": len(rows),
        "executed_count": sum(row["executed"] for row in rows),
        "killed_count": sum(row["killed"] for row in rows),
        "survivors": [row["mutation_id"] for row in rows if not row["killed"]],
        "mutations": rows,
    }
    report["semantic_digest"] = semantic_digest(report)
    return report


def _text(payload: Mapping[str, object]) -> str:
    return json.dumps(payload, indent=2, sort_keys=True) + "\n"


def build_outputs(spec: Mapping[str, Any], feature_card: Mapping[str, Any]) -> dict[str, dict[str, Any]]:
    errors = validate_feature_card(feature_card, spec)
    if errors:
        raise ActInbandModulationError("; ".join(errors[:10]))
    outputs = _science_payloads(spec, feature_card)
    metadata = _common_metadata(spec, feature_card)
    outputs["mutation"] = build_mutation_report(
        feature_card,
        spec,
        metadata,
        outputs,
    )
    if outputs["mutation"]["survivors"]:
        raise ActInbandModulationError("PR-177 mutation survivors remain")
    artifact_hashes = {key: hashlib.sha256(_text(payload).encode("utf-8")).hexdigest() for key, payload in outputs.items()}
    manifest: dict[str, Any] = {
        "schema": "htt.pr177.artifact_manifest.v1",
        **metadata,
        "process_execution_status": "PASS_REPRODUCIBLE_RESULT",
        "scientific_result": outputs["card"]["scientific_result"],
        "scientific_status": outputs["card"]["scientific_status"],
        "analysis_support": feature_card["analysis_support"],
        "artifacts": {str(OUTPUTS[key].relative_to(REPO)): digest for key, digest in artifact_hashes.items()},
        "source_feature_card": {
            "path": str(FEATURE_PATH.relative_to(REPO)),
            "sha256": _sha(FEATURE_PATH),
            "semantic_digest": feature_card["semantic_digest"],
        },
        "source_deep_replay_receipt": {
            "path": str(DEEP_REPLAY_PATH.relative_to(REPO)),
            "sha256": _sha(DEEP_REPLAY_PATH),
            "semantic_digest": _json(DEEP_REPLAY_PATH)["semantic_digest"],
        },
        "allowed_use": [
            "internal_ACT_release_simulation_conditional_modulation_candidate_or_null",
            "finite_ensemble_numerical_resolution",
            "registered_mask_control_sensitivity",
        ],
        "forbidden_use": list(spec["forbidden_claims"]),
        "raw_payload_rehashed_by_runner": False,
        "raw_qe_reproduced": False,
    }
    manifest["semantic_digest"] = semantic_digest(manifest)
    outputs["manifest"] = manifest
    support_errors = result_support_errors(outputs, EXPECTED_SUPPORT)
    if support_errors:
        raise ActInbandModulationError("; ".join(support_errors))
    return outputs


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--write", action="store_true")
    mode.add_argument("--check", action="store_true")
    args = parser.parse_args(argv)
    spec = _spec()
    feature_card = _json(FEATURE_PATH)
    outputs = build_outputs(spec, feature_card)
    problems: list[str] = []
    for key, path in OUTPUTS.items():
        expected = _text(outputs[key])
        if args.check:
            if not path.is_file() or path.read_text(encoding="utf-8") != expected:
                problems.append(f"stale {path.relative_to(REPO)}")
        else:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(expected, encoding="utf-8")
    if problems:
        print(json.dumps({"ok": False, "errors": problems}, sort_keys=True))
        return 1
    card = outputs["card"]
    print(
        json.dumps(
            {
                "ok": True,
                "mode": "check" if args.check else "write",
                "scientific_result": card["scientific_result"],
                "rank_summary": card["rank_summary"],
                "delete_replicates": 400,
                "mutation_survivors": outputs["mutation"]["survivors"],
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
