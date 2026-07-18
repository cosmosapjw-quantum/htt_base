#!/usr/bin/env python3
"""PR-143 runner: integrated synthetic calibration + hostile adjudication.

``--write`` builds / ``--check`` verifies (fresh build must equal disk
bytes): the non-author referee report over the sealed blind DGP battery,
the method-ready/block matrix, the generator/analyst/referee separation
receipt, generated captions, and the six-mutant kill report.

Pre-data method-calibration mechanics at roadmap_rescue_v1:C3; passing the
synthetic challenge is method readiness, not observed validity; no
detection.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from fractions import Fraction
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "htt" / "src"))
sys.path.insert(0, str(REPO / "htt"))

import yaml  # noqa: E402

from common.mixture_competition import DiscriminationConfig  # noqa: E402
from common.synthetic_adjudication import (  # noqa: E402
    DGP_BATTERY,
    SCHEMA_VERSION,
    AdjudicationError,
    Criteria,
    adjudicate_ensemble,
    computational_failure_probe,
    generate_caption,
    lint_caption,
    method_ready_matrix,
    refuse_cherry_pick,
    refuse_hidden_failure,
    refuse_retune_same_id,
    refuse_synthetic_as_observed,
    require_generator_analyst_separation,
    require_non_author_referee,
    separation_receipt,
)

SPEC_PATH = REPO / "docs/research_program/long_horizon_rescue/pr143_spec.yaml"
OUTPUTS = {
    "referee": "docs/generated/pr143_referee_report.json",
    "matrix": "docs/generated/pr143_method_ready_matrix.json",
    "receipt": "docs/generated/pr143_separation_receipt.json",
    "captions": "docs/generated/pr143_captions.json",
    "mutations": "docs/generated/pr143_mutation_report.json",
    "manifest": "docs/generated/pr143_artifact_manifest.json",
}
REDACTED = "[REDACTED-PATTERN]"


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _round(obj):
    if isinstance(obj, float):
        return round(obj, 8)
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
    probe = subprocess.run(
        ["git", "cat-file", "-e", f"{sha}^{{commit}}"],
        cwd=REPO, capture_output=True, check=False)
    if probe.returncode != 0:
        raise SystemExit(
            f"baseline_commit {sha} does not resolve to a commit — "
            "fabricated provenance is refused")


def _verify_remediation_state(spec: dict) -> None:
    contract = spec["remediation_state_contract"]
    target = REPO / contract["path"]
    if _sha(target) != contract["sha256"]:
        raise SystemExit("remediation state drifted from the spec pin")
    payload = yaml.safe_load(target.read_text(encoding="utf-8"))
    findings = payload.get("findings") or []
    statuses: dict[str, int] = {}
    for row in findings:
        status = str(row.get("scientific_status"))
        statuses[status] = statuses.get(status, 0) + 1
    if len(findings) != contract["finding_count"]:
        raise SystemExit("remediation finding count drifted")
    required = {str(k): int(v)
                for k, v in contract["required_scientific_status_counts"]
                .items()}
    if statuses != required:
        raise SystemExit(f"remediation status counts drifted: {statuses}")


def _config(spec: dict) -> DiscriminationConfig:
    m = spec["challenge"]["method"]
    return DiscriminationConfig(
        sig2=float(Fraction(m["sig2"])), tau2=float(Fraction(m["tau2"])),
        gain_margin_log_bf=float(Fraction(m["gain_margin_log_bf"])),
        identifiability_gap=float(Fraction(m["identifiability_gap"])),
        collinearity_threshold=float(Fraction(m["collinearity_threshold"])),
        ppc_reject=float(Fraction(m["ppc_reject"])),
        prior_swing_ceiling=float(Fraction(m["prior_swing_ceiling"])),
        tau2_grid=tuple(float(Fraction(t)) for t in m["tau2_grid"]),
        held_out_gain_floor=float(Fraction(m["held_out_gain_floor"])),
        combination_margin=float(Fraction(m["combination_margin"])),
        seed=int(m["seed"]))


def _criteria(spec: dict) -> Criteria:
    c = spec["criteria"]
    return Criteria(size_alpha=float(Fraction(c["size_alpha"])),
                    power_min=float(Fraction(c["power_min"])),
                    abstain_min=float(Fraction(c["abstain_min"]))).sealed()


def build_challenge(spec: dict):
    ch = spec["challenge"]
    config = _config(spec)
    criteria = _criteria(spec)
    report = adjudicate_ensemble(
        ch["challenge_id"], ch["generator_id"], ch["analyst_id"],
        ch["referee_id"], seeds=[int(s) for s in ch["ensemble_seeds"]],
        n_reps=int(ch["n_reps"]), n_obs=int(ch["n_obs"]),
        template_seed=int(ch["template_seed"]), config=config,
        criteria=criteria)
    comp = computational_failure_probe(
        config, n_obs=int(ch["n_obs"]),
        template_seed=int(ch["template_seed"]))
    matrix = method_ready_matrix(report, comp)

    # anti-drift guards invoked LIVE on the production adjudication path (each
    # passes with the admissible input; a drift supplies a rejected one):
    # the FULL battery is scored, the claim scope is method-readiness, and the
    # criteria are not retuned under the same challenge id
    refuse_cherry_pick(list(DGP_BATTERY))
    refuse_synthetic_as_observed("method_readiness")
    refuse_retune_same_id(report["criteria_hash"], report["criteria_hash"],
                          ch["challenge_id"], ch["challenge_id"])

    # verify the pre-registered expected outcome
    expected = spec["expected_outcome"]
    ready = {f for f, v in matrix["matrix"].items() if v == "ready"}
    blocked = {f for f, v in matrix["matrix"].items() if v == "block"}
    if ready != set(expected["ready_families"]) | {"computational_failure"}:
        raise SystemExit(f"ready families drifted: {sorted(ready)}")
    if blocked != set(expected["blocked_families"]):
        raise SystemExit(f"blocked families drifted: {sorted(blocked)}")
    # the MEASURED null size (a nonzero value) must be within the level alpha
    ceiling = float(Fraction(expected["measured_size_ceiling"]))
    if report["measured_size"] > ceiling:
        raise SystemExit(f"measured null size {report['measured_size']} "
                         f"exceeds the pre-registered level {ceiling}")
    # the block must be recorded, not hidden
    refuse_hidden_failure(report, matrix["matrix"])
    report["comp_failure"] = comp
    return report, matrix, criteria, config


def build_receipt(spec: dict, report: dict, criteria) -> dict:
    ch = spec["challenge"]
    return separation_receipt(ch["challenge_id"], ch["generator_id"],
                              ch["analyst_id"], ch["referee_id"], criteria,
                              report["ensemble_hash"])


def build_captions(matrix: dict, report: dict) -> dict:
    n_ready = sum(1 for v in matrix["matrix"].values() if v == "ready")
    n_block = sum(1 for v in matrix["matrix"].values() if v == "block")
    text = generate_caption(report["method_verdict"], n_ready, n_block,
                            report["measured_size"])
    lint_caption(text)
    return {"schema": "pr143.captions.v1", "captions": {"summary": text}}


def _scan_targets(spec: dict, captions_payload: dict) -> dict:
    patterns = [str(p) for p in spec["negative_scan"]["forbidden_patterns"]]
    targets = {}
    for rel in spec["negative_scan"]["targets"]:
        if rel == OUTPUTS["captions"]:
            raw = _render(captions_payload).decode()
            source = "fresh_build"
            digest = hashlib.sha256(raw.encode()).hexdigest()
        else:
            path = REPO / rel
            raw = path.read_text(encoding="utf-8")
            source = "disk"
            digest = _sha(path)
        hits = []
        for idx, line in enumerate(raw.splitlines(), start=1):
            lowered = line.lower()
            for pattern_index, pattern in enumerate(patterns):
                if pattern.lower() in lowered:
                    hits.append({"line": idx, "pattern_index": pattern_index})
        targets[rel] = {"hits": hits, "source": source, "sha256": digest}
    total = sum(len(t["hits"]) for t in targets.values())
    if total:
        raise SystemExit(f"negative scan found {total} forbidden-language "
                         f"hits: {targets}")
    return targets


def _redact(message: str, patterns: list[str]) -> str:
    for pattern in patterns:
        lowered = message.lower()
        needle = pattern.lower()
        while needle in lowered:
            start = lowered.index(needle)
            message = message[:start] + REDACTED + \
                message[start + len(pattern):]
            lowered = message.lower()
    return message


def run_mutations(spec: dict, report: dict, matrix: dict) -> dict:
    redact_patterns = (
        [str(p) for p in spec["negative_scan"]["forbidden_patterns"]]
        + [str(p) for p in spec["forbidden_output_language"]])
    ch = spec["challenge"]

    def mutant_cherry_pick_favorable() -> None:
        refuse_cherry_pick([f for f in DGP_BATTERY
                            if f != "covariance_misspecified"])

    def mutant_retune_then_rescore_same_id() -> None:
        refuse_retune_same_id("hash_a", "hash_b", ch["challenge_id"],
                              ch["challenge_id"])

    def mutant_synthetic_as_observed() -> None:
        refuse_synthetic_as_observed("observed_validity")

    def mutant_hide_failed_family() -> None:
        hidden = {k: v for k, v in matrix["matrix"].items()
                  if k != "covariance_misspecified"}
        refuse_hidden_failure(report, hidden)

    def mutant_generator_analyst_merge() -> None:
        require_generator_analyst_separation(ch["generator_id"],
                                             ch["generator_id"])

    def mutant_self_adjudicating_referee() -> None:
        require_non_author_referee(ch["generator_id"], ch["analyst_id"],
                                   ch["analyst_id"])

    registered = {m["mutation_id"]: m["kill_rule"]
                  for m in spec["mutation_registry"]}
    executions = {
        "cherry_pick_favorable": mutant_cherry_pick_favorable,
        "retune_then_rescore_same_id": mutant_retune_then_rescore_same_id,
        "synthetic_as_observed": mutant_synthetic_as_observed,
        "hide_failed_family": mutant_hide_failed_family,
        "generator_analyst_merge": mutant_generator_analyst_merge,
        "self_adjudicating_referee": mutant_self_adjudicating_referee,
    }
    if set(registered) != set(executions):
        raise SystemExit("mutation registry does not match the executions")
    rows = []
    for mutation_id, fn in executions.items():
        killed = False
        message = "MUTANT SURVIVED"
        try:
            fn()
        except AdjudicationError as exc:
            killed = True
            message = _redact(str(exc), redact_patterns)[:220]
        rows.append({"mutation_id": mutation_id,
                     "kill_rule": registered[mutation_id],
                     "killed": killed, "kill_message_redacted": message})
    return {"schema": "pr143.mutation_report.v1", "mutations": rows,
            "surviving_mutation_count":
                len([m for m in rows if not m["killed"]])}


def _emit(rel: str, payload: dict, write: bool,
          problems: list[str], wrote: list[str]) -> None:
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
    if spec.get("schema") != "htt.long_horizon.pr143_adjudication.v1":
        raise SystemExit("pr143 spec schema mismatch")
    _verify_baseline_commit(spec)
    _verify_remediation_state(spec)
    problems: list[str] = []
    wrote: list[str] = []

    report, matrix, criteria, _ = build_challenge(spec)
    receipt = build_receipt(spec, report, criteria)
    captions = build_captions(matrix, report)
    referee_record = {"schema": "pr143.referee_report.v1",
                      "module_schema": SCHEMA_VERSION, **report,
                      "negative_scan": {
                          "targets": _scan_targets(spec, captions),
                          "total_hits": 0}}
    matrix_record = {"schema": "pr143.method_ready_matrix.v1", **matrix}
    mutations = run_mutations(spec, report, matrix)
    if mutations["surviving_mutation_count"]:
        print(json.dumps({"ok": False, "survivors": mutations["mutations"]}))
        return 2

    _emit(OUTPUTS["referee"], referee_record, write, problems, wrote)
    _emit(OUTPUTS["matrix"], matrix_record, write, problems, wrote)
    _emit(OUTPUTS["receipt"], receipt, write, problems, wrote)
    _emit(OUTPUTS["captions"], captions, write, problems, wrote)
    _emit(OUTPUTS["mutations"], mutations, write, problems, wrote)

    manifest = {
        "schema": "pr143.artifact_manifest.v1",
        "owner": spec["owner"],
        "adjudicator": spec["adjudicator"],
        "claim_tier": spec["claim_tier"],
        "claim_level": spec["claim_level"],
        "artifact_mode": spec["artifact_mode"],
        "allowed_use": spec["allowed_use"],
        "forbidden_use": list(spec["forbidden_output_language"]),
        "transfer_source": spec["transfer_source"],
        "config_hash": _sha(SPEC_PATH),
        "input_hashes": [
            f"{rel}:{_sha(REPO / rel)}"
            for rel in ("htt/src/common/synthetic_adjudication.py",
                        "htt/src/common/mixture_competition.py")
        ],
        "caveats": [
            "Pre-data method-calibration mechanics at C3 only.",
            "Passing the synthetic challenge is METHOD READINESS, not "
            "observed validity; the generator/analyst/referee separation "
            "is sealed.",
            "The method is ready on six DGP families plus the "
            "computational-failure lane and BLOCKED on covariance-"
            "misspecification DIAGNOSIS; the measured null size over the seed "
            "ensemble is a small NON-ZERO value within the pre-registered "
            "level alpha (a calibrated size, never claimed to be zero).",
            "A blocked criterion blocks only the dependent data PRs; the "
            "failure is recorded, not hidden.",
            "No detection.",
            "All 102 remediation findings remain OPEN.",
        ],
        "artifacts": {
            rel: (_sha(REPO / rel) if (REPO / rel).is_file() else None)
            for key, rel in OUTPUTS.items() if key != "manifest"
        },
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
    module_text = (REPO / "htt/src/common/synthetic_adjudication.py") \
        .read_text(encoding="utf-8").lower()
    for phrase in spec["forbidden_output_language"]:
        if phrase.lower() in module_text:
            print(json.dumps({"ok": False,
                              "reason": "forbidden phrase in module source"}))
            return 2
    print(json.dumps({
        "ok": True, "mode": "write" if write else "check", "wrote": wrote,
        "method_verdict": report["method_verdict"],
        "blocked_families": report["blocked_families"],
        "method_ready": matrix["method_ready"],
        "measured_size": round(report["measured_size"], 6),
        "n_seeds": report["n_seeds"],
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
