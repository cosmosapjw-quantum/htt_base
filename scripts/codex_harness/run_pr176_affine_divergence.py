#!/usr/bin/env python3
"""Produce or verify the prospectively frozen PR-176 result pack.

``--preflight`` authenticates authorities without importing the numerical
evaluator. ``--write`` executes one recoverable manifest-last transaction. ``--check`` recomputes
the complete generation in memory and compares canonical bytes without
modifying the workspace.
"""

from __future__ import annotations

import argparse
import copy
import fcntl
import hashlib
import importlib
import json
import os
from pathlib import Path
import platform
import shutil
import sys
from typing import Callable, Iterator, Mapping

import yaml


REPO = Path(__file__).resolve().parents[2]
SPEC_PATH = REPO / "docs/research_program/long_horizon_rescue/pr176_spec.yaml"
ERRATUM_PATH = REPO / "docs/research_program/long_horizon_rescue/pr176_spec_erratum.yaml"
GENERATED = REPO / "docs/generated"
GROUPS_PATH = REPO / "workdir/obs_bundle/pecvel/cf4_full/cf4_groups.npz"
SPEC_COMMIT = "06083de0b575e19aada5d56ef10fb043f654faf2"
FROZEN_SPEC_SHA256 = "d92d31f6adf8a879e62f47f82fefa47b2aa79f504fd0ce71b2fefce1cbb6c945"
FROZEN_ERRATUM_SHA256 = "1793516af0032e2e2b341ef37ff4cb59c49f2b7871e664e2d12154c1bb3cfd92"
NUMERICAL_PRIMITIVE_SHA256 = "d400bade76acabbc37486029607cd9aac2df799cd08e5dd380577938978dda0d"
OUTPUT_NAMES = (
    "pr176_source_authority.json",
    "pr176_divergence_measurement.json",
    "pr176_injection_validation.json",
    "pr176_dependence_bound.json",
    "pr176_cross_falsifier_result.json",
    "pr176_mutation_report.json",
    "pr176_result_card.json",
    "pr176_execution_receipt.json",
    "pr176_artifact_manifest.json",
)
LOCK_NAME = ".pr176-write.lock"
JOURNAL_NAME = ".pr176-transaction.json"
STAGE_NAME = ".pr176-stage"
BACKUP_NAME = ".pr176-backup"
RELEVANT_PATHS = (
    "docs/research_program/long_horizon_rescue/pr176_spec.yaml",
    "docs/research_program/long_horizon_rescue/pr176_spec_erratum.yaml",
    "docs/audits/pr176_primary_sources/tsagas_divergence_record.md",
    "htt/obsstat/cf4_affine_divergence.py",
    "htt/obsstat/cf4_velocity_estimators.py",
    "htt/obsstat/cf4_forward_simulator.py",
    "scripts/codex_harness/run_pr176_affine_divergence.py",
)
REQUIRED_METADATA = {
    "owner",
    "implementation_scope",
    "claim_tier",
    "claim_level",
    "scientific_artifact_mode",
    "public_use",
    "transfer_source",
    "config_hash",
    "input_hashes",
    "sky_support_status",
    "mask_status",
    "covariance_status",
    "null_mock_status",
    "caveats",
    "generating_command",
    "git_commit_or_worktree_state",
}


class Pr176RunnerError(ValueError):
    """Fail-closed PR-176 production or verification error."""


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _canonical_bytes(payload: object) -> bytes:
    return (json.dumps(
        payload,
        sort_keys=True,
        indent=2,
        allow_nan=False,
    ) + "\n").encode("utf-8")


def _semantic_hash(payload: object) -> str:
    return hashlib.sha256(json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    ).encode("utf-8")).hexdigest()


def _load_yaml(path: Path) -> dict:
    payload = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise Pr176RunnerError(f"{path.relative_to(REPO)} must be a mapping")
    return payload


def _pr_card() -> tuple[dict, str]:
    backlog = _load_yaml(REPO / "docs/codex_handoff/pr_backlog.yaml")
    cards = backlog.get("prs", backlog)
    if not isinstance(cards, list):
        raise Pr176RunnerError("canonical backlog has no PR-card list")
    matches = [row for row in cards if isinstance(row, dict) and row.get("id") == "PR-176"]
    if len(matches) != 1:
        raise Pr176RunnerError("canonical backlog must contain exactly one PR-176 card")
    return matches[0], _semantic_hash(matches[0])


def _iter_authorities(spec: Mapping[str, object]) -> Iterator[Mapping[str, object]]:
    sources = spec.get("source_authorities")
    if not isinstance(sources, Mapping):
        raise Pr176RunnerError("source authorities missing from SPEC")
    for section_name in ("dependency_receipts", "upstream_manifests", "code_authorities"):
        section = sources.get(section_name)
        if not isinstance(section, Mapping):
            raise Pr176RunnerError(f"source authority section {section_name} missing")
        for authority in section.values():
            if not isinstance(authority, Mapping):
                raise Pr176RunnerError(f"invalid authority in {section_name}")
            yield authority
    for name in ("compact_cf4_groups", "primary_formula_record"):
        authority = sources.get(name)
        if not isinstance(authority, Mapping):
            raise Pr176RunnerError(f"source authority {name} missing")
        yield authority


