#!/usr/bin/env python3
"""PR-148 runner: depth-resolved fsigma8 with a same-data joint covariance bound.

``--write`` builds / ``--check`` verifies (fresh build must equal disk bytes):
the per-shell fsigma8 (constrained/unconstrained), the measured same-data joint
covariance (PSD + eigen), the joint-covariance-conditioned growth-difference
BOUND (nonidentified — only the nearest shell constrains fsigma8), the held-out
depth prediction, the shell-edge stability, the two CF4 P0 remediation-CANDIDATE
receipts, captions, and the six-mutant kill report.

Growth-difference bound mechanics at roadmap_rescue_v1:C3; the two CF4 P0s stay
OPEN; no global-tilt or anomaly claim.
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

from obsstat.cf4_growth_covariance import (  # noqa: E402
    GrowthCovarianceError,
    SCHEMA_VERSION,
    classify_constrained,
    depth_shell_preps,
    fsigma8_by_depth,
    generate_caption,
    growth_difference_bound,
    held_out_depth_prediction,
    joint_covariance,
    lint_caption,
    refuse_anomaly_claim,
    refuse_cf4_p0_closure,
    refuse_correlation_endpoint_selection,
    refuse_shell_bias_single_point,
    refuse_target_tension_sigma,
    require_positive_definite,
    shell_edge_stability,
    simultaneous_intervals,
)

SPEC_PATH = REPO / "docs/research_program/long_horizon_rescue/pr148_spec.yaml"
OUTPUTS = {
    "fsigma8": "docs/generated/pr148_fsigma8_by_depth.json",
    "covariance": "docs/generated/pr148_joint_covariance.json",
    "growth": "docs/generated/pr148_growth_difference_bound.json",
    "held_out": "docs/generated/pr148_held_out_prediction.json",
    "stability": "docs/generated/pr148_shell_stability.json",
    "p0": "docs/generated/pr148_p0_remediation_candidates.json",
    "captions": "docs/generated/pr148_captions.json",
    "mutations": "docs/generated/pr148_mutation_report.json",
    "manifest": "docs/generated/pr148_artifact_manifest.json",
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


def _groups(spec: dict) -> Path:
    return REPO / spec["data_scope"]["raw_data_paths"]["groups"]


def build_reports(spec: dict):
    m = spec["model"]
    groups = _groups(spec)
    n_shells = int(m["n_shells"])
    rel = float(m["constrained_relative_error_max"])
    # anti-drift guards invoked LIVE with admissible input
    refuse_target_tension_sigma("report_measured_bound")
    refuse_correlation_endpoint_selection("measured_covariance")
    refuse_shell_bias_single_point("per_shell_reported")
    refuse_anomaly_claim("no_claim")
    refuse_cf4_p0_closure("remediation_candidate")

    sub, dist, edges, preps = depth_shell_preps(
        groups, subsample=int(m["subsample"]), seed=int(m["subsample_seed"]),
        n_shells=n_shells)
    fs8 = {"schema": "pr148.fsigma8_by_depth.v1", "module_schema": SCHEMA_VERSION,
           **fsigma8_by_depth(preps)}
    cov = {"schema": "pr148.joint_covariance.v1",
           **joint_covariance(sub, preps, n_mock=int(m["n_mock"]),
                              seed=int(m["mock_seed"]))}
    require_positive_definite(cov)     # kill switch, live
    # the constrained/unconstrained disposition uses the ROBUST mock covariance
    classify_constrained(fs8, cov, constrained_rel_err=rel)
    growth = {"schema": "pr148.growth_difference_bound.v1",
              **growth_difference_bound(
                  fs8, cov, comparator=float(Fraction(m["comparator_fsigma8"])),
                  comparator_sigma=float(Fraction(m["comparator_fsigma8_sigma"])))}
    held = {"schema": "pr148.held_out_prediction.v1",
            **held_out_depth_prediction(fs8, cov)}
    sim = simultaneous_intervals(fs8, cov, family_conf=0.95)
    fs8["simultaneous_intervals"] = sim
    stab = {"schema": "pr148.shell_stability.v1",
            **shell_edge_stability(
                groups, subsample=int(m["subsample"]),
                seed=int(m["subsample_seed"]), n_shells=n_shells,
                jitter_fractions=[float(x) for x in m["shell_edge_jitter_fraction"]],
                constrained_rel_err=rel)}
    return fs8, cov, growth, held, stab


def build_p0_candidates(fs8: dict, growth: dict) -> dict:
    n_con = growth["n_constrained_shells"]
    return {
        "schema": "pr148.p0_remediation_candidates.v1",
        "candidates": [
            {"finding_id": "C1-K5-MV-F1", "status": "OPEN",
             "disposition": "remediation_candidate",
             "mechanics": "the depth-resolved growth rate is measured with a "
                          "MEASURED same-data joint covariance (not assumed "
                          f"diagonal); only {n_con} of "
                          f"{len(fs8['shells'])} shells constrain fsigma8, so "
                          "the growth DIFFERENCE across depth is NOT identified "
                          "and is reported as a bound consistent with zero — "
                          "there is no depth-dependence detection and no "
                          "historical tension figure",
             "closure": "impossible before the PR-157 adjudication"},
            {"finding_id": "C3-K5-VCORR-ML-F1", "status": "OPEN",
             "disposition": "remediation_candidate",
             "scope_note": "PR-148 implements the depth-resolved fsigma8 "
                           "amplitude estimator and its same-data joint "
                           "covariance directly; the broader velocity-"
                           "correlation ML remediation is scoped through the "
                           "same joint-covariance machinery",
             "mechanics": "the eigen-whitened QML amplitude estimator, the "
                          "same-data joint covariance and the growth-difference "
                          "bound are available; the full ML f sigma_8 "
                          "remediation is a scoped follow-up",
             "closure": "impossible before the PR-157 adjudication"},
        ],
        "note": "both CF4 P0s stay OPEN; PR-148 supplies growth-difference "
                "bound mechanics, not closure",
    }


def build_captions(fs8: dict, cov: dict, growth: dict) -> dict:
    text = generate_caption(fs8, cov, growth)
    lint_caption(text)
    return {"schema": "pr148.captions.v1", "captions": {"summary": text}}


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

    def mutant_target_tension_sigma() -> None:
        refuse_target_tension_sigma("target_tension_sigma")

    def mutant_correlation_endpoint_selection() -> None:
        refuse_correlation_endpoint_selection("correlation_zero")

    def mutant_shell_bias_single_point() -> None:
        refuse_shell_bias_single_point("single_weighted_point")

    def mutant_anomaly_claim() -> None:
        refuse_anomaly_claim("growth_anomaly")

    def mutant_cf4_p0_closure() -> None:
        refuse_cf4_p0_closure("cf4_p0_closed")

    def mutant_precision_from_unidentified_cov() -> None:
        require_positive_definite({"positive_definite": False})

    registered = {m["mutation_id"]: m["kill_rule"]
                  for m in spec["mutation_registry"]}
    executions = {
        "target_tension_sigma": mutant_target_tension_sigma,
        "correlation_endpoint_selection": mutant_correlation_endpoint_selection,
        "shell_bias_single_point": mutant_shell_bias_single_point,
        "anomaly_claim": mutant_anomaly_claim,
        "cf4_p0_closure": mutant_cf4_p0_closure,
        "precision_from_unidentified_cov": mutant_precision_from_unidentified_cov,
    }
    if set(registered) != set(executions):
        raise SystemExit("mutation registry does not match the executions")
    rows = []
    for mutation_id, fn in executions.items():
        killed, message = False, "MUTANT SURVIVED"
        try:
            fn()
        except GrowthCovarianceError as exc:
            killed = True
            message = _redact(str(exc), redact_patterns)[:220]
        rows.append({"mutation_id": mutation_id,
                     "kill_rule": registered[mutation_id],
                     "killed": killed, "kill_message_redacted": message})
    return {"schema": "pr148.mutation_report.v1", "mutations": rows,
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
    if spec.get("schema") != "htt.long_horizon.pr148_growth_covariance.v1":
        raise SystemExit("pr148 spec schema mismatch")
    _verify_baseline_commit(spec)
    _verify_remediation_state(spec)
    if not _groups(spec).is_file():
        raise SystemExit("CF4 groups npz absent — requires the read-only "
                         "external CF4 catalogue")
    problems: list[str] = []
    wrote: list[str] = []

    fs8, cov, growth, held, stab = build_reports(spec)
    p0 = build_p0_candidates(fs8, growth)
    captions = build_captions(fs8, cov, growth)
    fs8["negative_scan"] = {"targets": _scan_targets(spec, captions),
                            "total_hits": 0}
    mutations = run_mutations(spec)
    if mutations["surviving_mutation_count"]:
        print(json.dumps({"ok": False, "survivors": mutations["mutations"]}))
        return 2

    _emit(OUTPUTS["fsigma8"], fs8, write, problems, wrote)
    _emit(OUTPUTS["covariance"], cov, write, problems, wrote)
    _emit(OUTPUTS["growth"], growth, write, problems, wrote)
    _emit(OUTPUTS["held_out"], held, write, problems, wrote)
    _emit(OUTPUTS["stability"], stab, write, problems, wrote)
    _emit(OUTPUTS["p0"], p0, write, problems, wrote)
    _emit(OUTPUTS["captions"], captions, write, problems, wrote)
    _emit(OUTPUTS["mutations"], mutations, write, problems, wrote)

    manifest = {
        "schema": "pr148.artifact_manifest.v1",
        "owner": spec["owner"], "claim_tier": spec["claim_tier"],
        "claim_level": spec["claim_level"],
        "artifact_mode": spec["artifact_mode"],
        "allowed_use": spec["allowed_use"],
        "forbidden_use": list(spec["forbidden_output_language"]),
        "transfer_source": spec["transfer_source"],
        "config_hash": _sha(SPEC_PATH),
        "raw_data_pins": {"groups_sha256": _sha(_groups(spec))},
        "input_hashes": [f"{rel}:{_sha(REPO / rel)}" for rel in
                         ("htt/obsstat/cf4_growth_covariance.py",
                          "htt/obsstat/cf4_forward_simulator.py")],
        "caveats": [
            "Growth-difference bound mechanics at C3 only.",
            "Only the nearest shell constrains fsigma8; the growth difference "
            "across depth is NOT identified and is reported as a bound.",
            "The same-data joint covariance is MEASURED (near-diagonal, PSD), "
            "never assumed or set to a favourable correlation endpoint.",
            "No historical tension figure and no depth-dependence detection.",
            "The two CF4 P0s stay OPEN with remediation CANDIDATES; closure is "
            "impossible before the PR-157 adjudication.",
            "No global-tilt or anomaly claim; no detection.",
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
    module_text = (REPO / "htt/obsstat/cf4_growth_covariance.py") \
        .read_text(encoding="utf-8").lower()
    for phrase in spec["forbidden_output_language"]:
        if phrase.lower() in module_text:
            print(json.dumps({"ok": False,
                              "reason": "forbidden phrase in module"}))
            return 2
    print(json.dumps({
        "ok": True, "mode": "write" if write else "check", "wrote": wrote,
        "n_constrained_shells": growth["n_constrained_shells"],
        "growth_difference_identified": growth["growth_difference_identified"],
        "covariance_psd": cov["positive_definite"],
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
