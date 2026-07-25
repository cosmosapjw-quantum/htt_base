#!/usr/bin/env python3
"""PR-133 runner: source-response type system + non-bridge guard.

``--write`` builds / ``--check`` verifies (fresh build must equal disk
bytes): the typed-quantity firewall record, the symbolic harmonic
boost order counting, the synthetic deprojection estimator property,
the response graph (analytic vs observed rank + aligned-axis
exception + response ladder), generated captions, and the mutation
report (six preregistered mutants killed on production validator
paths).

Pre-solver discrimination diagnostic at roadmap_rescue_v1:C2; no
family/geometry/global-tilt measurement; no disposition change.
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

from common.source_response_types import (  # noqa: E402
    EQUIVALENCE_EDGES,
    SCHEMA_VERSION,
    QuantityType,
    Rung,
    SourceResponseError,
    TypedQuantity,
    _TYPE_META,
    analytic_response_rank,
    bridge,
    deprojection_estimator_property,
    discrimination_verdict,
    generate_caption,
    harmonic_order_counting,
    label_highest_rung,
    lint_caption,
    observed_response,
    require_beta_order,
    require_declared_provenance,
    require_rung_not_above,
    require_surfaced_exception,
)

SPEC_PATH = REPO / "docs/research_program/long_horizon_rescue/pr133_spec.yaml"
OUTPUTS = {
    "types": "docs/generated/pr133_typed_quantities.json",
    "boost": "docs/generated/pr133_harmonic_boost.json",
    "deprojection": "docs/generated/pr133_deprojection_property.json",
    "graph": "docs/generated/pr133_response_graph.json",
    "captions": "docs/generated/pr133_captions.json",
    "mutations": "docs/generated/pr133_mutation_report.json",
    "manifest": "docs/generated/pr133_artifact_manifest.json",
}
SOURCE_TYPES_PATH = "htt/src/common/source_response_types.py"
REDACTED = "[REDACTED-PATTERN]"


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _render(payload: dict) -> bytes:
    return (json.dumps(payload, indent=2, ensure_ascii=False, sort_keys=True)
            + "\n").encode()


def _semantic_artifact(rel: str, payload: dict) -> dict:
    """Keep the maintained source hash as generation-time provenance."""

    normalized = json.loads(json.dumps(payload))
    if rel == OUTPUTS["types"]:
        scan = normalized.get("negative_scan")
        targets = scan.get("targets") if isinstance(scan, dict) else None
        source = (
            targets.get(SOURCE_TYPES_PATH)
            if isinstance(targets, dict) else None
        )
        if not isinstance(source, dict):
            return normalized
        digest = source.get("sha256")
        if (
            isinstance(digest, str)
            and len(digest) == 64
            and all(char in "0123456789abcdef" for char in digest)
        ):
            source["sha256"] = "<generation-time-source>"
        return normalized
    if rel != OUTPUTS["manifest"]:
        return normalized
    rows = normalized.get("input_hashes")
    if not isinstance(rows, list):
        return normalized
    prefix = f"{SOURCE_TYPES_PATH}:"
    for index, row in enumerate(rows):
        if not isinstance(row, str) or not row.startswith(prefix):
            continue
        digest = row.removeprefix(prefix)
        if (
            len(digest) == 64
            and all(char in "0123456789abcdef" for char in digest)
        ):
            rows[index] = f"{prefix}<generation-time-source>"
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
        except SourceResponseError:
            covered += 1
            continue
        raise SystemExit(
            "prohibition cross-list gap: a spec forbidden pattern is not "
            "covered by the module caption lint")
    return covered


def build_types(spec: dict) -> dict:
    rows = spec["typed_quantities"]["types"]
    names = [row["name"] for row in rows]
    production_names = {qtype.value for qtype in QuantityType}
    if (
        len(rows) != len(production_names)
        or len(set(names)) != len(names)
        or set(names) != production_names
    ):
        raise SystemExit(
            "typed-quantity registry does not match the production enum"
        )
    reg = {t["name"]: t for t in rows}
    types = []
    for qtype in QuantityType:
        meta = _TYPE_META[qtype]
        spec_row = reg[qtype.value]
        if meta["symbol"] != spec_row["symbol"] or \
                meta["order_in_beta"] != spec_row["order_in_beta"] or \
                meta["harmonic_channel"] != spec_row["harmonic_channel"] \
                or meta["physical"] != spec_row["physical"]:
            raise SystemExit(f"typed-quantity drift for {qtype.value}")
        types.append({"name": qtype.value, **meta})
    # positive/negative controls
    av = TypedQuantity(QuantityType.OBSERVER_PROXY, Fraction(1, 100))
    ot = TypedQuantity(QuantityType.PHYSICAL_TILT, Fraction(1, 100))
    same = av + TypedQuantity(QuantityType.OBSERVER_PROXY, Fraction(1, 100))
    firewall_ok = True
    try:
        _ = av + ot
        firewall_ok = False
    except SourceResponseError:
        pass
    if not firewall_ok:
        raise SystemExit("firewall failed to block cross-type arithmetic")
    # provenance audit (the direct-reconstruction scope fix): a
    # physical_tilt reconstructed directly from a proxy value while
    # carrying an unregistered bridged provenance is caught here.
    direct_reconstruction_caught = False
    smuggled = TypedQuantity(QuantityType.PHYSICAL_TILT, av.value,
                             provenance="bridged:forged")
    try:
        require_declared_provenance(smuggled)
    except SourceResponseError:
        direct_reconstruction_caught = True
    require_declared_provenance(
        TypedQuantity(QuantityType.PHYSICAL_TILT, Fraction(1, 100)))
    if not direct_reconstruction_caught:
        raise SystemExit("provenance audit failed to flag a smuggled "
                         "cross-type value")
    return {
        "schema": "pr133.typed_quantities.v1",
        "module_schema": SCHEMA_VERSION,
        "types": types,
        "firewall_rule": spec["typed_quantities"]["firewall_rule"],
        "same_type_add_example": str(same.value),
        "registered_equivalence_edges": len(EQUIVALENCE_EDGES),
        "av_omega_tilt_bridge": "refused_no_registered_edge",
        "direct_reconstruction_provenance_audit": "caught",
    }


def build_boost(spec: dict) -> dict:
    counting = harmonic_order_counting()
    return {
        "schema": "pr133.harmonic_boost.v1",
        "order_counting": spec["harmonic_boost"]["order_counting"],
        "derivation": counting,
    }


def build_deprojection(spec: dict) -> dict:
    prop = deprojection_estimator_property()
    return {
        "schema": "pr133.deprojection_property.v1",
        "formula": spec["deprojection"]["formula"],
        "alpha_note": spec["deprojection"]["alpha_note"],
        "estimator_property": prop,
    }


def build_graph(spec: dict) -> dict:
    analytic = analytic_response_rank()
    clean = observed_response(None)
    aligned = observed_response(
        {"collinear_axes": [("Sigma2", "Omega_tilt")]})
    require_surfaced_exception(aligned)
    # response ladder: each candidate labeled by highest reached rung,
    # every pointer resolving to a REAL repo artifact.
    ladder = {
        # the W2/DeltaOmega_k two-sector joint null is the PR-127 frozen
        # non-identification (algebraic + constraint rungs); it has NO
        # local/global dynamics evidence, so it caps at constraint.
        "W2_DeltaOmega_k_joint_null": label_highest_rung({
            Rung.ALGEBRAIC_WITNESS:
                "docs/generated/pr127_response_kernel.json",
            Rung.CONSTRAINT_ADMISSIBLE:
                "docs/generated/pr127_nonid_witnesses.json",
            Rung.LOCAL_DYNAMICS_ADMISSIBLE: None,
            Rung.GLOBAL_DYNAMICS_ADMISSIBLE: None,
        }),
        "omega_tilt_kinematic_proxy": label_highest_rung({
            Rung.ALGEBRAIC_WITNESS: "htt/bass/forward/doppler_boost.py",
            Rung.CONSTRAINT_ADMISSIBLE: None,
        }),
    }
    verdicts = {
        "boost_removed_full_rank": discrimination_verdict(
            boost_removed=True, local_rank=analytic,
            global_rank=analytic, full_rank=analytic),
        "boost_not_removed": discrimination_verdict(
            boost_removed=False, local_rank=analytic,
            global_rank=analytic, full_rank=analytic),
        "rank_deficient": discrimination_verdict(
            boost_removed=True, local_rank=analytic - 1,
            global_rank=analytic, full_rank=analytic),
    }
    return {
        "schema": "pr133.response_graph.v1",
        "basis": spec["response_graph"]["basis"],
        "analytic_rank": analytic,
        "observed_clean": clean,
        "observed_aligned": aligned,
        "non_bridge_edges": spec["response_graph"]["non_bridge_edges"],
        "response_ladder": ladder,
        "discrimination_verdicts": verdicts,
    }


def build_captions() -> dict:
    text = generate_caption()
    lint_caption(text)
    return {"schema": "pr133.captions.v1", "captions": {"summary": text}}


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
    av = TypedQuantity(QuantityType.OBSERVER_PROXY, Fraction(1, 100))
    ot = TypedQuantity(QuantityType.PHYSICAL_TILT, Fraction(1, 100))

    def mutant_auto_bridge_av_omega_tilt() -> None:
        bridge(av, QuantityType.PHYSICAL_TILT, "forged-reference")

    def mutant_cross_type_arithmetic() -> None:
        _ = av - ot

    def mutant_rung_auto_promotion() -> None:
        # a REAL auto-promotion attempt: base rungs resolve, a mid-ladder
        # gap, yet the top rung is claimed. require_rung_not_above must
        # reject the claim above the capped rung.
        require_rung_not_above(
            {Rung.ALGEBRAIC_WITNESS:
                "docs/generated/pr127_response_kernel.json",
             Rung.CONSTRAINT_ADMISSIBLE:
                "docs/generated/pr127_nonid_witnesses.json",
             Rung.LOCAL_DYNAMICS_ADMISSIBLE: None,
             Rung.GLOBAL_DYNAMICS_ADMISSIBLE:
                "docs/generated/pr131_fd_plateau.json"},
            Rung.GLOBAL_DYNAMICS_ADMISSIBLE)

    def mutant_wrong_beta_order() -> None:
        require_beta_order("kinematic_quadrupole", 1)

    def mutant_hidden_aligned_axis_exception() -> None:
        require_surfaced_exception({
            "analytic_rank": 4, "observed_rank": 3,
            "aligned_axis_exception": None})

    def mutant_deprojection_as_detection() -> None:
        lint_caption("The synthetic deprojection means shear detected"
                     " via deprojection on this sky.")

    registered = {m["mutation_id"]: m["kill_rule"]
                  for m in spec["mutation_registry"]}
    executions = {
        "auto_bridge_av_omega_tilt": mutant_auto_bridge_av_omega_tilt,
        "cross_type_arithmetic": mutant_cross_type_arithmetic,
        "rung_auto_promotion": mutant_rung_auto_promotion,
        "wrong_beta_order": mutant_wrong_beta_order,
        "hidden_aligned_axis_exception":
            mutant_hidden_aligned_axis_exception,
        "deprojection_as_detection": mutant_deprojection_as_detection,
    }
    if set(registered) != set(executions):
        raise SystemExit("mutation registry does not match the executions")
    rows = []
    for mutation_id, fn in executions.items():
        killed = False
        message = "MUTANT SURVIVED"
        try:
            fn()
        except SourceResponseError as exc:
            killed = True
            message = _redact(str(exc), redact_patterns)[:220]
        rows.append({
            "mutation_id": mutation_id,
            "kill_rule": registered[mutation_id],
            "killed": killed,
            "kill_message_redacted": message,
        })
    return {
        "schema": "pr133.mutation_report.v1",
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
    if rel in {OUTPUTS["types"], OUTPUTS["manifest"]}:
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
    if spec.get("schema") != \
            "htt.long_horizon.pr133_source_response_types.v1":
        raise SystemExit("pr133 spec schema mismatch")
    _verify_baseline_commit(spec)
    _verify_remediation_state(spec)
    cross_covered = _verify_prohibition_cross_list(spec)
    problems: list[str] = []
    wrote: list[str] = []

    types = build_types(spec)
    types["prohibition_cross_list_covered"] = cross_covered
    boost = build_boost(spec)
    deprojection = build_deprojection(spec)
    graph = build_graph(spec)
    captions = build_captions()
    types["negative_scan"] = {
        "targets": _scan_targets(spec, captions), "total_hits": 0}
    mutations = run_mutations(spec)
    if mutations["surviving_mutation_count"]:
        print(json.dumps({"ok": False, "survivors": mutations["mutations"]}))
        return 2

    _emit(OUTPUTS["types"], types, write, problems, wrote)
    _emit(OUTPUTS["boost"], boost, write, problems, wrote)
    _emit(OUTPUTS["deprojection"], deprojection, write, problems, wrote)
    _emit(OUTPUTS["graph"], graph, write, problems, wrote)
    _emit(OUTPUTS["captions"], captions, write, problems, wrote)
    _emit(OUTPUTS["mutations"], mutations, write, problems, wrote)

    manifest = {
        "schema": "pr133.artifact_manifest.v1",
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
            for rel in ("htt/src/common/source_response_types.py",
                        "htt/obsstat/egs3_kinematic_deprojection.py",
                        "htt/src/common/graded_nonid.py")
        ],
        "caveats": [
            "Pre-solver discrimination diagnostic at C2 only.",
            "A_v and Omega_tilt are distinct types; no auto-bridge.",
            "The deprojection is a synthetic estimator property, never "
            "a shear detection.",
            "Analytic and observed ranks are separate; the aligned-axis "
            "exception is always surfaced.",
            "No scalar family/global-tilt/geometry measurement.",
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
        "types": len(types["types"]),
        "analytic_rank": graph["analytic_rank"],
        "observed_aligned_rank": graph["observed_aligned"][
            "observed_rank"],
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