def _config_projection(spec: Mapping[str, object]) -> tuple[dict[str, object], dict[str, str]]:
    domain = spec.get("catalogue_domain")
    estimand = spec.get("divergence_estimand")
    injection = spec.get("channel_injections")
    if not all(isinstance(value, Mapping) for value in (domain, estimand, injection)):
        raise Pr176RunnerError("numerical SPEC sections must be mappings")
    coverage = injection.get("covariance_self_consistency")
    if not isinstance(coverage, Mapping):
        raise Pr176RunnerError("coverage contract missing")
    radii = tuple(float(value) for value in domain["cumulative_physical_radius_mpc"])
    seed_map = coverage.get("seed_by_radius")
    if not isinstance(seed_map, Mapping):
        raise Pr176RunnerError("coverage seed map missing")
    coverage_interval = coverage.get("accepted_component_coverage_interval")
    if not isinstance(coverage_interval, list) or len(coverage_interval) != 2:
        raise Pr176RunnerError("coverage interval must have two endpoints")
    if domain.get("velocity_definition") != "v_radial=V3k-H0_fixed*Dist":
        raise Pr176RunnerError("velocity convention drift")
    if domain.get("harmonic_scale_convention") != "lambda_physical=2*catalogue_ball_radius":
        raise Pr176RunnerError("radius/diameter convention drift")
    values: dict[str, tuple[object, str]] = {
        "h0_km_s_mpc": (float(domain["fixed_h0_km_s_mpc"]), "catalogue_domain.fixed_h0_km_s_mpc"),
        "sigma_nl_km_s": (float(domain["nonlinear_dispersion_km_s"]), "catalogue_domain.nonlinear_dispersion_km_s"),
        "subsample_rows": (int(domain["subsample_rows"]), "catalogue_domain.subsample_rows"),
        "subsample_seed": (int(domain["subsample_seed"]), "catalogue_domain.subsample_seed"),
        "radii_mpc": (radii, "catalogue_domain.cumulative_physical_radius_mpc"),
        "primary_radius_mpc": (float(domain["primary_radius_mpc"]), "catalogue_domain.primary_radius_mpc"),
        "c_km_s": (299792.458, "catalogue_domain.frame[registered_speed_of_light]"),
        "rank_tolerance": (float(estimand["rank_tolerance"]), "divergence_estimand.rank_tolerance"),
        "minimum_singular_value_ratio": (float(estimand["minimum_singular_value_ratio"]), "divergence_estimand.minimum_singular_value_ratio"),
        "maximum_standardized_condition_number": (float(estimand["maximum_standardized_condition_number"]), "divergence_estimand.maximum_standardized_condition_number"),
        "minimum_theta_retained_information": (float(estimand["minimum_theta_retained_information"]), "divergence_estimand.minimum_theta_retained_information"),
        "exact_injection_tolerance_relative": (
            float(injection["deterministic_exact"]["tolerance_relative"]),
            "channel_injections.deterministic_exact.tolerance_relative",
        ),
        "coverage_draws": (int(coverage["draws_per_radius"]), "channel_injections.covariance_self_consistency.draws_per_radius"),
        "coverage_seeds": (tuple(int(seed_map[f"{radius:g}"]) for radius in radii), "channel_injections.covariance_self_consistency.seed_by_radius"),
        "confidence_level": (float(coverage["confidence_level"]), "channel_injections.covariance_self_consistency.confidence_level"),
        "minimum_component_coverage": (float(coverage_interval[0]), "channel_injections.covariance_self_consistency.accepted_component_coverage_interval[0]"),
        "maximum_component_coverage": (float(coverage_interval[1]), "channel_injections.covariance_self_consistency.accepted_component_coverage_interval[1]"),
        "covariance_jitter_kms2": (1.0e-6, "PR146_registered_cholesky_jitter"),
    }
    kwargs = {key: value for key, (value, _) in values.items()}
    crosswalk = {key: source for key, (_, source) in values.items()}
    return kwargs, crosswalk


def preflight(*, require_evaluator_unimported: bool = True) -> dict[str, object]:
    evaluator_imported = "obsstat.cf4_affine_divergence" in sys.modules
    if require_evaluator_unimported and evaluator_imported:
        raise Pr176RunnerError("preflight imported the numerical evaluator")
    spec = _load_yaml(SPEC_PATH)
    if _sha256(SPEC_PATH) != FROZEN_SPEC_SHA256:
        raise Pr176RunnerError("prospectively frozen PR-176 SPEC hash drift")
    if _sha256(ERRATUM_PATH) != FROZEN_ERRATUM_SHA256:
        raise Pr176RunnerError("review-issued PR-176 erratum hash drift")
    if spec.get("schema") != "htt.pr176.spec.v1" or spec.get("frozen_before_result") is not True:
        raise Pr176RunnerError("invalid or non-frozen PR-176 SPEC")
    erratum = _load_yaml(ERRATUM_PATH)
    if erratum.get("schema") != "htt.pr176.spec_erratum.v1":
        raise Pr176RunnerError("invalid PR-176 review erratum")
    integrity = erratum.get("result_integrity")
    if not isinstance(integrity, Mapping) or any(
        integrity.get(key) is not False
        for key in ("seeds_changed", "thresholds_changed", "radius_or_frame_changed",
                    "q_response_authority_changed", "covariance_authority_changed")
    ):
        raise Pr176RunnerError("PR-176 erratum changes a frozen scientific choice")
    prospective = spec.get("prospective_review")
    if not isinstance(prospective, Mapping) or prospective.get(
        "observed_velocity_or_divergence_values_seen_before_freeze"
    ) is not False:
        raise Pr176RunnerError("result-blind prospective receipt missing")
    card, card_hash = _pr_card()
    if card.get("owner") != "OBSSTAT" or card.get("public_use") is not False:
        raise Pr176RunnerError("PR-card owner/public-use authority drift")
    if card.get("claim_tier_ceiling") != "conditional":
        raise Pr176RunnerError("PR-card claim ceiling drift")
    expected_dependencies = {"PR-133", "PR-144", "PR-146", "PR-148", "PR-167", "PR-173"}
    if set(card.get("depends", [])) != expected_dependencies:
        raise Pr176RunnerError("PR-card dependency drift")
    status = _load_yaml(REPO / "docs/codex_handoff/pr_status.yaml")
    completed = set(status.get("completed", []))
    missing_dependencies = sorted(expected_dependencies - completed)
    if missing_dependencies:
        raise Pr176RunnerError(f"PR-176 dependencies incomplete: {missing_dependencies}")
    checked: dict[str, str] = {}
    for authority in _iter_authorities(spec):
        relative = str(authority.get("path", ""))
        expected = str(authority.get("sha256", ""))
        path = REPO / relative
        if not path.is_file() or not expected:
            raise Pr176RunnerError(f"missing authority: {relative}")
        actual = _sha256(path)
        if actual != expected:
            raise Pr176RunnerError(f"authority hash drift: {relative}")
        checked[relative] = actual
    kwargs, crosswalk = _config_projection(spec)
    return {
        "ok": True,
        "schema": "htt.pr176.preflight.v1",
        "spec_sha256": FROZEN_SPEC_SHA256,
        "erratum_sha256": FROZEN_ERRATUM_SHA256,
        "spec_commit": SPEC_COMMIT,
        "pr_card_semantic_hash": card_hash,
        "dependencies_complete": sorted(expected_dependencies),
        "authorities": checked,
        "config": {
            key: list(value) if isinstance(value, tuple) else value
            for key, value in kwargs.items()
        },
        "config_crosswalk": crosswalk,
        "numerical_evaluator_imported": evaluator_imported,
        "partial_pr151_mock_use": False,
    }


