#!/usr/bin/env python3
"""Build and verify the PR-173 finite-ensemble resolution audit pack."""
from __future__ import annotations

import argparse
import copy
import hashlib
import json
import math
import platform
import sys
from pathlib import Path
from typing import Any, Mapping

import numpy as np
import yaml


REPO = Path(__file__).resolve().parents[2]
HTT = REPO / "htt"
if str(HTT) not in sys.path:
    sys.path.insert(0, str(HTT))

from obsstat.finite_ensemble import (  # noqa: E402
    INPUT_AVAILABLE,
    INPUT_PARTIAL_FORBIDDEN,
    LINEAGE_CERTIFIED,
    LINEAGE_INVALID,
    LINEAGE_MISSING,
    RESOLVED,
    UNRESOLVED,
    batch_means_se,
    certificate_errors,
    clustered_rank_bootstrap,
    iid_rank_delete_one_jackknife_se,
    infer_exceedance_count,
    not_certifiable_certificate,
    not_evaluated_certificate,
    plus_one_rank,
    rank_certificate,
    scalar_certificate,
    seed_sem,
    semantic_digest,
)


SPEC_PATH = REPO / "docs/research_program/long_horizon_rescue/pr173_spec.yaml"
MODULE_PATH = REPO / "htt/obsstat/finite_ensemble.py"
SCRIPT_PATH = Path(__file__).resolve()
OUT = {
    "report": REPO / "docs/generated/pr173_error_budget_report.json",
    "validation": REPO / "docs/generated/pr173_method_validation.json",
    "mutation": REPO / "docs/generated/pr173_mutation_report.json",
    "card": REPO / "docs/generated/pr173_result_card.json",
    "manifest": REPO / "docs/generated/pr173_artifact_manifest.json",
}


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"{path} must contain a JSON object")
    return value


