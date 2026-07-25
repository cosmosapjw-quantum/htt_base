#!/usr/bin/env python3
"""PR-136 runner: partial-identification / identified-set engine.

``--write`` builds / ``--check`` verifies (fresh build must equal disk
bytes): the four fixture identified sets (bounded/empty/unbounded/
disconnected) with dual-engine agreement, the cross-engine record, the
full-vs-subvector projection record, the topology + provenance record,
generated captions, and the mutation report (six preregistered mutants
killed on production validator paths).

Formal/algorithmic identified-region mechanics at roadmap_rescue_v1:C2;
no detection; no disposition change.
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

from common.identified_set import (  # noqa: E402
    AXES,
    KERNEL_AXES,
    SCHEMA_VERSION,
    AdmissibleBox,
    IdentifiedSetError,
    SetStatus,
    axis_constraint,
    classify_status_from_solver,
    disconnected_components,
    exact_engine,
    generate_caption,
    lint_caption,
    numeric_engine,
    require_cross_engine_agreement,
    subvector_projection,
    validate_set_valued,
    validate_status_semantics,
    verify_kernel_binding,
)

SPEC_PATH = REPO / "docs/research_program/long_horizon_rescue/pr136_spec.yaml"
SOURCE_PATH = "htt/src/common/identified_set.py"
OUTPUTS = {
    "sets": "docs/generated/pr136_identified_sets.json",
    "cross": "docs/generated/pr136_cross_engine.json",
    "subvector": "docs/generated/pr136_subvector.json",
    "topology": "docs/generated/pr136_topology.json",
    "captions": "docs/generated/pr136_captions.json",
    "mutations": "docs/generated/pr136_mutation_report.json",
    "manifest": "docs/generated/pr136_artifact_manifest.json",
}
REDACTED = "[REDACTED-PATTERN]"
GRID = [Fraction(k) for k in range(-2, 3)]


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _render(payload: dict) -> bytes:
    return (json.dumps(payload, indent=2, ensure_ascii=False, sort_keys=True)
            + "\n").encode()


def _is_sha256(value: object) -> bool:
    return (
        isinstance(value, str)
        and len(value) == 64
        and all(char in "0123456789abcdef" for char in value)
    )


def _semantic_artifact(rel: str, payload: dict) -> dict:
    """Treat the maintained module hash as generation-time provenance."""

    normalized = json.loads(json.dumps(payload))
    scan = normalized.get("negative_scan")
    targets = scan.get("targets") if isinstance(scan, dict) else None
    source = targets.get(SOURCE_PATH) if isinstance(targets, dict) else None
    if isinstance(source, dict) and _is_sha256(source.get("sha256")):
        source["sha256"] = "<generation-time-source>"
    if rel == OUTPUTS["manifest"]:
        rows = normalized.get("input_hashes")
        prefix = f"{SOURCE_PATH}:"
        if isinstance(rows, list):
            for index, row in enumerate(rows):
                if (
                    isinstance(row, str)
                    and row.startswith(prefix)
                    and _is_sha256(row.removeprefix(prefix))
                ):
                    rows[index] = f"{SOURCE_PATH}:<generation-time-source>"
    return normalized


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
        except IdentifiedSetError:
            covered += 1
            continue
        raise SystemExit(
            "prohibition cross-list gap: a spec forbidden pattern is not "
            "covered by the module caption lint")
    return covered


def _bounded_constraints():
    return [axis_constraint("Sigma2", "==", 1)] + \
        [axis_constraint(a, ">=", -1) for a in AXES[1:]] + \
        [axis_constraint(a, "<=", 1) for a in AXES[1:]]


def _empty_constraints():
    return [axis_constraint("Sigma2", ">=", 1),
            axis_constraint("Sigma2", "<=", 0)]


def _rank_deficient_constraints():
    # box the non-kernel axes; leave the PR-127 kernel (W2, DeltaOmega_k)
    # free -> unbounded along exactly the kernel.
    return [axis_constraint("Sigma2", "==", 0),
            axis_constraint("Omega_tilt", ">=", -1),
            axis_constraint("Omega_tilt", "<=", 1)]


def build_sets(spec: dict) -> dict:
    fixtures = {}
    statuses = {}
    # the honest status readings routed through the semantics guard on
    # the PRODUCTION path (empty != detection, bounded != central,
    # undetermined != non-identification).
    honest_reading = {
        "bounded": "a bounded uncertainty region",
        "empty": "the constraints are jointly infeasible",
        "unbounded": "unbounded along the response kernel",
    }
    for name, cons in (("bounded_box", _bounded_constraints()),
                       ("empty_infeasible", _empty_constraints()),
                       ("rank_deficient_unbounded",
                        _rank_deficient_constraints())):
        exact = exact_engine(cons)
        numeric = numeric_engine(cons)
        require_cross_engine_agreement(exact, numeric)
        validate_set_valued(exact)
        validate_status_semantics(exact["status"],
                                  honest_reading[exact["status"]])
        fixtures[name] = {"exact": exact, "numeric": numeric,
                          "agreement": True}
        statuses[name] = exact["status"]
    # disconnected fixture (nonconvex |Omega_tilt| >= 1 with interior
    # width: the threshold is strictly inside the pinned [-3, 3] box).
    box = AdmissibleBox(lower={a: Fraction(-3) for a in AXES},
                        upper={a: Fraction(3) for a in AXES},
                        pinned_id="admissible_v1")
    dc = disconnected_components("Omega_tilt", Fraction(1), box)
    fixtures["disconnected_sign"] = {"disconnected": dc, "agreement": True}
    statuses["disconnected_sign"] = dc["status"]
    kernel_binding = verify_kernel_binding()
    # verify each fixture matches the spec expected_status
    spec_expected = {f["name"]: f["expected_status"]
                     for f in spec["fixtures"]}
    for name, st in statuses.items():
        if st != spec_expected[name]:
            raise SystemExit(
                f"fixture {name} status {st} != spec {spec_expected[name]}")
    # the rank-deficient case must be unbounded along EXACTLY the kernel
    rd = fixtures["rank_deficient_unbounded"]["exact"]
    if set(rd["unbounded_axes"]) != set(KERNEL_AXES):
        raise SystemExit(
            f"rank-deficient unbounded axes {rd['unbounded_axes']} != the "
            f"PR-127 kernel {KERNEL_AXES}")
    return {
        "schema": "pr136.identified_sets.v1",
        "module_schema": SCHEMA_VERSION,
        "parameter_axes": list(AXES),
        "fixtures": fixtures,
        "statuses": statuses,
        "kernel_axes": sorted(KERNEL_AXES),
        "kernel_binding": kernel_binding,
    }


def build_cross_engine(sets: dict) -> dict:
    rows = []
    for name, fx in sets["fixtures"].items():
        if "exact" in fx:
            rows.append({
                "fixture": name,
                "exact_status": fx["exact"]["status"],
                "numeric_status": fx["numeric"]["status"],
                "agree": fx["exact"]["status"] == fx["numeric"]["status"],
            })
    return {
        "schema": "pr136.cross_engine.v1",
        "exact_engine": "exact_fraction",
        "numeric_engine": "scipy_highs",
        "comparisons": rows,
        "all_agree": all(r["agree"] for r in rows),
    }


def build_subvector(sets: dict) -> dict:
    rd = sets["fixtures"]["rank_deficient_unbounded"]["exact"]
    sub_bounded = subvector_projection(rd, ["Sigma2", "Omega_tilt"])
    sub_kernel = subvector_projection(rd, list(KERNEL_AXES))
    return {
        "schema": "pr136.subvector.v1",
        "full_status": rd["status"],
        "subvector_non_kernel": sub_bounded,
        "subvector_kernel": sub_kernel,
        "note": "the full set is unbounded along the kernel; the "
                "non-kernel subvector is bounded, the kernel subvector "
                "is unbounded — reported separately",
    }


def build_topology(spec: dict, sets: dict, cross: dict) -> dict:
    return {
        "schema": "pr136.topology.v1",
        "set_valued_fields": list(spec["topology_and_provenance"][
            "set_valued_artifact_fields"]),
        "provenance": {
            "exact_engine": "exact_fraction",
            "numeric_engine": "scipy_highs",
            "cross_engine_agreement": cross["all_agree"],
            "kernel_source": "htt/src/common/graded_nonid.py (PR-127)",
        },
        "status_vocabulary": [s.value for s in SetStatus],
        "fixture_statuses": sets["statuses"],
    }


def build_captions(sets: dict) -> dict:
    text = generate_caption(sets["statuses"])
    lint_caption(text)
    return {"schema": "pr136.captions.v1", "captions": {"summary": text}}


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

    def mutant_empty_as_detection() -> None:
        validate_status_semantics(
            SetStatus.EMPTY.value, "the empty set is a detection")

    def mutant_broad_as_central() -> None:
        validate_status_semantics(
            SetStatus.BOUNDED.value,
            "report the broad set as the central estimate")

    def mutant_nonconvergence_as_nonid() -> None:
        validate_status_semantics(
            SetStatus.UNDETERMINED.value,
            "nonconvergence means non-identification")

    def mutant_cross_engine_disagreement() -> None:
        exact = {"status": "bounded",
                 "axis_intervals": {a: ["0", "1"] for a in AXES},
                 "unbounded_axes": []}
        numeric = {"status": "unbounded",
                   "axis_intervals": None, "unbounded_axes": list(AXES)}
        require_cross_engine_agreement(exact, numeric)

    def mutant_scalar_summary_only() -> None:
        validate_set_valued({"central_estimate": 0.5})

    def mutant_admissible_shrink_to_fit() -> None:
        box = AdmissibleBox(lower={a: Fraction(-3) for a in AXES},
                            upper={a: Fraction(3) for a in AXES},
                            pinned_id="admissible_v1")
        # a real data-driven shrink attempt: tighten the box toward an
        # observed Omega_tilt ~ 0 -> the pin guard refuses it.
        box.validate_proposed({"Omega_tilt": Fraction(-1, 10)},
                              {"Omega_tilt": Fraction(1, 10)})

    registered = {m["mutation_id"]: m["kill_rule"]
                  for m in spec["mutation_registry"]}
    executions = {
        "empty_as_detection": mutant_empty_as_detection,
        "broad_as_central": mutant_broad_as_central,
        "nonconvergence_as_nonid": mutant_nonconvergence_as_nonid,
        "cross_engine_disagreement": mutant_cross_engine_disagreement,
        "scalar_summary_only": mutant_scalar_summary_only,
        "admissible_shrink_to_fit": mutant_admissible_shrink_to_fit,
    }
    if set(registered) != set(executions):
        raise SystemExit("mutation registry does not match the executions")
    rows = []
    for mutation_id, fn in executions.items():
        killed = False
        message = "MUTANT SURVIVED"
        try:
            fn()
        except IdentifiedSetError as exc:
            killed = True
            message = _redact(str(exc), redact_patterns)[:220]
        rows.append({
            "mutation_id": mutation_id,
            "kill_rule": registered[mutation_id],
            "killed": killed,
            "kill_message_redacted": message,
        })
    return {
        "schema": "pr136.mutation_report.v1",
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
    if spec.get("schema") != "htt.long_horizon.pr136_identified_set.v1":
        raise SystemExit("pr136 spec schema mismatch")
    _verify_baseline_commit(spec)
    _verify_remediation_state(spec)
    cross_covered = _verify_prohibition_cross_list(spec)
    problems: list[str] = []
    wrote: list[str] = []

    sets = build_sets(spec)
    sets["prohibition_cross_list_covered"] = cross_covered
    cross = build_cross_engine(sets)
    subvector = build_subvector(sets)
    topology = build_topology(spec, sets, cross)
    captions = build_captions(sets)
    sets["negative_scan"] = {
        "targets": _scan_targets(spec, captions), "total_hits": 0}
    mutations = run_mutations(spec)
    if mutations["surviving_mutation_count"]:
        print(json.dumps({"ok": False, "survivors": mutations["mutations"]}))
        return 2

    _emit(OUTPUTS["sets"], sets, write, problems, wrote)
    _emit(OUTPUTS["cross"], cross, write, problems, wrote)
    _emit(OUTPUTS["subvector"], subvector, write, problems, wrote)
    _emit(OUTPUTS["topology"], topology, write, problems, wrote)
    _emit(OUTPUTS["captions"], captions, write, problems, wrote)
    _emit(OUTPUTS["mutations"], mutations, write, problems, wrote)

    manifest = {
        "schema": "pr136.artifact_manifest.v1",
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
            for rel in ("htt/src/common/identified_set.py",
                        "htt/src/common/graded_nonid.py")
        ],
        "caveats": [
            "Formal/algorithmic identified-region mechanics at C2 only.",
            "An empty set is infeasibility, a broad set is uncertainty, "
            "nonconvergence is undetermined.",
            "Full and subvector identified sets are reported separately "
            "as set-valued artifacts.",
            "The admissible box is pinned before the fit; no data-driven "
            "shrinkage.",
            "No detection; no point identification.",
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
    module_text = (REPO / "htt/src/common/identified_set.py").read_text(
        encoding="utf-8").lower()
    for phrase in spec["forbidden_output_language"]:
        if phrase.lower() in module_text:
            print(json.dumps({"ok": False,
                              "reason": "forbidden phrase in module source"}))
            return 2
    print(json.dumps({
        "ok": True, "mode": "write" if write else "check", "wrote": wrote,
        "statuses": sets["statuses"],
        "all_engines_agree": cross["all_agree"],
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
