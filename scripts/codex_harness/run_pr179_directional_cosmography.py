#!/usr/bin/env python3
"""Produce/check the frozen PR-179 raw-CF4 directional result pack.

``--preflight`` performs authority and spec checks without importing the
numerical evaluator.  ``--write`` executes the complete 19,999-draw analysis
and atomically publishes one generation.  ``--check`` independently rebuilds
the generation from the frozen sources and performs a read-only comparison.
"""

from __future__ import annotations

import argparse
import contextlib
import datetime as dt
import fcntl
import hashlib
import importlib
import json
import math
import os
from pathlib import Path
import platform
import shutil
import subprocess
import sys
import tempfile
from typing import Iterator, Mapping

import yaml


REPO = Path(__file__).resolve().parents[2]
SPEC_PATH = REPO / "docs/research_program/long_horizon_rescue/pr179_spec.yaml"
GENERATED = REPO / "docs/generated"
OUTPUT_NAMES = (
    "pr179_estimand_contract.json",
    "pr179_raw_catalogue_receipt.json",
    "pr179_response_identifiability.json",
    "pr179_null_calibration.json",
    "pr179_raw_systematics.json",
    "pr179_directional_cosmography_result.json",
    "pr179_result_card.json",
    "pr179_mutation_report.json",
    "pr179_execution_receipt.json",
    "pr179_artifact_manifest.json",
)
SPEC_COMMIT = "652f7c52"
FROZEN_SPEC_SHA256 = "ee92d8fb2862718b7d565d23c691dfe65aa730429588f825964ceaf8aa684106"
EXECUTION_RECEIPT_NAME = "pr179_execution_receipt.json"
JOURNAL_NAME = ".pr179-transaction.json"
LOCK_NAME = ".pr179-write.lock"
RELEVANT_EXECUTION_PATHS = (
    "docs/research_program/long_horizon_rescue/pr179_spec.yaml",
    "htt/obsstat/__init__.py",
    "htt/obsstat/catalogs/__init__.py",
    "htt/obsstat/catalogs/cf4_raw.py",
    "htt/obsstat/directional_cosmography.py",
    "htt/obsstat/finite_ensemble.py",
    "htt/src/common/finite_null_ranking.py",
    "scripts/codex_harness/run_pr179_directional_cosmography.py",
    "tests/obsstat/test_cf4_raw_catalog.py",
    "tests/pr_cards/test_pr_179_reconstruction_independent_directional_cosmograp.py",
)


class Pr179RunnerError(ValueError):
    """Fail-closed PR-179 producer/verifier error."""


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