def _spec() -> dict[str, Any]:
    value = yaml.safe_load(SPEC_PATH.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError("PR-173 spec must be a mapping")
    return value


def _normalize_hash(value: object) -> str:
    text = str(value)
    if text.startswith("sha256:"):
        text = text[7:]
    if len(text) != 64 or any(char not in "0123456789abcdef" for char in text):
        raise ValueError(f"invalid SHA-256 value: {value!r}")
    return text


def _declared_hash(manifest: Mapping[str, Any], artifact: str) -> str | None:
    artifacts = manifest.get("artifacts")
    if isinstance(artifacts, Mapping) and artifact in artifacts:
        return _normalize_hash(artifacts[artifact])
    metadata = manifest.get("artifact_metadata")
    if isinstance(metadata, Mapping):
        rows = metadata.get("input_hashes")
        if isinstance(rows, list):
            for row in rows:
                if isinstance(row, Mapping) and row.get("path") == artifact:
                    return _normalize_hash(row.get("sha256"))
    rows = manifest.get("files")
    if isinstance(rows, list):
        for row in rows:
            if isinstance(row, Mapping) and row.get("path") == artifact:
                return _normalize_hash(row.get("sha256"))
    return None


def _authority_receipt(
    *,
    artifact: str,
    authority: str,
    expected_sha256: str,
    verify_small_metadata_bytes: bool,
) -> dict[str, Any]:
    manifest = _json(REPO / authority)
    declared = _declared_hash(manifest, artifact)
    expected = _normalize_hash(expected_sha256)
    actual = _sha(REPO / artifact) if verify_small_metadata_bytes else None
    matched = declared == expected and (actual is None or actual == expected)
    return {
        "artifact": artifact,
        "authority": authority,
        "expected_sha256": expected,
        "authority_declared_sha256": declared,
        "actual_metadata_sha256": actual,
        "matched": matched,
        "authentication_mode": (
            "small_metadata_byte_hash_and_upstream_manifest"
            if verify_small_metadata_bytes
            else "upstream_manifest_reference_and_output_replay_no_repeat_byte_hash"
        ),
        "small_metadata_bytes_hashed": verify_small_metadata_bytes,
        "raw_payload_rehashed_by_pr173": False,
    }


def _authority_receipts(spec: Mapping[str, Any]) -> list[dict[str, Any]]:
    receipts: list[dict[str, Any]] = []
    for source_id, row in spec["source_authorities"].items():
        artifact = row.get("artifact")
        if artifact is None:
            continue
        receipt = _authority_receipt(
            artifact=artifact,
            authority=row["authority"],
            expected_sha256=row["declared_sha256"],
            verify_small_metadata_bytes=True,
        )
        receipt["source_id"] = source_id
        receipt["support_only"] = False
        receipts.append(receipt)
        support = row.get("support_artifact")
        if support:
            support_receipt = _authority_receipt(
                artifact=support,
                authority=row["authority"],
                expected_sha256=row["support_declared_sha256"],
                verify_small_metadata_bytes=False,
            )
            support_receipt["source_id"] = source_id
            support_receipt["support_only"] = True
            receipts.append(support_receipt)
    return receipts


def _common_metadata(spec: Mapping[str, Any]) -> dict[str, Any]:
    receipts = _authority_receipts(spec)
    source_hashes = {row["artifact"]: row["expected_sha256"] for row in receipts}
    local_hashes = {
        str(SPEC_PATH.relative_to(REPO)): _sha(SPEC_PATH),
        str(MODULE_PATH.relative_to(REPO)): _sha(MODULE_PATH),
        str(SCRIPT_PATH.relative_to(REPO)): _sha(SCRIPT_PATH),
    }
    receipt_material = json.dumps(
        {"local": local_hashes, "upstream": source_hashes},
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    content_receipt = hashlib.sha256(receipt_material).hexdigest()
    baseline = str(spec["baseline_commit"])
    return {
        "owner": "OBSSTAT",
        "contributors": ["COMMON"],
        "implementation_scope": ["obsstat"],
        "claim_tier": "exploratory",
        "claim_level": {"scheme": "roadmap_rescue_v1", "level": "C1"},
        "scientific_artifact_mode": "standard_internal",
        "public_use": False,
        "transfer_source": "none",
        "config_hash": _sha(SPEC_PATH),
        "input_hashes": {**local_hashes, **source_hashes},
        "input_authentication": (
            "small_metadata_byte_hashes_plus_upstream_manifest_references; "
            "support_array_uses_manifest_hash_and_deterministic_output_replay"
        ),
        "sky_support_status": "source_specific_planck_act_cf4_mio_and_partial_forbidden_desi",
        "mask_status": "source_specific_no_new_mask_operation",
        "covariance_status": "source_specific_not_reestimated_by_pr173",
        "null_mock_status": "finite_ensemble_resolution_audit_only",
        "generating_command": (
            "PYTHONPATH=htt venv/bin/python -B "
            "scripts/codex_harness/run_pr173_finite_ensemble.py --write"
        ),
        "git_commit": baseline,
        "worktree_content_receipt": content_receipt,
        "worktree_state": f"{baseline}+content-sha256:{content_receipt}",
        "runtime_environment": {"python": platform.python_version(), "numpy": np.__version__},
        "caveats": [
            "Numerical-resolution status is not a physical signal/noise or validation label.",
            "Upstream null, mask, covariance, transfer, and exchangeability caveats remain unchanged.",
            "PR-173 does not rehash raw payloads or repeat-hash the Planck support array.",
            "No partial PR-151 mock is used.",
        ],
    }


def _decision(spec: Mapping[str, Any], target_id: str) -> dict[str, Any]:
    for row in spec["registered_targets"]:
        if row["target_id"] == target_id:
            return dict(row["decision"])
    raise KeyError(target_id)


def _target_from_certificate(
    *, certificate: Mapping[str, Any], target_id: str, source: str, quantity: str
) -> dict[str, Any]:
    return {
        "target_id": target_id,
        "source": source,
        "quantity": quantity,
        "input_availability_status": certificate["input_availability_status"],
        "replicate_lineage_status": certificate["replicate_lineage_status"],
        "numerical_resolution_status": certificate["numerical_resolution_status"],
        "certificate": dict(certificate),
    }


def _planck_target(spec: Mapping[str, Any]) -> dict[str, Any]:
    authority = spec["source_authorities"]["planck_pr150_e2e_rank"]
    summary = _json(REPO / authority["artifact"])
    support = _json(REPO / authority["support_artifact"])
    n_null = int(summary["simulation_count"])
    reported_p = float(summary["look_elsewhere_global_p"])
    exceedance_count = infer_exceedance_count(reported_p, n_null, tolerance=1.0e-12)
    clusters: dict[int, list[bool]] = {}
    for row in support["result"]["simulation_max_scores"]:
        clusters.setdefault(int(row["noise_id"]), []).append(
            bool(row["exceeds_observed"])
        )
    method = spec["registered_uncertainty_methods"]["clustered_rank_bootstrap"]
    bootstrap = clustered_rank_bootstrap(
        clusters,
        seed=int(method["seed"]),
        replicates=int(method["replicates"]),
    )
    if bootstrap["row_count"] != n_null or bootstrap["exceedance_count"] != exceedance_count:
        raise ValueError("Planck cluster support does not reproduce the registered rank")
    upstream_bootstrap = summary["noise_reuse_sensitivity"]["noise_cluster_bootstrap"]
    expected_interval = [float(value) for value in upstream_bootstrap["percentile_95_interval"]]
    reproduced = (
        bootstrap["seed"] == int(upstream_bootstrap["seed"])
        and bootstrap["replicates"] == int(upstream_bootstrap["replicates"])
        and bootstrap["percentile_95_interval"] == expected_interval
        and bootstrap["median"] == float(upstream_bootstrap["median_p"])
    )
    if not reproduced:
        raise ValueError("Planck cluster bootstrap does not reproduce the upstream receipt")
    decision = _decision(spec, "PR173-PLANCK-RANK")
    certificate = rank_certificate(
        n_null=n_null,
        exceedance_count=exceedance_count,
        uncertainty_interval=bootstrap["percentile_95_interval"],
        boundary=float(decision["boundary"]),
        direction=str(decision["direction"]),
        confidence_level=float(decision["confidence_level"]),
        mc_se=float(bootstrap["mc_se"]),
        uncertainty_method="whole_cluster_bootstrap_plus_one_rank",
    )
    result = _target_from_certificate(
        certificate=certificate,
        target_id="PR173-PLANCK-RANK",
        source="planck_pr150_e2e_rank",
        quantity="look_elsewhere_global_pooled_rank",
    )
    result.update(
        {
            "dependence_contract": "300_noise_clusters_reused_across_999_CMB_rows",
            "reported_value": reported_p,
            "decision_contract": decision,
            "uncertainty_receipt": bootstrap,
            "upstream_bootstrap_reproduction": {
                "matched": reproduced,
                "seed": int(upstream_bootstrap["seed"]),
                "replicates": int(upstream_bootstrap["replicates"]),
                "percentile_95_interval": expected_interval,
                "median": float(upstream_bootstrap["median_p"]),
            },
            "claim_boundary": "PR3_FFP10_E2E_conditional_numerical_resolution_only",
        }
    )
    return result


def _act_targets(spec: Mapping[str, Any]) -> list[dict[str, Any]]:
    authority = spec["source_authorities"]["act_pr152_release_rank_and_bandpower"]
    source = _json(REPO / authority["artifact"])
    n_null = int(source["n_sims"])
    reported_p = float(source["observation_inclusive_crossfit_pooled_rank_p"])
    exceedance_count = infer_exceedance_count(reported_p, n_null, tolerance=1.0e-12)
    simulations = [float(value) for value in source["simulation_band_powers"]]
    if len(simulations) != n_null:
        raise ValueError("ACT simulation vector length does not match n_sims")
    simulation_mean = float(np.mean(simulations))
    if not math.isclose(
        simulation_mean,
        float(source["simulation_band_power_mean"]),
        rel_tol=0.0,
        abs_tol=1.0e-18,
    ):
        raise ValueError("ACT simulation mean does not reproduce the source artifact")
    difference = float(source["S_data"]) - simulation_mean
    rank_certificate_blocked = not_certifiable_certificate(
        reason=(
            "crossfit_scores_share_observation_and_simulation_derived_mean_fields; "
            "conditional_rank_identity_does_not_supply_iid_MC_error"
        ),
        required_method="full_crossfit_delete_independent_unit_recomputation",
        lineage_status=LINEAGE_INVALID,
    )
    mean_certificate_blocked = not_certifiable_certificate(
        reason=(
            "release_simulation_bandpowers_are_exchangeable_null_units_not_authenticated_"
            "independent_seed_estimates_of_the_observed_minus_mean_estimand"
        ),
        required_method="authenticated_independent_release_unit_or_seed_sem",
        lineage_status=LINEAGE_INVALID,
    )
    common = {
        "dependence_contract": "jointly_exchangeable_crossfit_with_coupled_scores",
        "inside_release_validated_range": bool(source["inside_release_validated_range"]),
        "analysis_ell_range": source["analysis_ell_range"],
        "release_validated_ell_range": source["release_validated_ell_range"],
        "claim_boundary": "ACT_release_simulation_conditional_not_raw_QE",
    }
    rank = _target_from_certificate(
        certificate=rank_certificate_blocked,
        target_id="PR173-ACT-RANK",
        source="act_pr152_release_rank_and_bandpower",
        quantity="release_simulation_conditional_pooled_rank",
    )
    rank.update(
        {
            **common,
            "reported_value": reported_p,
            "reported_rank_identity": {
                "n_null": n_null,
                "exceedance_count": exceedance_count,
                "rank_fraction": str(plus_one_rank(n_null, exceedance_count)),
                "tie_policy": "conservative_ge",
                "identity_role": "exact_conditional_rank_not_MC_error_certificate",
            },
            "decision_contract": _decision(spec, "PR173-ACT-RANK"),
        }
    )
    bandpower = _target_from_certificate(
        certificate=mean_certificate_blocked,
        target_id="PR173-ACT-BANDPOWER-MEAN",
        source="act_pr152_release_rank_and_bandpower",
        quantity="observed_minus_simulation_mean_band_power",
    )
    bandpower.update(
        {
            **common,
            "reported_value": difference,
            "simulation_mean": simulation_mean,
            "estimand_unit": "kappa_band_power",
            "decision_contract": _decision(spec, "PR173-ACT-BANDPOWER-MEAN"),
        }
    )
    return [rank, bandpower]


def _pi_target(spec: Mapping[str, Any]) -> dict[str, Any]:
    authority = spec["source_authorities"]["mio_pr142_pi_tail"]
    source = _json(REPO / authority["artifact"])
    pi = source["Pi"]
    n_null = int(pi["n_null"])
    reported_p = float(pi["p_value"])
    exceedance_count = infer_exceedance_count(reported_p, n_null, tolerance=5.0e-9)
    certificate = not_certifiable_certificate(
        reason=(
            "aggregate_sign_flip_and_bootstrap_summaries_lack_authenticated_replicate_"
            "identities_seed_and_resampling_unit_lineage"
        ),
        required_method="authenticated_sign_flip_and_bootstrap_replicate_lineage",
        lineage_status=LINEAGE_MISSING,
    )
    result = _target_from_certificate(
        certificate=certificate,
        target_id="PR173-MIO-PI",
        source="mio_pr142_pi_tail",
        quantity="Pi_signed_contrast_and_two_sided_rank",
    )
    result.update(
        {
            "reported_values": {
                "observed": float(pi["observed"]),
                "p_value": reported_p,
                "bootstrap_se": float(pi["bootstrap_se"]),
                "bootstrap_se_role": "reported_aggregate_not_PR173_certified_MC_error",
                "rank_identity": {
                    "n_null": n_null,
                    "exceedance_count": exceedance_count,
                    "rank_fraction": str(plus_one_rank(n_null, exceedance_count)),
                },
            },
            "dependence_contract": "aggregate_sign_flip_and_bootstrap_summary_only",
            "decision_contract": _decision(spec, "PR173-MIO-PI"),
            "claim_boundary": "MIO_matched_null_diagnostic_not_posterior_or_evidence",
        }
    )
    return result


def _cf4_injection_target(spec: Mapping[str, Any]) -> dict[str, Any]:
    authority = spec["source_authorities"]["cf4_pr117_injection_rmse"]
    source = _json(REPO / authority["artifact"])
    injection = source["lanes"]["cf4_monopole_propagation"]["injection_recovery"]
    certificate = not_certifiable_certificate(
        reason="aggregate_RMSE_only_without_per_injection_or_leave_one_replicate_lineage",
        required_method="delete_one_jackknife",
        lineage_status=LINEAGE_MISSING,
    )
    result = _target_from_certificate(
        certificate=certificate,
        target_id="PR173-CF4-INJECTION-RMSE",
        source="cf4_pr117_injection_rmse",
        quantity="constrained_minus_standard_on_model_injection_RMSE",
    )
    result.update(
        {
            "reported_values": {
                "n_injections": int(injection["n"]),
                "standard_rmse_kms": float(injection["standard_rmse_kms"]),
                "nulled_rmse_kms": float(injection["nulled_rmse_kms"]),
                "aggregate_only": True,
            },
            "decision_contract": _decision(spec, "PR173-CF4-INJECTION-RMSE"),
            "claim_boundary": "audit_only_on_model_sensitivity_not_corrected_flow",
        }
    )
    return result


def _fsigma_target(spec: Mapping[str, Any]) -> dict[str, Any]:
    authority = spec["source_authorities"]["cf4_pr148_fsigma8"]
    source = _json(REPO / authority["artifact"])
    certificate = not_certifiable_certificate(
        reason="mock_dispersion_is_scientific_covariance_not_MC_error_of_the_reported_estimator",
        required_method="delete_one_jackknife_or_independent_seed_sem",
        lineage_status=LINEAGE_MISSING,
    )
    result = _target_from_certificate(
        certificate=certificate,
        target_id="PR173-CF4-FSIGMA8",
        source="cf4_pr148_fsigma8",
        quantity="depth_shell_fsigma8_mock_calibration",
    )
    result.update(
        {
            "reported_values": {
                "n_constrained_shells": int(source["n_constrained_shells"]),
                "shells": [
                    {
                        "shell": int(row["shell"]),
                        "fsigma8": float(row["fsigma8"]),
                        "mock_sigma": float(row["mock_sigma"]),
                        "n_groups": int(row["n_groups"]),
                    }
                    for row in source["shells"]
                ],
                "mock_sigma_role": "scientific_mock_dispersion_not_MC_standard_error",
            },
            "decision_contract": _decision(spec, "PR173-CF4-FSIGMA8"),
            "claim_boundary": "growth_difference_bound_mechanics_not_precision_growth_claim",
        }
    )
    return result


def _desi_target(spec: Mapping[str, Any]) -> dict[str, Any]:
    certificate = not_evaluated_certificate(
        reason="PR151_official_mock_acquisition_non_terminal_and_partial_mock_use_forbidden",
        required_method="clustered_rank_bootstrap_after_terminal_1025_mock_receipt",
        availability_status=INPUT_PARTIAL_FORBIDDEN,
    )
    result = _target_from_certificate(
        certificate=certificate,
        target_id="PR173-DESI-RANK",
        source="desi_pr151_mock_rank",
        quantity="official_mock_calibrated_rank",
    )
    result.update(
        {
            "partial_mock_count_used": 0,
            "reported_value": None,
            "decision_contract": _decision(spec, "PR173-DESI-RANK"),
            "claim_boundary": "no_DESI_mock_calibrated_rank_before_PR151_terminal_receipt",
        }
    )
    return result


def _authoritative_targets(spec: Mapping[str, Any]) -> list[dict[str, Any]]:
    """Rebuild every target from frozen source authorities and registered methods."""

    return [
        _planck_target(spec),
        *_act_targets(spec),
        _pi_target(spec),
        _cf4_injection_target(spec),
        _fsigma_target(spec),
        _desi_target(spec),
    ]


def _target_errors(row: Mapping[str, Any]) -> list[str]:
    errors: list[str] = []
    certificate = row.get("certificate")
    if not isinstance(certificate, Mapping):
        return ["target has no certificate"]
    errors.extend(certificate_errors(certificate))
    for field in (
        "input_availability_status",
        "replicate_lineage_status",
        "numerical_resolution_status",
    ):
        if row.get(field) != certificate.get(field):
            errors.append(f"target {field} does not match certificate")
    availability = row.get("input_availability_status")
    lineage = row.get("replicate_lineage_status")
    numerical = row.get("numerical_resolution_status")
    if availability == INPUT_AVAILABLE:
        if lineage == LINEAGE_CERTIFIED and numerical not in (RESOLVED, UNRESOLVED):
            errors.append("certified available target requires a typed numerical status")
        if lineage in (LINEAGE_MISSING, LINEAGE_INVALID) and numerical is not None:
            errors.append("not-certifiable target must have null numerical status")
        if lineage not in (LINEAGE_CERTIFIED, LINEAGE_MISSING, LINEAGE_INVALID):
            errors.append("available target has invalid lineage status")
    else:
        if lineage is not None or numerical is not None:
            errors.append("not-evaluated target must have null lineage and numerical status")
    return errors


def validate_report(
    report: Mapping[str, Any],
    spec: Mapping[str, Any],
    *,
    authoritative_targets: list[dict[str, Any]] | None = None,
    authoritative_metadata: Mapping[str, Any] | None = None,
    authoritative_receipts: list[dict[str, Any]] | None = None,
) -> list[str]:
    """Validate a report against independent frozen-source reconstruction.

    The optional authoritative values are an internal performance hook for the
    mutation battery.  Public callers omit them, forcing a fresh source-bound
    reconstruction rather than trusting any self-consistent candidate fields.
    """

    errors: list[str] = []
    expected_targets = (
        _authoritative_targets(spec)
        if authoritative_targets is None
        else authoritative_targets
    )
    expected_metadata = (
        _common_metadata(spec)
        if authoritative_metadata is None
        else authoritative_metadata
    )
    expected_receipts = (
        _authority_receipts(spec)
        if authoritative_receipts is None
        else authoritative_receipts
    )
    for field, expected in expected_metadata.items():
        if report.get(field) != expected:
            errors.append(f"frozen metadata mismatch: {field}")
    targets = report.get("targets")
    if not isinstance(targets, list):
        return ["targets must be a list"]
    registered = [row["target_id"] for row in spec["registered_targets"]]
    actual = [row.get("target_id") for row in targets if isinstance(row, Mapping)]
    if actual != registered:
        errors.append("target registry/order mismatch")
    if targets != expected_targets:
        errors.append("target payload differs from frozen-source reconstruction")
    by_id = {row.get("target_id"): row for row in targets if isinstance(row, Mapping)}
    for target_id in registered:
        row = by_id.get(target_id)
        if not isinstance(row, Mapping):
            errors.append(f"missing target {target_id}")
            continue
        errors.extend(f"{target_id}: {error}" for error in _target_errors(row))
        if row.get("decision_contract") != _decision(spec, target_id):
            errors.append(f"{target_id}: decision contract drift")

    planck = by_id.get("PR173-PLANCK-RANK", {})
    planck_certificate = planck.get("certificate", {})
    if planck_certificate.get("rank_fraction") != "39/1000":
        errors.append("PR173-PLANCK-RANK: exact rank identity mismatch")
    if planck_certificate.get("uncertainty_method") != "whole_cluster_bootstrap_plus_one_rank":
        errors.append("PR173-PLANCK-RANK: dependence-aware uncertainty method mismatch")
    if planck.get("numerical_resolution_status") != UNRESOLVED:
        errors.append("PR173-PLANCK-RANK: registered 0.05 boundary must remain unresolved")

    act_rank = by_id.get("PR173-ACT-RANK", {})
    if act_rank.get("reported_rank_identity", {}).get("rank_fraction") != "146/401":
        errors.append("PR173-ACT-RANK: exact conditional rank identity mismatch")
    for target_id in (
        "PR173-ACT-RANK",
        "PR173-ACT-BANDPOWER-MEAN",
    ):
        row = by_id.get(target_id, {})
        if row.get("replicate_lineage_status") != LINEAGE_INVALID:
            errors.append(f"{target_id}: coupled crossfit lineage must remain invalid for MC decision")
        if row.get("numerical_resolution_status") is not None:
            errors.append(f"{target_id}: numerical status must be null")
    for target_id in (
        "PR173-MIO-PI",
        "PR173-CF4-INJECTION-RMSE",
        "PR173-CF4-FSIGMA8",
    ):
        row = by_id.get(target_id, {})
        if row.get("replicate_lineage_status") != LINEAGE_MISSING:
            errors.append(f"{target_id}: missing lineage route mismatch")
        if row.get("numerical_resolution_status") is not None:
            errors.append(f"{target_id}: numerical status must be null")
    fsigma_role = by_id.get("PR173-CF4-FSIGMA8", {}).get("reported_values", {}).get(
        "mock_sigma_role"
    )
    if fsigma_role != "scientific_mock_dispersion_not_MC_standard_error":
        errors.append("PR173-CF4-FSIGMA8: mock dispersion role drift")
    desi = by_id.get("PR173-DESI-RANK", {})
    if desi.get("input_availability_status") != INPUT_PARTIAL_FORBIDDEN:
        errors.append("PR173-DESI-RANK: nonterminal input must remain partial-forbidden")
    if desi.get("partial_mock_count_used") != 0:
        errors.append("PR173-DESI-RANK: partial mock use is forbidden")

    receipts = report.get("source_authority_receipts")
    if not isinstance(receipts, list) or not receipts:
        errors.append("source authority receipts missing")
    else:
        if receipts != expected_receipts:
            errors.append("source authority receipts differ from frozen reconstruction")
        for receipt in receipts:
            if not isinstance(receipt, Mapping) or not receipt.get("matched"):
                errors.append("source authority receipt mismatch")
                continue
            expected = receipt.get("expected_sha256")
            if receipt.get("authority_declared_sha256") != expected:
                errors.append("authority-declared hash mismatch")
            if receipt.get("support_only") is False and receipt.get("actual_metadata_sha256") != expected:
                errors.append("small metadata byte hash mismatch")
            if receipt.get("support_only") is True and receipt.get("actual_metadata_sha256") is not None:
                errors.append("support array must not be repeat-byte-hashed")
            if receipt.get("raw_payload_rehashed_by_pr173") is not False:
                errors.append("raw payload rehash is forbidden")
    if report.get("raw_payload_hashing_performed") is not False:
        errors.append("raw payload hashing must be false")
    if report.get("small_metadata_hashing_performed") is not True:
        errors.append("small metadata byte hashing must be true")
    for row in targets:
        certificate = row.get("certificate") if isinstance(row, Mapping) else None
        if isinstance(certificate, Mapping) and certificate.get("gaussian_sigma_emitted") is True:
            errors.append(f"{row.get('target_id')}: Gaussian sigma emission forbidden")

    numerical = [row.get("numerical_resolution_status") for row in targets]
    lineages = [row.get("replicate_lineage_status") for row in targets]
    availability = [row.get("input_availability_status") for row in targets]
    expected_summary = {
        "target_count": len(targets),
        "resolved_count": numerical.count(RESOLVED),
        "unresolved_count": numerical.count(UNRESOLVED),
        "not_certifiable_count": sum(
            value in (LINEAGE_MISSING, LINEAGE_INVALID) for value in lineages
        ),
        "not_evaluated_count": sum(value != INPUT_AVAILABLE for value in availability),
        "all_routes_typed": all(not _target_errors(row) for row in targets),
    }
    if report.get("summary") != expected_summary:
        errors.append("summary does not match orthogonal target statuses")
    if report.get("terminal") != "PASS_REPRODUCIBLE_FINITE_ENSEMBLE_AUDIT_WITH_BLOCKED_LANES":
        errors.append("terminal mismatch")
    if report.get("semantic_digest") != semantic_digest(report):
        errors.append("semantic digest mismatch")
    return errors


def _explicit_rank_jackknife(n_null: int, exceedance_count: int) -> float:
    indicators = [1] * exceedance_count + [0] * (n_null - exceedance_count)
    values = [
        float(plus_one_rank(n_null - 1, exceedance_count - value))
        for value in indicators
    ]
    mean = float(np.mean(values))
    return float(
        math.sqrt((n_null - 1.0) / n_null * sum((value - mean) ** 2 for value in values))
    )


def _method_validation() -> dict[str, Any]:
    formula = iid_rank_delete_one_jackknife_se(17, 5)
    explicit = _explicit_rank_jackknife(17, 5)
    cluster_fixture = {"a": [1, 0, 0], "b": [0, 1], "c": [0, 0, 0, 0]}
    cluster_a = clustered_rank_bootstrap(cluster_fixture, seed=91, replicates=512)
    cluster_b = clustered_rank_bootstrap(cluster_fixture, seed=91, replicates=512)
    touching = rank_certificate(
        n_null=99,
        exceedance_count=3,
        uncertainty_interval=[0.04, 0.04],
        boundary=0.05,
        direction="below",
        confidence_level=0.95,
        uncertainty_method="method_fixture_only",
    )
    scalar_touching = scalar_certificate(
        estimate=0.0,
        uncertainty_interval=[-0.5, 0.5],
        boundary=0.0,
        direction="away_from",
        confidence_level=0.95,
        uncertainty_method="method_fixture_only",
        estimand_unit="fixture_unit",
    )
    checks = {
        "iid_rank_formula_matches_explicit_delete_one_method_fixture": abs(formula - explicit) <= 1.0e-15,
        "batch_means_fixture": batch_means_se([1.0, 3.0, 5.0, 7.0], batch_size=2) == 2.0,
        "seed_sem_fixture": seed_sem([1.0, 3.0]) == 1.0,
        "cluster_bootstrap_deterministic": cluster_a == cluster_b,
        "rank_guard_touching_boundary_is_unresolved": touching["numerical_resolution_status"] == UNRESOLVED,
        "scalar_interval_crossing_boundary_is_unresolved": scalar_touching["numerical_resolution_status"] == UNRESOLVED,
    }
    return {
        "schema": "htt.pr173.method_validation.v2",
        "checks": checks,
        "all_passed": all(checks.values()),
        "rank_formula_value": formula,
        "rank_explicit_value": explicit,
        "cluster_fixture_receipt": cluster_a,
        "independent_numerical_oracle_count": 1,
        "oracle_note": (
            "Closed-form iid rank jackknife matches explicit enumeration as a method-only "
            "fixture; this does not authorize iid treatment of ACT or Planck."
        ),
    }


def _mutation_report(
    report: Mapping[str, Any],
    spec: Mapping[str, Any],
    *,
    authoritative_targets: list[dict[str, Any]],
    authoritative_metadata: Mapping[str, Any],
    authoritative_receipts: list[dict[str, Any]],
) -> dict[str, Any]:
    mutations: list[dict[str, Any]] = []

    def execute(mutation_id: str, mutate) -> None:
        candidate = copy.deepcopy(report)
        mutate(candidate)
        candidate["semantic_digest"] = semantic_digest(candidate)
        errors = validate_report(
            candidate,
            spec,
            authoritative_targets=authoritative_targets,
            authoritative_metadata=authoritative_metadata,
            authoritative_receipts=authoritative_receipts,
        )
        mutations.append(
            {
                "mutation_id": mutation_id,
                "executed": True,
                "killed": bool(errors),
                "error_fingerprint": hashlib.sha256(
                    json.dumps(errors, sort_keys=True).encode("utf-8")
                ).hexdigest(),
                "errors": errors,
            }
        )

    execute(
        "planck_unresolved_false_promotion",
        lambda value: value["targets"][0].update(
            {"numerical_resolution_status": RESOLVED}
        ),
    )
    execute(
        "act_invalid_lineage_numerical_promotion",
        lambda value: value["targets"][1].update(
            {"numerical_resolution_status": UNRESOLVED}
        ),
    )
    execute(
        "aggregate_rmse_numerical_promotion",
        lambda value: value["targets"][4].update(
            {"numerical_resolution_status": RESOLVED}
        ),
    )
    execute(
        "mock_dispersion_relabeled_mcse",
        lambda value: value["targets"][5]["reported_values"].update(
            {"mock_sigma_role": "MC_standard_error"}
        ),
    )
    execute(
        "partial_desi_consumed",
        lambda value: value["targets"][6].update({"partial_mock_count_used": 1}),
    )
    execute(
        "small_metadata_hash_mismatch",
        lambda value: value["source_authority_receipts"][0].update(
            {"actual_metadata_sha256": "0" * 64}
        ),
    )
    execute(
        "raw_payload_rehash_claimed",
        lambda value: value.update({"raw_payload_hashing_performed": True}),
    )
    execute(
        "finite_rank_sigma_emitted",
        lambda value: value["targets"][0]["certificate"].update(
            {"gaussian_sigma_emitted": True}
        ),
    )
    execute(
        "planck_boundary_removed",
        lambda value: value["targets"][0]["certificate"].pop("boundary"),
    )
    execute(
        "planck_boundary_unit_changed",
        lambda value: value["targets"][0]["certificate"].update(
            {"boundary_unit": "km/s"}
        ),
    )
    execute(
        "boolean_null_count",
        lambda value: value["targets"][0]["certificate"].update({"n_null": True}),
    )
    execute(
        "desi_partial_lineage_fabricated",
        lambda value: value["targets"][6].update(
            {"replicate_lineage_status": LINEAGE_CERTIFIED}
        ),
    )

    def forge_planck_uncertainty(value: dict[str, Any]) -> None:
        target = value["targets"][0]
        original = target["certificate"]
        forged = rank_certificate(
            n_null=int(original["n_null"]),
            exceedance_count=int(original["exceedance_count"]),
            uncertainty_interval=[0.001, 0.051],
            boundary=float(original["boundary"]),
            direction=str(original["direction"]),
            confidence_level=float(original["confidence_level"]),
            uncertainty_method=str(original["uncertainty_method"]),
            mc_se=0.0,
        )
        target["certificate"] = forged
        target["numerical_resolution_status"] = forged["numerical_resolution_status"]

    execute("coordinated_planck_uncertainty_forgery", forge_planck_uncertainty)
    execute(
        "planck_uncertainty_receipt_mcse_drift",
        lambda value: value["targets"][0]["uncertainty_receipt"].update(
            {"mc_se": 999.0}
        ),
    )
    execute(
        "planck_upstream_replay_false",
        lambda value: value["targets"][0]["upstream_bootstrap_reproduction"].update(
            {"matched": False}
        ),
    )
    execute(
        "coordinated_config_hash_drift",
        lambda value: value.update({"config_hash": "0" * 64}),
    )
    execute(
        "coordinated_local_input_hash_drift",
        lambda value: value["input_hashes"].update(
            {"htt/obsstat/finite_ensemble.py": "0" * 64}
        ),
    )
    execute(
        "registered_target_source_drift",
        lambda value: value["targets"][0].update({"source": "forged_source"}),
    )
    return {
        "schema": "htt.pr173.mutation_report.v2",
        "registered_count": len(mutations),
        "executed_count": sum(row["executed"] for row in mutations),
        "killed_count": sum(row["killed"] for row in mutations),
        "survivors": [row["mutation_id"] for row in mutations if not row["killed"]],
        "mutations": mutations,
    }


def build_outputs() -> dict[str, dict[str, Any]]:
    spec = _spec()
    metadata = _common_metadata(spec)
    receipts = _authority_receipts(spec)
    if not all(row["matched"] for row in receipts):
        raise ValueError("an upstream hash authority does not match the frozen spec")
    targets = _authoritative_targets(spec)
    numerical = [row["numerical_resolution_status"] for row in targets]
    lineages = [row["replicate_lineage_status"] for row in targets]
    availability = [row["input_availability_status"] for row in targets]
    report: dict[str, Any] = {
        "schema": "htt.pr173.error_budget_report.v2",
        "pr_id": "PR-173",
        **metadata,
        "source_authority_receipts": receipts,
        "raw_payload_hashing_performed": False,
        "small_metadata_hashing_performed": True,
        "targets": targets,
        "summary": {
            "target_count": len(targets),
            "resolved_count": numerical.count(RESOLVED),
            "unresolved_count": numerical.count(UNRESOLVED),
            "not_certifiable_count": sum(
                value in (LINEAGE_MISSING, LINEAGE_INVALID) for value in lineages
            ),
            "not_evaluated_count": sum(
                value != INPUT_AVAILABLE for value in availability
            ),
            "all_routes_typed": all(not _target_errors(row) for row in targets),
        },
        "terminal": "PASS_REPRODUCIBLE_FINITE_ENSEMBLE_AUDIT_WITH_BLOCKED_LANES",
        "scientific_status": "OPEN",
        "claim_boundary": "finite_ensemble_numerical_resolution_only",
        "historical_wording_superseded": (
            "PR-173 certifies numerical resolution at the current MC budget; it does not "
            "estimate or classify generic estimator noise."
        ),
    }
    report["semantic_digest"] = semantic_digest(report)
    report_errors = validate_report(
        report,
        spec,
        authoritative_targets=targets,
        authoritative_metadata=metadata,
        authoritative_receipts=receipts,
    )
    if report_errors:
        raise ValueError("report validation failed: " + "; ".join(report_errors))

    validation = {**_method_validation(), **metadata}
    mutation = {
        **_mutation_report(
            report,
            spec,
            authoritative_targets=targets,
            authoritative_metadata=metadata,
            authoritative_receipts=receipts,
        ),
        **metadata,
    }
    if not validation["all_passed"]:
        raise ValueError("method validation failed")
    if mutation["survivors"]:
        raise ValueError("mutation survivors remain")
    card = {
        "schema": "htt.pr173.result_card.v2",
        "pr_id": "PR-173",
        **metadata,
        "process_execution_status": "PASS_REPRODUCIBLE_TERMINAL_EVIDENCE",
        "scientific_result": (
            "0_RESOLVED_1_NUMERICALLY_UNRESOLVED_5_NOT_CERTIFIABLE_"
            "1_NOT_EVALUATED"
        ),
        "scientific_status": "OPEN",
        "success_dependency_satisfied": True,
        "result_path": str(OUT["report"].relative_to(REPO)),
        "method_validation_path": str(OUT["validation"].relative_to(REPO)),
        "mutation_report_path": str(OUT["mutation"].relative_to(REPO)),
        "resolved_target_ids": [
            row["target_id"] for row in targets
            if row["numerical_resolution_status"] == RESOLVED
        ],
        "unresolved_target_ids": [
            row["target_id"] for row in targets
            if row["numerical_resolution_status"] == UNRESOLVED
        ],
        "not_certifiable_target_ids": [
            row["target_id"] for row in targets
            if row["replicate_lineage_status"] in (LINEAGE_MISSING, LINEAGE_INVALID)
        ],
        "not_evaluated_target_ids": [
            row["target_id"] for row in targets
            if row["input_availability_status"] != INPUT_AVAILABLE
        ],
        "claim_boundary": "C1 numerical-resolution infrastructure; no physical promotion",
    }
    preliminary = {
        "report": report,
        "validation": validation,
        "mutation": mutation,
        "card": card,
    }
    artifacts = {
        str(OUT[name].relative_to(REPO)): hashlib.sha256(
            (json.dumps(payload, indent=2, sort_keys=True, allow_nan=False) + "\n").encode(
                "utf-8"
            )
        ).hexdigest()
        for name, payload in preliminary.items()
    }
    manifest = {
        "schema": "htt.pr173.artifact_manifest.v2",
        "pr_id": "PR-173",
        **metadata,
        "artifact_count": len(artifacts),
        "artifacts": artifacts,
        "source_authority_receipts": receipts,
        "success_dependency_satisfied": True,
        "scientific_status": "OPEN",
        "allowed_use": [
            "finite_ensemble_numerical_resolution_reporting",
            "downstream_MC_budget_gate",
        ],
        "forbidden_use": [
            "physical_signal_or_noise_classification",
            "null_model_validation",
            "family_or_geometry_identification",
            "native_transfer_validation",
            "partial_DESI_mock_calibration",
        ],
    }
    return {**preliminary, "manifest": manifest}


def _render(payload: Mapping[str, Any]) -> str:
    return json.dumps(payload, indent=2, sort_keys=True, allow_nan=False) + "\n"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--write", action="store_true")
    group.add_argument("--check", action="store_true")
    args = parser.parse_args(argv)
    outputs = build_outputs()
    mismatches: list[str] = []
    for name, payload in outputs.items():
        path = OUT[name]
        rendered = _render(payload)
        if args.write:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(rendered, encoding="utf-8")
        elif not path.is_file() or path.read_text(encoding="utf-8") != rendered:
            mismatches.append(str(path.relative_to(REPO)))
    receipt = {
        "ok": not mismatches,
        "mismatches": mismatches,
        "terminal": outputs["report"]["terminal"],
        "summary": outputs["report"]["summary"],
    }
    print(json.dumps(receipt, indent=2, sort_keys=True))
    return 0 if not mismatches else 2


if __name__ == "__main__":
    raise SystemExit(main())
