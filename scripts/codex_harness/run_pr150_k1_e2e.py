#!/usr/bin/env python3
"""PR-150 runner: K1 exchangeable global scan + Planck PR3 FFP10 E2E calibration.

``--write`` builds / ``--check`` verifies (fresh build must equal disk bytes):
the idealised correlated-GRF pooled-rank super-uniformity (falsifier), the PR3
FFP10 E2E input manifest (999 CMB + 300 noise Monte-Carlo maps), the
exchangeable pooled-rank global-p read from the heavy E2E max-scan card, the
non-numeric PR4 skip receipt, captions, and the six-mutant kill report.

The heavy E2E max-scan card is produced ONCE by
``scripts/k1_global_maxscan.py --precision`` on the FFP10 ensemble; this runner
reads it (the ACT pattern) and never re-runs the 600 GB read.

PR3/FFP10-E2E-conditional morphology diagnostic at roadmap_rescue_v1:C2; no
detection, no Bianchi-family claim; PR4/NPIPE is a non-numeric skip.
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
    "pr4": "docs/generated/pr150_pr4_skip_receipt.json",
    "captions": "docs/generated/pr150_captions.json",
    "mutations": "docs/generated/pr150_mutation_report.json",
    "manifest": "docs/generated/pr150_artifact_manifest.json",
}
REDACTED = "[REDACTED-PATTERN]"


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _round(obj):
    if isinstance(obj, float):
        return round(obj, 6)
    if isinstance(obj, dict):
        return {k: _round(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_round(v) for v in obj]
    return obj


def _render(payload: dict) -> bytes:
    return (json.dumps(_round(payload), indent=2, ensure_ascii=False,
                       sort_keys=True) + "\n").encode()


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
    pooled = {"schema": "pr150.e2e_pooled_rank.v1",
              **pooled_rank_from_e2e_card(card_path)}
    pr4 = {"schema": "pr150.pr4_skip_receipt.v1", **pr4_npipe_skip_receipt()}
    return idealised, manifest_e2e, pooled, pr4


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
    elif target.read_bytes() != rendered:
        problems.append(f"stale artifact: {rel}")


def build(write: bool) -> int:
    spec = yaml.safe_load(SPEC_PATH.read_text(encoding="utf-8"))
    if spec.get("schema") != "htt.long_horizon.pr150_k1_e2e.v1":
        raise SystemExit("pr150 spec schema mismatch")
    _verify_baseline_commit(spec)
    _verify_remediation_state(spec)
    problems: list[str] = []
    wrote: list[str] = []

    idealised, manifest_e2e, pooled, pr4 = build_reports(spec)
    captions = build_captions(idealised, manifest_e2e, pooled)
    idealised["negative_scan"] = {"targets": _scan_targets(spec, captions),
                                  "total_hits": 0}
    mutations = run_mutations(spec)
    if mutations["surviving_mutation_count"]:
        print(json.dumps({"ok": False, "survivors": mutations["mutations"]}))
        return 2

    _emit(OUTPUTS["idealised"], idealised, write, problems, wrote)
    _emit(OUTPUTS["manifest_e2e"], manifest_e2e, write, problems, wrote)
    _emit(OUTPUTS["pooled_rank"], pooled, write, problems, wrote)
    _emit(OUTPUTS["pr4"], pr4, write, problems, wrote)
    _emit(OUTPUTS["captions"], captions, write, problems, wrote)
    _emit(OUTPUTS["mutations"], mutations, write, problems, wrote)

    ds = spec["data_scope"]["raw_data_paths"]
    manifest = {
        "schema": "pr150.artifact_manifest.v1",
        "owner": spec["owner"], "claim_tier": spec["claim_tier"],
        "claim_level": spec["claim_level"],
        "artifact_mode": spec["artifact_mode"],
        "allowed_use": spec["allowed_use"],
        "forbidden_use": list(spec["forbidden_output_language"]),
        "transfer_source": spec["transfer_source"],
        "config_hash": _sha(SPEC_PATH),
        "raw_data_pins": {
            "e2e_card_sha256": _sha(REPO / ds["e2e_card"])},
        "input_hashes": [f"htt/obsstat/k1_e2e_calibration.py:"
                         f"{_sha(REPO / 'htt/obsstat/k1_e2e_calibration.py')}"],
        "caveats": [
            "PR3/FFP10-E2E-conditional morphology diagnostic at C2 only.",
            "The idealised GRF super-uniformity is a method-calibration "
            "falsifier, NEVER promoted to a Planck systematics calibration.",
            "No real-sky p-value without the E2E ensemble.",
            "PR4/NPIPE is a non-numeric skip receipt; no PR3+PR4 joint result.",
            "No detection or Bianchi-family claim; the two CF4 P0s are "
            "untouched and stay OPEN.",
            "All 102 remediation findings remain OPEN.",
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
