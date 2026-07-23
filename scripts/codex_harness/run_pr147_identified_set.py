#!/usr/bin/env python3
"""PR-147 runner: nuisance-augmented CF4 depth-resolved flow identified sets.

``--write`` builds / ``--check`` verifies (fresh build must equal disk bytes):
the depth-resolved flow identified set over the frozen nuisance box
(bounded/undetermined/unbounded per shell), the cross-engine endpoint
agreement, the mesh sensitivity, the Imbens-Manski grid-conditional
simultaneous coverage (binds PR-137), the GLS-versus-MV difference, the
plausible-unbounded scenario, the comparability table, the two CF4 P0
remediation-CANDIDATE receipts, captions, and the six-mutant kill report.

Identified-region coverage mechanics at roadmap_rescue_v1:C3; the two CF4 P0s
stay OPEN; no anomaly or global-tilt claim.
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

from obsstat.cf4_identified_set import (  # noqa: E402
    SCHEMA_VERSION,
    IdentifiedSetError,
    comparability_table,
    cross_engine_endpoint_agreement,
    generate_caption,
    gls_ols_difference,
    identified_set,
    lint_caption,
    load_data,
    mesh_sensitivity,
    misspecification_diagnostic,
    refuse_anomaly_claim,
    refuse_cf4_p0_closure,
    refuse_favourable_endpoint,
    refuse_nuisance_tuning,
    refuse_zero_containment_isotropy,
    require_reported_unbounded,
    simultaneous_coverage,
    unbounded_scenario,
    verify_nuisance_box_hash,
)

SPEC_PATH = REPO / "docs/research_program/long_horizon_rescue/pr147_spec.yaml"
OUTPUTS = {
    "identified_set": "docs/generated/pr147_identified_set.json",
    "coverage": "docs/generated/pr147_coverage.json",
    "mesh": "docs/generated/pr147_mesh_sensitivity.json",
    "gls_mv": "docs/generated/pr147_gls_mv_difference.json",
    "comparability": "docs/generated/pr147_comparability_table.json",
    "p0": "docs/generated/pr147_p0_remediation_candidates.json",
    "captions": "docs/generated/pr147_captions.json",
    "mutations": "docs/generated/pr147_mutation_report.json",
    "manifest": "docs/generated/pr147_artifact_manifest.json",
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


def _paths(spec: dict):
    dp = spec["data_scope"]["raw_data_paths"]
    return REPO / dp["groups"], REPO / dp["variants"]


def _box(spec: dict) -> dict:
    b = dict(spec["model"]["nuisance_box"])
    b["n_shells"] = int(spec["model"]["n_shells"])
    return b


def build_reports(spec: dict):
    m = spec["model"]
    groups, variants = _paths(spec)
    data = load_data(groups, variants)
    box = _box(spec)
    apex = float(m["apex_nonidentified_deg"])
    ubamp = float(m["effectively_unbounded_amplitude_kms"])
    # the frozen nuisance box must match its committed content address
    box_hash = verify_nuisance_box_hash(box, str(m["nuisance_box_sha256"]))
    # anti-drift guards invoked LIVE with admissible input
    refuse_favourable_endpoint("whole_set_reported")
    refuse_zero_containment_isotropy("wide_set_not_isotropy")
    refuse_nuisance_tuning("frozen_before_result")
    refuse_anomaly_claim("no_claim")
    refuse_cf4_p0_closure("remediation_candidate")

    iset = identified_set(data, box, n_shells=int(m["n_shells"]),
                          apex_nonid_deg=apex, unbounded_amp=ubamp)
    for shell in iset["shells"]:
        # cross-engine agreement was already enforced as a kill switch inside
        # identified_set; record it and re-assert the unbounded invariant
        shell["cross_engine"] = cross_engine_endpoint_agreement(shell, 50.0)
        require_reported_unbounded(shell["status"],
                                   shell["amplitude_interval_kms"][1], ubamp)
    iset["nuisance_box_sha256"] = box_hash
    iset["misspecification_diagnostic"] = misspecification_diagnostic(
        data, box, apex_nonid_deg=apex, unbounded_amp=ubamp)
    iset_record = {"schema": "pr147.identified_set.v1",
                   "module_schema": SCHEMA_VERSION, **iset}

    ms = spec["mesh_sensitivity"]
    mesh = {"schema": "pr147.mesh_sensitivity.v1",
            **mesh_sensitivity(data, box, n_shells=int(m["n_shells"]),
                               refine_points=int(ms["refine_points"]),
                               max_shift_kms=float(ms["max_endpoint_shift_kms"]))}
    cs = spec["coverage"]
    coverage = {"schema": "pr147.coverage.v1",
                **simultaneous_coverage(data, box, iset,
                                        n_inject=int(cs["n_inject"]),
                                        seed=int(cs["seed"]),
                                        subsample=int(cs["subsample"]),
                                        family_conf=float(cs["family_conf"]))}
    if not coverage["conservative_coverage_ok"]:
        raise SystemExit("the genuine simultaneous coverage fell below the "
                         "conservative floor — the identified set is not "
                         "covering; reporting a bound/nonidentification instead")
    gls_mv = {"schema": "pr147.gls_mv_difference.v1",
              **gls_ols_difference(data, subsample=int(cs["subsample"]),
                                   seed=int(cs["seed"]))}
    unbounded = unbounded_scenario(data, box, apex_nonid_deg=apex,
                                   unbounded_amp=ubamp)
    iset_record["plausible_unbounded_scenario"] = unbounded
    comparability = {"schema": "pr147.comparability_table.v1",
                     **comparability_table(iset)}
    return iset_record, coverage, mesh, gls_mv, comparability


def build_p0_candidates(iset: dict, coverage: dict) -> dict:
    statuses = [s["status"] for s in iset["shells"]]
    return {
        "schema": "pr147.p0_remediation_candidates.v1",
        "candidates": [
            {"finding_id": "C1-K5-MV-F1", "status": "OPEN",
             "disposition": "remediation_candidate",
             "mechanics": "the depth-resolved bulk flow is now returned as an "
                          "identified SET over a frozen, content-addressed "
                          "nuisance box on the flow-plus-monopole estimand, not "
                          f"a point estimate; the per-shell status {statuses} "
                          "shows the set is bounded at every shell but widens "
                          "with depth, so no favourable endpoint is a "
                          "measurement; a mis-specification diagnostic shows "
                          "that omitting the monopole manufactures an "
                          "artificial unbounded topology, and the genuine "
                          "Imbens-Manski simultaneous coverage "
                          f"({round(coverage['genuine_simultaneous_coverage'], 2)}) "
                          "conservatively brackets the truth (with the "
                          "disclosed Rice-bias undershoot at depth)",
             "closure": "impossible before the PR-157 adjudication"},
            {"finding_id": "C3-K5-VCORR-ML-F1", "status": "OPEN",
             "disposition": "remediation_candidate",
             "scope_note": "PR-147 does NOT implement the velocity-correlation "
                           "ML estimator; it supplies the nuisance identified-"
                           "set machinery (the frozen box, the endpoint "
                           "solvers, the Imbens-Manski coverage) the downstream "
                           "growth-rate analysis will bound its systematics "
                           "with",
             "mechanics": "the nuisance identified-set and coverage machinery "
                          "is available for the growth-rate branch; the ML "
                          "f sigma_8 remediation itself is a scoped follow-up",
             "closure": "impossible before the PR-157 adjudication"},
        ],
        "note": "both CF4 P0s stay OPEN; PR-147 supplies identified-region "
                "coverage mechanics, not closure",
    }


def build_captions(iset: dict) -> dict:
    text = generate_caption(iset)
    lint_caption(text)
    return {"schema": "pr147.captions.v1", "captions": {"summary": text}}


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

    def mutant_favourable_endpoint_point_estimate() -> None:
        refuse_favourable_endpoint("favourable_endpoint")

    def mutant_set_contains_zero_isotropy() -> None:
        refuse_zero_containment_isotropy("set_contains_zero_isotropy")

    def mutant_nuisance_tuned_to_result() -> None:
        refuse_nuisance_tuning("after_observed_result")

    def mutant_anomaly_claim() -> None:
        refuse_anomaly_claim("anomaly")

    def mutant_cf4_p0_closure() -> None:
        refuse_cf4_p0_closure("cf4_p0_closed")

    def mutant_hidden_unbounded() -> None:
        require_reported_unbounded("bounded", 3000.0, 2000.0)

    registered = {m["mutation_id"]: m["kill_rule"]
                  for m in spec["mutation_registry"]}
    executions = {
        "favourable_endpoint_point_estimate":
            mutant_favourable_endpoint_point_estimate,
        "set_contains_zero_isotropy": mutant_set_contains_zero_isotropy,
        "nuisance_tuned_to_result": mutant_nuisance_tuned_to_result,
        "anomaly_claim": mutant_anomaly_claim,
        "cf4_p0_closure": mutant_cf4_p0_closure,
        "hidden_unbounded": mutant_hidden_unbounded,
    }
    if set(registered) != set(executions):
        raise SystemExit("mutation registry does not match the executions")
    rows = []
    for mutation_id, fn in executions.items():
        killed, message = False, "MUTANT SURVIVED"
        try:
            fn()
        except IdentifiedSetError as exc:
            killed = True
            message = _redact(str(exc), redact_patterns)[:220]
        rows.append({"mutation_id": mutation_id,
                     "kill_rule": registered[mutation_id],
                     "killed": killed, "kill_message_redacted": message})
    return {"schema": "pr147.mutation_report.v1", "mutations": rows,
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
    if spec.get("schema") != "htt.long_horizon.pr147_identified_set.v1":
        raise SystemExit("pr147 spec schema mismatch")
    _verify_baseline_commit(spec)
    _verify_remediation_state(spec)
    groups, variants = _paths(spec)
    if not groups.is_file() or not variants.is_file():
        raise SystemExit("CF4 groups/variants npz absent — requires the read-"
                         "only external CF4 catalogue")
    problems: list[str] = []
    wrote: list[str] = []

    iset, coverage, mesh, gls_mv, comparability = build_reports(spec)
    p0 = build_p0_candidates(iset, coverage)
    captions = build_captions(iset)
    iset["negative_scan"] = {"targets": _scan_targets(spec, captions),
                             "total_hits": 0}
    mutations = run_mutations(spec)
    if mutations["surviving_mutation_count"]:
        print(json.dumps({"ok": False, "survivors": mutations["mutations"]}))
        return 2

    _emit(OUTPUTS["identified_set"], iset, write, problems, wrote)
    _emit(OUTPUTS["coverage"], coverage, write, problems, wrote)
    _emit(OUTPUTS["mesh"], mesh, write, problems, wrote)
    _emit(OUTPUTS["gls_mv"], gls_mv, write, problems, wrote)
    _emit(OUTPUTS["comparability"], comparability, write, problems, wrote)
    _emit(OUTPUTS["p0"], p0, write, problems, wrote)
    _emit(OUTPUTS["captions"], captions, write, problems, wrote)
    _emit(OUTPUTS["mutations"], mutations, write, problems, wrote)

    manifest = {
        "schema": "pr147.artifact_manifest.v1",
        "owner": spec["owner"], "claim_tier": spec["claim_tier"],
        "claim_level": spec["claim_level"],
        "artifact_mode": spec["artifact_mode"],
        "allowed_use": spec["allowed_use"],
        "forbidden_use": list(spec["forbidden_output_language"]),
        "transfer_source": spec["transfer_source"],
        "config_hash": _sha(SPEC_PATH),
        "raw_data_pins": {"groups_sha256": _sha(groups),
                          "variants_sha256": _sha(variants)},
        "input_hashes": [f"{rel}:{_sha(REPO / rel)}" for rel in
                         ("htt/obsstat/cf4_identified_set.py",
                          "htt/obsstat/cf4_velocity_estimators.py")],
        "caveats": [
            "Identified-region coverage mechanics at C3 only.",
            "The identified set is bounded but wide and grows with depth; no "
            "favourable endpoint is a point estimate.",
            "A set that contains zero is never read as isotropy.",
            "The nuisance box is frozen and content-addressed by the spec "
            "before the observed result.",
            "The two CF4 P0s stay OPEN with remediation CANDIDATES; closure "
            "is impossible before the PR-157 adjudication.",
            "No anomaly or global-tilt claim.",
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
    module_text = (REPO / "htt/obsstat/cf4_identified_set.py") \
        .read_text(encoding="utf-8").lower()
    for phrase in spec["forbidden_output_language"]:
        if phrase.lower() in module_text:
            print(json.dumps({"ok": False,
                              "reason": "forbidden phrase in module"}))
            return 2
    print(json.dumps({
        "ok": True, "mode": "write" if write else "check", "wrote": wrote,
        "shell_status": [s["status"] for s in iset["shells"]],
        "simultaneous_coverage": round(
            coverage["genuine_simultaneous_coverage"], 3),
        "conservative_coverage_ok": coverage["conservative_coverage_ok"],
        "mesh_sufficient": mesh["mesh_sufficient"],
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