def _metadata(config: Mapping[str, object], preflight_receipt: Mapping[str, object],
              relevant_hashes: Mapping[str, str]) -> dict[str, object]:
    input_hashes = dict(preflight_receipt["authorities"])
    relevant_root = _semantic_hash(dict(relevant_hashes))
    return {
        "owner": "OBSSTAT",
        "contributors": ["BASS", "HTT"],
        "implementation_scope": ["obsstat"],
        "claim_tier": "conditional",
        "claim_level": {"scheme": "roadmap_rescue_v1", "level": "C3"},
        "scientific_artifact_mode": "standard_internal",
        "public_use": False,
        "transfer_source": "none",
        "config_hash": _semantic_hash(dict(config)),
        "input_hashes": input_hashes,
        "sky_support_status": "fixed CF4 group catalogue support in published CMB frame; no apex scan",
        "mask_status": "cumulative physical-radius balls after one fixed PR-145 subsample; no external sky mask",
        "covariance_status": (
            "within-divergence PR-146 Gorski-plus-measurement propagation only; "
            "matched divergence-q covariance unidentified; PR-148 covariance not reused"
        ),
        "null_mock_status": (
            "deterministic channel injections and 5000-draw coefficient-covariance self-consistency; "
            "no matched q-channel null"
        ),
        "caveats": [
            "The affine trace is a raw-catalogue window coefficient, not an exact GR or light-cone divergence field.",
            "Theta is scalar and has no apex; structural separation from translation/monopole is not leakage immunity.",
            "H0 is fixed at 74.6 km/s/Mpc because theta has the exact theta(H0+dH)=theta(H0)-3dH alias.",
            "Both signed q response bridges and their matched cross-channel covariance are unavailable.",
            "The covariance injections are propagation self-consistency, not independent physical validation.",
            "A frozen covariance self-consistency gate miss is retained on a separate validation axis and is not rethresholded.",
            "No detection, acceleration, cosmological anisotropy, geometry, family, or transfer claim is made.",
        ],
        "generating_command": [
            "venv/bin/python",
            "-B",
            "scripts/codex_harness/run_pr176_affine_divergence.py",
            "--write",
        ],
        "git_commit_or_worktree_state": {
            "prospective_spec_commit": SPEC_COMMIT,
            "relevant_content_root": relevant_root,
            "production_code_bound_by_content_hash": True,
        },
        "spec_sha256": FROZEN_SPEC_SHA256,
        "spec_erratum_sha256": FROZEN_ERRATUM_SHA256,
        "code_hashes": dict(relevant_hashes),
    }


def _validate_metadata(payload: Mapping[str, object]) -> None:
    metadata = payload.get("metadata")
    if not isinstance(metadata, Mapping) or not REQUIRED_METADATA <= set(metadata):
        raise Pr176RunnerError("artifact metadata incomplete")
    if metadata.get("owner") != "OBSSTAT" or metadata.get("public_use") is not False:
        raise Pr176RunnerError("artifact owner/public-use drift")


def _numerical_primitive_projection(
    pack: Mapping[str, Mapping[str, object]],
) -> dict[str, object]:
    measurement = pack["pr176_divergence_measurement.json"]
    injection = pack["pr176_injection_validation.json"]
    result = pack["pr176_cross_falsifier_result.json"]
    return {
        "candidate_coefficients_by_radius": measurement.get("candidate_coefficients_by_radius"),
        "simultaneous_theta_intervals": measurement.get("simultaneous_theta_intervals"),
        "all_divergence_response_gates_pass": measurement.get(
            "all_divergence_response_gates_pass"
        ),
        "channel_injections": injection.get("channel_injections"),
        "all_injection_gates_pass": injection.get("all_injection_gates_pass"),
        "all_deterministic_exact_injections_pass": injection.get(
            "all_deterministic_exact_injections_pass"
        ),
        "all_covariance_self_consistency_gates_pass": injection.get(
            "all_covariance_self_consistency_gates_pass"
        ),
        "terminal": result.get("terminal"),
        "divergence_rank_information_gate_pass": result.get(
            "divergence_rank_information_gate_pass"
        ),
        "deterministic_channel_injection_gate_pass": result.get(
            "deterministic_channel_injection_gate_pass"
        ),
        "covariance_self_consistency_gate_pass": result.get(
            "covariance_self_consistency_gate_pass"
        ),
        "divergence_candidate_coefficients": result.get(
            "divergence_candidate_coefficients"
        ),
    }