def _load_spec() -> dict:
    payload = yaml.safe_load(SPEC_PATH.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise Pr179RunnerError("PR-179 spec must be a mapping")
    return payload


def _config_projection(
    spec: Mapping[str, object],
) -> tuple[dict[str, object], dict[str, dict[str, object]]]:
    """Project every numerical config field from the frozen SPEC.

    The one execution-only field (batch size) is declared explicitly here;
    it changes memory scheduling, not the estimand or random stream.
    """

    domain = spec["domain"]
    crossfit = spec["crossfit"]
    null = spec["matched_null"]
    response = spec["response_identifiability"]
    finite = spec["finite_rank"]
    fit = spec["catalogue_fit"]
    if not all(isinstance(value, Mapping) for value in (
        domain, crossfit, null, response, finite, fit
    )):
        raise Pr179RunnerError("PR-179 numerical SPEC sections must be mappings")
    if crossfit["cluster"] != "HEALPix_Nside2_NESTED_pixel_x_method_family":
        raise Pr179RunnerError("fold support is not the frozen Nside2 contract")
    if null["stratum"] != (
        "fold_x_HEALPix_Nside1_NESTED_x_broad_method_family_x_redshift_bin"
    ):
        raise Pr179RunnerError("null support is not the frozen Nside1 contract")
    nuisance = fit["nuisance"]
    if "train_only_Nside4_by_depth_selection_density" not in nuisance:
        raise Pr179RunnerError("selection nuisance is not the frozen Nside4 contract")
    cubic = response["directional_cubic_q_stress"]
    if not isinstance(cubic, Mapping) or cubic.get("nuisance") != "z_squared_times_n":
        raise Pr179RunnerError("q directional-cubic stress contract drift")
    if cubic.get("max_canonical_correlation") != response["max_H_q_canonical_correlation"]:
        raise Pr179RunnerError("one config threshold cannot represent divergent correlation gates")
    if finite["rng"] != "numpy_PCG64DXSM":
        raise Pr179RunnerError("frozen RNG contract drift")
    if fit["q_scale_b_q"] != 1.0:
        raise Pr179RunnerError("implemented q target requires frozen q_scale_b_q=1")
    uncertainty = str(finite["uncertainty"])
    if "Two-sided 95 percent Clopper-Pearson" not in uncertainty:
        raise Pr179RunnerError("finite-rank confidence-level contract drift")

    values: dict[str, tuple[object, str]] = {
        "c_km_s": (float(domain["c_km_s"]), "domain.c_km_s"),
        "z_min": (float(domain["z_min_inclusive"]), "domain.z_min_inclusive"),
        "z_max": (float(domain["z_max_inclusive"]), "domain.z_max_inclusive"),
        "peculiar_velocity_floor_km_s": (
            float(domain["peculiar_velocity_floor_km_s"]),
            "domain.peculiar_velocity_floor_km_s",
        ),
        "systematic_floor_mag": (
            float(domain["systematic_floor_mag"]), "domain.systematic_floor_mag"
        ),
        "folds": (int(crossfit["folds"]), "crossfit.folds"),
        "fold_nside": (2, "crossfit.cluster[HEALPix_Nside2]"),
        "stratum_nside": (1, "matched_null.stratum[HEALPix_Nside1]"),
        "selection_nside": (
            4, "catalogue_fit.nuisance[train_only_Nside4_by_depth_selection_density]"
        ),
        "redshift_bin_edges": (
            tuple(float(value) for value in null["redshift_bin_edges"]),
            "matched_null.redshift_bin_edges",
        ),
        "minimum_stratum_groups": (
            int(null["minimum_stratum_groups"]), "matched_null.minimum_stratum_groups"
        ),
        "minimum_overall_supported_fraction": (
            float(null["minimum_overall_supported_fraction"]),
            "matched_null.minimum_overall_supported_fraction",
        ),
        "minimum_broad_method_supported_fraction": (
            float(null["minimum_broad_method_supported_fraction"]),
            "matched_null.minimum_broad_method_supported_fraction",
        ),
        "max_condition_number": (
            float(response["max_condition_number"]),
            "response_identifiability.max_condition_number",
        ),
        "minimum_information_h": (
            float(response["minimum_retained_information_H"]),
            "response_identifiability.minimum_retained_information_H",
        ),
        "minimum_information_q": (
            float(response["minimum_retained_information_q"]),
            "response_identifiability.minimum_retained_information_q",
        ),
        "minimum_information_q_cubic": (
            float(cubic["minimum_retained_information"]),
            "response_identifiability.directional_cubic_q_stress.minimum_retained_information",
        ),
        "max_hq_canonical_correlation": (
            float(response["max_H_q_canonical_correlation"]),
            "response_identifiability.max_H_q_canonical_correlation",
        ),
        "null_draws": (int(finite["null_draws"]), "finite_rank.null_draws"),
        "null_batch_size": (64, "runner_execution_contract.null_batch_size"),
        "seed_entropy": (
            tuple(int(value) for value in finite["seed_sequence_entropy"]),
            "finite_rank.seed_sequence_entropy",
        ),
        "alpha": (float(finite["alpha"]), "finite_rank.alpha"),
        "confidence_level": (0.95, "finite_rank.uncertainty[two-sided_95_percent]"),
    }
    kwargs = {key: value for key, (value, _) in values.items()}
    crosswalk = {
        key: {
            "source": source,
            "value": list(value) if isinstance(value, tuple) else value,
        }
        for key, (value, source) in values.items()
    }
    return kwargs, crosswalk


def _pr179_card() -> tuple[dict, str, str]:
    backlog_path = REPO / "docs/codex_handoff/pr_backlog.yaml"
    backlog = yaml.safe_load(backlog_path.read_text(encoding="utf-8"))
    cards = backlog.get("prs", backlog) if isinstance(backlog, dict) else backlog
    if not isinstance(cards, list):
        raise Pr179RunnerError("canonical backlog has no PR card list")
    matches = [row for row in cards if isinstance(row, dict) and row.get("id") == "PR-179"]
    if len(matches) != 1:
        raise Pr179RunnerError("canonical backlog must contain exactly one PR-179 card")
    return matches[0], _semantic_hash(matches[0]), _sha256(backlog_path)


def preflight() -> dict[str, object]:
    spec = _load_spec()
    actual_spec_hash = _sha256(SPEC_PATH)
    if actual_spec_hash != FROZEN_SPEC_SHA256:
        raise Pr179RunnerError("prospectively frozen PR-179 SPEC hash drift")
    if spec.get("schema") != "htt.pr179.spec.v1":
        raise Pr179RunnerError("wrong PR-179 spec schema")
    if spec.get("frozen_before_result") is not True:
        raise Pr179RunnerError("PR-179 spec is not prospectively frozen")
    prospective = spec.get("prospective_review", {})
    if prospective.get("observed_directional_values_seen_before_freeze") is not False:
        raise Pr179RunnerError("prospective no-result-seen receipt missing")
    amendment = prospective.get("preflight_amendment", {})
    if amendment.get("observed_directional_values_seen") is not False:
        raise Pr179RunnerError("preflight amendment is not result-blind")
    card, card_hash, backlog_hash = _pr179_card()
    if card.get("owner") != "OBSSTAT" or card.get("public_use") is not False:
        raise Pr179RunnerError("PR-179 owner/public-use authority drift")
    if card.get("claim_tier_ceiling") != "conditional":
        raise Pr179RunnerError("PR-179 claim ceiling drift")
    expected_dependencies = {"PR-134", "PR-135", "PR-139", "PR-144", "PR-167", "PR-173"}
    if set(card.get("depends", [])) != expected_dependencies:
        raise Pr179RunnerError("PR-179 dependency authority drift")

    checked: dict[str, str] = {}
    sources = spec["source_authorities"]
    authorities: list[Mapping[str, object]] = list(
        sources["dependency_receipts"].values()
    ) + [sources["pr144_manifest"], sources["readme"], sources["table3"], sources["table4"]]
    for authority in authorities:
        relative = str(authority["path"])
        path = REPO / relative
        if not path.is_file():
            raise Pr179RunnerError(f"missing frozen authority: {relative}")
        actual = _sha256(path)
        if actual != authority["sha256"]:
            raise Pr179RunnerError(f"frozen authority hash mismatch: {relative}")
        checked[relative] = actual
    manifest = json.loads((REPO / sources["pr144_manifest"]["path"]).read_text())
    if manifest.get("status") != "authenticated" or manifest.get("id_parity", {}).get("parity") is not True:
        raise Pr179RunnerError("PR-144 authentication/parity gate failed")
    if manifest.get("id_parity", {}).get("n_unique") != 38053:
        raise Pr179RunnerError("PR-144 group-count authority drift")
    if spec["finite_rank"].get("null_draws") != 19999:
        raise Pr179RunnerError("production null budget drift")
    if spec["finite_rank"].get("tie_policy") != "conservative_greater_equal":
        raise Pr179RunnerError("finite-rank tie policy drift")
    config_kwargs, config_crosswalk = _config_projection(spec)
    return {
        "schema": "htt.pr179.preflight_receipt.v1",
        "ok": True,
        "numerical_evaluator_imported": False,
        "spec_sha256": actual_spec_hash,
        "pr179_card_semantic_sha256": card_hash,
        "backlog_sha256": backlog_hash,
        "authority_hashes": checked,
        "source_rows": {"table3": 38053, "table4": 38053, "unique_1PGC": 38053},
        "column_firewall_frozen": True,
        "matched_null_frozen": True,
        "null_draws": 19999,
        "config_projection_sha256": _semantic_hash({
            key: list(value) if isinstance(value, tuple) else value
            for key, value in config_kwargs.items()
        }),
        "config_crosswalk": config_crosswalk,
        "claim_ceiling": "roadmap_rescue_v1:C3 conditional",
        "public_use": False,
    }


def _runtime_versions(np_module, scipy_module, hp_module) -> dict[str, str]:
    return {
        "python": platform.python_version(),
        "numpy": str(np_module.__version__),
        "scipy": str(scipy_module.__version__),
        "healpy": str(hp_module.__version__),
        "platform": platform.platform(),
    }


def _git(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", *args], cwd=REPO, text=True, capture_output=True, check=False
    )


def _capture_execution_receipt() -> dict[str, object]:
    head = _git("rev-parse", "HEAD")
    if head.returncode != 0:
        raise Pr179RunnerError("cannot resolve generation git HEAD")
    status = _git("status", "--short", "--", *RELEVANT_EXECUTION_PATHS)
    if status.returncode != 0:
        raise Pr179RunnerError("cannot capture relevant generation worktree state")
    path_hashes = {
        relative: _sha256(REPO / relative) for relative in RELEVANT_EXECUTION_PATHS
    }
    argv = [sys.executable, *sys.argv]
    if not argv or argv[-1] != "--write":
        raise Pr179RunnerError("execution receipt may only be captured by --write")
    thread_environment = {
        key: os.environ.get(key)
        for key in (
            "PYTHONHASHSEED", "OPENBLAS_NUM_THREADS", "OMP_NUM_THREADS",
            "MKL_NUM_THREADS", "MPLCONFIGDIR", "PYTHONPATH",
        )
    }
    return {
        "schema": "htt.pr179.execution_receipt.v1",
        "captured_at_utc": dt.datetime.now(dt.timezone.utc).isoformat(),
        "argv": argv,
        "cwd": str(Path.cwd().resolve()),
        "git_head": head.stdout.strip(),
        "git_status_porcelain_relevant": status.stdout.splitlines(),
        "relevant_worktree_dirty": bool(status.stdout.strip()),
        "relevant_paths": list(RELEVANT_EXECUTION_PATHS),
        "relevant_path_hashes": path_hashes,
        "relevant_content_root": _semantic_hash(path_hashes),
        "thread_environment": thread_environment,
        "process_nice": os.getpriority(os.PRIO_PROCESS, 0),
    }


def _verify_execution_receipt(receipt: Mapping[str, object]) -> dict[str, object]:
    if receipt.get("schema") != "htt.pr179.execution_receipt.v1":
        raise Pr179RunnerError("execution receipt schema mismatch")
    if receipt.get("relevant_paths") != list(RELEVANT_EXECUTION_PATHS):
        raise Pr179RunnerError("execution receipt relevant-path allowlist drift")
    recorded_hashes = receipt.get("relevant_path_hashes")
    if not isinstance(recorded_hashes, Mapping):
        raise Pr179RunnerError("execution receipt path hashes are malformed")
    actual_hashes = {
        relative: _sha256(REPO / relative) for relative in RELEVANT_EXECUTION_PATHS
    }
    if dict(recorded_hashes) != actual_hashes:
        raise Pr179RunnerError("execution receipt source-content drift")
    if receipt.get("relevant_content_root") != _semantic_hash(actual_hashes):
        raise Pr179RunnerError("execution receipt content-root mismatch")
    head = receipt.get("git_head")
    if not isinstance(head, str) or len(head) != 40:
        raise Pr179RunnerError("execution receipt git commit is malformed")
    exists = _git("cat-file", "-e", f"{head}^{{commit}}")
    if exists.returncode != 0:
        raise Pr179RunnerError("execution receipt git commit no longer resolves")
    argv = receipt.get("argv")
    if not isinstance(argv, list) or not argv or argv[-1] != "--write":
        raise Pr179RunnerError("execution receipt did not record the producer invocation")
    return {key: value for key, value in receipt.items() if key != "metadata"}


def _metadata(
    *,
    spec_sha256: str,
    config_sha256: str,
    input_hashes: Mapping[str, str],
    code_hashes: Mapping[str, str],
    runtime_versions: Mapping[str, str],
    execution_receipt: Mapping[str, object],
) -> dict[str, object]:
    execution_hash = _semantic_hash(dict(execution_receipt))
    return {
        "owner": "OBSSTAT",
        "contributors": ["HTT"],
        "implementation_scope": ["obsstat"],
        "claim_tier": "conditional",
        "claim_level": {"scheme": "roadmap_rescue_v1", "level": "C3"},
        "scientific_artifact_mode": "standard_internal",
        "public_use": False,
        "transfer_source": "none",
        "spec_sha256": spec_sha256,
        "config_hash": config_sha256,
        "input_hashes": dict(sorted(input_hashes.items())),
        "code_hashes": dict(sorted(code_hashes.items())),
        "sky_support_status": "frozen J2000 catalogue support; no sky rotation",
        "mask_status": "no external sky mask; observed catalogue footprint held fixed",
        "selection_status": "broad-method/depth/sky/fold matched residual-permutation support",
        "covariance_status": (
            "reported marginal DMzp errors plus frozen velocity/systematic floors; "
            "unreported cross-method covariance not authenticated"
        ),
        "null_mock_status": "position-preserving finite matched-null permutations",
        "caveats": [
            "H_cat and q_cat are catalogue-fit coefficient labels, not physical cosmological fields.",
            "Result is conditional on available selection/method metadata and within-stratum residual exchangeability.",
            "Raw distance-modulus calibration, method mix, missingness, and sky-selection leakage remain possible.",
            "No reconstruction, CF4 P0 estimator, cosmology-corrected column, transfer, geometry, or family claim.",
        ],
        "generating_command": list(execution_receipt["argv"]),
        "execution_environment": dict(execution_receipt["thread_environment"]),
        "execution_receipt_core_sha256": execution_hash,
        "runtime_versions": dict(runtime_versions),
        "git_commit_or_worktree_state": {
            "git_head": execution_receipt["git_head"],
            "relevant_worktree_dirty": execution_receipt["relevant_worktree_dirty"],
            "git_status_porcelain_relevant": execution_receipt[
                "git_status_porcelain_relevant"
            ],
            "relevant_content_root": execution_receipt["relevant_content_root"],
            "prospective_spec_commit": SPEC_COMMIT,
        },
    }


def _validate_scientific_core(analysis: Mapping[str, object]) -> None:
    result = analysis["result"]
    raw = analysis["raw_catalogue_receipt"]
    if result["selection_systematics_conditional"] is not True:
        raise Pr179RunnerError("conditionality flag missing")
    if result["not_cosmological_anisotropy"] is not True:
        raise Pr179RunnerError("cosmological non-interpretation flag missing")
    firewall = raw["column_firewall"]
    if firewall.get("runtime_value_access_receipt_complete") is not True:
        raise Pr179RunnerError("runtime column-access receipt is incomplete")
    expected_access = {
        "table3": sorted([
            "1PGC", "Vcmb", "RAdeg", "DEdeg", "o_DMcal", "o_DMsnIa",
            "o_DMfp", "o_DMtf", "o_DMsbfo", "o_DMsbfi", "DMcal",
            "DMsnIa", "e_DMsnIa", "DMfp", "e_DMfp", "DMtf", "e_DMtf",
            "DMsbfo", "e_DMsbfo", "DMsbfi", "e_DMsbfi", "DMsnII", "e_DMsnII",
        ]),
        "table4": sorted(["1PGC", "DMzp", "e_DMzp"]),
    }
    if raw.get("accessed_columns") != expected_access:
        raise Pr179RunnerError("runtime column-access capability receipt drift")
    if any(firewall[key] for key in (
        "reconstruction_columns_used",
        "cosmology_corrected_columns_used",
        "cartesian_columns_used",
        "Dist_used",
        "P0_estimator_reused",
        "cosmological_monopole_modelled_or_subtracted",
    )):
        raise Pr179RunnerError("column or P0 firewall breach")
    terminal = result["terminal"]
    allowed = {
        "MATCHED_NULL_CONTAINS_DIRECTIONAL_STATISTIC",
        "CATALOGUE_SELECTION_SYSTEMATICS_CONDITIONAL_DIRECTIONAL_RESIDUAL",
        "NUMERICALLY_UNRESOLVED_AT_FROZEN_MC_BUDGET",
        "H_ONLY_SELECTION_SYSTEMATICS_CONDITIONAL",
        "NON_INFORMATIVE_RESPONSE_OVERLAP",
        "NON_INFORMATIVE_SELECTION_SYSTEMATICS_DOMINATED",
        "DESCRIPTIVE_ONLY_NULL_NOT_CERTIFIABLE",
    }
    if terminal not in allowed:
        raise Pr179RunnerError("unregistered scientific terminal")
    null = analysis["matched_null"]
    if null is not None:
        lineage = null["lineage"]
        if lineage["complete"] is not True or lineage["draws"] != 19999:
            raise Pr179RunnerError("matched-null lineage incomplete")
        cert = null["rank_certificate"]
        expected = (1 + null["exceedance_count"]) / 20000.0
        if not math.isclose(cert["estimate"], expected, rel_tol=0.0, abs_tol=1e-15):
            raise Pr179RunnerError("finite-rank arithmetic mismatch")
        if cert["tie_policy"] != "conservative_ge" or cert["gaussian_sigma_emitted"] is not False:
            raise Pr179RunnerError("finite-rank policy breach")
        stability = null["stability"]
        if stability["expected_cases"] != (
            stability["evaluated_cases"] + stability["failed_cases"]
        ):
            raise Pr179RunnerError("deletion-case coverage arithmetic mismatch")
        if stability["pass"] is True and stability["failed_cases"] != 0:
            raise Pr179RunnerError("deletion failure silently passed stability")
    if result["analysis_branch"] == "H_ONLY":
        coefficient = result["coefficient_summary"]
        if coefficient is not None and any(coefficient[key] is not None for key in (
            "q_cat_dipole_vector", "q_cat_dipole_amplitude", "q_cat_positive_axis_J2000"
        )):
            raise Pr179RunnerError("q_cat leaked through failed response gate")
        if result["terminal"] != "H_ONLY_SELECTION_SYSTEMATICS_CONDITIONAL":
            raise Pr179RunnerError("H-only response did not reach its frozen terminal")
        if result.get("supporting_h_only_matched_null_disposition") is None:
            raise Pr179RunnerError("H-only matched-null supporting disposition missing")
    for fold in analysis["response_identifiability"]["folds"]:
        if "q_directional_cubic_canonical_correlation" not in fold:
            raise Pr179RunnerError("directional-cubic canonical-correlation gate missing")
        value = fold["q_directional_cubic_canonical_correlation"]
        if not isinstance(value, (int, float)) or not math.isfinite(value):
            raise Pr179RunnerError("invalid directional-cubic canonical correlation")


def _run_mutations(raw_module, finite_module, analysis: Mapping[str, object]) -> dict[str, object]:
    mutations: list[dict[str, object]] = []

    def killed(mutation_id: str, callable_, expected_type: type[BaseException],
               expected_text: str) -> None:
        try:
            callable_()
        except Exception as exc:  # expected, but class and reason are checked
            matched = isinstance(exc, expected_type) and expected_text in str(exc)
            mutations.append({
                "mutation_id": mutation_id,
                "killed": matched,
                "exception": type(exc).__name__,
                "reason": str(exc),
                "expected_exception": expected_type.__name__,
                "expected_reason_contains": expected_text,
            })
        else:
            mutations.append({
                "mutation_id": mutation_id, "killed": False, "exception": None,
                "reason": None, "expected_exception": expected_type.__name__,
                "expected_reason_contains": expected_text,
            })

    for column in raw_module.CF4_PR179_DENYLIST:
        killed(
            f"forbidden_value_access_{column}",
            lambda value=column: raw_module.require_pr179_value_access("table4", value),
            raw_module.Cf4RawInputError,
            "forbidden PR-179 value access",
        )
    killed(
        "unknown_value_access",
        lambda: raw_module.require_pr179_value_access("table3", "invented_column"),
        raw_module.Cf4RawInputError,
        "unregistered PR-179 value access",
    )
    killed("negative_rank_count", lambda: finite_module.plus_one_rank(19999, -1),
           finite_module.FiniteEnsembleError, "exceedance_count must be")
    killed("overflow_rank_count", lambda: finite_module.plus_one_rank(19999, 20000),
           finite_module.FiniteEnsembleError, "exceedance_count must be")
    killed("boolean_rank_count", lambda: finite_module.plus_one_rank(19999, True),
           finite_module.FiniteEnsembleError, "exceedance_count must be")
    killed("nan_canonical_payload", lambda: _canonical_bytes({"value": float("nan")}),
           ValueError, "Out of range float values")
    changed = json.loads(json.dumps(analysis))
    changed["result"]["selection_systematics_conditional"] = False
    killed("conditionality_promotion", lambda: _validate_scientific_core(changed),
           Pr179RunnerError, "conditionality flag missing")
    changed = json.loads(json.dumps(analysis))
    changed["raw_catalogue_receipt"]["column_firewall"]["P0_estimator_reused"] = True
    killed("P0_reuse", lambda: _validate_scientific_core(changed),
           Pr179RunnerError, "column or P0 firewall breach")
    changed = json.loads(json.dumps(analysis))
    changed["raw_catalogue_receipt"]["accessed_columns"]["table4"].append("Dist")
    killed("runtime_column_access_receipt", lambda: _validate_scientific_core(changed),
           Pr179RunnerError, "runtime column-access capability receipt drift")
    changed = json.loads(json.dumps(analysis))
    if changed["matched_null"] is not None:
        changed["matched_null"]["lineage"]["draws"] = 19998
        killed("null_lineage_count", lambda: _validate_scientific_core(changed),
               Pr179RunnerError, "matched-null lineage incomplete")
        changed = json.loads(json.dumps(analysis))
        changed["matched_null"]["stability"]["evaluated_cases"] -= 1
        killed("deletion_case_coverage", lambda: _validate_scientific_core(changed),
               Pr179RunnerError, "deletion-case coverage arithmetic mismatch")
    changed = json.loads(json.dumps(analysis))
    del changed["response_identifiability"]["folds"][0][
        "q_directional_cubic_canonical_correlation"
    ]
    killed("q_cubic_correlation_gate", lambda: _validate_scientific_core(changed),
           Pr179RunnerError, "directional-cubic canonical-correlation gate missing")
    if not mutations or not all(row["killed"] for row in mutations):
        raise Pr179RunnerError("one or more registered mutations survived")
    return {
        "schema": "htt.pr179.mutation_report.v1",
        "mutations": mutations,
        "killed": len(mutations),
        "survived": 0,
        "all_killed": True,
    }


def build_generation(execution_receipt: Mapping[str, object]) -> dict[str, bytes]:
    receipt = preflight()
    execution_core = _verify_execution_receipt(execution_receipt)
    # Numerical imports occur only after preflight has completed successfully.
    np_module = importlib.import_module("numpy")
    scipy_module = importlib.import_module("scipy")
    hp_module = importlib.import_module("healpy")
    raw_module = importlib.import_module("obsstat.catalogs.cf4_raw")
    science_module = importlib.import_module("obsstat.directional_cosmography")
    finite_module = importlib.import_module("obsstat.finite_ensemble")

    spec = _load_spec()
    sources = spec["source_authorities"]
    config_kwargs, config_crosswalk = _config_projection(spec)
    config = science_module.DirectionalCosmographyConfig(**config_kwargs)
    expected_config = {
        key: list(value) if isinstance(value, tuple) else value
        for key, value in config_kwargs.items()
    }
    if config.to_dict() != expected_config:
        raise Pr179RunnerError("SPEC-to-config projection is incomplete")
    catalogue = raw_module.load_authenticated_cf4_raw_groups(
        REPO / sources["table3"]["path"],
        REPO / sources["table4"]["path"],
        expected_table3_sha256=sources["table3"]["sha256"],
        expected_table4_sha256=sources["table4"]["sha256"],
        expected_rows=38053,
    )
    analysis = science_module.analyze_directional_cosmography(catalogue, config)
    _validate_scientific_core(analysis)
    spec_hash = str(receipt["spec_sha256"])
    input_hashes = dict(receipt["authority_hashes"])
    code_paths = {
        "raw_adapter": REPO / "htt/obsstat/catalogs/cf4_raw.py",
        "estimator": REPO / "htt/obsstat/directional_cosmography.py",
        "runner": Path(__file__).resolve(),
        "finite_ensemble": REPO / "htt/obsstat/finite_ensemble.py",
        "finite_null_rank": REPO / "htt/src/common/finite_null_ranking.py",
    }
    code_hashes = {key: _sha256(path) for key, path in code_paths.items()}
    runtime = _runtime_versions(np_module, scipy_module, hp_module)
    metadata = _metadata(
        spec_sha256=spec_hash,
        config_sha256=analysis["config_sha256"],
        input_hashes=input_hashes,
        code_hashes=code_hashes,
        runtime_versions=runtime,
        execution_receipt=execution_core,
    )
    mutation = _run_mutations(raw_module, finite_module, analysis)

    result = analysis["result"]
    null = analysis["matched_null"]
    response = analysis["response_identifiability"]
    raw_receipt = analysis["raw_catalogue_receipt"]
    systematics = {
        "schema": "htt.pr179.raw_systematics.v1",
        "support": raw_receipt["support"],
        "stability": None if null is None else null["stability"],
        "unreported_covariance_status": "not authenticated; result remains catalogue-conditional",
        "fine_cell_method_support_is_descriptive": True,
    }
    estimand = {
        "schema": "htt.pr179.estimand_contract.v1",
        "analysis_id": "CF4_RAW_DIRECTIONAL_COSMOGRAPHY_V1",
        "spec_sha256": spec_hash,
        "pr179_card_semantic_sha256": receipt["pr179_card_semantic_sha256"],
        "observation_unit": "unique CF4 group 1PGC",
        "response": spec["catalogue_fit"]["transformed_response"],
        "relation": spec["catalogue_fit"]["relation"],
        "primary_columns": spec["column_firewall"]["primary_fit"],
        "hard_forbidden_values": spec["column_firewall"]["hard_forbidden_values"],
        "matched_null": spec["matched_null"],
        "finite_rank": spec["finite_rank"],
        "config_projection": expected_config,
        "config_crosswalk": config_crosswalk,
        "claim": spec["claim"],
    }
    rank = None if null is None else null["rank_certificate"]
    result_card = {
        "schema": "htt.pr179.result_card.v1",
        "pr_id": "PR-179",
        "terminal": result["terminal"],
        "analysis_branch": result["analysis_branch"],
        "groups": raw_receipt["inferential_groups"],
        "observed_score": result["observed_score"],
        "finite_rank": rank,
        "coefficient_summary": result["coefficient_summary"],
        "response_identifiability": {
            "h_pass_all_folds": response["h_pass_all_folds"],
            "q_pass_all_folds": response["q_pass_all_folds"],
            "q_withheld": response["q_withheld"],
        },
        "mandatory_claim_language": (
            "Selection/systematics-conditional raw-catalogue directional statistic "
            "with a matched null; not cosmological anisotropy. H_cat and q_cat are "
            "catalogue-fit coefficient labels, not physical cosmological fields."
        ),
        "terminal_language": result["terminal_reason"],
        "public_use": False,
    }

    payloads: dict[str, object] = {
        "pr179_estimand_contract.json": {**estimand, "metadata": metadata},
        "pr179_raw_catalogue_receipt.json": {**raw_receipt, "metadata": metadata},
        "pr179_response_identifiability.json": {
            "schema": "htt.pr179.response_identifiability.v1",
            **response,
            "metadata": metadata,
        },
        "pr179_null_calibration.json": {
            "schema": "htt.pr179.null_calibration.v1",
            "matched_null": null,
            "metadata": metadata,
        },
        "pr179_raw_systematics.json": {**systematics, "metadata": metadata},
        "pr179_directional_cosmography_result.json": {**result, "metadata": metadata},
        "pr179_result_card.json": {**result_card, "metadata": metadata},
        "pr179_mutation_report.json": {**mutation, "metadata": metadata},
        EXECUTION_RECEIPT_NAME: {**execution_core, "metadata": metadata},
    }
    encoded = {name: _canonical_bytes(payload) for name, payload in payloads.items()}
    entries = {
        name: {"sha256": hashlib.sha256(content).hexdigest(), "size_bytes": len(content)}
        for name, content in sorted(encoded.items())
    }
    manifest = {
        "schema": "htt.pr179.artifact_manifest.v1",
        "generation_root": _semantic_hash(entries),
        "artifacts": entries,
        "metadata": metadata,
        "source_edges": {
            "spec": spec_hash,
            "pr179_card": receipt["pr179_card_semantic_sha256"],
            "raw_design": raw_receipt["design_sha256"],
            "null_scores": None if null is None else null["null_scores_sha256"],
            "execution_receipt_core": metadata["execution_receipt_core_sha256"],
        },
        "candidate_cannot_authorize_itself": True,
    }
    encoded["pr179_artifact_manifest.json"] = _canonical_bytes(manifest)
    if set(encoded) != set(OUTPUT_NAMES):
        raise Pr179RunnerError("generation output allowlist mismatch")
    return encoded


def _fsync_directory(path: Path) -> None:
    descriptor = os.open(path, os.O_RDONLY | getattr(os, "O_DIRECTORY", 0))
    try:
        os.fsync(descriptor)
    finally:
        os.close(descriptor)


def _write_durable(path: Path, content: bytes) -> None:
    with path.open("wb") as handle:
        handle.write(content)
        handle.flush()
        os.fsync(handle.fileno())


def _write_journal(path: Path, payload: Mapping[str, object]) -> None:
    descriptor, temporary = tempfile.mkstemp(prefix=".pr179-journal-", dir=path.parent)
    temp_path = Path(temporary)
    try:
        with os.fdopen(descriptor, "wb") as handle:
            handle.write(_canonical_bytes(payload))
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temp_path, path)
        _fsync_directory(path.parent)
    finally:
        temp_path.unlink(missing_ok=True)


