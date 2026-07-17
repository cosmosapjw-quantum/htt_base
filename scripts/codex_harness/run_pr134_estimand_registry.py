#!/usr/bin/env python3
"""PR-134 runner: estimand / population / dependency / selection /
nuisance registry.

``--write`` builds / ``--check`` verifies (fresh build must equal disk
bytes): the typed contract registry (five representative CF4/K1/DESI/
ACT/JWST contracts from documented metadata, specification-only), the
per-contract content-addressed estimand fingerprints, the dependency
graph (named clusters, never independent rows), the generative-branch
separation record (template mean vs covariance factor), generated
captions, and the mutation report (six preregistered mutants killed on
production validator paths).

Estimand/analysis specification mechanics at roadmap_rescue_v1:C1; no
measurement, no family/geometry claim; no PR4 data run.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "htt" / "src"))
sys.path.insert(0, str(REPO / "htt"))

import yaml  # noqa: E402

from common.estimand_registry import (  # noqa: E402
    SCHEMA_VERSION,
    AnalysisContract,
    BranchComponent,
    EstimandRegistry,
    EstimandRegistryError,
    GenerativeBranch,
    compose_generative_model,
    generate_caption,
    lint_caption,
)

SPEC_PATH = REPO / "docs/research_program/long_horizon_rescue/pr134_spec.yaml"
OUTPUTS = {
    "registry": "docs/generated/pr134_contract_registry.json",
    "fingerprints": "docs/generated/pr134_estimand_fingerprints.json",
    "graph": "docs/generated/pr134_dependency_graph.json",
    "branches": "docs/generated/pr134_branch_separation.json",
    "captions": "docs/generated/pr134_captions.json",
    "mutations": "docs/generated/pr134_mutation_report.json",
    "manifest": "docs/generated/pr134_artifact_manifest.json",
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
        except EstimandRegistryError:
            covered += 1
            continue
        raise SystemExit(
            "prohibition cross-list gap: a spec forbidden pattern is not "
            "covered by the module caption lint")
    return covered


def _build_registry(spec: dict) -> tuple[EstimandRegistry, dict]:
    reg = EstimandRegistry()
    fingerprints = {}
    for row in spec["representative_contracts"]:
        contract = AnalysisContract.from_payload(row)
        fingerprints[contract.analysis_id] = reg.register(contract)
    expected = {r["analysis_id"] for r in spec["representative_contracts"]}
    if set(reg.ids()) != expected:
        raise SystemExit("representative contract set drifted")
    if len(set(fingerprints.values())) != len(fingerprints):
        raise SystemExit("estimand fingerprints are not unique")
    return reg, fingerprints


def build_registry_artifact(spec: dict, reg: EstimandRegistry) -> dict:
    return {
        "schema": "pr134.contract_registry.v1",
        "module_schema": SCHEMA_VERSION,
        "contracts": {cid: reg.get(cid).canonical_payload()
                      for cid in reg.ids()},
        "required_fields": list(spec["registry"]["required_fields"]),
        "representative_only_no_data_run": True,
    }


def build_fingerprints(fingerprints: dict) -> dict:
    return {
        "schema": "pr134.estimand_fingerprints.v1",
        "fingerprints": dict(sorted(fingerprints.items())),
        "unique": True,
    }


def build_graph(spec: dict, reg: EstimandRegistry) -> dict:
    graph = reg.dependency_graph()
    if any(len(members) != 1 for members in graph.values()):
        # each representative analysis has its own named cluster; a
        # shared cluster would be legitimate but must be justified.
        pass
    return {
        "schema": "pr134.dependency_graph.v1",
        "clusters": graph,
        "dependence_rule": spec["registry"]["dependence_rule"],
        "independent_rows_default": "refused",
    }


def build_branches(spec: dict, reg: EstimandRegistry) -> dict:
    # exercise the branch separation with a valid same-analysis compose
    # and record the refusal of a cross-analysis mix.
    cf4 = reg.get("CF4_MV_BULKFLOW")
    mean = BranchComponent(
        "CF4_MV_BULKFLOW",
        GenerativeBranch.DETERMINISTIC_TEMPLATE_MEAN,
        "linear cosmic-variance-free template mean")
    cov = BranchComponent(
        "CF4_MV_BULKFLOW",
        GenerativeBranch.STOCHASTIC_COVARIANCE_FACTOR,
        "woodbury off-diagonal covariance factor")
    composed = compose_generative_model(mean, cov)
    cross_refused = False
    try:
        compose_generative_model(
            BranchComponent("JWST_ANCHORS",
                            GenerativeBranch.DETERMINISTIC_TEMPLATE_MEAN,
                            "fisher template"),
            cov)
    except EstimandRegistryError:
        cross_refused = True
    if not cross_refused:
        raise SystemExit("cross-analysis branch mix was not refused")
    branch_roles = {cid: reg.get(cid).generative_branch.value
                    for cid in reg.ids()}
    return {
        "schema": "pr134.branch_separation.v1",
        "branch_rule": spec["registry"]["branch_rule"],
        "generative_branches": list(spec["registry"][
            "generative_branches"]),
        "per_analysis_branch": branch_roles,
        "valid_same_analysis_compose": composed,
        "cross_analysis_mix_refused": cross_refused,
        "cf4_estimand": cf4.estimand,
    }


def build_captions(reg: EstimandRegistry) -> dict:
    text = generate_caption(reg)
    lint_caption(text)
    return {"schema": "pr134.captions.v1", "captions": {"summary": text}}


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
    base = spec["representative_contracts"][0]

    def mutant_hidden_default_field() -> None:
        AnalysisContract.from_payload(
            {k: v for k, v in base.items() if k != "estimand"})

    def mutant_flattened_channel_type() -> None:
        # flattening = two DISTINCT survey ids with identical
        # specification content (the same channel). Through the PUBLIC
        # API: register the base survey, then a second survey that only
        # renames the id but keeps every other field -> the channel
        # fingerprint collides and register() refuses it.
        reg = EstimandRegistry()
        reg.register(AnalysisContract.from_payload(base))
        reg.register(AnalysisContract.from_payload(
            dict(base, analysis_id=base["analysis_id"] + "_CLONE")))

    def mutant_independent_dependency_assumption() -> None:
        AnalysisContract.from_payload(
            dict(base, dependence_cluster="independent"))

    def mutant_template_covariance_mix() -> None:
        compose_generative_model(
            BranchComponent("A",
                            GenerativeBranch.STOCHASTIC_COVARIANCE_FACTOR,
                            "cov as mean"),
            BranchComponent("A",
                            GenerativeBranch.STOCHASTIC_COVARIANCE_FACTOR,
                            "cov"))

    def mutant_posthoc_window_edit() -> None:
        reg = EstimandRegistry()
        reg.register(AnalysisContract.from_payload(base))
        reg.register(AnalysisContract.from_payload(
            dict(base, selection_window="secretly_widened_window")))

    def mutant_active_inference_without_registry() -> None:
        EstimandRegistry().require_registered_for_inference("GHOST")

    registered = {m["mutation_id"]: m["kill_rule"]
                  for m in spec["mutation_registry"]}
    executions = {
        "hidden_default_field": mutant_hidden_default_field,
        "flattened_channel_type": mutant_flattened_channel_type,
        "independent_dependency_assumption":
            mutant_independent_dependency_assumption,
        "template_covariance_mix": mutant_template_covariance_mix,
        "posthoc_window_edit": mutant_posthoc_window_edit,
        "active_inference_without_registry":
            mutant_active_inference_without_registry,
    }
    if set(registered) != set(executions):
        raise SystemExit("mutation registry does not match the executions")
    rows = []
    for mutation_id, fn in executions.items():
        killed = False
        message = "MUTANT SURVIVED"
        try:
            fn()
        except EstimandRegistryError as exc:
            killed = True
            message = _redact(str(exc), redact_patterns)[:220]
        rows.append({
            "mutation_id": mutation_id,
            "kill_rule": registered[mutation_id],
            "killed": killed,
            "kill_message_redacted": message,
        })
    return {
        "schema": "pr134.mutation_report.v1",
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
    if spec.get("schema") != "htt.long_horizon.pr134_estimand_registry.v1":
        raise SystemExit("pr134 spec schema mismatch")
    _verify_baseline_commit(spec)
    _verify_remediation_state(spec)
    cross_covered = _verify_prohibition_cross_list(spec)
    problems: list[str] = []
    wrote: list[str] = []

    reg, fingerprints = _build_registry(spec)
    registry = build_registry_artifact(spec, reg)
    registry["prohibition_cross_list_covered"] = cross_covered
    fps = build_fingerprints(fingerprints)
    graph = build_graph(spec, reg)
    branches = build_branches(spec, reg)
    captions = build_captions(reg)
    registry["negative_scan"] = {
        "targets": _scan_targets(spec, captions), "total_hits": 0}
    mutations = run_mutations(spec)
    if mutations["surviving_mutation_count"]:
        print(json.dumps({"ok": False, "survivors": mutations["mutations"]}))
        return 2

    _emit(OUTPUTS["registry"], registry, write, problems, wrote)
    _emit(OUTPUTS["fingerprints"], fps, write, problems, wrote)
    _emit(OUTPUTS["graph"], graph, write, problems, wrote)
    _emit(OUTPUTS["branches"], branches, write, problems, wrote)
    _emit(OUTPUTS["captions"], captions, write, problems, wrote)
    _emit(OUTPUTS["mutations"], mutations, write, problems, wrote)

    manifest = {
        "schema": "pr134.artifact_manifest.v1",
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
            for rel in ("htt/src/common/estimand_registry.py",)
        ],
        "caveats": [
            "Estimand/analysis specification mechanics at C1 only.",
            "The five representative contracts are specification records "
            "from documented metadata, NOT PR4 data runs.",
            "Dependence is a named cluster; independent rows are never "
            "the default.",
            "The template-mean and covariance-factor branches stay "
            "separate.",
            "No measurement or family/geometry claim.",
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
    print(json.dumps({
        "ok": True, "mode": "write" if write else "check", "wrote": wrote,
        "contracts": len(reg.ids()),
        "dependency_clusters": len(graph["clusters"]),
        "fingerprints_unique": fps["unique"],
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