def _validate_core(pack: Mapping[str, Mapping[str, object]], spec: Mapping[str, object]) -> None:
    source = pack["pr176_source_authority.json"]
    measurement = pack["pr176_divergence_measurement.json"]
    injection = pack["pr176_injection_validation.json"]
    dependence = pack["pr176_dependence_bound.json"]
    result = pack["pr176_cross_falsifier_result.json"]
    card = pack["pr176_result_card.json"]
    for payload in pack.values():
        _validate_metadata(payload)
    if source.get("authority_ok") is not True:
        raise Pr176RunnerError("source authority not satisfied")
    expected_input = spec["source_authorities"]["compact_cf4_groups"]["sha256"]
    if source.get("compact_cf4_sha256") != expected_input:
        raise Pr176RunnerError("compact CF4 source hash drift")
    if source.get("raw_reconstruction_values_used") != []:
        raise Pr176RunnerError("raw reconstruction value entered PR-176")
    if measurement.get("theta_is_scalar_without_apex") is not True:
        raise Pr176RunnerError("scalar theta was assigned an apex")
    if measurement.get("theta_apex") is not None:
        raise Pr176RunnerError("theta apex must be null")
    if measurement.get("structurally_distinct_not_leakage_immune") is not True:
        raise Pr176RunnerError("structural-distinction/leakage firewall failed")
    if measurement.get("legacy_beta_closure_used") is not False:
        raise Pr176RunnerError("legacy beta closure entered the measurement")
    rows = measurement.get("candidate_coefficients_by_radius")
    if not isinstance(rows, list) or [row.get("radius_mpc") for row in rows] != [75.0, 100.0, 125.0]:
        raise Pr176RunnerError("frozen radius rows missing or reordered")
    response_from_rows = True
    for row in rows:
        if row.get("h0_km_s_mpc") != 74.6:
            raise Pr176RunnerError("frozen H0 drift")
        if row.get("q_point_estimate") is not None or row.get("q_interval") is not None:
            raise Pr176RunnerError("unauthenticated q estimate emitted")
        diagnostics = row.get("diagnostics")
        coefficients = row.get("coefficient_summary")
        if not isinstance(diagnostics, Mapping) or not isinstance(coefficients, Mapping):
            raise Pr176RunnerError("candidate coefficient or diagnostic row missing")
        response_from_rows = response_from_rows and diagnostics.get("response_gate_pass") is True
        if set(coefficients) != {
            "Bx", "By", "Bz", "M", "theta", "Sxx_minus_Szz",
            "Syy_minus_Szz", "Sxy", "Sxz", "Syz",
        }:
            raise Pr176RunnerError("corrected affine coefficient basis labels missing")
    response_flag = measurement.get("all_divergence_response_gates_pass")
    if response_flag is not response_from_rows:
        raise Pr176RunnerError("aggregate divergence response flag contradicts radius diagnostics")
    injection_rows = injection.get("channel_injections")
    if not isinstance(injection_rows, list) or len(injection_rows) != 3:
        raise Pr176RunnerError("three radius injection receipts required")
    exact_pass = all(
        row.get("deterministic_exact", {}).get("all_pass") is True
        for row in injection_rows
    )
    covariance_pass = all(
        row.get("covariance_self_consistency", {}).get("all_pass") is True
        for row in injection_rows
    )
    if injection.get("all_deterministic_exact_injections_pass") is not exact_pass:
        raise Pr176RunnerError("deterministic injection aggregate contradicts primitives")
    if injection.get("all_covariance_self_consistency_gates_pass") is not covariance_pass:
        raise Pr176RunnerError("covariance injection aggregate contradicts primitives")
    if injection.get("all_injection_gates_pass") is not (exact_pass and covariance_pass):
        raise Pr176RunnerError("combined injection aggregate contradicts primitives")
    expected_validation_axis = (
        "PASS" if covariance_pass else "FROZEN_COVARIANCE_SELF_CONSISTENCY_GATE_FAILED"
    )
    if injection.get("validation_axis") != expected_validation_axis:
        raise Pr176RunnerError("validation axis contradicts frozen injection primitives")
    bridges = dependence.get("q_response_bridges")
    if not isinstance(bridges, list) or len(bridges) != 2:
        raise Pr176RunnerError("two signed q response receipts required")
    if any(bridge.get("authenticated_for_cf4_window") is not False for bridge in bridges):
        raise Pr176RunnerError("q response was self-authorized")
    covariance = dependence.get("matched_divergence_q_covariance")
    if not isinstance(covariance, Mapping):
        raise Pr176RunnerError("matched cross-channel covariance receipt missing")
    if covariance.get("available") is not False or covariance.get("source") is not None:
        raise Pr176RunnerError("unidentified covariance was promoted")
    if covariance.get("pr148_covariance_reused") is not False:
        raise Pr176RunnerError("PR-148 covariance was reused")
    if dependence.get("nested_radius_independence_assumed") is not False:
        raise Pr176RunnerError("nested-radius independence was assumed")
    terminal = str(result.get("terminal", ""))
    expected_terminal = (
        "NON_INFORMATIVE_DIVERGENCE_RESPONSE"
        if not response_from_rows
        else "NON_INFORMATIVE_Q_RESPONSE_UNAVAILABLE"
    )
    if terminal != expected_terminal:
        raise Pr176RunnerError("terminal does not follow the frozen ordered truth table")
    if result.get("divergence_rank_information_gate_pass") is not response_from_rows:
        raise Pr176RunnerError("result divergence gate contradicts measurement primitives")
    if result.get("deterministic_channel_injection_gate_pass") is not exact_pass:
        raise Pr176RunnerError("result exact-injection gate contradicts primitives")
    if result.get("covariance_self_consistency_gate_pass") is not covariance_pass:
        raise Pr176RunnerError("result covariance gate contradicts primitives")
    if result.get("validation_axis") != expected_validation_axis:
        raise Pr176RunnerError("result validation axis contradicts injection receipt")
    expected_candidates = [
        {
            "radius_mpc": row["radius_mpc"],
            "theta": row["coefficient_summary"]["theta"],
        }
        for row in rows
    ]
    if result.get("divergence_candidate_coefficients") != expected_candidates:
        raise Pr176RunnerError("cross-result candidate coefficients drift from source rows")
    if result.get("divergence_channel_accepted_measurement") is not False:
        raise Pr176RunnerError("candidate coefficients were promoted to an accepted measurement")
    if terminal.startswith("NON_INFORMATIVE_"):
        if result.get("q_channel_result") is not None or result.get("significance") is not None:
            raise Pr176RunnerError("non-informative terminal promoted a q result")
        if terminal == "NON_INFORMATIVE_Q_RESPONSE_UNAVAILABLE" and all(
            bridge.get("authenticated_for_cf4_window") is True for bridge in bridges
        ):
            raise Pr176RunnerError("q-response-unavailable terminal contradicts receipts")
    elif not all(bridge.get("authenticated_for_cf4_window") is True for bridge in bridges):
        raise Pr176RunnerError("informative terminal without signed q response")
    if result.get("success_dependency_satisfied") is not True:
        raise Pr176RunnerError("reproducible non-identification must satisfy dependency success")
    if card.get("status") != terminal:
        raise Pr176RunnerError("result card terminal drift")
    mandatory = str(card.get("mandatory_claim_language", "")).lower()
    for phrase in (
        "structurally distinct",
        "not leakage-immune",
        "non_informative_q_response_unavailable",
        "covariance self-consistency gate failed",
    ):
        if phrase not in mandatory:
            raise Pr176RunnerError(f"mandatory claim language missing: {phrase}")
    primitive_hash = _semantic_hash(_numerical_primitive_projection(pack))
    if primitive_hash != NUMERICAL_PRIMITIVE_SHA256:
        raise Pr176RunnerError(
            f"numerical primitive reference drift: actual={primitive_hash}"
        )


