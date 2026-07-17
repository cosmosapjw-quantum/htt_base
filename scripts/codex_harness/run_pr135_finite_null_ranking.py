#!/usr/bin/env python3
"""PR-135 runner: exchangeable observation-inclusive finite-null
global ranking.

``--write`` builds / ``--check`` verifies (fresh build must equal disk
bytes): the exact-discrete rank estimator record, the exact small-N
enumeration (uniform-on-grid super-uniformity), the seeded type-I
simulation (super-uniform at every alpha), the dependence-preserving
max-scan record, generated captions, and the mutation report (six
preregistered mutants killed on production validator paths).

Matched-null-conditioned global calibration mechanics at
roadmap_rescue_v1:C2; no detection; no disposition change.
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

from common.finite_null_ranking import (  # noqa: E402
    SCHEMA_VERSION,
    CalibrationSplit,
    FiniteNullError,
    broken_flattened_scan_scores,
    calibration_fingerprint,
    exact_rank_distribution,
    gaussian_sigma_from_p,
    generate_caption,
    lint_caption,
    naive_zero_permitting_p,
    pooled_rank_p,
    require_identical_scoring,
    require_rowwise_reduction,
    resolution_floor,
    scan_pooled_rank_p,
    split_evaluated_rank_p,
    support_grid,
    type_i_simulation,
    validate_reported_p,
)

SPEC_PATH = REPO / "docs/research_program/long_horizon_rescue/pr135_spec.yaml"
OUTPUTS = {
    "estimator": "docs/generated/pr135_rank_estimator.json",
    "enumeration": "docs/generated/pr135_exact_enumeration.json",
    "simulation": "docs/generated/pr135_type_i_simulation.json",
    "scan": "docs/generated/pr135_max_scan.json",
    "captions": "docs/generated/pr135_captions.json",
    "mutations": "docs/generated/pr135_mutation_report.json",
    "manifest": "docs/generated/pr135_artifact_manifest.json",
}
REDACTED = "[REDACTED-PATTERN]"


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _render(payload: dict) -> bytes:
    return (json.dumps(payload, indent=2, ensure_ascii=False, sort_keys=True)
            + "\n").encode()


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


def _verify_prohibition_cross_list(spec: dict) -> int:
    covered = 0
    for pattern in spec["negative_scan"]["forbidden_patterns"]:
        try:
            lint_caption(f"benign text then {pattern} then more text")
        except FiniteNullError:
            covered += 1
            continue
        raise SystemExit(
            "prohibition cross-list gap: a spec forbidden pattern is not "
            "covered by the module caption lint")
    return covered


def build_estimator(spec: dict) -> dict:
    ranking = spec["ranking"]
    # canonical worked examples on a small N
    n = 4
    examples = [
        {"obs": 5.0, "nulls": [1.0, 2.0, 3.0, 4.0],
         "p": str(pooled_rank_p(5.0, [1.0, 2.0, 3.0, 4.0]))},
        {"obs": 2.5, "nulls": [1.0, 2.0, 3.0, 4.0],
         "p": str(pooled_rank_p(2.5, [1.0, 2.0, 3.0, 4.0]))},
        {"obs": 0.0, "nulls": [1.0, 2.0, 3.0, 4.0],
         "p": str(pooled_rank_p(0.0, [1.0, 2.0, 3.0, 4.0]))},
    ]
    # fully-tied column -> p = 1
    tied = str(pooled_rank_p(1.0, [1.0, 1.0, 1.0]))
    return {
        "schema": "pr135.rank_estimator.v1",
        "module_schema": SCHEMA_VERSION,
        "estimator": ranking["estimator"],
        "tie_policy": ranking["tie_policy"],
        "support_example_n4": [str(v) for v in support_grid(n)],
        "resolution_floor_n4": str(resolution_floor(n)),
        "worked_examples": examples,
        "fully_tied_column_p": tied,
        "min_p_is_nonzero": True,
    }


def build_enumeration(spec: dict) -> dict:
    rows = {}
    all_ok = True
    for n in spec["verification"]["exact_enumeration"]["N_values"]:
        enum = exact_rank_distribution(int(n))
        rows[str(n)] = enum
        all_ok = all_ok and enum["all_super_uniform"]
    return {
        "schema": "pr135.exact_enumeration.v1",
        "distributions": rows,
        "all_super_uniform": all_ok,
    }


def build_simulation(spec: dict) -> dict:
    cfg = spec["verification"]["type_i_simulation"]
    alpha_grid = [Fraction(a) for a in cfg["alpha_grid"]]
    result = type_i_simulation(int(cfg["N"]), int(cfg["trials"]),
                               int(cfg["seed"]), alpha_grid)
    return {"schema": "pr135.type_i_simulation.v1",
            "bit_generator": cfg["bit_generator"], **result}


def build_scan(spec: dict) -> dict:
    # a matched dependence-preserving scan: each row is a 5-point
    # correlated scan; the score is the within-row maximum.
    obs_row = [0.4, 1.1, 0.9, 0.7, 0.5]
    null_rows = [
        [0.3, 0.5, 0.4, 0.6, 0.2],
        [1.4, 1.2, 0.9, 1.1, 0.8],
        [0.1, 0.2, 0.15, 0.3, 0.25],
        [0.9, 1.0, 1.05, 0.95, 0.6],
    ]
    require_identical_scoring("max_scan", "max_scan")
    # the full-pool pooled rank (all 4 nulls)
    full = scan_pooled_rank_p(obs_row, null_rows)
    validate_reported_p(full["p"], full["n_null"])
    # the SPLIT-evaluated p: calibration rows held out, p computed over
    # the disjoint evaluation rows only (the split is load-bearing).
    split = CalibrationSplit(calibration_ids=(0, 1),
                            evaluation_ids=(2, 3))
    split_result = split_evaluated_rank_p(obs_row, null_rows, split)
    validate_reported_p(split_result["p"], split_result["n_null"])
    fp = calibration_fingerprint(
        statistic_family="max_of_scan", scan_range="0..4",
        mask="full", tie_policy="conservative_ge",
        n_null=len(null_rows))
    return {
        "schema": "pr135.max_scan.v1",
        "obs_score": full["obs_score"],
        "null_scores": full["null_scores"],
        "scan_length": full["scan_length"],
        "n_null": full["n_null"],
        "full_pool_p": str(full["p"]),
        "scored_identically": full["scored_identically"],
        "reduction": full["reduction"],
        "calibration_fingerprint": fp,
        "split_evaluated": {
            "calibration_ids": list(split.calibration_ids),
            "evaluation_ids": list(split.evaluation_ids),
            "disjoint": True,
            "evaluation_n_null": split_result["evaluation_n_null"],
            "p_over_evaluation_rows_only": str(split_result["p"]),
            "resolution_floor": str(split_result["resolution_floor"]),
        },
        "dependence_preserved": "each null row is reduced by the same "
                                "within-row max as the observation, "
                                "producing one score per row (not a "
                                "flattened iid pool of scan points)",
    }


def build_captions(spec: dict) -> dict:
    n = int(spec["verification"]["type_i_simulation"]["N"])
    text = generate_caption(n)
    lint_caption(text)
    return {"schema": "pr135.captions.v1", "captions": {"summary": text}}


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
                    hits.append({"line": idx,
                                 "pattern_index": pattern_index})
        targets[rel] = {"hits": hits, "source": source, "sha256": digest}
    total = sum(len(t["hits"]) for t in targets.values())
    if total:
        raise SystemExit(f"negative scan found {total} forbidden-"
                         f"language hits: {targets}")
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


def run_mutations(spec: dict) -> dict:
    redact_patterns = (
        [str(p) for p in spec["negative_scan"]["forbidden_patterns"]]
        + [str(p) for p in spec["forbidden_output_language"]])

    def mutant_zero_p_value() -> None:
        # the anti-conservative b/N estimator returns 0 when no null
        # exceeds the observation; route its result through the SAME
        # production floor gate (validate_reported_p) every reported p
        # passes -> rejected.
        bad_p = naive_zero_permitting_p(5.0, [1.0, 2.0, 3.0, 4.0])
        validate_reported_p(bad_p, 4)

    def mutant_local_observation_only_rank() -> None:
        require_identical_scoring("max_scan", "sum_over_scan")

    def mutant_subresolution_sigma() -> None:
        gaussian_sigma_from_p(Fraction(1, 40), 39)

    def mutant_non_conservative_tie() -> None:
        pooled_rank_p(1.0, [1.0, 2.0], tie_policy="strict_gt")

    def mutant_dependence_broken_scan() -> None:
        # flatten every scan point of every row into one iid pool
        # (N*scan_len scores) -> the row-wise reduction guard rejects it.
        null_rows = [[1.0, 2.0, 3.0], [0.5, 0.6, 0.7]]
        flattened = broken_flattened_scan_scores(null_rows)
        require_rowwise_reduction(flattened, len(null_rows))

    def mutant_calibration_evaluation_overlap() -> None:
        CalibrationSplit(calibration_ids=(0, 1, 2),
                        evaluation_ids=(2, 3, 4))

    registered = {m["mutation_id"]: m["kill_rule"]
                  for m in spec["mutation_registry"]}
    executions = {
        "zero_p_value": mutant_zero_p_value,
        "local_observation_only_rank": mutant_local_observation_only_rank,
        "subresolution_sigma": mutant_subresolution_sigma,
        "non_conservative_tie": mutant_non_conservative_tie,
        "dependence_broken_scan": mutant_dependence_broken_scan,
        "calibration_evaluation_overlap":
            mutant_calibration_evaluation_overlap,
    }
    if set(registered) != set(executions):
        raise SystemExit("mutation registry does not match the executions")
    rows = []
    for mutation_id, fn in executions.items():
        killed = False
        message = "MUTANT SURVIVED"
        try:
            fn()
        except FiniteNullError as exc:
            killed = True
            message = _redact(str(exc), redact_patterns)[:220]
        rows.append({
            "mutation_id": mutation_id,
            "kill_rule": registered[mutation_id],
            "killed": killed,
            "kill_message_redacted": message,
        })
    return {
        "schema": "pr135.mutation_report.v1",
        "mutations": rows,
        "surviving_mutation_count": len(
            [m for m in rows if not m["killed"]]),
    }


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
    if spec.get("schema") != "htt.long_horizon.pr135_finite_null_ranking.v1":
        raise SystemExit("pr135 spec schema mismatch")
    _verify_baseline_commit(spec)
    _verify_remediation_state(spec)
    cross_covered = _verify_prohibition_cross_list(spec)
    problems: list[str] = []
    wrote: list[str] = []

    estimator = build_estimator(spec)
    estimator["prohibition_cross_list_covered"] = cross_covered
    enumeration = build_enumeration(spec)
    simulation = build_simulation(spec)
    scan = build_scan(spec)
    captions = build_captions(spec)
    estimator["negative_scan"] = {
        "targets": _scan_targets(spec, captions), "total_hits": 0}
    mutations = run_mutations(spec)
    if mutations["surviving_mutation_count"]:
        print(json.dumps({"ok": False, "survivors": mutations["mutations"]}))
        return 2

    _emit(OUTPUTS["estimator"], estimator, write, problems, wrote)
    _emit(OUTPUTS["enumeration"], enumeration, write, problems, wrote)
    _emit(OUTPUTS["simulation"], simulation, write, problems, wrote)
    _emit(OUTPUTS["scan"], scan, write, problems, wrote)
    _emit(OUTPUTS["captions"], captions, write, problems, wrote)
    _emit(OUTPUTS["mutations"], mutations, write, problems, wrote)

    manifest = {
        "schema": "pr135.artifact_manifest.v1",
        "owner": spec["owner"],
        "claim_tier": spec["claim_tier"],
        "claim_level": spec["claim_level"],
        "artifact_mode": spec["artifact_mode"],
        "allowed_use": spec["allowed_use"],
        "forbidden_use": list(spec["forbidden_output_language"]),
        "transfer_source": spec["transfer_source"],
        "config_hash": _sha(SPEC_PATH),
        "input_hashes": [
            f"{rel}:{_sha(REPO / rel)}"
            for rel in ("htt/src/common/finite_null_ranking.py",)
        ],
        "caveats": [
            "Matched-null-conditioned global calibration mechanics at "
            "C2 only.",
            "The p-value is exact-discrete on {1/(N+1), ..., 1} — never "
            "0, never below the finite resolution.",
            "The max scan preserves within-row dependence; no iid "
            "per-scan-point draw.",
            "No detection; no significance finer than the resolution.",
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
    # also sweep the module source against the FULL forbidden list (the
    # phrases are assembled from fragments so no literal appears there).
    module_text = (REPO / "htt/src/common/finite_null_ranking.py").read_text(
        encoding="utf-8").lower()
    for phrase in spec["forbidden_output_language"]:
        if phrase.lower() in module_text:
            print(json.dumps({"ok": False,
                              "reason": "forbidden phrase in module source"}))
            return 2
    print(json.dumps({
        "ok": True, "mode": "write" if write else "check", "wrote": wrote,
        "enumeration_super_uniform": enumeration["all_super_uniform"],
        "type_i_super_uniform": simulation["super_uniform"],
        "scan_full_pool_p": scan["full_pool_p"],
        "negative_control_caught": simulation["negative_control"][
            "caught_by_floor_gate"],
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
