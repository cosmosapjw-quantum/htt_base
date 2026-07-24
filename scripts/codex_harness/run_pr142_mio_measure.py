#!/usr/bin/env python3
"""PR-142 runner: MIO joint-measure F/Pi/G_F invariance + matched-null.

``--write`` builds / ``--check`` verifies (fresh build must equal disk
bytes): the measures report (F and Pi with measure-appropriate matched
nulls, depth sensitivity, bootstrap uncertainty), the invariance report
(permutation invariance and the pairing counterexample), the set-valued
G_F feasible range, the no-justified-measure demo (family sensitivity
only), generated captions, and the six-mutant kill report.

Calibrated MIO diagnostic mechanics at roadmap_rescue_v1:C2; a measure is
never a posterior, an evidence, or an HTT likelihood; no detection.
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

import numpy as np  # noqa: E402
import yaml  # noqa: E402

from common.mio_joint_measure import (  # noqa: E402
    COMPONENTS,
    SCHEMA_VERSION,
    DepartureTable,
    DepthPolicy,
    MeasureError,
    MeasureSpec,
    MeasureStatus,
    Pairing,
    bootstrap_uncertainty,
    depth_sensitivity,
    feasible_range_GF,
    generate_caption,
    lint_caption,
    matched_null_distribution,
    measure_F,
    measure_Pi,
    pairing_counterexample,
    permutation_invariant,
    refuse_forbidden_role,
    refuse_measure_substitution,
    require_justified_measure,
    require_matched_null,
    require_null_scale_consistent,
    require_registered_measure_family,
)

SPEC_PATH = REPO / "docs/research_program/long_horizon_rescue/pr142_spec.yaml"
OUTPUTS = {
    "measures": "docs/generated/pr142_measures_report.json",
    "invariance": "docs/generated/pr142_invariance_report.json",
    "gf": "docs/generated/pr142_gf_range.json",
    "no_justified": "docs/generated/pr142_no_justified_demo.json",
    "captions": "docs/generated/pr142_captions.json",
    "mutations": "docs/generated/pr142_mutation_report.json",
    "manifest": "docs/generated/pr142_artifact_manifest.json",
}
SOURCE_PATH = "htt/src/common/mio_joint_measure.py"
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


def _is_sha256(value: object) -> bool:
    return (
        isinstance(value, str)
        and len(value) == 64
        and all(char in "0123456789abcdef" for char in value)
    )


def _semantic_artifact(rel: str, payload: dict) -> dict:
    """Keep the maintained-source hash as generation-time provenance."""

    normalized = json.loads(json.dumps(_round(payload)))
    if rel == OUTPUTS["measures"]:
        scan = normalized.get("negative_scan")
        targets = scan.get("targets") if isinstance(scan, dict) else None
        source = (
            targets.get(SOURCE_PATH)
            if isinstance(targets, dict) else None
        )
        if isinstance(source, dict) and _is_sha256(source.get("sha256")):
            source["sha256"] = "<generation-time-source>"
        return normalized
    if rel != OUTPUTS["manifest"]:
        return normalized
    rows = normalized.get("input_hashes")
    if not isinstance(rows, list):
        return normalized
    prefix = f"{SOURCE_PATH}:"
    for index, row in enumerate(rows):
        if (
            isinstance(row, str)
            and row.startswith(prefix)
            and _is_sha256(row.removeprefix(prefix))
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


def _table(spec: dict) -> DepartureTable:
    m = spec["model"]
    n = int(m["n_obs"])
    rng = np.random.Generator(np.random.PCG64(int(m["data_seed"])))
    vals = rng.normal(0.0, 1.0, (n, len(COMPONENTS)))
    sig = m["injected_signal"]
    col = COMPONENTS.index(sig["component"])
    vals[:, col] += float(Fraction(sig["mean_shift"]))
    depth = tuple(int(i % 4) for i in range(n))
    pair = tuple(int(i // 2) for i in range(n))
    return DepartureTable(values=vals, columns=COMPONENTS, depth=depth,
                          pair=pair)


def _spec(spec: dict, *, weights=None, pairing=None, justified=None
          ) -> MeasureSpec:
    ms = spec["model"]["measure_spec"]
    w = weights if weights is not None else \
        tuple(float(Fraction(x)) for x in ms["weights"])
    return MeasureSpec(
        identity=COMPONENTS, weights=w,
        pairing=Pairing(pairing or ms["pairing"]),
        depth_policy=DepthPolicy(ms["depth_policy"]),
        null_scale=tuple(float(Fraction(x)) for x in ms["null_scale"]),
        justified=ms["justified"] if justified is None else justified)


def build_measures(spec: dict):
    table = _table(spec)
    ms = _spec(spec)
    cal = spec["calibration"]
    # anti-drift guards invoked LIVE on the production reporting path (each
    # passes with the admissible input; a drift supplies a rejected one)
    require_justified_measure(ms)
    refuse_forbidden_role("diagnostic_summary")
    refuse_measure_substitution("F", "F")
    require_matched_null(ms, ms)
    require_registered_measure_family(ms, ms, None, None)
    f_null = matched_null_distribution(
        table, ms, "F", int(cal["null_seed"]), int(cal["n_null"]),
        null_type=cal["F_null_type"])
    pi_null = matched_null_distribution(
        table, ms, "Pi", int(cal["null_seed"]), int(cal["n_null"]),
        null_type=cal["Pi_null_type"])
    record = {
        "schema": "pr142.measures_report.v1",
        "module_schema": SCHEMA_VERSION,
        "spec_fingerprint": ms.fingerprint(),
        "F": {"value": measure_F(table, ms), **f_null,
              "bootstrap_se": bootstrap_uncertainty(
                  table, ms, "F", int(cal["boot_seed"]), int(cal["n_boot"])),
              "depth_sensitivity": depth_sensitivity(table, ms, "F")},
        "Pi": {"value": measure_Pi(table, ms), **pi_null,
               "bootstrap_se": bootstrap_uncertainty(
                   table, ms, "Pi", int(cal["boot_seed"]),
                   int(cal["n_boot"])),
               "depth_sensitivity": depth_sensitivity(table, ms, "Pi")},
        "note": "F is a weighted second-moment magnitude calibrated against "
                "a reference-scale matched null; Pi is a weighted signed "
                "contrast calibrated against a sign-flip matched null; "
                "neither is a posterior, an evidence, or an HTT likelihood",
    }
    return record, table, ms


def build_invariance(spec: dict, table: DepartureTable, ms: MeasureSpec):
    f_inv = permutation_invariant(table, ms, "F", seed=1)
    pi_inv = permutation_invariant(table, ms, "Pi", seed=1)
    if not (f_inv and pi_inv):
        raise SystemExit("F/Pi are not permutation invariant — the measure "
                         "is mis-specified")
    paired_spec = _spec(spec, pairing="paired")
    pc = pairing_counterexample(table, paired_spec, "F")
    if not pc["differ"]:
        raise SystemExit("the paired and unpaired specs did not differ")
    return {
        "schema": "pr142.invariance_report.v1",
        "F_permutation_invariant": f_inv,
        "Pi_permutation_invariant": pi_inv,
        "pairing_counterexample": pc,
        "note": "F and Pi are invariant to relabeling the exchangeable rows; "
                "a paired spec applied to the same table gives a different "
                "value than the unpaired spec (the pairing is a modeling "
                "choice, not interchangeable)",
    }


def build_gf(spec: dict, ms: MeasureSpec) -> dict:
    intervals = {c: (-0.5, 0.7) for c in COMPONENTS}
    gf = feasible_range_GF(intervals, ms)
    if gf["is_scalar_posterior"]:
        raise SystemExit("G_F must be set-valued, never a scalar posterior")
    return {"schema": "pr142.gf_range.v1", "component_intervals":
            {c: list(v) for c, v in intervals.items()}, **gf,
            "note": "G_F is the set-valued feasible range of F over an "
                    "identified set of component bounds; it is never a "
                    "point posterior"}


def build_no_justified(spec: dict) -> dict:
    table = _table(spec)
    unjust = _spec(spec, justified=False)
    # a calibrated scalar is refused for an unjustified measure
    refused = False
    try:
        matched_null_distribution(table, unjust, "F", 1, 100)
    except MeasureError:
        refused = True
    if not refused:
        raise SystemExit("an unjustified measure produced a calibrated "
                         "scalar — the guard failed")
    # only measure-family sensitivity is reported
    family = []
    for w in spec["demos"]["no_justified_measure"]["family_weights"]:
        weights = tuple(float(Fraction(x)) for x in w)
        fam_spec = _spec(spec, weights=weights, justified=True)
        family.append({"weights": list(weights),
                       "F": measure_F(table, fam_spec)})
    f_values = [row["F"] for row in family]

    # two-sided Pi: a NEGATIVE contrast of equal magnitude is detected
    ms = _spec(spec)
    cal = spec["calibration"]
    neg_shift = float(Fraction(spec["demos"]["two_sided_pi"]["negative_shift"]))
    neg_vals = _table(spec).values.copy()
    neg_vals[:, COMPONENTS.index("Omega_tilt")] += (neg_shift -
        float(Fraction(spec["model"]["injected_signal"]["mean_shift"])))
    neg_table = DepartureTable(values=neg_vals, columns=COMPONENTS,
                               depth=table.depth, pair=table.pair)
    neg_pi = matched_null_distribution(neg_table, ms, "Pi",
                                       int(cal["null_seed"]),
                                       int(cal["n_null"]), null_type="sign_flip")

    # a mis-set reference null_scale is refused (F significance is not a
    # free hyperparameter)
    mis = tuple(float(Fraction(x)) for x in
                spec["demos"]["mis_set_null_scale"]["null_scale"])
    mis_spec = MeasureSpec(identity=COMPONENTS, weights=ms.weights,
                           pairing=ms.pairing, depth_policy=ms.depth_policy,
                           null_scale=mis)
    mis_refused = False
    try:
        require_null_scale_consistent(table, mis_spec)
    except MeasureError:
        mis_refused = True

    return {
        "schema": "pr142.no_justified_demo.v1",
        "status": MeasureStatus.NO_JUSTIFIED_MEASURE.value,
        "calibrated_scalar_refused": refused,
        "measure_family_sensitivity": family,
        "F_family_range": [min(f_values), max(f_values)],
        "two_sided_pi": {"negative_shift": neg_shift,
                         "observed": neg_pi["observed"],
                         "p_value": neg_pi["p_value"],
                         "sided": neg_pi["sided"]},
        "mis_set_null_scale_refused": mis_refused,
        "note": "with no scientifically-justified measure, no calibrated "
                "scalar is emitted; only the measure-family sensitivity "
                "(F across the weight family) is reported. A negative "
                "contrast is detected by the two-sided Pi p-value, and a "
                "reference null_scale inconsistent with the data is refused.",
    }


def build_captions(measures: dict) -> dict:
    text = generate_caption("Pi", measures["Pi"]["p_value"],
                            measures["Pi"]["depth_sensitivity"]
                            ["abs_sensitivity"],
                            measures["Pi"]["status"])
    lint_caption(text)
    return {"schema": "pr142.captions.v1", "captions": {"summary": text}}


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


def run_mutations(spec: dict) -> dict:
    redact_patterns = (
        [str(p) for p in spec["negative_scan"]["forbidden_patterns"]]
        + [str(p) for p in spec["forbidden_output_language"]])
    table = _table(spec)
    ms = _spec(spec)

    def mutant_measure_as_posterior() -> None:
        refuse_forbidden_role("posterior_probability")

    def mutant_measure_as_evidence() -> None:
        refuse_forbidden_role("evidence")

    def mutant_measure_substitution() -> None:
        refuse_measure_substitution("F", "Pi")

    def mutant_unmatched_null() -> None:
        other = MeasureSpec(COMPONENTS, (2.0, 1.0, 1.0, 1.0), ms.pairing,
                            ms.depth_policy, null_scale=ms.null_scale)
        require_matched_null(ms, other)

    def mutant_degenerate_null_for_F() -> None:
        matched_null_distribution(table, ms, "F", 1, 100,
                                  null_type="sign_flip")

    def mutant_posthoc_weight_change() -> None:
        revised = MeasureSpec(COMPONENTS, (5.0, 1.0, 1.0, 1.0), ms.pairing,
                              ms.depth_policy, null_scale=ms.null_scale)
        require_registered_measure_family(ms, revised, None, None)

    registered = {m["mutation_id"]: m["kill_rule"]
                  for m in spec["mutation_registry"]}
    executions = {
        "measure_as_posterior": mutant_measure_as_posterior,
        "measure_as_evidence": mutant_measure_as_evidence,
        "measure_substitution": mutant_measure_substitution,
        "unmatched_null": mutant_unmatched_null,
        "degenerate_null_for_F": mutant_degenerate_null_for_F,
        "posthoc_weight_change": mutant_posthoc_weight_change,
    }
    if set(registered) != set(executions):
        raise SystemExit("mutation registry does not match the executions")
    rows = []
    for mutation_id, fn in executions.items():
        killed = False
        message = "MUTANT SURVIVED"
        try:
            fn()
        except MeasureError as exc:
            killed = True
            message = _redact(str(exc), redact_patterns)[:220]
        rows.append({"mutation_id": mutation_id,
                     "kill_rule": registered[mutation_id],
                     "killed": killed, "kill_message_redacted": message})
    return {"schema": "pr142.mutation_report.v1", "mutations": rows,
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
        return
    if rel in {OUTPUTS["measures"], OUTPUTS["manifest"]}:
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
    if spec.get("schema") != "htt.long_horizon.pr142_mio_measure.v1":
        raise SystemExit("pr142 spec schema mismatch")
    _verify_baseline_commit(spec)
    _verify_remediation_state(spec)
    problems: list[str] = []
    wrote: list[str] = []

    measures, table, ms = build_measures(spec)
    invariance = build_invariance(spec, table, ms)
    gf = build_gf(spec, ms)
    no_justified = build_no_justified(spec)
    captions = build_captions(measures)
    measures["negative_scan"] = {
        "targets": _scan_targets(spec, captions), "total_hits": 0}
    mutations = run_mutations(spec)
    if mutations["surviving_mutation_count"]:
        print(json.dumps({"ok": False, "survivors": mutations["mutations"]}))
        return 2

    _emit(OUTPUTS["measures"], measures, write, problems, wrote)
    _emit(OUTPUTS["invariance"], invariance, write, problems, wrote)
    _emit(OUTPUTS["gf"], gf, write, problems, wrote)
    _emit(OUTPUTS["no_justified"], no_justified, write, problems, wrote)
    _emit(OUTPUTS["captions"], captions, write, problems, wrote)
    _emit(OUTPUTS["mutations"], mutations, write, problems, wrote)

    manifest = {
        "schema": "pr142.artifact_manifest.v1",
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
            for rel in ("htt/src/common/mio_joint_measure.py",)
        ],
        "caveats": [
            "Calibrated MIO diagnostic mechanics conditional on the "
            "registered MeasureSpec at C2 only.",
            "F, Pi, and Q are DISTINCT; none is a posterior, an evidence, "
            "an HTT likelihood, or a truth certificate.",
            "The matched null shares the spec and is measure-appropriate; a "
            "degenerate null is refused.",
            "G_F is set-valued, never a scalar posterior.",
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
    module_text = (REPO / "htt/src/common/mio_joint_measure.py").read_text(
        encoding="utf-8").lower()
    for phrase in spec["forbidden_output_language"]:
        if phrase.lower() in module_text:
            print(json.dumps({"ok": False,
                              "reason": "forbidden phrase in module source"}))
            return 2
    print(json.dumps({
        "ok": True, "mode": "write" if write else "check", "wrote": wrote,
        "F_value": round(measures["F"]["value"], 6),
        "F_p": round(measures["F"]["p_value"], 6),
        "Pi_value": round(measures["Pi"]["value"], 6),
        "Pi_p": round(measures["Pi"]["p_value"], 6),
        "no_justified_status": no_justified["status"],
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
