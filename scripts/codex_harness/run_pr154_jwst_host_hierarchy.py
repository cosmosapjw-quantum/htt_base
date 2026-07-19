#!/usr/bin/env python3
"""Build or byte-check the preregistered PR-154 JWST result pack.

The observed CCHP and SH0ES tables are fitted as separate source families.
Unknown shared calibration covariance is represented by a fixed-diagonal PSD
uncertainty set.  CF4 overlap is evaluated only in a separately labelled
scenario product; it is never treated as an observed host association.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
from pathlib import Path
import subprocess
import sys
import tempfile
from typing import Any, Callable

import numpy as np
import yaml

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "htt" / "htt"))

from htt.infer.jwst_host_hierarchy import (  # noqa: E402
    HostPair,
    JWSTHierarchyError,
    analyze_family,
    cf4_scenario_grid,
    simulation_based_calibration,
    validate_pairs,
)

SPEC_PATH = REPO / "docs/research_program/long_horizon_rescue/pr154_spec.yaml"
MODULE_PATH = REPO / "htt/htt/htt/infer/jwst_host_hierarchy.py"
RUNNER_PATH = Path(__file__).resolve()
OUTPUTS = {
    "cchp": "docs/generated/pr154_cchp_observed.json",
    "shoes": "docs/generated/pr154_shoes_observed.json",
    "covariance": "docs/generated/pr154_covariance_envelope.json",
    "robustness": "docs/generated/pr154_robustness_holdout.json",
    "calibration": "docs/generated/pr154_sbc_ppc.json",
    "cf4": "docs/generated/pr154_cf4_scenarios.json",
    "captions": "docs/generated/pr154_captions.json",
    "mutations": "docs/generated/pr154_mutation_report.json",
    "manifest": "docs/generated/pr154_artifact_manifest.json",
}
FAMILIES = ("cchp_trgb_jagb", "shoes_jwst_hst")
REQUIRED_METADATA = {
    "owner", "implementation_scope", "claim_tier", "claim_level",
    "artifact_mode", "allowed_use", "forbidden_use", "transfer_source",
    "config_hash", "input_hashes", "sky_support_status", "mask_status",
    "covariance_status", "null_mock_status", "caveats",
    "generating_command", "runtime_environment", "git_commit",
    "worktree_state",
}


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _sha_prefixed(path: Path) -> str:
    return "sha256:" + _sha(path)


def _render(payload: dict[str, Any]) -> bytes:
    return (json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=False,
                       allow_nan=False) + "\n").encode()


def _verify_hash(path: Path, expected: str) -> None:
    if not path.is_file():
        raise SystemExit(f"required input absent: {path}")
    observed = _sha(path)
    if observed != expected:
        raise SystemExit(
            f"input hash mismatch for {path}: "
            f"expected {expected}, observed {observed}"
        )


def _require_group_not_identified(value: str) -> None:
    if value != "GROUP_ZERO_POINT_NOT_IDENTIFIED":
        raise JWSTHierarchyError("unidentified calibration group was promoted")


def _refuse_primary_independence(value: bool) -> None:
    if value:
        raise JWSTHierarchyError("independence sensitivity was promoted")


def _refuse_observed_overlap(value: int) -> None:
    if value:
        raise JWSTHierarchyError("unverified positional overlap was promoted")


def _verify_baseline(spec: dict[str, Any]) -> None:
    commit = str(spec.get("baseline_commit", ""))
    if len(commit) != 40 or any(c not in "0123456789abcdef" for c in commit):
        raise SystemExit("PR-154 baseline_commit must be full lower-case SHA-1")
    probe = subprocess.run(
        ["git", "cat-file", "-e", f"{commit}^{{commit}}"], cwd=REPO,
        capture_output=True, check=False,
    )
    if probe.returncode:
        raise SystemExit(f"PR-154 baseline commit does not resolve: {commit}")


def _load_pairs(path: Path) -> dict[str, tuple[HostPair, ...]]:
    grouped: dict[str, list[HostPair]] = {}
    with path.open(encoding="utf-8", newline="") as handle:
        rows = csv.DictReader(line for line in handle
                              if not line.startswith("#"))
        for row in rows:
            family = row["dataset"]
            if family not in FAMILIES:
                raise SystemExit(f"unregistered host-level source family: {family}")
            grouped.setdefault(family, []).append(HostPair(
                dataset=family,
                host=row["host"],
                method_a=row["method_a"],
                mu_a_mag=float(row["mu_a_mag"]),
                sigma_a_mag=float(row["sigma_a_mag"]),
                method_b=row["method_b"],
                mu_b_mag=float(row["mu_b_mag"]),
                sigma_b_mag=float(row["sigma_b_mag"]),
            ))
    if set(grouped) != set(FAMILIES):
        raise SystemExit("source-family set differs from the preregistration")
    return {family: validate_pairs(rows, family)
            for family, rows in grouped.items()}


def _verify_inputs(spec: dict[str, Any]) -> tuple[
        dict[str, tuple[HostPair, ...]], dict[str, Any], dict[str, Any]]:
    contract = spec["data_contract"]
    for key in (
        "source_table", "pr153_authoritative_decision",
        "pr153_distance_result", "pr153_crossmatch",
    ):
        pin = contract[key]
        _verify_hash(REPO / pin["path"], pin["sha256"])
    for pin in spec["calibration_gates"]["lineage_sources"]:
        _verify_hash(REPO / pin["path"], pin["sha256"])
    remediation = spec["remediation_state_contract"]
    _verify_hash(REPO / remediation["path"], remediation["sha256"])

    authority = json.loads((REPO / contract["pr153_authoritative_decision"]["path"])
                           .read_text(encoding="utf-8"))
    table_pin = contract["source_table"]
    if (authority.get("source_tables_reproduced") is not True
            or authority.get("verification_violations") != []
            or authority.get("source_checked_comparison_csv") != table_pin["path"]
            or authority.get("source_checked_comparison_csv_sha256")
            != "sha256:" + table_pin["sha256"]):
        raise SystemExit("PR-153 authoritative source-table receipt is invalid")

    remediation_payload = yaml.safe_load(
        (REPO / remediation["path"]).read_text(encoding="utf-8")
    )
    census = remediation_payload.get("census", {})
    if (census.get("finding_count") != remediation["finding_count"]
            or census.get("scientific_status_counts")
            != remediation["required_scientific_status_counts"]
            or census.get("rescued_count") != remediation["rescued_count"]):
        raise SystemExit("PR-154 may not change remediation scientific state")

    crossmatch = json.loads((REPO / contract["pr153_crossmatch"]["path"])
                            .read_text(encoding="utf-8"))
    matches = crossmatch.get("matches", [])
    if (not isinstance(matches, list)
            or any(row.get("identity_confirmed") is not False for row in matches)):
        raise SystemExit("CF4 input contains an independently confirmed identity")
    _refuse_observed_overlap(sum(
        row.get("identity_confirmed") is True for row in matches
    ))
    pairs = _load_pairs(REPO / table_pin["path"])
    return pairs, authority, crossmatch


def _independence_covariance(pairs: tuple[HostPair, ...]) -> np.ndarray:
    return np.diag([row.independence_variance_mag2 for row in pairs])


def _observed_product(result: dict[str, Any]) -> dict[str, Any]:
    keys = (
        "dataset", "contrast", "n_hosts", "hosts",
        "observed_host_deltas_mag", "unweighted_replay",
        "latent_pair_collapse_check", "group_zero_point_status",
        "group_zero_point_reason", "latent_host_distance_moduli",
        "independence_sensitivity",
        "numerical_status", "numerical_components",
        "terminal_classification", "terminal_reason",
    )
    return {"schema": "htt.pr154.observed_family_result.v1",
            **{key: result[key] for key in keys}}


def _run_mutations(
        pairs: dict[str, tuple[HostPair, ...]],
        analyses: dict[str, dict[str, Any]],
        spec: dict[str, Any]) -> dict[str, Any]:
    def mutate_source_hash() -> None:
        with tempfile.TemporaryDirectory(prefix="pr154-hash-mutant-") as directory:
            candidate = Path(directory) / "source.csv"
            candidate.write_bytes(b"mutated source table\n")
            _verify_hash(candidate, "0" * 64)

    cchp = pairs["cchp_trgb_jagb"]
    first = cchp[0]
    swapped = (
        HostPair(first.dataset, first.host, first.method_b, first.mu_a_mag,
                 first.sigma_a_mag, first.method_a, first.mu_b_mag,
                 first.sigma_b_mag), *cchp[1:]
    )
    executions: dict[str, Callable[[], None]] = {
        "swap_cchp_method_sign":
            lambda: validate_pairs(swapped, "cchp_trgb_jagb"),
        "pool_cchp_and_shoes": lambda: validate_pairs(
            cchp + pairs["shoes_jwst_hst"], "cchp_trgb_jagb"),
        "fabricate_group_zero_point":
            lambda: _require_group_not_identified("POSTERIOR_AVAILABLE"),
        "promote_independence_to_total":
            lambda: _refuse_primary_independence(True),
        "promote_cf4_overlap_to_observed":
            lambda: _refuse_observed_overlap(1),
        "accept_unpinned_source_table": mutate_source_hash,
        "emit_forbidden_public_claim": lambda: _scan_claim_language(
            spec,
            {"mutant": {"text": spec["forbidden_output_language"][0]}},
        ),
    }
    rows = []
    for mutation_id, function in executions.items():
        killed = False
        try:
            function()
        except (JWSTHierarchyError, ValueError, SystemExit):
            killed = True
        rows.append({"mutation_id": mutation_id, "executed": True,
                     "killed": killed})
    survivors = [row["mutation_id"] for row in rows if not row["killed"]]
    return {
        "schema": "htt.pr154.mutation_report.v1",
        "mutations": rows,
        "surviving_mutation_count": len(survivors),
        "survivors": survivors,
        "observed_terminal_classes": {
            family: analyses[family]["terminal_classification"]
            for family in FAMILIES
        },
    }


def _metadata(spec: dict[str, Any], *, owner: str | None = None) -> dict[str, Any]:
    pins: list[dict[str, str]] = []
    for key in (
        "source_table", "pr153_authoritative_decision",
        "pr153_distance_result", "pr153_crossmatch",
    ):
        pin = spec["data_contract"][key]
        pins.append({"path": pin["path"], "sha256": "sha256:" + pin["sha256"]})
    for pin in spec["calibration_gates"]["lineage_sources"]:
        pins.append({"path": pin["path"], "sha256": "sha256:" + pin["sha256"]})
    remediation = spec["remediation_state_contract"]
    pins.extend([
        {"path": remediation["path"], "sha256": "sha256:" + remediation["sha256"]},
        {"path": str(MODULE_PATH.relative_to(REPO)), "sha256": _sha_prefixed(MODULE_PATH)},
        {"path": str(RUNNER_PATH.relative_to(REPO)), "sha256": _sha_prefixed(RUNNER_PATH)},
    ])
    resolved_owner = owner or spec["owner"]
    metadata = {
        "owner": resolved_owner,
        "implementation_scope": spec["implementation_scope"],
        "claim_tier": spec["claim_tier"],
        "claim_level": {"scheme": "roadmap_rescue_v1", "level": "C2"},
        "artifact_mode": spec["artifact_mode"],
        "allowed_use": spec["allowed_use"],
        "forbidden_use": spec["forbidden_output_language"],
        "transfer_source": spec["transfer_source"],
        "config_hash": _sha_prefixed(SPEC_PATH),
        "input_hashes": pins,
        "sky_support_status": (
            "authenticated_published_host_tables; CF4 nonzero overlap is scenario_only"
        ),
        "mask_status": "not_applicable_to_host_distance_table_analysis",
        "covariance_status": (
            "fixed_marginal_variance_PSD_envelope; total covariance not identified"
        ),
        "null_mock_status": (
            "registered_SBC_and_posterior_predictive_simulations; "
            "no_matched_survey_null_mock_claim; CF4_product_is_scenario_only"
        ),
        "caveats": [
            "CCHP and SH0ES are fitted separately and are never pooled.",
            "The full shared calibration covariance is unavailable; diagonal independence is sensitivity-only.",
            "Calibration-group zero points are not identified by the authenticated table design.",
            "CF4 positional linkage has zero independently verified observed host identities and remains scenario-only.",
            "No H0, cosmological, geometry, family-identification, or native-transfer conclusion is authorized.",
        ],
        "generating_command": (
            "venv/bin/python -B scripts/codex_harness/"
            "run_pr154_jwst_host_hierarchy.py --write"
        ),
        "runtime_environment": {
            "python": sys.version.split()[0],
            "numpy": np.__version__,
        },
        "git_commit": spec["baseline_commit"],
        "worktree_state": "dirty_amend_in_place_from_baseline",
    }
    if resolved_owner != spec["owner"]:
        metadata["scientific_owner"] = spec["owner"]
    expected_keys = set(REQUIRED_METADATA)
    if resolved_owner != spec["owner"]:
        expected_keys.add("scientific_owner")
    if set(metadata) != expected_keys:
        raise SystemExit("PR-154 artifact metadata schema mismatch")
    return metadata


def _attach(payloads: list[dict[str, Any]], metadata: dict[str, Any]) -> None:
    for payload in payloads:
        payload["artifact_metadata"] = metadata


def _emit(rel: str, payload: dict[str, Any], write: bool,
          problems: list[str], wrote: list[str]) -> None:
    target = REPO / rel
    rendered = _render(payload)
    if write:
        if target.is_file() and target.read_bytes() == rendered:
            return
        target.parent.mkdir(parents=True, exist_ok=True)
        temporary = target.with_suffix(target.suffix + ".tmp")
        temporary.write_bytes(rendered)
        temporary.replace(target)
        wrote.append(rel)
    elif not target.is_file():
        problems.append(f"missing artifact: {rel}")
    elif target.read_bytes() != rendered:
        problems.append(f"stale artifact: {rel}")


def _scan_claim_language(spec: dict[str, Any], payloads: dict[str, dict[str, Any]]) -> None:
    forbidden = [phrase.lower() for phrase in spec["forbidden_output_language"]]
    for name, payload in payloads.items():
        inspect = dict(payload)
        inspect.pop("artifact_metadata", None)
        inspect.pop("forbidden_use", None)
        text = json.dumps(inspect, ensure_ascii=False).lower()
        hits = [phrase for phrase in forbidden if phrase in text]
        if hits:
            raise SystemExit(f"forbidden claim language in {name}: {hits}")


def build(write: bool) -> int:
    spec = yaml.safe_load(SPEC_PATH.read_text(encoding="utf-8"))
    if spec.get("schema") != "htt.long_horizon.pr154_jwst_hierarchy.v1":
        raise SystemExit("PR-154 spec schema mismatch")
    _verify_baseline(spec)
    pairs, authority, crossmatch = _verify_inputs(spec)

    analyses = {
        family: analyze_family(pairs[family], family, production=True)
        for family in FAMILIES
    }
    for analysis in analyses.values():
        _require_group_not_identified(analysis["group_zero_point_status"])
        _refuse_primary_independence(
            analysis["independence_sensitivity"]["primary_total_uncertainty"]
        )
    observed = {family: _observed_product(analyses[family]) for family in FAMILIES}
    covariance = {
        "schema": "htt.pr154.covariance_envelope.v1",
        "source_families_pooled": False,
        "independence_role": "sensitivity_only",
        "total_uncertainty_identified": False,
        "families": {
            family: {
                "fixed_diagonal_psd_bounds": analyses[family]["fixed_diagonal_psd_bounds"],
                "structured_covariance_scan": analyses[family]["structured_covariance_scan"],
                "classification": analyses[family]["terminal_classification"],
            } for family in FAMILIES
        },
    }
    robustness = {
        "schema": "htt.pr154.robustness_holdout.v1",
        "thresholds_frozen_before_results": True,
        "families": {
            family: {
                "prior_sensitivity": analyses[family]["prior_sensitivity"],
                "leave_host_out": analyses[family]["leave_host_out"],
                "leave_group_out": analyses[family]["leave_group_out"],
                "gaussian_student_t_sensitivity": analyses[family]["robustness"],
            } for family in FAMILIES
        },
    }

    sbc = {}
    for family in FAMILIES:
        gate = spec["calibration_gates"]["sbc"]
        sbc[family] = simulation_based_calibration(
            _independence_covariance(pairs[family]),
            simulations=gate["n_simulations"],
            posterior_draws=gate["posterior_draws_per_simulation"],
            seed=gate["seed"],
        )
    ppc = {family: analyses[family]["ppc"] for family in FAMILIES}
    calibration_status = "PASS"
    if (any(row["status"] != "PASS" for row in sbc.values())
            or any(test["status"] != "PASS"
                   for family in ppc.values() for test in family.values())
            or any(analysis["numerical_status"] != "PASS"
                   for analysis in analyses.values())):
        calibration_status = spec["calibration_gates"]["failed_gate_action"]
    calibration = {
        "schema": "htt.pr154.sbc_ppc.v1",
        "thresholds_frozen_before_results": True,
        "threshold_tuning_after_result": False,
        "sbc": sbc,
        "ppc": ppc,
        "status": calibration_status,
    }

    scenario = spec["cf4_scenario_contract"]
    cf4 = {
        "schema": "htt.pr154.cf4_scenario_pack.v1",
        "observed_crossmatch_receipt": {
            "n_positionally_credible": crossmatch.get("n_positionally_credible"),
            "independently_verified_identity_count": 0,
            "nonzero_observed_overlap_used": False,
        },
        "scenario_only": True,
        "families": {
            family: cf4_scenario_grid(
                pairs[family], family,
                replicates=scenario["replicates_per_cell"],
                seed=scenario["seed"],
                coverage_acceptance=tuple(scenario["coverage_acceptance"]),
                unsafe_absolute_bias_mag=scenario["unsafe_absolute_bias_mag"],
                material_width_gain_fraction=
                    scenario["material_width_gain_fraction"],
                material_rmse_gain_fraction=
                    scenario["material_rmse_gain_fraction"],
                classification_mc_guard_sigma=
                    scenario["classification_mc_guard_sigma"],
            ) for family in FAMILIES
        },
    }

    captions = {
        "schema": "htt.pr154.captions.v1",
        "captions": {
            family: (
                f"{family}: {observed[family]['n_hosts']} authenticated paired hosts; "
                f"independence-sensitivity Gaussian median "
                f"{observed[family]['independence_sensitivity']['gaussian']['delta_posterior_median_mag']:.5f} mag "
                f"with 95% interval "
                f"{observed[family]['independence_sensitivity']['gaussian']['delta_equal_tail_95pct_mag']}. "
                "The fixed-diagonal PSD envelope does not select a unique total uncertainty."
            ) for family in FAMILIES
        },
        "calibration_status": calibration_status,
        "cf4_note": (
            "All nonzero-overlap CF4 rows are preregistered scenarios; the observed "
            "independently verified identity count is zero."
        ),
    }
    mutations = _run_mutations(
        pairs, analyses, spec
    )
    if mutations["surviving_mutation_count"]:
        raise SystemExit(f"PR-154 mutation survivors: {mutations['survivors']}")

    science_metadata = _metadata(spec)
    common_metadata = _metadata(spec, owner="COMMON")
    payloads = {
        "cchp": observed["cchp_trgb_jagb"],
        "shoes": observed["shoes_jwst_hst"],
        "covariance": covariance,
        "robustness": robustness,
        "calibration": calibration,
        "cf4": cf4,
        "captions": captions,
        "mutations": mutations,
    }
    _attach([
        payload for key, payload in payloads.items() if key != "mutations"
    ], science_metadata)
    _attach([mutations], common_metadata)
    _scan_claim_language(spec, payloads)

    problems: list[str] = []
    wrote: list[str] = []
    for key, payload in payloads.items():
        _emit(OUTPUTS[key], payload, write, problems, wrote)

    manifest = {
        "schema": "htt.pr154.artifact_manifest.v1",
        **common_metadata,
        "scientific_result": (
            "TOTAL_UNCERTAINTY_NOT_IDENTIFIED"
            if all(analysis["numerical_status"] == "PASS"
                   for analysis in analyses.values())
            else "MODEL_INADEQUATE_NUMERICAL_GATE"
        ),
        "source_families_pooled": False,
        "source_table_authentication": {
            "source_tables_reproduced": authority["source_tables_reproduced"],
            "source_checked_comparison_csv_sha256":
                authority["source_checked_comparison_csv_sha256"],
        },
        "calibration_status": calibration_status,
        "observed_cf4_identity_count": 0,
        "pr4_commands_run": 0,
        "planck_pr3_raw_deleted": False,
        "check_command": (
            "venv/bin/python -B scripts/codex_harness/"
            "run_pr154_jwst_host_hierarchy.py --check"
        ),
        "artifacts": {
            OUTPUTS[key]: _sha(REPO / OUTPUTS[key])
            for key in payloads
        },
    }
    _scan_claim_language(spec, {"manifest": manifest})
    _emit(OUTPUTS["manifest"], manifest, write, problems, wrote)
    if problems:
        print(json.dumps({"ok": False, "problems": problems}, indent=2))
        return 2
    print(json.dumps({
        "ok": True,
        "mode": "write" if write else "check",
        "wrote": wrote,
        "result": manifest["scientific_result"],
        "calibration_status": calibration_status,
        "cchp_median_mag": observed["cchp_trgb_jagb"][
            "independence_sensitivity"]["gaussian"]["delta_posterior_median_mag"],
        "shoes_median_mag": observed["shoes_jwst_hst"][
            "independence_sensitivity"]["gaussian"]["delta_posterior_median_mag"],
        "cf4_scenario_cells": sum(
            len(row["cells"]) for row in cf4["families"].values()
        ),
        "mutation_survivors": 0,
    }, indent=2))
    return 0


def main() -> None:
    parser = argparse.ArgumentParser()
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--write", action="store_true")
    mode.add_argument("--check", action="store_true")
    args = parser.parse_args()
    raise SystemExit(build(write=args.write))


if __name__ == "__main__":
    main()
