#!/usr/bin/env python3
"""PR-152 runner: ACT DR6 raw-QE gate + release-simulation cross-fit.

``--write`` builds / ``--check`` verifies (fresh build must equal disk bytes):
the authenticated inventory, the leave-one-simulation cross-fit mean field, the
exact finite rank, the stochastic-vs-fixed-template injection law, the upstream
raw-QE availability decision, captions and the six-mutant kill report --- all
read from the heavy card produced once by ``scripts/act_raw_qe_card.py`` on the
real ACT DR6 lensing release (the ACT pattern; this runner never re-runs the
~60 GB read).

Because the raw-QE inputs are absent, only the release-simulation cross-fit
diagnostic is closed.  ACT-release-simulation diagnostic at roadmap_rescue_v1:C3;
no convergence detection, anisotropy, or Bianchi-family claim.
"""
from __future__ import annotations

import argparse
import hashlib
import json
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
    "rank": "docs/generated/pr152_exact_rank.json",
    "injection": "docs/generated/pr152_injection_law.json",
    "decision": "docs/generated/pr152_availability_decision.json",
    "captions": "docs/generated/pr152_captions.json",
    "mutations": "docs/generated/pr152_mutation_report.json",
    "manifest": "docs/generated/pr152_artifact_manifest.json",
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
    if not CARD_PATH.is_file():
        raise SystemExit(
            "the ACT raw-QE card is absent — run scripts/act_raw_qe_card.py on "
            "the real ACT DR6 lensing release first")
    card = json.loads(CARD_PATH.read_text(encoding="utf-8"))
    if card.get("status") != "RELEASE_SIMULATION_CROSSFIT":
        raise SystemExit(f"ACT card status is {card.get('status')}")
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
    rank = {"schema": "pr152.exact_rank.v1", **card["exact_rank"]}
    injection = {"schema": "pr152.injection_law.v1", **card["injection_law"]}
    decision = {"schema": "pr152.availability_decision.v1",
                **card["availability_decision"]}
    return inventory, crossfit, rank, injection, decision


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
    if spec.get("schema") != "htt.long_horizon.pr152_act_raw_qe.v1":
        raise SystemExit("pr152 spec schema mismatch")
    _verify_baseline_commit(spec)
    _verify_remediation_state(spec)
    problems: list[str] = []
    wrote: list[str] = []

    inventory, crossfit, rank, injection, decision = build_reports(spec)
    captions = build_captions(inventory, crossfit, decision)
    inventory["negative_scan"] = {"targets": _scan_targets(spec, captions),
                                  "total_hits": 0}
    mutations = run_mutations(spec)
    if mutations["surviving_mutation_count"]:
        print(json.dumps({"ok": False, "survivors": mutations["mutations"]}))
        return 2

    _emit(OUTPUTS["inventory"], inventory, write, problems, wrote)
    _emit(OUTPUTS["crossfit"], crossfit, write, problems, wrote)
    _emit(OUTPUTS["rank"], rank, write, problems, wrote)
    _emit(OUTPUTS["injection"], injection, write, problems, wrote)
    _emit(OUTPUTS["decision"], decision, write, problems, wrote)
    _emit(OUTPUTS["captions"], captions, write, problems, wrote)
    _emit(OUTPUTS["mutations"], mutations, write, problems, wrote)

    manifest = {
        "schema": "pr152.artifact_manifest.v1",
        "owner": spec["owner"], "claim_tier": spec["claim_tier"],
        "claim_level": spec["claim_level"],
        "artifact_mode": spec["artifact_mode"],
        "allowed_use": spec["allowed_use"],
        "forbidden_use": list(spec["forbidden_output_language"]),
        "transfer_source": spec["transfer_source"],
        "config_hash": _sha(SPEC_PATH),
        "raw_data_pins": {"act_raw_qe_card_sha256": _sha(CARD_PATH)},
        "input_hashes": [f"htt/obsstat/act_raw_qe_gate.py:"
                         f"{_sha(REPO / 'htt/obsstat/act_raw_qe_gate.py')}"],
        "caveats": [
            "ACT-release-simulation cross-fit diagnostic at C3 only.",
            "The raw-QE inputs (raw filtered CMB maps + QE pipeline) are absent, "
            "so the raw-QE inference is abandoned "
            "(ABANDON_CURRENT_DATASET_FOR_NATIVE_LOW_L_SKY_POWER).",
            "The mean field is a leave-one-simulation cross-fit; released "
            "convergence plus a signal is never called a pre-QE-stage transfer.",
            "No L=2..10 sky-power limit is computed from absent raw-QE inputs.",
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
        "crossfit_pooled_rank_p": crossfit["crossfit_pooled_rank_p"],
        "exact_finite_rank": rank["exact_finite_rank"],
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