def _mutation_report(base: Mapping[str, Mapping[str, object]], spec: Mapping[str, object],
                     metadata: Mapping[str, object]) -> dict[str, object]:
    mutations: list[tuple[str, tuple[str, ...], object]] = [
        ("source_hash_reseal", ("pr176_source_authority.json", "compact_cf4_sha256"), "0" * 64),
        ("raw_reconstruction_truth", ("pr176_source_authority.json", "raw_reconstruction_values_used"), ["Vpec"]),
        ("scalar_theta_apex", ("pr176_divergence_measurement.json", "theta_apex"), {"ra_deg": 1.0, "dec_deg": 2.0}),
        ("theta_scalar_flag_removed", ("pr176_divergence_measurement.json", "theta_is_scalar_without_apex"), False),
        ("leakage_immunity_promotion", ("pr176_divergence_measurement.json", "structurally_distinct_not_leakage_immune"), False),
        ("legacy_beta_closure", ("pr176_divergence_measurement.json", "legacy_beta_closure_used"), True),
        ("h0_refit", ("pr176_divergence_measurement.json", "candidate_coefficients_by_radius", "0", "h0_km_s_mpc"), 70.0),
        ("q_point_reseal", ("pr176_divergence_measurement.json", "candidate_coefficients_by_radius", "0", "q_point_estimate"), -0.2),
        ("theta_numeric_reseal", ("pr176_divergence_measurement.json", "candidate_coefficients_by_radius", "0", "coefficient_summary", "theta", "estimate"), 1.0e99),
        ("theta_covariance_reseal", ("pr176_divergence_measurement.json", "candidate_coefficients_by_radius", "0", "coefficient_summary", "theta", "marginal_sd"), 1.0e99),
        ("response_gate_reseal", ("pr176_divergence_measurement.json", "all_divergence_response_gates_pass"), False),
        ("injection_gate_reseal", ("pr176_injection_validation.json", "all_injection_gates_pass"), True),
        ("interval_reseal", ("pr176_divergence_measurement.json", "simultaneous_theta_intervals", "theta_intervals_by_radius", "75", "0"), -1.0e99),
        ("q_bridge_unity", ("pr176_dependence_bound.json", "q_response_bridges", "0", "authenticated_for_cf4_window"), True),
        ("matched_covariance_self_authorized", ("pr176_dependence_bound.json", "matched_divergence_q_covariance", "available"), True),
        ("pr148_covariance_reuse", ("pr176_dependence_bound.json", "matched_divergence_q_covariance", "pr148_covariance_reused"), True),
        ("nested_radius_independence", ("pr176_dependence_bound.json", "nested_radius_independence_assumed"), True),
        ("informative_terminal_without_response", ("pr176_cross_falsifier_result.json", "terminal"), "CONSERVATIVE_CHANNEL_FALSIFIER"),
        ("noninformative_q_result_promotion", ("pr176_cross_falsifier_result.json", "q_channel_result"), {"delta_q": -1.0}),
        ("success_dependency_denied", ("pr176_cross_falsifier_result.json", "success_dependency_satisfied"), False),
        ("public_use_promotion", ("pr176_result_card.json", "metadata", "public_use"), True),
    ]
    rows: list[dict[str, object]] = []
    for name, path, replacement in mutations:
        candidate = copy.deepcopy(base)
        target: object = candidate
        for component in path[:-1]:
            if isinstance(target, list):
                target = target[int(component)]
            else:
                target = target[component]  # type: ignore[index]
        if isinstance(target, list):
            target[int(path[-1])] = replacement
        else:
            target[path[-1]] = replacement  # type: ignore[index]
        killed = False
        reason = None
        try:
            _validate_core(candidate, spec)
        except Pr176RunnerError as exc:
            killed = True
            reason = str(exc)
        rows.append({"mutation": name, "killed": killed, "reason": reason})
    return {
        "schema": "htt.pr176.mutation_report.v1",
        "metadata": dict(metadata),
        "mutations": rows,
        "killed": sum(bool(row["killed"]) for row in rows),
        "survived": sum(not bool(row["killed"]) for row in rows),
        "all_killed": all(bool(row["killed"]) for row in rows),
    }