def _transaction_directory(root: Path, raw: object, prefix: str) -> Path:
    candidate = Path(str(raw)).resolve()
    if candidate.parent != root.resolve() or not candidate.name.startswith(prefix):
        raise Pr179RunnerError("unsafe PR-179 transaction directory")
    return candidate


def _recover_transaction(generated_dir: Path) -> str | None:
    journal = generated_dir / JOURNAL_NAME
    if not journal.is_file():
        return None
    payload = json.loads(journal.read_text(encoding="utf-8"))
    if payload.get("schema") != "htt.pr179.write_transaction.v1":
        raise Pr179RunnerError("PR-179 transaction journal schema mismatch")
    if payload.get("output_names") != list(OUTPUT_NAMES):
        raise Pr179RunnerError("PR-179 transaction output allowlist mismatch")
    staging = _transaction_directory(
        generated_dir, payload.get("staging_dir"), ".pr179-stage-"
    )
    backup = _transaction_directory(
        generated_dir, payload.get("backup_dir"), ".pr179-backup-"
    )
    entries = payload.get("entries")
    if not isinstance(entries, list) or len(entries) != len(OUTPUT_NAMES):
        raise Pr179RunnerError("PR-179 transaction entries are malformed")
    by_name = {str(row.get("name")): row for row in entries if isinstance(row, Mapping)}
    if set(by_name) != set(OUTPUT_NAMES):
        raise Pr179RunnerError("PR-179 transaction target set mismatch")
    all_new = all(
        (generated_dir / name).is_file()
        and _sha256(generated_dir / name) == by_name[name].get("new_sha256")
        for name in OUTPUT_NAMES
    )
    disposition = "rolled_forward" if all_new else "rolled_back"
    if not all_new:
        for name in OUTPUT_NAMES:
            row = by_name[name]
            target = generated_dir / name
            if row.get("prior_exists") is True:
                source = backup / name
                if (
                    not source.is_file()
                    or _sha256(source) != row.get("prior_sha256")
                ):
                    raise Pr179RunnerError(
                        f"PR-179 rollback backup missing or corrupt: {name}"
                    )
                _write_durable(target, source.read_bytes())
            else:
                target.unlink(missing_ok=True)
        for name in OUTPUT_NAMES:
            row = by_name[name]
            target = generated_dir / name
            if row.get("prior_exists") is True:
                if not target.is_file() or _sha256(target) != row.get("prior_sha256"):
                    raise Pr179RunnerError(f"PR-179 rollback verification failed: {name}")
            elif target.exists():
                raise Pr179RunnerError(f"PR-179 rollback left new target: {name}")
        _fsync_directory(generated_dir)
    for directory in (staging, backup):
        if directory.exists():
            shutil.rmtree(directory)
    journal.unlink(missing_ok=True)
    _fsync_directory(generated_dir)
    return disposition


