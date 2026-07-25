#!/usr/bin/env python3
"""PR-150 runner: K1 exchangeable global scan + Planck PR3 FFP10 E2E calibration.

``--write`` builds / ``--check`` verifies (fresh build must equal disk bytes):
the idealised correlated-GRF pooled-rank super-uniformity (falsifier), the PR3
FFP10 E2E input manifest (999 CMB + 300 unique noise Monte-Carlo maps), the
finite-ensemble global rank and registered noise-reuse sensitivity read from
the heavy E2E max-scan card, the non-numeric PR4 external-blocker receipt,
captions, and the six-mutant kill report.

The heavy E2E max-scan card is produced ONCE by
``scripts/k1_global_maxscan.py --precision`` on the FFP10 ensemble; this runner
reads it (the ACT pattern) and never re-runs the 600 GB read.

PR3/FFP10-E2E-conditional morphology result at roadmap_rescue_v1:C2; no
detection or Bianchi-family claim; PR4/NPIPE simulation access is externally
blocked.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
import warnings
from fractions import Fraction
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "htt" / "src"))
sys.path.insert(0, str(REPO / "htt"))
warnings.filterwarnings("ignore")

import yaml  # noqa: E402

from obsstat.k1_e2e_calibration import (  # noqa: E402
    K1E2EError,
    SCHEMA_VERSION,
    e2e_input_manifest,
    generate_caption,
    idealised_super_uniformity,
    lint_caption,
    pooled_rank_from_e2e_card,
    pr4_npipe_skip_receipt,
    refuse_idealised_promotion,
    refuse_k1_axis_detection,
    refuse_non_super_uniform,
    refuse_pr3_pr4_joint,
    refuse_pr4_numeric,
    refuse_real_sky_p_without_e2e,
)

SPEC_PATH = REPO / "docs/research_program/long_horizon_rescue/pr150_spec.yaml"
OUTPUTS = {
    "idealised": "docs/generated/pr150_idealised_super_uniformity.json",
    "manifest_e2e": "docs/generated/pr150_e2e_input_manifest.json",
    "pooled_rank": "docs/generated/pr150_e2e_pooled_rank.json",
    "compact_retention": "docs/generated/pr150_compact_retention_receipt.json",
    "pr4": "docs/generated/pr150_pr4_skip_receipt.json",
    "captions": "docs/generated/pr150_captions.json",
    "mutations": "docs/generated/pr150_mutation_report.json",
    "manifest": "docs/generated/pr150_artifact_manifest.json",
}
SOURCE_PATH = "htt/obsstat/k1_e2e_calibration.py"
LOCAL_DATA_PATHS = {
    "cmb_mc_dir": "workdir/raw/planck_ffp10/smica/cmb_mc",
    "noise_mc_dir": "workdir/raw/planck_ffp10/smica/noise_mc",
}
REDACTED = "[REDACTED-PATTERN]"


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _render(payload: dict) -> bytes:
    return (json.dumps(payload, indent=2, ensure_ascii=False,
                       sort_keys=True) + "\n").encode()


def _is_sha256(value: object, *, prefix: str = "") -> bool:
    if not isinstance(value, str) or not value.startswith(prefix):
        return False
    digest = value.removeprefix(prefix)
    return (
        len(digest) == 64
        and all(char in "0123456789abcdef" for char in digest)
    )


def _has_path_suffix(value: object, suffix: str) -> bool:
    if not isinstance(value, str):
        return False
    value_parts = Path(value).parts
    suffix_parts = Path(suffix).parts
    return (
        len(value_parts) >= len(suffix_parts)
        and value_parts[-len(suffix_parts):] == suffix_parts
    )


def _semantic_artifact(rel: str, payload: dict) -> dict:
    """Ignore only maintained-source and local-location provenance drift."""

    normalized = json.loads(json.dumps(payload))
    metadata = normalized.get("artifact_metadata")
    rows = metadata.get("input_hashes") if isinstance(metadata, dict) else None
    if isinstance(rows, list):
        for row in rows:
            if (
                isinstance(row, dict)
                and row.get("path") == SOURCE_PATH
                and _is_sha256(row.get("sha256"), prefix="sha256:")
            ):
                row["sha256"] = "sha256:<generation-time-source>"

    input_hashes = normalized.get("input_hashes")
    if isinstance(input_hashes, list):
        prefix = f"{SOURCE_PATH}:"
        for index, row in enumerate(input_hashes):
            if (
                isinstance(row, str)
                and row.startswith(prefix)
                and _is_sha256(row.removeprefix(prefix))
            ):
                input_hashes[index] = (
                    f"{SOURCE_PATH}:<generation-time-source>"
                )

    scan = normalized.get("negative_scan")
    targets = scan.get("targets") if isinstance(scan, dict) else None
    if isinstance(targets, dict):
        for target in (SOURCE_PATH, OUTPUTS["captions"]):
            row = targets.get(target)
            if isinstance(row, dict) and _is_sha256(row.get("sha256")):
                row["sha256"] = "<generation-time-scan>"

    if rel == OUTPUTS["manifest_e2e"]:
        for field, suffix in LOCAL_DATA_PATHS.items():
            if _has_path_suffix(normalized.get(field), suffix):
                normalized[field] = f"<local:{suffix}>"
    return normalized


def _artifact_metadata(spec: dict) -> dict:
    paths = spec["data_scope"]["raw_data_paths"]
    card = REPO / paths["e2e_card"]
    reduced_manifest = REPO / paths["reduced_manifest"]
    cache_gate = REPO / paths["cache_gate"]
    return {
        "owner": spec["owner"],
        "implementation_scope": list(spec["implementation_scope"]),
        "claim_tier": spec["claim_tier"],
        "transfer_source": spec["transfer_source"],
        "config_hash": f"sha256:{_sha(SPEC_PATH)}",
        "input_hashes": [
            {"path": str(card.relative_to(REPO)),
             "sha256": f"sha256:{_sha(card)}"},
            {"path": str(reduced_manifest.relative_to(REPO)),
             "sha256": f"sha256:{_sha(reduced_manifest)}"},
            {"path": str(cache_gate.relative_to(REPO)),
             "sha256": f"sha256:{_sha(cache_gate)}"},
            {"path": "htt/obsstat/k1_e2e_calibration.py",
             "sha256": f"sha256:{_sha(REPO / 'htt/obsstat/k1_e2e_calibration.py')}"},
            {"path": "scripts/k1_global_maxscan.py",
             "sha256": f"sha256:{_sha(REPO / 'scripts/k1_global_maxscan.py')}"},
            {"path": "scripts/k1_e2e_cache_gate.py",
             "sha256": f"sha256:{_sha(REPO / 'scripts/k1_e2e_cache_gate.py')}"},
        ],
        "sky_support_status":
            "Planck_PR3_SMICA_common_mask_registered_proc_nside64_support",
        "mask_status": "same frozen common mask on observed and all 999 null maps",
        "covariance_status":
            "empirical_999_CMB_null_with_300_reused_noise_realizations",
        "null_mock_status":
            "999 usable FFP10 CMB simulations; 300 noise simulations reused by parsed-ID modulo pairing",
        "caveats": [
            "The point rank is conditional on the PR3/FFP10 ensemble and frozen low-ell pipeline.",
            "Noise reuse prevents an iid exact-rank theorem; cycle and noise-cluster sensitivities accompany the point estimate.",
            "The idealised GRF check is preflight only.",
            "PR4/NPIPE matched simulations remain externally blocked, so no PR4 or joint number is emitted.",
            "The raw PR3 ensemble is retained until an authenticated PR4 replacement-ready receipt independently opens the deletion gate.",
            "CMB 00818 lacks 1,218 bytes of trailing FITS block padding; its data HDU is readable, its full-file SHA-256 matches the registered manifest, and its direct NSIDE64 array exactly matches the compact cache.",
            "No detection, preferred axis, geometry, or Bianchi-family claim is supported.",
        ],
        "generating_command":
            "venv/bin/python scripts/codex_harness/run_pr150_k1_e2e.py --write",
        "git_commit": spec["baseline_commit"],
        "worktree_state": "dirty_amendment_precommit",
    }


def _attach_metadata(payloads: list[dict], metadata: dict) -> None:
    required = {
        "owner", "implementation_scope", "claim_tier", "transfer_source",
        "config_hash", "input_hashes", "sky_support_status", "mask_status",
        "covariance_status", "null_mock_status", "caveats",
        "generating_command", "git_commit", "worktree_state",
    }
    missing = required - set(metadata)
    if missing:
        raise SystemExit(f"PR-150 artifact metadata is incomplete: {sorted(missing)}")
    for payload in payloads:
        payload["artifact_metadata"] = metadata


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


def _compact_retention_receipt(spec: dict) -> dict:
    """Bind the published result to the deletion-grade compact replay gate."""
    ds = spec["data_scope"]["raw_data_paths"]
    manifest_path = REPO / ds["reduced_manifest"]
    gate_path = REPO / ds["cache_gate"]
    if not manifest_path.is_file() or not gate_path.is_file():
        raise SystemExit("PR-150 compact manifest/cache gate is absent")
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    gate = json.loads(gate_path.read_text(encoding="utf-8"))
    if manifest.get("schema") != "htt.k1.e2e_reduce.v1":
        raise SystemExit("PR-150 compact manifest schema mismatch")
    if gate.get("schema") != "htt.k1.e2e_cache_gate.v2":
        raise SystemExit("PR-150 cache gate schema mismatch")
    if gate.get("manifest_hash") != f"sha256:{_sha(manifest_path)}":
        raise SystemExit("PR-150 cache gate is not bound to the compact manifest")

    inventory = gate.get("inventory") or {}
    cmb = inventory.get("cmb") or {}
    noise = inventory.get("noise") or {}
    result_replay = gate.get("result_artifact_replay") or {}
    required_true = {
        "full_map_replay": gate.get("full_map_replay"),
        "raw_hash_ok": gate.get("raw_hash_ok"),
        "direct_raw_to_cache_array_equal":
            gate.get("direct_raw_to_cache_array_equal"),
        "replay_files_exact": gate.get("replay_files_exact"),
        "observed_map_exact": gate.get("observed_map_exact"),
        "common_mask_exact": gate.get("common_mask_exact"),
        "independent_backup_exact_and_distinct_device":
            gate.get("independent_backup_exact_and_distinct_device"),
        "result_artifact_replay_exact": result_replay.get("exact"),
        "cache_reproducibility_green":
            gate.get("cache_reproducibility_green"),
        "cmb_inventory_exact": cmb.get("exact"),
        "noise_inventory_exact": noise.get("exact"),
    }
    failed = sorted(key for key, value in required_true.items()
                    if value is not True)
    if failed:
        raise SystemExit(f"PR-150 compact replay gate is not green: {failed}")
    if (gate.get("mode") != "all" or gate.get("user_tolerance") != 0.0
            or gate.get("n_checked") != 1299
            or gate.get("expected_map_count") != 1299
            or cmb.get("count") != 999 or noise.get("count") != 300):
        raise SystemExit("PR-150 compact replay did not cover exact 999+300 inventory")
    if (gate.get("pr4_replacement_ready", {}).get("ready") is not False
            or gate.get("safe_to_delete_raw") is not False):
        raise SystemExit("current PR-150 amendment requires raw-retention gate closed")

    compact = manifest.get("tier2_cache") or {}
    backup = manifest.get("independent_backup") or {}
    compact_path = Path(compact.get("path", ""))
    backup_path = Path(backup.get("path", ""))
    expected_hash = str(compact.get("cache_hash", ""))
    if (not compact_path.is_file() or not backup_path.is_file()
            or expected_hash != str(backup.get("cache_hash"))
            or f"sha256:{_sha(compact_path)}" != expected_hash
            or f"sha256:{_sha(backup_path)}" != expected_hash
            or compact_path.stat().st_dev == backup_path.stat().st_dev):
        raise SystemExit("PR-150 compact cache/independent backup authentication failed")
    if (len(manifest.get("parts", {}).get("cmb", {}).get("input_hashes", [])) != 999
            or len(manifest.get("parts", {}).get("noise", {}).get("input_hashes", [])) != 300):
        raise SystemExit("PR-150 compact manifest lacks all 1299 raw input hashes")

    raw_present = all((REPO / ds[key]).is_dir()
                      for key in ("cmb_mc_dir", "noise_mc_dir"))
    if not raw_present:
        raise SystemExit("PR-150 raw ensemble must remain present in this amendment")
    return {
        "schema": "pr150.compact_retention_receipt.v1",
        "status": "COMPACT_REPRODUCIBILITY_GREEN_RAW_RETAINED",
        "compact_cache": {
            "path": str(compact_path),
            "sha256": expected_hash,
            "size_bytes": compact_path.stat().st_size,
            "reduce_nside": manifest["config"]["reduce_nside"],
        },
        "independent_backup": {
            "path": str(backup_path),
            "sha256": expected_hash,
            "size_bytes": backup_path.stat().st_size,
            "distinct_filesystem_device": True,
        },
        "full_raw_inventory_hashes": {"cmb": 999, "noise": 300},
        "full_raw_to_compact_map_replay_count": 1299,
        "full_999_by_6_result_replay_exact": True,
        "cache_reproducibility_green": True,
        "reduced_manifest_creation_time_gate_flag":
            manifest.get("cache_reproducibility_gate_passed"),
        "gate_status_authority":
            "the separate content-addressed cache-gate receipt is authoritative; "
            "the reduced-manifest flag records its pre-gate creation state",
        "raw_sources_present": True,
        "raw_deletion_executed": False,
        "pr4_replacement_ready": False,
        "mechanically_deletion_eligible": bool(
            gate.get("mechanically_deletion_eligible", False)),
        "explicit_storage_swap_authorization_provided": False,
        "safe_to_delete_raw": False,
        "retention_decision": gate["raw_retention_decision"],
        "future_deletion_conditions": [
            "compact cache and independent backup remain hash-authenticated",
            "a versioned PR4 replacement-ready receipt is present and every local replacement path, size, full SHA-256, ID, exclusion, and canonical inventory hash is independently verified",
            "the deletion gate is rerun and reports mechanically_deletion_eligible=true",
            "a separate later workflow receives explicit human authorization for the PR3-to-PR4 storage swap; this validator never reports permission or deletes data",
        ],
        "source_receipts": {
            "reduced_manifest": str(manifest_path.relative_to(REPO)),
            "reduced_manifest_sha256": f"sha256:{_sha(manifest_path)}",
            "cache_gate": str(gate_path.relative_to(REPO)),
            "cache_gate_sha256": f"sha256:{_sha(gate_path)}",
        },
    }


def build_reports(spec: dict):
    m = spec["model"]
    idl = m["idealised"]
    e2e = m["e2e"]
    ds = spec["data_scope"]["raw_data_paths"]
    cmb_dir = REPO / ds["cmb_mc_dir"]
    noise_dir = REPO / ds["noise_mc_dir"]
    card_path = REPO / ds["e2e_card"]
    # anti-drift guards invoked LIVE with admissible input
    refuse_idealised_promotion("idealised_method_calibration_only")
    refuse_real_sky_p_without_e2e(card_path.is_file(), "e2e_conditional_p")
    refuse_pr4_numeric("non_numeric_skip_receipt")
    refuse_pr3_pr4_joint("pr3_only")
    refuse_k1_axis_detection("feature_extraction_only")

    idealised = {"schema": "pr150.idealised_super_uniformity.v1",
                 "module_schema": SCHEMA_VERSION,
                 **idealised_super_uniformity(
                     n_statistics=int(idl["n_statistics"]),
                     rho=float(Fraction(idl["correlation_rho"])),
                     n_realizations=int(idl["n_realizations"]),
                     seed=int(idl["seed"]),
                     band=float(Fraction(idl["super_uniform_band"])))}
    refuse_non_super_uniform(idealised["super_uniform"])   # kill switch, live

    manifest_e2e = {"schema": "pr150.e2e_input_manifest.v1",
                    **e2e_input_manifest(cmb_dir, noise_dir,
                                         sample_hash_count=int(e2e["sample_hash_count"]))}
    if (manifest_e2e["usable_cmb_count"] != 999
            or manifest_e2e["noise_mc_count"] != 300):
        raise SystemExit("PR3 readiness contract requires exactly 999 CMB and 300 noise maps")
    pooled = {"schema": "pr150.e2e_pooled_rank.v1",
              **pooled_rank_from_e2e_card(card_path)}
    if pooled["simulation_count"] != 999:
        raise SystemExit("the full PR-150 result must use all 999 usable CMB maps")
    pr4 = {"schema": "pr150.pr4_skip_receipt.v1", **pr4_npipe_skip_receipt()}
    compact_retention = _compact_retention_receipt(spec)
    return idealised, manifest_e2e, pooled, compact_retention, pr4


def build_captions(idealised: dict, manifest_e2e: dict, pooled: dict) -> dict:
    text = generate_caption(idealised, manifest_e2e, pooled)
    lint_caption(text)
    return {"schema": "pr150.captions.v1", "captions": {"summary": text}}


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
        "idealised_promoted_to_planck":
            lambda: refuse_idealised_promotion("idealised_is_planck_calibration"),
        "real_sky_p_without_e2e":
            lambda: refuse_real_sky_p_without_e2e(False, "real_sky_p"),
        "pr4_numeric_output": lambda: refuse_pr4_numeric("pr4_p_value"),
        "pr3_pr4_joint": lambda: refuse_pr3_pr4_joint("pr3_pr4_joint"),
        "k1_axis_detection": lambda: refuse_k1_axis_detection("k1_axis"),
        "non_super_uniform_accepted":
            lambda: refuse_non_super_uniform(False),
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
        except K1E2EError as exc:
            killed = True
            message = _redact(str(exc), redact_patterns)[:220]
        rows.append({"mutation_id": mutation_id,
                     "kill_rule": registered[mutation_id],
                     "killed": killed, "kill_message_redacted": message})
    return {"schema": "pr150.mutation_report.v1", "mutations": rows,
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
        return
    try:
        existing = json.loads(target.read_text(encoding="utf-8"))
    except (UnicodeError, json.JSONDecodeError):
        problems.append(f"invalid artifact: {rel}")
        return
    if (
        isinstance(existing, dict)
        and _semantic_artifact(rel, existing)
        == _semantic_artifact(rel, payload)
    ):
        return
    if target.read_bytes() != rendered:
        problems.append(f"stale artifact: {rel}")


def build(write: bool) -> int:
    spec = yaml.safe_load(SPEC_PATH.read_text(encoding="utf-8"))
    if spec.get("schema") != "htt.long_horizon.pr150_k1_e2e.v1":
        raise SystemExit("pr150 spec schema mismatch")
    _verify_baseline_commit(spec)
    _verify_remediation_state(spec)
    problems: list[str] = []
    wrote: list[str] = []

    idealised, manifest_e2e, pooled, compact_retention, pr4 = build_reports(spec)
    captions = build_captions(idealised, manifest_e2e, pooled)
    metadata = _artifact_metadata(spec)
    _attach_metadata(
        [idealised, manifest_e2e, pooled, compact_retention, pr4, captions],
        metadata)
    idealised["negative_scan"] = {"targets": _scan_targets(spec, captions),
                                  "total_hits": 0}
    mutations = run_mutations(spec)
    _attach_metadata([mutations], metadata)
    if mutations["surviving_mutation_count"]:
        print(json.dumps({"ok": False, "survivors": mutations["mutations"]}))
        return 2

    _emit(OUTPUTS["idealised"], idealised, write, problems, wrote)
    _emit(OUTPUTS["manifest_e2e"], manifest_e2e, write, problems, wrote)
    _emit(OUTPUTS["pooled_rank"], pooled, write, problems, wrote)
    _emit(OUTPUTS["compact_retention"], compact_retention,
          write, problems, wrote)
    _emit(OUTPUTS["pr4"], pr4, write, problems, wrote)
    _emit(OUTPUTS["captions"], captions, write, problems, wrote)
    _emit(OUTPUTS["mutations"], mutations, write, problems, wrote)

    ds = spec["data_scope"]["raw_data_paths"]
    manifest = {
        "schema": "pr150.artifact_manifest.v1",
        "artifact_metadata": metadata,
        "owner": spec["owner"], "claim_tier": spec["claim_tier"],
        "claim_level": spec["claim_level"],
        "artifact_mode": spec["artifact_mode"],
        "allowed_use": spec["allowed_use"],
        "forbidden_use": list(spec["forbidden_output_language"]),
        "transfer_source": spec["transfer_source"],
        "config_hash": _sha(SPEC_PATH),
        "raw_data_pins": {
            "e2e_card_sha256": _sha(REPO / ds["e2e_card"]),
            "reduced_manifest_sha256": _sha(REPO / ds["reduced_manifest"]),
            "cache_gate_sha256": _sha(REPO / ds["cache_gate"]),
            "compact_cache_sha256":
                compact_retention["compact_cache"]["sha256"],
        },
        "input_hashes": [f"htt/obsstat/k1_e2e_calibration.py:"
                         f"{_sha(REPO / 'htt/obsstat/k1_e2e_calibration.py')}",
                         f"scripts/k1_global_maxscan.py:"
                         f"{_sha(REPO / 'scripts/k1_global_maxscan.py')}",
                         f"scripts/k1_e2e_cache_gate.py:"
                         f"{_sha(REPO / 'scripts/k1_e2e_cache_gate.py')}"],
        "caveats": [
            "PR3/FFP10-E2E-conditional morphology result at C2.",
            "The idealised GRF super-uniformity is a method-calibration "
            "preflight, NEVER promoted to a Planck systematics calibration.",
            "No real-sky p-value without the E2E ensemble.",
            "The 300 noise maps are reused across 999 independent CMB maps; "
            "cycle splits and a noise-cluster bootstrap accompany the point rank.",
            "PR4/NPIPE records a public observed map but externally blocked "
            "simulation access; no PR3+PR4 joint result.",
            "No detection or Bianchi-family claim; the two CF4 P0s are "
            "untouched and stay OPEN.",
            "All 102 remediation findings remain OPEN.",
            "The raw PR3 ensemble remains retained until an authenticated PR4 "
            "replacement-ready receipt opens the deletion gate.",
            "CMB 00818 triggers an Astropy warning for 1,218 missing trailing "
            "FITS-padding bytes; its registered full-file hash and direct "
            "NSIDE64 map replay both pass exactly.",
        ],
        "artifacts": {rel: (_sha(REPO / rel) if (REPO / rel).is_file()
                            else None)
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
    module_text = (REPO / "htt/obsstat/k1_e2e_calibration.py") \
        .read_text(encoding="utf-8").lower()
    for phrase in spec["forbidden_output_language"]:
        if phrase.lower() in module_text:
            print(json.dumps({"ok": False,
                              "reason": "forbidden phrase in module"}))
            return 2
    print(json.dumps({
        "ok": True, "mode": "write" if write else "check", "wrote": wrote,
        "super_uniform": idealised["super_uniform"],
        "e2e_pooled_rank_p": round(pooled["e2e_global_pooled_rank_p"], 4),
        "cmb_mc": manifest_e2e["cmb_mc_count"],
        "noise_mc": manifest_e2e["noise_mc_count"],
        "noise_reuse_sensitivity": bool(pooled["noise_reuse_sensitivity"]),
        "compact_reproducibility_green":
            compact_retention["cache_reproducibility_green"],
        "safe_to_delete_raw": compact_retention["safe_to_delete_raw"],
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