def _build_payloads() -> dict[str, dict[str, object]]:
    pre = preflight(require_evaluator_unimported=False)
    spec = _load_yaml(SPEC_PATH)
    kwargs, crosswalk = _config_projection(spec)
    module = importlib.import_module("obsstat.cf4_affine_divergence")
    config = module.AffineDivergenceConfig(**kwargs)
    analysis = module.analyze_cf4_affine_divergence(str(GROUPS_PATH), config)
    relevant_hashes = {path: _sha256(REPO / path) for path in RELEVANT_PATHS}
    metadata = _metadata(config.to_dict(), pre, relevant_hashes)
    source = {
        "schema": "htt.pr176.source_authority.v1",
        "metadata": metadata,
        "authority_ok": True,
        "spec_commit": SPEC_COMMIT,
        "spec_sha256": FROZEN_SPEC_SHA256,
        "spec_erratum_sha256": FROZEN_ERRATUM_SHA256,
        "pr_card_semantic_hash": pre["pr_card_semantic_hash"],
        "authenticated_authorities": pre["authorities"],
        "compact_cf4_sha256": spec["source_authorities"]["compact_cf4_groups"]["sha256"],
        "primary_formula_record": spec["source_authorities"]["primary_formula_record"],
        "raw_reconstruction_values_used": [],
        "partial_pr151_mock_use": False,
    }
    measurement = {
        "schema": "htt.pr176.divergence_measurement.v1",
        "metadata": metadata,
        "estimand": "raw_CF4_affine_trace_theta",
        "units": "km_s_Mpc",
        "candidate_coefficients_by_radius": analysis["measurements"],
        "simultaneous_theta_intervals": analysis["simultaneous_theta_intervals"],
        "all_divergence_response_gates_pass": analysis["all_divergence_response_gates_pass"],
        "theta_is_scalar_without_apex": True,
        "theta_apex": None,
        "structurally_distinct_not_leakage_immune": True,
        "legacy_beta_closure_used": False,
        "h0_alias_registered": "theta_hat(H0+delta_H)=theta_hat(H0)-3*delta_H",
        "coefficient_rows_are_accepted_measurement": False,
        "coefficient_status": "COMPUTED_CANDIDATE_DIAGNOSTICS_COVARIANCE_SELF_CONSISTENCY_GATE_FAILED",
        "physical_interpretation": "catalogue_window_affine_trace_candidate_only",
    }
    all_exact_injections_pass = all(
        bool(row["deterministic_exact"].get("all_pass", False))
        for row in analysis["injection_validation"]
    )
    all_covariance_injections_pass = all(
        bool(row["covariance_self_consistency"].get("all_pass", False))
        for row in analysis["injection_validation"]
    )
    injection = {
        "schema": "htt.pr176.injection_validation.v1",
        "metadata": metadata,
        "channel_injections": analysis["injection_validation"],
        "all_injection_gates_pass": analysis["all_injection_gates_pass"],
        "all_deterministic_exact_injections_pass": all_exact_injections_pass,
        "all_covariance_self_consistency_gates_pass": all_covariance_injections_pass,
        "validation_axis": (
            "PASS" if all_covariance_injections_pass
            else "FROZEN_COVARIANCE_SELF_CONSISTENCY_GATE_FAILED"
        ),
        "physical_covariance_validated": False,
        "interpretation": "response and covariance-propagation self-consistency only",
    }
    dependence = {
        "schema": "htt.pr176.dependence_bound.v1",
        "metadata": metadata,
        "pre_pr155_conservative_only": True,
        "within_divergence_scales": analysis["simultaneous_theta_intervals"],
        "nested_radius_independence_assumed": False,
        "q_response_bridges": [
            {
                "id": bridge["id"],
                "source_equation": bridge["source_equation"],
                "authenticated_for_cf4_window": False,
                "response": None,
            }
            for bridge in spec["q_response_bridges"]["required"]
        ],
        "formula_response_coefficients_only": [
            {
                "radius_mpc": row["radius_mpc"],
                "lambda_mpc": row["lambda_mpc"],
                "coefficients": row["formula_response_coefficients_only"],
                "scientific_q_use": False,
            }
            for row in analysis["measurements"]
        ],
        "matched_divergence_q_covariance": {
            "available": False,
            "source": None,
            "pr148_covariance_reused": False,
            "reason": "no matched divergence-q joint replicate or authenticated covariance",
        },
        "future_conservative_bound": spec["dependence_contract"]["future_bound"],
        "future_familywise_contrasts": spec["dependence_contract"]["future_cross_channel_contrasts"],
        "evaluated_cross_channel_interval": None,
    }
    divergence_identifiable = bool(analysis["all_divergence_response_gates_pass"])
    if not divergence_identifiable:
        terminal = "NON_INFORMATIVE_DIVERGENCE_RESPONSE"
        reason = "one or more frozen divergence rank/condition/information gates failed"
    else:
        terminal = "NON_INFORMATIVE_Q_RESPONSE_UNAVAILABLE"
        reason = "both separately signed CF4-window q response bridges are unavailable"
    result = {
        "schema": "htt.pr176.cross_falsifier_result.v1",
        "metadata": metadata,
        "terminal": terminal,
        "terminal_reason": reason,
        "scientific_result_reproducible": True,
        "success_dependency_satisfied": True,
        "divergence_rank_information_gate_pass": divergence_identifiable,
        "deterministic_channel_injection_gate_pass": all_exact_injections_pass,
        "covariance_self_consistency_gate_pass": all_covariance_injections_pass,
        "validation_axis": injection["validation_axis"],
        "raw_coefficients_computed": divergence_identifiable,
        "divergence_channel_accepted_measurement": False,
        "divergence_candidate_coefficients": [
            {
                "radius_mpc": row["radius_mpc"],
                "theta": None if row["coefficient_summary"] is None else row["coefficient_summary"]["theta"],
            }
            for row in analysis["measurements"]
        ],
        "q_channel_result": None,
        "significance": None,
        "family_identification": None,
        "native_transfer_validation": None,
        "structurally_distinct_not_leakage_immune": True,
        "interpretation": (
            "Raw-CF4 affine coefficients were computed as candidate diagnostics, but the "
            "frozen covariance self-consistency gate failed, so no accepted covariance-validated "
            "divergence measurement is emitted. The registered cross-channel terminal is a typed "
            "q-response non-identification."
        ),
    }
    card = {
        "schema": "htt.pr176.result_card.v1",
        "metadata": metadata,
        "pr_id": "PR-176",
        "status": terminal,
        "mandatory_claim_language": (
            "Raw-CF4 affine coefficients are computed candidate diagnostics, not an accepted "
            "covariance-validated measurement: the frozen covariance self-consistency gate failed. "
            "The channel is structurally distinct from bulk translation and a radial monopole, "
            "but is not leakage-immune. The registered cross-channel terminal is NON_INFORMATIVE_Q_RESPONSE_UNAVAILABLE "
            "because both signed CF4-window q responses are unavailable."
        ),
        "allowed_use": "internal conditional candidate diagnostics and reproducible q-response non-identification",
        "public_use": False,
        "forbidden_uses": spec["forbidden_claims"],
    }
    core: dict[str, dict[str, object]] = {
        "pr176_source_authority.json": source,
        "pr176_divergence_measurement.json": measurement,
        "pr176_injection_validation.json": injection,
        "pr176_dependence_bound.json": dependence,
        "pr176_cross_falsifier_result.json": result,
        "pr176_result_card.json": card,
    }
    _validate_core(core, spec)
    mutation = _mutation_report(core, spec, metadata)
    if mutation["all_killed"] is not True:
        raise Pr176RunnerError("mutation suite did not kill every registered drift")
    execution = {
        "schema": "htt.pr176.execution_receipt.v1",
        "metadata": metadata,
        "argv": metadata["generating_command"],
        "cwd": str(REPO),
        "prospective_spec_commit": SPEC_COMMIT,
        "relevant_path_hashes": relevant_hashes,
        "relevant_content_root": _semantic_hash(relevant_hashes),
        "runtime_versions": {
            "python": platform.python_version(),
            "platform": platform.platform(),
            "numpy": importlib.import_module("numpy").__version__,
            "scipy": importlib.import_module("scipy").__version__,
        },
        "thread_environment": {
            key: os.environ.get(key)
            for key in ("PYTHONHASHSEED", "OPENBLAS_NUM_THREADS", "OMP_NUM_THREADS", "MKL_NUM_THREADS")
        },
        "full_rehash_of_external_large_payloads": False,
        "compact_cf4_rehashed": True,
        "publication_mode": "recoverable_durable_manifest_last_transaction",
        "reader_locking": "shared_check_lock_vs_exclusive_writer_lock",
    }
    payloads = dict(core)
    payloads["pr176_mutation_report.json"] = mutation
    payloads["pr176_execution_receipt.json"] = execution
    artifact_entries = {
        name: {
            "sha256": hashlib.sha256(_canonical_bytes(payload)).hexdigest(),
            "size_bytes": len(_canonical_bytes(payload)),
        }
        for name, payload in payloads.items()
    }
    manifest = {
        "schema": "htt.pr176.artifact_manifest.v1",
        "metadata": metadata,
        "candidate_cannot_authorize_itself": True,
        "independent_closeout_authorization": {
            "status": "PENDING_EXTERNAL_ADJUDICATION",
            "receipt": None,
            "policy": "this candidate generation supplies integrity but cannot authorize its own scientific closeout",
        },
        "artifacts": artifact_entries,
        "generation_root": _semantic_hash(artifact_entries),
        "source_edges": {
            "spec": FROZEN_SPEC_SHA256,
            "spec_erratum": FROZEN_ERRATUM_SHA256,
            "compact_cf4": source["compact_cf4_sha256"],
            "pr_card": source["pr_card_semantic_hash"],
            "relevant_content": execution["relevant_content_root"],
            "numerical_primitive_reference": NUMERICAL_PRIMITIVE_SHA256,
        },
    }
    payloads["pr176_artifact_manifest.json"] = manifest
    if set(payloads) != set(OUTPUT_NAMES):
        raise Pr176RunnerError("result-pack filename contract drift")
    return payloads


