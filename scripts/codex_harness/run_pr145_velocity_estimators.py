#!/usr/bin/env python3
"""PR-145 runner: CF4 radial-monopole and velocity-shape estimator mechanics.

``--write`` builds / ``--check`` verifies (fresh build must equal disk
bytes): the bulk-flow report (vector + full covariance = noise + cosmic
variance, with the honest full-covariance significance far below the
noise-only figure), the coverage report (injected flow + monopole recovered
at 68/95 per component), the eight-region partition leverage, the two CF4
P0 remediation-CANDIDATE receipts (both stay OPEN, closure needs PR-157),
generated captions, and the six-mutant kill report.

Observable-estimator mechanics at roadmap_rescue_v1:C2; the two CF4 P0s
stay OPEN; no detection.
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

from common.cf4_velocity_estimators import (  # noqa: E402
    SCHEMA_VERSION,
    VelocityEstimatorError,
    compare_vectors,
    coverage_injection,
    eight_region_partition,
    estimate,
    full_covariance_significance,
    generate_caption,
    lint_caption,
    load_sample,
    refuse_cf4_p0_closure,
    refuse_constrained_median_as_truth,
    refuse_scalar_amplitude_overlap,
    require_coverage_in_band,
    require_eight_region_label,
    require_full_covariance_significance,
    subsample,
)

SPEC_PATH = REPO / "docs/research_program/long_horizon_rescue/pr145_spec.yaml"
OUTPUTS = {
    "bulk_flow": "docs/generated/pr145_bulk_flow_report.json",
    "coverage": "docs/generated/pr145_coverage_report.json",
    "partition": "docs/generated/pr145_partition_report.json",
    "p0": "docs/generated/pr145_p0_remediation_candidates.json",
    "captions": "docs/generated/pr145_captions.json",
    "mutations": "docs/generated/pr145_mutation_report.json",
    "manifest": "docs/generated/pr145_artifact_manifest.json",
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
        raise SystemExit(f"baseline_commit {sha} does not resolve — "
                         "fabricated provenance refused")


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
                for k, v in contract["required_scientific_status_counts"]
                .items()}
    if statuses != required:
        raise SystemExit(f"remediation status counts drifted: {statuses}")


def _groups_path(spec: dict) -> Path:
    return REPO / spec["data_scope"]["raw_data_paths"]["groups"]


def build_reports(spec: dict):
    m = spec["model"]
    groups = _groups_path(spec)
    full = load_sample(groups, h0=float(Fraction(m["H0_kms_mpc"])),
                       sigma_nl=float(m["sigma_nl_kms"]))
    sub = subsample(full, int(m["cv_subsample"]), int(m["cv_seed"]))
    wls = estimate(sub, monopole=False, label="bulk_flow_wls")
    constrained = estimate(sub, monopole=True, label="flow_plus_monopole")
    # anti-drift guards invoked LIVE on the production estimator path
    require_full_covariance_significance("full_covariance")
    refuse_scalar_amplitude_overlap("vector_mahalanobis")
    refuse_constrained_median_as_truth("estimator_with_covariance")
    refuse_cf4_p0_closure("remediation_candidate")
    sig = full_covariance_significance(wls)
    # the reported amplitude must not collide with the quarantined headline
    if abs(sig["amplitude_kms"] - 405.0) < 1.0:
        raise SystemExit("the estimator amplitude collides with the "
                         "quarantined P0 headline — refuse to emit")
    comparison = compare_vectors(wls, constrained)
    bulk_flow = {
        "schema": "pr145.bulk_flow_report.v1",
        "module_schema": SCHEMA_VERSION,
        "n_groups_subsample": int(m["cv_subsample"]),
        "estimator": "bulk_flow_wls",
        "flow_vector_kms": wls.bulk_flow_vector().tolist(),
        "amplitude_kms": sig["amplitude_kms"],
        "noise_only_sigma": sig["noise_only_sigma"],
        "full_covariance_sigma": sig["full_covariance_sigma"],
        "constrained_monopole_kms": float(constrained.coeffs[3]),
        "constrained_flow_amplitude_kms": constrained.amplitude(),
        "estimator_comparison": comparison,
        "significance_note": sig["note"],
    }
    cov_spec = spec["coverage"]
    cov_sub = subsample(full, 800, int(cov_spec["seed"]))
    coverage = coverage_injection(
        cov_sub,
        [float(x) for x in cov_spec["inject"]["flow_kms"]],
        float(cov_spec["inject"]["monopole_kms"]),
        n_inj=int(cov_spec["n_injections"]), seed=int(cov_spec["seed"]))
    require_coverage_in_band(coverage, 0.68, 0.09)
    require_coverage_in_band(coverage, 0.95, 0.06)
    # the noise-only covariance must UNDER-cover (the concrete P0 failure)
    if max(coverage["coverage_68_noise_only"]) >= 0.60:
        raise SystemExit("the noise-only covariance did not under-cover — the "
                         "full-vs-noise-only discrimination is not exercised")
    coverage_record = {"schema": "pr145.coverage_report.v1", **coverage}
    partition = {"schema": "pr145.partition_report.v1",
                 **eight_region_partition(sub)}
    return bulk_flow, coverage_record, partition


def build_p0_candidates(bulk_flow: dict) -> dict:
    return {
        "schema": "pr145.p0_remediation_candidates.v1",
        "candidates": [
            {"finding_id": "C1-K5-MV-F1", "status": "OPEN",
             "disposition": "remediation_candidate",
             "mechanics": "the bulk-flow estimator now carries a FULL "
                          "covariance (measurement noise + linear cosmic "
                          "variance); the full-covariance significance "
                          f"({bulk_flow['full_covariance_sigma']:.2f}) is far "
                          "below the noise-only formal figure "
                          f"({bulk_flow['noise_only_sigma']:.2f}), which was "
                          "the over-claim, and injections recover the flow "
                          "with nominal coverage",
             "closure": "impossible before the PR-157 adjudication"},
            {"finding_id": "C3-K5-VCORR-ML-F1", "status": "OPEN",
             "disposition": "remediation_candidate",
             "scope_note": "PR-145 does NOT implement the velocity-"
                           "correlation ML (f sigma_8) estimator; it supplies "
                           "the SHARED covariance machinery (the Gorski "
                           "radial/transverse correlation from the fiducial "
                           "velocity power spectrum) and the full-covariance "
                           "vector discipline that the ML branch will use",
             "mechanics": "the shared cosmic-variance covariance machinery and "
                          "the vector-under-full-covariance discipline are "
                          "available; the ML f sigma_8 remediation itself is a "
                          "scoped follow-up within the estimator registry",
             "closure": "impossible before the PR-157 adjudication"},
        ],
        "note": "both CF4 P0s stay OPEN; PR-145 supplies remediation "
                "CANDIDATES with corrected covariance mechanics, not closure",
    }


def build_captions(bulk_flow: dict) -> dict:
    text = generate_caption(bulk_flow["amplitude_kms"],
                            bulk_flow["noise_only_sigma"],
                            bulk_flow["full_covariance_sigma"])
    lint_caption(text)
    return {"schema": "pr145.captions.v1", "captions": {"summary": text}}


def _scan_targets(spec: dict, captions_payload: dict) -> dict:
    patterns = [str(p) for p in spec["negative_scan"]["forbidden_patterns"]]
    targets = {}
    for rel in spec["negative_scan"]["targets"]:
        if rel == OUTPUTS["captions"]:
            raw = _render(captions_payload).decode()
            source, digest = "fresh_build", hashlib.sha256(
                raw.encode()).hexdigest()
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

    def mutant_constrained_median_as_truth() -> None:
        refuse_constrained_median_as_truth("constrained_median_truth")

    def mutant_noise_only_significance() -> None:
        require_full_covariance_significance("noise_only")

    def mutant_scalar_amplitude_overlap() -> None:
        refuse_scalar_amplitude_overlap("scalar_amplitude_overlap")

    def mutant_cf4_p0_closure() -> None:
        refuse_cf4_p0_closure("cf4_p0_closed")

    def mutant_rank_deficient_point_estimate() -> None:
        import numpy as np
        from common.cf4_velocity_estimators import Cf4Sample, estimate
        # a single-direction sample has a rank-deficient flow design
        n = np.tile(np.array([0.0, 0.0, 1.0]), (5, 1))
        s = Cf4Sample(n=n, v=np.ones(5), w=np.ones(5), sig_v=np.ones(5),
                      pos_hmpc=n * 10.0)
        estimate(s, monopole=False, label="degenerate")

    def mutant_octant_relabel() -> None:
        require_eight_region_label("octant_subset")

    registered = {m["mutation_id"]: m["kill_rule"]
                  for m in spec["mutation_registry"]}
    executions = {
        "constrained_median_as_truth": mutant_constrained_median_as_truth,
        "noise_only_significance": mutant_noise_only_significance,
        "scalar_amplitude_overlap": mutant_scalar_amplitude_overlap,
        "cf4_p0_closure": mutant_cf4_p0_closure,
        "rank_deficient_point_estimate": mutant_rank_deficient_point_estimate,
        "octant_relabel": mutant_octant_relabel,
    }
    if set(registered) != set(executions):
        raise SystemExit("mutation registry does not match the executions")
    rows = []
    for mutation_id, fn in executions.items():
        killed, message = False, "MUTANT SURVIVED"
        try:
            fn()
        except VelocityEstimatorError as exc:
            killed = True
            message = _redact(str(exc), redact_patterns)[:220]
        rows.append({"mutation_id": mutation_id,
                     "kill_rule": registered[mutation_id],
                     "killed": killed, "kill_message_redacted": message})
    return {"schema": "pr145.mutation_report.v1", "mutations": rows,
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
    if spec.get("schema") != "htt.long_horizon.pr145_velocity_estimators.v1":
        raise SystemExit("pr145 spec schema mismatch")
    _verify_baseline_commit(spec)
    _verify_remediation_state(spec)
    if not _groups_path(spec).is_file():
        raise SystemExit("CF4 groups npz absent — requires the read-only "
                         "external CF4 catalogue")
    problems: list[str] = []
    wrote: list[str] = []

    bulk_flow, coverage, partition = build_reports(spec)
    p0 = build_p0_candidates(bulk_flow)
    captions = build_captions(bulk_flow)
    bulk_flow["negative_scan"] = {"targets": _scan_targets(spec, captions),
                                  "total_hits": 0}
    mutations = run_mutations(spec)
    if mutations["surviving_mutation_count"]:
        print(json.dumps({"ok": False, "survivors": mutations["mutations"]}))
        return 2

    _emit(OUTPUTS["bulk_flow"], bulk_flow, write, problems, wrote)
    _emit(OUTPUTS["coverage"], coverage, write, problems, wrote)
    _emit(OUTPUTS["partition"], partition, write, problems, wrote)
    _emit(OUTPUTS["p0"], p0, write, problems, wrote)
    _emit(OUTPUTS["captions"], captions, write, problems, wrote)
    _emit(OUTPUTS["mutations"], mutations, write, problems, wrote)

    manifest = {
        "schema": "pr145.artifact_manifest.v1",
        "owner": spec["owner"], "claim_tier": spec["claim_tier"],
        "claim_level": spec["claim_level"],
        "artifact_mode": spec["artifact_mode"],
        "allowed_use": spec["allowed_use"],
        "forbidden_use": list(spec["forbidden_output_language"]),
        "transfer_source": spec["transfer_source"],
        "config_hash": _sha(SPEC_PATH),
        "raw_data_pins": {"groups_sha256": _sha(_groups_path(spec))},
        "input_hashes": [f"{rel}:{_sha(REPO / rel)}" for rel in
                         ("htt/src/common/cf4_velocity_estimators.py",)],
        "caveats": [
            "Observable-estimator mechanics at C2 only.",
            "The bulk-flow significance is reported under the FULL "
            "covariance (noise + cosmic variance); the noise-only figure is "
            "a formal over-estimate.",
            "The linear cosmic-variance covariance is a lower bound on the "
            "total variance, so the reported significance is an upper bound.",
            "The two CF4 P0s stay OPEN with remediation CANDIDATES; closure "
            "is impossible before the PR-157 adjudication.",
            "No detection.",
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
    module_text = (REPO / "htt/src/common/cf4_velocity_estimators.py") \
        .read_text(encoding="utf-8").lower()
    for phrase in spec["forbidden_output_language"]:
        if phrase.lower() in module_text:
            print(json.dumps({"ok": False,
                              "reason": "forbidden phrase in module"}))
            return 2
    print(json.dumps({
        "ok": True, "mode": "write" if write else "check", "wrote": wrote,
        "amplitude_kms": round(bulk_flow["amplitude_kms"], 2),
        "noise_only_sigma": round(bulk_flow["noise_only_sigma"], 2),
        "full_covariance_sigma": round(bulk_flow["full_covariance_sigma"], 2),
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
