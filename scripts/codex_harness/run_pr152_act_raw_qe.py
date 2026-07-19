#!/usr/bin/env python3
"""PR-152 runner: ACT DR6 raw-QE gate + release-simulation cross-fit.

``--write`` builds / ``--check`` verifies (fresh build must equal disk bytes):
the authenticated inventory, the leave-one-simulation cross-fit mean field, the
exact algebraic finite-rank ceiling, the stochastic-vs-fixed-template injection
law, the upstream
raw-QE availability decision, captions and the six-mutant kill report --- all
read from the heavy card produced once by ``scripts/act_raw_qe_card.py`` on the
real ACT DR6 lensing release (the ACT pattern; this runner never re-runs the
~60 GB read).

The release-simulation-conditioned null comparison is a concrete result. The
public raw-QE/RDN0 path is a separate large reconstruction that is feasible but
not executed locally. No convergence detection, isotropy proof, anisotropy, or
Bianchi-family claim.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import subprocess
import sys
import warnings
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "htt" / "src"))
sys.path.insert(0, str(REPO / "htt"))
warnings.filterwarnings("ignore")

import yaml  # noqa: E402

from obsstat.act_raw_qe_gate import (  # noqa: E402
    ACTRawQEError,
    SCHEMA_VERSION,
    generate_caption,
    injection_law_distinction,
    lint_caption,
    refuse_act_detection,
    refuse_bianchi_from_act,
    refuse_naive_self_mean_field,
    refuse_pre_qe_transfer_label,
    refuse_raw_qe_without_inputs,
    refuse_sky_power_limit_without_raw_qe,
)

SPEC_PATH = REPO / "docs/research_program/long_horizon_rescue/pr152_spec.yaml"
CARD_PATH = REPO / "docs/generated/act_raw_qe_card.json"
OUTPUTS = {
    "inventory": "docs/generated/pr152_inventory.json",
    "crossfit": "docs/generated/pr152_crossfit_mean_field.json",
    "legacy_sensitivity": "docs/generated/pr152_legacy_mean_field_sensitivity.json",
    "rank": "docs/generated/pr152_rank_ceiling.json",
    "injection": "docs/generated/pr152_injection_law.json",
    "decision": "docs/generated/pr152_availability_decision.json",
    "captions": "docs/generated/pr152_captions.json",
    "mutations": "docs/generated/pr152_mutation_report.json",
    "manifest": "docs/generated/pr152_artifact_manifest.json",
}
REDACTED = "[REDACTED-PATTERN]"
CARD_SCHEMA = "htt.act_raw_qe_card.v2"
INPUT_MANIFEST_SCHEMA = "htt.act.release_input_manifest.v2"
CACHE_SCHEMA = "htt.act.lowl_cache.v2"
REQUIRED_ARTIFACT_METADATA = {
    "owner", "implementation_scope", "claim_tier", "transfer_source",
    "config_hash", "input_hashes", "sky_support_status", "mask_status",
    "covariance_status", "null_mock_status", "caveats",
    "generating_command", "git_commit", "worktree_state",
}


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _sha_prefixed(path: Path) -> str:
    return "sha256:" + _sha(path)


def _canonical_sha256(payload: dict) -> str:
    raw = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
    return "sha256:" + hashlib.sha256(raw).hexdigest()


def _valid_sha256(value: object) -> bool:
    if not isinstance(value, str) or not value.startswith("sha256:"):
        return False
    digest = value.removeprefix("sha256:")
    return len(digest) == 64 and all(c in "0123456789abcdef" for c in digest)


def _finite_number(value: object) -> bool:
    return (isinstance(value, (int, float)) and not isinstance(value, bool)
            and math.isfinite(float(value)))


def _close(left: object, right: object, *, atol: float = 1e-15) -> bool:
    return (_finite_number(left) and _finite_number(right)
            and math.isclose(float(left), float(right), rel_tol=1e-12,
                             abs_tol=atol))


def _render(payload: dict) -> bytes:
    return (json.dumps(payload, indent=2, ensure_ascii=False,
                       sort_keys=True) + "\n").encode()


def _resolve_recorded_path(value: str) -> Path:
    path = Path(value)
    return path if path.is_absolute() else REPO / path


def _validate_file_record(record: object, *, label: str,
                          problems: list[str]) -> None:
    if not isinstance(record, dict):
        problems.append(f"{label} is not a file record")
        return
    if not isinstance(record.get("path"), str) or not record["path"]:
        problems.append(f"{label}.path invalid")
    if not isinstance(record.get("size_bytes"), int) or record["size_bytes"] <= 0:
        problems.append(f"{label}.size_bytes invalid")
    if not _valid_sha256(record.get("sha256")):
        problems.append(f"{label}.sha256 invalid")


def validate_artifact_metadata(payload: dict) -> None:
    metadata = payload.get("artifact_metadata")
    if not isinstance(metadata, dict):
        raise ValueError("artifact_metadata missing")
    missing = sorted(REQUIRED_ARTIFACT_METADATA - set(metadata))
    if missing:
        raise ValueError(f"artifact_metadata missing fields: {missing}")
    if not _valid_sha256(metadata["config_hash"]):
        raise ValueError("artifact config_hash is not full SHA-256")
    if (not isinstance(metadata["input_hashes"], list)
            or not metadata["input_hashes"]
            or not all(_valid_sha256(row.get("sha256"))
                       for row in metadata["input_hashes"]
                       if isinstance(row, dict))
            or not all(isinstance(row, dict) for row in metadata["input_hashes"])):
        raise ValueError("artifact input_hashes are incomplete")


def _validate_card(card: dict, spec: dict) -> None:
    """Fail closed on every cheap cross-field and provenance invariant."""
    problems: list[str] = []
    expected_config = {
        "ell_min": int(spec["model"]["band"]["ell_min"]),
        "ell_max": int(spec["model"]["band"]["ell_max"]),
        "n_sims": int(spec["model"]["sims"]["exact_count"]),
        "seed": int(spec["model"]["sims"]["seed"]),
    }
    if card.get("schema") != CARD_SCHEMA:
        problems.append("card schema mismatch")
    if card.get("status") != "RELEASE_SIMULATION_CONDITIONAL_RESULT":
        problems.append("card status mismatch")
    if card.get("config") != expected_config:
        problems.append("card config is not spec-exact")

    provenance = card.get("input_provenance")
    if not isinstance(provenance, dict):
        problems.append("input_provenance missing")
        provenance = {}
    manifest = provenance.get("input_manifest")
    if not isinstance(manifest, dict):
        problems.append("input manifest missing")
        manifest = {}
    if manifest.get("schema") != INPUT_MANIFEST_SCHEMA:
        problems.append("input manifest schema mismatch")
    registered_manifest_hash = manifest.get("manifest_sha256")
    hash_payload = dict(manifest)
    hash_payload.pop("manifest_sha256", None)
    recomputed_manifest_hash = _canonical_sha256(hash_payload)
    if (not _valid_sha256(registered_manifest_hash)
            or registered_manifest_hash != recomputed_manifest_hash
            or provenance.get("input_manifest_sha256") != registered_manifest_hash):
        problems.append("input manifest hash mismatch")
    manifest_config = manifest.get("config")
    if manifest_config != {
            "ell_min": expected_config["ell_min"],
            "ell_max": expected_config["ell_max"],
            "mode_weights": "m0=1,m_positive=2",
            "expected_simulation_count": expected_config["n_sims"],
            "seed": expected_config["seed"]}:
        problems.append("input manifest config mismatch")
    data_record = manifest.get("data_alm")
    _validate_file_record(data_record, label="data_alm", problems=problems)
    producer_record = manifest.get("producer")
    _validate_file_record(producer_record, label="producer", problems=problems)
    if isinstance(producer_record, dict):
        producer_path = REPO / "scripts/act_raw_qe_card.py"
        if (producer_record.get("path") != "scripts/act_raw_qe_card.py"
                or producer_record.get("sha256") != _sha_prefixed(producer_path)
                or producer_record.get("size_bytes") != producer_path.stat().st_size):
            problems.append("producer record does not bind current producer bytes")
    simulations = manifest.get("ordered_simulation_alms")
    if not isinstance(simulations, list) or len(simulations) != expected_config["n_sims"]:
        problems.append("ordered simulation manifest must contain exactly 400 rows")
        simulations = []
    for index, record in enumerate(simulations):
        _validate_file_record(record, label=f"simulation[{index}]",
                              problems=problems)
    sim_paths = [row.get("path") for row in simulations if isinstance(row, dict)]
    if (len(sim_paths) != len(set(sim_paths))
            or sim_paths != sorted(sim_paths)):
        problems.append("simulation paths are not unique and ordered")
    if isinstance(data_record, dict):
        expected_data = spec["data_scope"]["raw_data_paths"]["data_kappa_alm"]
        if data_record.get("path") != expected_data:
            problems.append("data alm path differs from spec")

    if provenance.get("cache_schema") != CACHE_SCHEMA:
        problems.append("cache schema mismatch")
    if provenance.get("cache_binding_verified") is not True:
        problems.append("cache binding not verified")
    cache_path_value = provenance.get("cache_path")
    if not isinstance(cache_path_value, str) or not cache_path_value:
        problems.append("cache path missing")
    else:
        cache_path = _resolve_recorded_path(cache_path_value)
        if (not cache_path.is_file()
                or provenance.get("cache_sha256") != _sha_prefixed(cache_path)):
            problems.append("cache bytes do not match provenance")
    if not _valid_sha256(provenance.get("cache_sha256")):
        problems.append("cache full SHA-256 missing")
    environment = provenance.get("generation_environment")
    if (not isinstance(environment, dict)
            or not all(environment.get(k) for k in
                       ("python", "numpy", "healpy", "git_commit", "worktree_state"))):
        problems.append("generation environment incomplete")

    inventory = card.get("inventory")
    if not isinstance(inventory, dict):
        problems.append("inventory missing")
        inventory = {}
    present = inventory.get("present_products")
    if not isinstance(present, dict):
        problems.append("present_products missing")
        present = {}
    for key in ("kappa_alm_data", "n0_curve", "kappa_filter_response",
                "n1_derivative_kk", "clkk_bandpowers",
                "ordered_simulation_manifest_sha256"):
        if not _valid_sha256(present.get(key)):
            problems.append(f"present product {key} lacks full SHA-256")
    if isinstance(data_record, dict) and present.get("kappa_alm_data") != data_record.get("sha256"):
        problems.append("data digest differs between inventory and input manifest")
    if (present.get("ordered_simulation_manifest_sha256")
            != registered_manifest_hash):
        problems.append("simulation manifest digest differs from cache input key")
    if present.get("n_reconstructed_sims") != expected_config["n_sims"]:
        problems.append("inventory simulation count mismatch")
    if inventory.get("validated_ell_range") != [40, 763]:
        problems.append("release validated ell range mismatch")
    if inventory.get("raw_qe_inputs_on_disk") is not False:
        problems.append("raw-QE availability is inconsistent with this card")
    readiness = inventory.get("raw_qe_readiness_receipt")
    if not isinstance(readiness, dict) or readiness.get("ready") is not False:
        problems.append("raw-QE readiness receipt must remain incomplete")
    if not inventory.get("local_missing_raw_qe_inputs"):
        problems.append("missing raw-QE inputs were not enumerated")

    decision = card.get("availability_decision")
    if not isinstance(decision, dict):
        problems.append("availability decision missing")
        decision = {}
    if (decision.get("decision")
            != "DEFER_RAW_QE_RDN0_PUBLIC_INPUTS_LARGE_RECONSTRUCTION"
            or decision.get("raw_qe_available") is not False
            or decision.get("readiness_evidence_complete") is not False
            or decision.get("closed_result")
            != "release_simulation_conditioned_null_comparison"):
        problems.append("availability decision contradicts inventory")

    crossfit = card.get("crossfit_mean_field")
    if not isinstance(crossfit, dict):
        problems.append("crossfit result missing")
        crossfit = {}
    scores = crossfit.get("simulation_band_powers")
    if (not isinstance(scores, list)
            or len(scores) != expected_config["n_sims"]
            or not all(_finite_number(value) and float(value) >= 0
                       for value in scores)):
        problems.append("crossfit must retain 400 finite nonnegative null scores")
        scores = []
    n_total = expected_config["n_sims"] + 1
    observed = crossfit.get("S_data")
    if not _finite_number(observed) or float(observed) < 0:
        problems.append("crossfit observed score invalid")
        observed = math.nan
    if (crossfit.get("n_sims") != expected_config["n_sims"]
            or crossfit.get("n_exchangeable_units") != n_total
            or crossfit.get("permutation_equivariant_transform") is not True):
        problems.append("crossfit count/equivariance invariant failed")
    if not _close(crossfit.get("support_resolution"), 1 / n_total):
        problems.append("crossfit support resolution mismatch")
    if scores and math.isfinite(float(observed)):
        exceedance = sum(float(value) >= float(observed) for value in scores)
        ties = sum(float(value) == float(observed) for value in scores)
        expected_p = (1 + exceedance) / n_total
        if (crossfit.get("upper_exceedance_count") != exceedance
                or crossfit.get("tie_count") != ties
                or not _close(crossfit.get(
                    "observation_inclusive_crossfit_pooled_rank_p"), expected_p)
                or not _close(crossfit.get("simulation_band_power_mean"),
                              sum(float(v) for v in scores) / len(scores))):
            problems.append("crossfit rank/count/mean arithmetic mismatch")
    if (crossfit.get("analysis_ell_range")
            != [expected_config["ell_min"], expected_config["ell_max"]]
            or crossfit.get("release_validated_ell_range") != [40, 763]
            or crossfit.get("inside_release_validated_range") is not False
            or crossfit.get("validation_boundary")
            != "exploratory_outside_release_spectrum_validation_range"):
        problems.append("crossfit release-validation boundary missing")
    for field in ("data_mean_field_band_power", "simulation_band_power_mean"):
        if not _finite_number(crossfit.get(field)):
            problems.append(f"crossfit {field} is non-finite")

    rank = card.get("rank_ceiling")
    n_modes = sum(2 * ell + 1 for ell in range(
        expected_config["ell_min"], expected_config["ell_max"] + 1))
    expected_rank = min(n_modes, expected_config["n_sims"] - 1)
    if (not isinstance(rank, dict)
            or rank.get("ell_min") != expected_config["ell_min"]
            or rank.get("ell_max") != expected_config["ell_max"]
            or rank.get("n_real_harmonic_dof") != n_modes
            or rank.get("sample_rank") != expected_config["n_sims"] - 1
            or rank.get("finite_rank_ceiling") != expected_rank
            or rank.get("realized_numerical_rank_measured") is not False):
        problems.append("algebraic finite-rank ceiling relation mismatch")

    injection = card.get("injection_law")
    if scores and isinstance(injection, dict):
        recomputed = injection_law_distinction(
            scores,
            injection_amplitude=float(spec["model"]["injection_amplitude"]),
            seed=expected_config["seed"],
        )
        for field in ("injection_amplitude", "sim_band_power_mean",
                      "sim_band_power_std", "stochastic_mean_pooled_rank_p",
                      "fixed_template_mean_pooled_rank_p"):
            if not _close(injection.get(field), recomputed[field]):
                problems.append(f"injection field {field} mismatch")
        if injection.get("laws_distinct") is not recomputed["laws_distinct"]:
            problems.append("injection law distinction mismatch")
    else:
        problems.append("injection result missing")

    legacy = card.get("legacy_simulation_only_sensitivity")
    if (not isinstance(legacy, dict)
            or legacy.get("n_sims") != expected_config["n_sims"]
            or legacy.get("joint_exchangeability_exact") is not False
            or not _close(legacy.get(
                "algebraic_bias_ratio_n_minus_1_over_n_squared"),
                ((expected_config["n_sims"] - 1) /
                 expected_config["n_sims"]) ** 2)):
        problems.append("legacy sensitivity contract mismatch")

    if problems:
        raise SystemExit("invalid ACT heavy card: " + "; ".join(problems))


def _verify_baseline_commit(spec: dict) -> None:
    import subprocess
    sha = str(spec.get("baseline_commit") or "")
    if len(sha) != 40:
        raise SystemExit("baseline_commit must be a full 40-hex id")
    probe = subprocess.run(["git", "cat-file", "-e", f"{sha}^{{commit}}"],
                           cwd=REPO, capture_output=True, check=False)
    if probe.returncode != 0:
        raise SystemExit(f"baseline_commit {sha} does not resolve")


def _verify_remediation_state(spec: dict) -> None:
    contract = spec["remediation_state_contract"]
    target = REPO / contract["path"]
    if _sha(target) != contract["sha256"]:
        raise SystemExit("remediation state drifted from the spec pin")
    payload = yaml.safe_load(target.read_text(encoding="utf-8"))
    findings = payload.get("findings") or []
    statuses: dict[str, int] = {}
    for row in findings:
        statuses[str(row.get("scientific_status"))] = \
            statuses.get(str(row.get("scientific_status")), 0) + 1
    if len(findings) != contract["finding_count"]:
        raise SystemExit("remediation finding count drifted")
    required = {str(k): int(v)
                for k, v in contract["required_scientific_status_counts"].items()}
    if statuses != required:
        raise SystemExit(f"remediation status counts drifted: {statuses}")


def build_reports(spec: dict):
    if not CARD_PATH.is_file():
        raise SystemExit(
            "the ACT raw-QE card is absent — run scripts/act_raw_qe_card.py on "
            "the real ACT DR6 lensing release first")
    card = json.loads(CARD_PATH.read_text(encoding="utf-8"))
    _validate_card(card, spec)
    raw_qe = bool(card["inventory"].get("raw_qe_inputs_on_disk"))

    # anti-drift guards invoked LIVE with admissible input
    refuse_pre_qe_transfer_label("release_simulation_diagnostic")
    refuse_sky_power_limit_without_raw_qe(raw_qe, "release_simulation_crossfit")
    refuse_naive_self_mean_field(True)     # the mean field IS a cross-fit
    refuse_act_detection("release_simulation_consistency")
    refuse_bianchi_from_act("no_geometry_claim")
    refuse_raw_qe_without_inputs(raw_qe, "release_simulation_crossfit")

    inventory = {"schema": "pr152.inventory.v1", "module_schema": SCHEMA_VERSION,
                 **card["inventory"]}
    crossfit = {"schema": "pr152.crossfit_mean_field.v1",
                **card["crossfit_mean_field"]}
    legacy = {"schema": "pr152.legacy_mean_field_sensitivity.v1",
              **card["legacy_simulation_only_sensitivity"]}
    rank = {"schema": "pr152.rank_ceiling.v1", **card["rank_ceiling"]}
    injection = {"schema": "pr152.injection_law.v1", **card["injection_law"]}
    decision = {"schema": "pr152.availability_decision.v1",
                **card["availability_decision"]}
    return card, inventory, crossfit, legacy, rank, injection, decision


def _artifact_metadata(spec: dict, card: dict) -> dict:
    provenance = card["input_provenance"]
    environment = provenance["generation_environment"]
    caveats = [
        "The result is conditional on exchangeability of the released ACT "
        "reconstruction data and 400 released simulations.",
        "The analysed L=2..10 band lies outside the release spectrum "
        "validation range L=40..763 and is exploratory.",
        "Public four-split maps and open QE software make RDN0 reproducible, "
        "but the configuration-locked raw-QE rerun is not executed locally.",
        "No convergence detection, isotropy proof, anisotropy, geometry, or "
        "Bianchi-family claim is supported.",
    ]
    return {
        "owner": spec["owner"],
        "implementation_scope": list(spec["implementation_scope"]),
        "claim_tier": spec["claim_tier"],
        "transfer_source": spec["transfer_source"],
        "config_hash": _sha_prefixed(SPEC_PATH),
        "input_hashes": [
            {"path": str(CARD_PATH.relative_to(REPO)),
             "sha256": _sha_prefixed(CARD_PATH)},
            {"path": "htt/obsstat/act_raw_qe_gate.py",
             "sha256": _sha_prefixed(REPO / "htt/obsstat/act_raw_qe_gate.py")},
            {"path": "scripts/act_raw_qe_card.py",
             "sha256": _sha_prefixed(REPO / "scripts/act_raw_qe_card.py")},
            {"path": provenance["cache_path"],
             "sha256": provenance["cache_sha256"]},
            {"path": "embedded:ordered_act_release_input_manifest",
             "sha256": provenance["input_manifest_sha256"]},
        ],
        "sky_support_status":
            "released_reconstructed_kappa_support_not_independently_reprocessed",
        "mask_status": "release_mask_lineage_present_raw_qe_mask_not_local",
        "covariance_status":
            "empirical_400_release_simulations_conditional_exchangeability",
        "null_mock_status": "400_release_reconstructed_kappa_simulations",
        "caveats": caveats,
        "generating_command":
            "venv/bin/python scripts/codex_harness/run_pr152_act_raw_qe.py --write",
        "git_commit": environment["git_commit"],
        "worktree_state": environment["worktree_state"],
        "runtime_environment": {
            "python": environment["python"],
            "numpy": environment["numpy"],
            "healpy": environment["healpy"],
        },
    }


def _attach_metadata(payloads: list[dict], metadata: dict) -> None:
    for payload in payloads:
        payload["artifact_metadata"] = metadata
        validate_artifact_metadata(payload)


def build_captions(inventory, crossfit, decision) -> dict:
    text = generate_caption(inventory, crossfit, decision)
    lint_caption(text)
    return {"schema": "pr152.captions.v1", "captions": {"summary": text}}


def _scan_targets(spec: dict, captions_payload: dict) -> dict:
    patterns = [str(p) for p in spec["negative_scan"]["forbidden_patterns"]]
    targets = {}
    for rel in spec["negative_scan"]["targets"]:
        if rel == OUTPUTS["captions"]:
            raw = _render(captions_payload).decode()
            source, digest = "fresh_build", hashlib.sha256(raw.encode()).hexdigest()
        else:
            path = REPO / rel
            raw = path.read_text(encoding="utf-8")
            source, digest = "disk", _sha(path)
        hits = []
        for idx, line in enumerate(raw.splitlines(), start=1):
            low = line.lower()
            for pi, pattern in enumerate(patterns):
                if pattern.lower() in low:
                    hits.append({"line": idx, "pattern_index": pi})
        targets[rel] = {"hits": hits, "source": source, "sha256": digest}
    total = sum(len(t["hits"]) for t in targets.values())
    if total:
        raise SystemExit(f"negative scan found {total} hits: {targets}")
    return targets


def _redact(message: str, patterns: list[str]) -> str:
    for pattern in patterns:
        low = message.lower()
        needle = pattern.lower()
        while needle in low:
            start = low.index(needle)
            message = message[:start] + REDACTED + message[start + len(pattern):]
            low = message.lower()
    return message


def run_mutations(spec: dict) -> dict:
    redact_patterns = (
        [str(p) for p in spec["negative_scan"]["forbidden_patterns"]]
        + [str(p) for p in spec["forbidden_output_language"]])
    executions = {
        "released_kappa_called_pre_qe_transfer":
            lambda: refuse_pre_qe_transfer_label("pre_qe_transfer"),
        "sky_power_limit_without_raw_qe":
            lambda: refuse_sky_power_limit_without_raw_qe(
                False, "l2_10_sky_power_limit"),
        "naive_self_mean_field": lambda: refuse_naive_self_mean_field(False),
        "act_kappa_detection":
            lambda: refuse_act_detection("act_kappa_detection"),
        "bianchi_family_from_act":
            lambda: refuse_bianchi_from_act("bianchi_family"),
        "raw_qe_inference_without_inputs":
            lambda: refuse_raw_qe_without_inputs(False, "raw_qe_inference"),
    }
    registered = {m["mutation_id"]: m["kill_rule"]
                  for m in spec["mutation_registry"]}
    if set(registered) != set(executions):
        raise SystemExit("mutation registry does not match the executions")
    rows = []
    for mutation_id, fn in executions.items():
        killed, message = False, "MUTANT SURVIVED"
        try:
            fn()
        except ACTRawQEError as exc:
            killed = True
            message = _redact(str(exc), redact_patterns)[:220]
        rows.append({"mutation_id": mutation_id,
                     "kill_rule": registered[mutation_id],
                     "killed": killed, "kill_message_redacted": message})
    return {"schema": "pr152.mutation_report.v1", "mutations": rows,
            "surviving_mutation_count":
                len([m for m in rows if not m["killed"]])}


def _emit(rel, payload, write, problems, wrote) -> None:
    target = REPO / rel
    rendered = _render(payload)
    if write:
        if target.is_file() and target.read_bytes() == rendered:
            return
        target.parent.mkdir(parents=True, exist_ok=True)
        tmp = target.with_suffix(target.suffix + ".tmp")
        tmp.write_bytes(rendered)
        tmp.replace(target)
        wrote.append(rel)
        return
    if not target.is_file():
        problems.append(f"missing artifact: {rel}")
    elif target.read_bytes() != rendered:
        problems.append(f"stale artifact: {rel}")


def build(write: bool) -> int:
    spec = yaml.safe_load(SPEC_PATH.read_text(encoding="utf-8"))
    if spec.get("schema") != "htt.long_horizon.pr152_act_raw_qe.v2":
        raise SystemExit("pr152 spec schema mismatch")
    _verify_baseline_commit(spec)
    _verify_remediation_state(spec)
    problems: list[str] = []
    wrote: list[str] = []

    card, inventory, crossfit, legacy, rank, injection, decision = \
        build_reports(spec)
    metadata = _artifact_metadata(spec, card)
    captions = build_captions(inventory, crossfit, decision)
    _attach_metadata(
        [inventory, crossfit, legacy, rank, injection, decision, captions],
        metadata,
    )
    inventory["negative_scan"] = {"targets": _scan_targets(spec, captions),
                                  "total_hits": 0}
    mutations = run_mutations(spec)
    _attach_metadata([mutations], metadata)
    if mutations["surviving_mutation_count"]:
        print(json.dumps({"ok": False, "survivors": mutations["mutations"]}))
        return 2

    _emit(OUTPUTS["inventory"], inventory, write, problems, wrote)
    _emit(OUTPUTS["crossfit"], crossfit, write, problems, wrote)
    _emit(OUTPUTS["legacy_sensitivity"], legacy, write, problems, wrote)
    _emit(OUTPUTS["rank"], rank, write, problems, wrote)
    _emit(OUTPUTS["injection"], injection, write, problems, wrote)
    _emit(OUTPUTS["decision"], decision, write, problems, wrote)
    _emit(OUTPUTS["captions"], captions, write, problems, wrote)
    _emit(OUTPUTS["mutations"], mutations, write, problems, wrote)

    manifest = {
        "schema": "pr152.artifact_manifest.v2",
        "owner": spec["owner"], "claim_tier": spec["claim_tier"],
        "implementation_scope": list(spec["implementation_scope"]),
        "claim_level": spec["claim_level"],
        "artifact_mode": spec["artifact_mode"],
        "allowed_use": spec["allowed_use"],
        "forbidden_use": list(spec["forbidden_output_language"]),
        "transfer_source": spec["transfer_source"],
        "config_hash": metadata["config_hash"],
        "input_hashes": metadata["input_hashes"],
        "raw_data_pins": {
            "act_raw_qe_card_sha256": _sha_prefixed(CARD_PATH),
            "ordered_input_manifest_sha256":
                card["input_provenance"]["input_manifest_sha256"],
            "low_l_cache_sha256": card["input_provenance"]["cache_sha256"],
        },
        "sky_support_status": metadata["sky_support_status"],
        "mask_status": metadata["mask_status"],
        "covariance_status": metadata["covariance_status"],
        "null_mock_status": metadata["null_mock_status"],
        "generating_command": metadata["generating_command"],
        "check_command":
            "venv/bin/python scripts/codex_harness/run_pr152_act_raw_qe.py --check",
        "git_commit": metadata["git_commit"],
        "worktree_state": metadata["worktree_state"],
        "runtime_environment": metadata["runtime_environment"],
        "analysis_ell_range": crossfit["analysis_ell_range"],
        "release_validated_ell_range":
            crossfit["release_validated_ell_range"],
        "inside_release_validated_range":
            crossfit["inside_release_validated_range"],
        "caveats": [
            "Concrete ACT-release-simulation-conditioned null comparison at C3.",
            "The primary score uses an observation-inclusive, permutation-"
            "equivariant leave-one-out mean-field transform over data plus sims.",
            "The legacy simulation-only LOO transform is retained only as a "
            "non-exact sensitivity because its data/simulation transforms differ.",
            "Public four-split maps and open QE software make RDN0 feasible, but "
            "the configuration-locked raw-QE rerun is not executed locally.",
            "No raw-QE L=2..10 sky-power limit is reported.",
            "No convergence detection, anisotropy, or Bianchi-family claim; the "
            "two CF4 P0s are untouched and stay OPEN.",
            "All 102 remediation findings remain OPEN.",
        ],
        "artifacts": {rel: (_sha(REPO / rel) if (REPO / rel).is_file() else None)
                      for key, rel in OUTPUTS.items() if key != "manifest"},
    }
    _emit(OUTPUTS["manifest"], manifest, write, problems, wrote)
    if problems:
        print(json.dumps({"ok": False, "problems": problems}))
        return 2

    for key, rel in OUTPUTS.items():
        payload = json.loads((REPO / rel).read_text(encoding="utf-8"))
        if isinstance(payload, dict):
            payload.pop("forbidden_use", None)
        text = json.dumps(payload, ensure_ascii=False).lower()
        for phrase in spec["forbidden_output_language"]:
            if phrase.lower() in text:
                print(json.dumps({"ok": False,
                                  "reason": f"forbidden phrase in {rel}"}))
                return 2
    module_text = (REPO / "htt/obsstat/act_raw_qe_gate.py") \
        .read_text(encoding="utf-8").lower()
    for phrase in spec["forbidden_output_language"]:
        if phrase.lower() in module_text:
            print(json.dumps({"ok": False,
                              "reason": "forbidden phrase in module"}))
            return 2
    print(json.dumps({
        "ok": True, "mode": "write" if write else "check", "wrote": wrote,
        "decision": decision["decision"],
        "crossfit_pooled_rank_p":
            crossfit["observation_inclusive_crossfit_pooled_rank_p"],
        "finite_rank_ceiling": rank["finite_rank_ceiling"],
        "injection_laws_distinct": injection["laws_distinct"],
        "surviving_mutations": 0,
    }, indent=2))
    return 0


def main() -> None:
    parser = argparse.ArgumentParser()
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--write", action="store_true")
    group.add_argument("--check", action="store_true")
    args = parser.parse_args()
    sys.exit(build(write=args.write))


if __name__ == "__main__":
    main()