def _fsync_file(path: Path) -> None:
    with path.open("rb") as handle:
        os.fsync(handle.fileno())


def _fsync_directory(path: Path) -> None:
    descriptor = os.open(path, os.O_RDONLY)
    try:
        os.fsync(descriptor)
    finally:
        os.close(descriptor)


def _write_durable(path: Path, content: bytes) -> None:
    with path.open("wb") as handle:
        handle.write(content)
        handle.flush()
        os.fsync(handle.fileno())


def _cleanup_transaction_files() -> None:
    shutil.rmtree(GENERATED / STAGE_NAME, ignore_errors=True)
    shutil.rmtree(GENERATED / BACKUP_NAME, ignore_errors=True)
    journal = GENERATED / JOURNAL_NAME
    if journal.exists():
        journal.unlink()
    _fsync_directory(GENERATED)


def _recover_transaction() -> dict[str, object]:
    """Recover an interrupted manifest-last transaction under writer lock."""

    journal_path = GENERATED / JOURNAL_NAME
    stage = GENERATED / STAGE_NAME
    backup = GENERATED / BACKUP_NAME
    if not journal_path.exists():
        # These fixed-name directories can only precede journal publication;
        # no tracked target has moved at that point.
        shutil.rmtree(stage, ignore_errors=True)
        shutil.rmtree(backup, ignore_errors=True)
        return {"recovered": False, "action": "none"}
    journal = json.loads(journal_path.read_text(encoding="utf-8"))
    if journal.get("schema") != "htt.pr176.transaction.v1":
        raise Pr176RunnerError("invalid interrupted-transaction journal")
    if journal.get("output_names") != list(OUTPUT_NAMES):
        raise Pr176RunnerError("interrupted transaction output set drift")
    new_hashes = journal.get("new_hashes")
    old_hashes = journal.get("old_hashes")
    if not isinstance(new_hashes, Mapping) or not isinstance(old_hashes, Mapping):
        raise Pr176RunnerError("interrupted transaction hash receipts missing")
    generation_complete = all(
        (GENERATED / name).is_file() and _sha256(GENERATED / name) == new_hashes[name]
        for name in OUTPUT_NAMES
    )
    if generation_complete:
        _cleanup_transaction_files()
        return {"recovered": True, "action": "roll_forward_complete_generation"}
    for name in OUTPUT_NAMES:
        target = GENERATED / name
        saved = backup / name
        old_hash = old_hashes.get(name)
        if saved.is_file():
            os.replace(saved, target)
        elif old_hash is None:
            if target.exists():
                target.unlink()
        elif not target.is_file() or _sha256(target) != old_hash:
            raise Pr176RunnerError(f"cannot safely roll back interrupted artifact: {name}")
    _fsync_directory(GENERATED)
    for name, old_hash in old_hashes.items():
        target = GENERATED / name
        if old_hash is None:
            if target.exists():
                raise Pr176RunnerError(f"rollback retained new artifact: {name}")
        elif not target.is_file() or _sha256(target) != old_hash:
            raise Pr176RunnerError(f"rollback hash mismatch: {name}")
    _cleanup_transaction_files()
    return {"recovered": True, "action": "rollback_to_previous_generation"}