@contextlib.contextmanager
def _writer_lock(generated_dir: Path) -> Iterator[None]:
    generated_dir.mkdir(parents=True, exist_ok=True)
    descriptor = os.open(generated_dir / LOCK_NAME, os.O_RDWR | os.O_CREAT, 0o660)
    acquired = False
    try:
        try:
            fcntl.flock(descriptor, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError as exc:
            raise Pr179RunnerError("PR-179 artifact writer lock is held") from exc
        acquired = True
        yield
    finally:
        if acquired:
            fcntl.flock(descriptor, fcntl.LOCK_UN)
        os.close(descriptor)


def _write_generation(
    generation: Mapping[str, bytes],
    *,
    generated_dir: Path = GENERATED,
    fail_after: int | None = None,
) -> None:
    if set(generation) != set(OUTPUT_NAMES):
        raise Pr179RunnerError("write generation output allowlist mismatch")
    generated_dir = generated_dir.resolve()
    with _writer_lock(generated_dir):
        _recover_transaction(generated_dir)
        staging = Path(tempfile.mkdtemp(prefix=".pr179-stage-", dir=generated_dir))
        backup = Path(tempfile.mkdtemp(prefix=".pr179-backup-", dir=generated_dir))
        entries: list[dict[str, object]] = []
        journal_written = False
        try:
            for name in OUTPUT_NAMES:
                staged = staging / name
                _write_durable(staged, generation[name])
                target = generated_dir / name
                prior_exists = target.is_file()
                prior_sha = _sha256(target) if prior_exists else None
                if prior_exists:
                    _write_durable(backup / name, target.read_bytes())
                entries.append({
                    "name": name,
                    "prior_exists": prior_exists,
                    "prior_sha256": prior_sha,
                    "new_sha256": hashlib.sha256(generation[name]).hexdigest(),
                })
            _fsync_directory(staging)
            _fsync_directory(backup)
            journal_payload = {
                "schema": "htt.pr179.write_transaction.v1",
                "output_names": list(OUTPUT_NAMES),
                "staging_dir": str(staging),
                "backup_dir": str(backup),
                "entries": entries,
            }
            _write_journal(generated_dir / JOURNAL_NAME, journal_payload)
            journal_written = True
            installed = 0
            # OUTPUT_NAMES fixes manifest-last publication.
            for name in OUTPUT_NAMES:
                os.replace(staging / name, generated_dir / name)
                installed += 1
                _fsync_directory(generated_dir)
                if fail_after is not None and installed == fail_after:
                    raise OSError("injected PR-179 publication interruption")
            if any(
                _sha256(generated_dir / name)
                != hashlib.sha256(generation[name]).hexdigest()
                for name in OUTPUT_NAMES
            ):
                raise OSError("PR-179 transaction post-write hash verification failed")
            _recover_transaction(generated_dir)
            journal_written = False
        except BaseException:
            if journal_written:
                _recover_transaction(generated_dir)
                journal_written = False
            raise
        finally:
            if not journal_written:
                for directory in (staging, backup):
                    if directory.exists():
                        shutil.rmtree(directory)


def _check_generation(
    generation: Mapping[str, bytes], *, generated_dir: Path = GENERATED
) -> dict[str, object]:
    mismatches: list[str] = []
    for name in OUTPUT_NAMES:
        path = generated_dir / name
        if not path.is_file():
            mismatches.append(f"missing:{name}")
        elif path.read_bytes() != generation[name]:
            mismatches.append(f"byte_mismatch:{name}")
    extras = sorted(path.name for path in generated_dir.glob("pr179_*.json")
                    if path.name not in OUTPUT_NAMES)
    if extras:
        mismatches.extend(f"unregistered:{name}" for name in extras)
    return {
        "schema": "htt.pr179.check_receipt.v1",
        "ok": not mismatches,
        "checked": len(OUTPUT_NAMES),
        "mismatches": mismatches,
        "read_only": True,
        "generation_root": hashlib.sha256(
            generation["pr179_artifact_manifest.json"]
        ).hexdigest(),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--preflight", action="store_true")
    group.add_argument("--write", action="store_true")
    group.add_argument("--check", action="store_true")
    args = parser.parse_args()
    if args.preflight:
        print(json.dumps(preflight(), sort_keys=True))
        return 0
    if args.write:
        execution_receipt = _capture_execution_receipt()
        generation = build_generation(execution_receipt)
        _write_generation(generation)
        manifest = json.loads(generation["pr179_artifact_manifest.json"])
        result = json.loads(generation["pr179_directional_cosmography_result.json"])
        print(json.dumps({
            "ok": True,
            "written": len(generation),
            "generation_root": manifest["generation_root"],
            "terminal": result["terminal"],
            "analysis_branch": result["analysis_branch"],
        }, sort_keys=True))
        return 0
    receipt_path = GENERATED / EXECUTION_RECEIPT_NAME
    if not receipt_path.is_file():
        raise Pr179RunnerError("missing producer execution receipt for read-only check")
    execution_receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
    generation = build_generation(execution_receipt)
    receipt = _check_generation(generation)
    print(json.dumps(receipt, sort_keys=True))
    return 0 if receipt["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