def _publish_generation(
    payloads: Mapping[str, Mapping[str, object]],
    *,
    replace: Callable[[Path, Path], None] | None = None,
) -> None:
    """Durably publish with backups, a journal, and deterministic recovery."""

    replace_file = replace or (lambda source, target: os.replace(source, target))
    stage = GENERATED / STAGE_NAME
    backup = GENERATED / BACKUP_NAME
    journal_path = GENERATED / JOURNAL_NAME
    if stage.exists() or backup.exists() or journal_path.exists():
        raise Pr176RunnerError("transaction paths must be recovered before publication")
    stage.mkdir()
    backup.mkdir()
    new_hashes: dict[str, str] = {}
    old_hashes: dict[str, str | None] = {}
    for name in OUTPUT_NAMES:
        content = _canonical_bytes(payloads[name])
        staged = stage / name
        _write_durable(staged, content)
        new_hashes[name] = hashlib.sha256(content).hexdigest()
        target = GENERATED / name
        old_hashes[name] = _sha256(target) if target.is_file() else None
    _fsync_directory(stage)
    _fsync_directory(backup)
    journal = {
        "schema": "htt.pr176.transaction.v1",
        "output_names": list(OUTPUT_NAMES),
        "manifest_installed_last": OUTPUT_NAMES[-1],
        "new_hashes": new_hashes,
        "old_hashes": old_hashes,
    }
    _write_durable(journal_path, _canonical_bytes(journal))
    _fsync_directory(GENERATED)
    for name in OUTPUT_NAMES:
        target = GENERATED / name
        if target.is_file():
            replace_file(target, backup / name)
    _fsync_directory(backup)
    _fsync_directory(GENERATED)
    for name in OUTPUT_NAMES:
        replace_file(stage / name, GENERATED / name)
    _fsync_directory(GENERATED)
    for name, expected_hash in new_hashes.items():
        if not (GENERATED / name).is_file() or _sha256(GENERATED / name) != expected_hash:
            raise Pr176RunnerError(f"published artifact verification failed: {name}")
    _cleanup_transaction_files()


def write_generation() -> dict[str, object]:
    GENERATED.mkdir(parents=True, exist_ok=True)
    lock_path = GENERATED / LOCK_NAME
    with lock_path.open("a+b") as lock:
        fcntl.flock(lock.fileno(), fcntl.LOCK_EX)
        recovery = _recover_transaction()
        payloads = _build_payloads()
        _publish_generation(payloads)
        return {
            "ok": True,
            "mode": "write",
            "written": len(OUTPUT_NAMES),
            "terminal": payloads["pr176_cross_falsifier_result.json"]["terminal"],
            "generation_root": payloads["pr176_artifact_manifest.json"]["generation_root"],
            "recovery": recovery,
        }


def check_generation() -> dict[str, object]:
    GENERATED.mkdir(parents=True, exist_ok=True)
    lock_path = GENERATED / LOCK_NAME
    with lock_path.open("a+b") as lock:
        fcntl.flock(lock.fileno(), fcntl.LOCK_SH)
        if (GENERATED / JOURNAL_NAME).exists():
            raise Pr176RunnerError("interrupted publication requires writer recovery")
        expected = _build_payloads()
        mismatches: list[str] = []
        for name in OUTPUT_NAMES:
            path = GENERATED / name
            if not path.is_file() or path.read_bytes() != _canonical_bytes(expected[name]):
                mismatches.append(name)
        if mismatches:
            raise Pr176RunnerError(f"result pack is stale or incomplete: {mismatches}")
        manifest = expected["pr176_artifact_manifest.json"]
        for name, receipt in manifest["artifacts"].items():
            path = GENERATED / name
            if _sha256(path) != receipt["sha256"] or path.stat().st_size != receipt["size_bytes"]:
                raise Pr176RunnerError(f"artifact receipt mismatch: {name}")
        return {
            "ok": True,
            "mode": "check",
            "checked": len(OUTPUT_NAMES),
            "read_only": True,
            "terminal": expected["pr176_cross_falsifier_result.json"]["terminal"],
            "generation_root": manifest["generation_root"],
        }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    modes = parser.add_mutually_exclusive_group(required=True)
    modes.add_argument("--preflight", action="store_true")
    modes.add_argument("--write", action="store_true")
    modes.add_argument("--check", action="store_true")
    args = parser.parse_args()
    try:
        if args.preflight:
            payload = preflight()
        elif args.write:
            payload = write_generation()
        else:
            payload = check_generation()
    except (Pr176RunnerError, OSError, ValueError, RuntimeError) as exc:
        print(json.dumps({"ok": False, "error": str(exc)}, sort_keys=True), file=sys.stderr)
        return 1
    print(json.dumps(payload, sort_keys=True, indent=2, allow_nan=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
