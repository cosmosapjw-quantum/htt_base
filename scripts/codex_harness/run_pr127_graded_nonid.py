#!/usr/bin/env python3
"""PR-127 runner: cancellation-preserving graded/PSD-cone non-identification.

``--write`` builds / ``--check`` verifies (fresh build must equal disk
bytes): the two-engine response kernel receipt (SymPy + SageMath QQ, one
sage invocation covering the base map and every registered probe row), the
non-identification witness registry (set-valued equivalence pairs with
A_C/algebraic_only labels), the added-observable rank table, and the
mutation report (six preregistered mutants, all killed by the real
validators).

Formal non-identification of the declared response map at C2 only; never
an isotropy statement; no disposition change.
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

import yaml  # noqa: E402

from common.graded_nonid import (  # noqa: E402
    EXPECTED_KERNEL_BASIS,
    EXPECTED_RANK,
    RESPONSE_ROWS,
    CarrierPoint,
    GradedNonIdError,
    added_row_raises_rank,
    constraint_assignment,
    forbid_psd_projection,
    lint_nonid_text,
    require_engine_agreement,
    require_registered_kernel,
    sage_rank_kernel,
    sympy_rank_kernel,
    validate_witness_pair,
    witness_label,
)

SPEC_PATH = REPO / "docs/research_program/long_horizon_rescue/pr127_spec.yaml"
OUTPUTS = {
    "kernel": "docs/generated/pr127_response_kernel.json",
    "witnesses": "docs/generated/pr127_nonid_witnesses.json",
    "rank_api": "docs/generated/pr127_rank_api_table.json",
    "mutations": "docs/generated/pr127_mutation_report.json",
    "manifest": "docs/generated/pr127_artifact_manifest.json",
}

# Registered witness pairs (difference along each kernel direction).
WITNESS_PAIRS = {
    "WIT-1-w2_direction": (
        CarrierPoint(sigma2=Fraction(1, 10**8), w2=Fraction(0),
                     omega_tilt=Fraction(1, 10**7),
                     delta_omega_k=Fraction(-1, 10**7)),
        CarrierPoint(sigma2=Fraction(1, 10**8), w2=Fraction(3, 10**8),
                     omega_tilt=Fraction(1, 10**7),
                     delta_omega_k=Fraction(-1, 10**7)),
    ),
    "WIT-2-delta_omega_k_direction": (
        CarrierPoint(sigma2=Fraction(2, 10**8), w2=Fraction(1, 10**8),
                     omega_tilt=Fraction(0),
                     delta_omega_k=Fraction(-1, 10**8)),
        CarrierPoint(sigma2=Fraction(2, 10**8), w2=Fraction(1, 10**8),
                     omega_tilt=Fraction(0),
                     delta_omega_k=Fraction(5, 10**8)),
    ),
}

# A verified physical assignment for WIT-1's first point:
# Omega_m + Omega_L + Omega_k_total + omega_tilt + sigma2 - w2 = 1
# Per-STATE assignments: a pair is physical only when BOTH states carry a
# verified assignment. Moving along the kernel direction inside
# A_C_comparator_level requires co-moving the nuisance Omega_L — that
# nuisance freedom is exactly what the non-identification statement says,
# and it is registered here explicitly rather than implied.
def _assignment_for(point) -> dict:
    return {
        "Omega_m": "3/10",
        "Omega_L": str(Fraction(7, 10) - point.sigma2 - point.omega_tilt
                       + point.w2),
        "Omega_k_total": "0",
    }


PHYSICAL_ASSIGNMENTS = {
    "WIT-1-w2_direction": tuple(
        _assignment_for(point)
        for point in WITNESS_PAIRS["WIT-1-w2_direction"]
    ),
    # WIT-2 deliberately carries NO assignment: it must stay algebraic_only.
    "WIT-2-delta_omega_k_direction": None,
}


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _render(payload: dict) -> bytes:
    return (json.dumps(payload, indent=2, ensure_ascii=False, sort_keys=True)
            + "\n").encode()


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
    if len(findings) != contract["finding_count"] or statuses != dict(
            contract["required_scientific_status_counts"]):
        raise SystemExit("remediation census mismatch")


def _verify_live_design_binding() -> None:
    """RESPONSE_ROWS must equal the LIVE registered design exactly — a
    silently changed channel_response_design cannot be re-blessed under a
    stale transcription."""
    import numpy as np

    sys.path.insert(0, str(REPO / "htt"))
    from htt.obsstat.egs3_graded_comparator import channel_response_design

    live = channel_response_design()
    transcribed = np.array([[float(x) for x in row] for row in RESPONSE_ROWS])
    if live.shape != transcribed.shape or not np.array_equal(live,
                                                             transcribed):
        raise GradedNonIdError(
            "RESPONSE_ROWS transcription drifted from the live "
            "channel_response_design — re-register the response map"
        )


def build_kernel_receipt(spec: dict, sage_result: dict) -> dict:
    _verify_live_design_binding()
    sympy_result = sympy_rank_kernel(RESPONSE_ROWS)
    agreement = require_engine_agreement([sympy_result, sage_result])
    if agreement["rank"] != EXPECTED_RANK:
        raise GradedNonIdError(
            f"KILL SWITCH: agreed rank {agreement['rank']} != expected "
            f"{EXPECTED_RANK}"
        )
    require_registered_kernel(sympy_result["kernel_basis"])
    got = sorted(tuple(str(Fraction(e)) for e in vec)
                 for vec in sympy_result["kernel_basis"])
    return {
        "schema": "pr127.response_kernel.v1",
        "response_rows": [[str(x) for x in row] for row in RESPONSE_ROWS],
        "sectors": list(spec["response_map"]["sectors"]),
        "rank": agreement["rank"],
        "kernel_basis": [list(vec) for vec in got],
        "engines": agreement["engines"],
        "engine_results": {
            "sympy": sympy_result,
            "sage_qq": {k: sage_result[k]
                        for k in ("engine", "rank", "kernel_basis")},
        },
        "scope": (
            "the DECLARED registered response map only; silent about any "
            "other map, transfer, mask, or window"
        ),
    }


def build_witness_registry() -> dict:
    rows = {}
    for wit_id, (a, b) in WITNESS_PAIRS.items():
        verdict = validate_witness_pair(a, b)
        assignments = PHYSICAL_ASSIGNMENTS[wit_id]
        if assignments is None:
            label = "algebraic_only"
            assignment_rows = None
            nuisance_note = None
        else:
            labels = [witness_label(state, assignment)
                      for state, assignment in zip((a, b), assignments)]
            label = ("physical" if all(l == "physical" for l in labels)
                     else "algebraic_only")
            assignment_rows = list(assignments)
            nuisance_note = (
                "the kernel move stays inside A_C_comparator_level only by "
                "co-moving the nuisance Omega_L (verified per state) — the "
                "registered nuisance freedom IS the non-identification"
            )
        rows[wit_id] = {
            "state_a": {k: str(getattr(a, k)) for k in
                        ("sigma2", "w2", "omega_tilt", "delta_omega_k")},
            "state_b": {k: str(getattr(b, k)) for k in
                        ("sigma2", "w2", "omega_tilt", "delta_omega_k")},
            "x_c_state_a": str(a.x_c()),
            "x_c_state_b": str(b.x_c()),
            "label": label,
            "assignments_per_state": assignment_rows,
            "nuisance_note": nuisance_note,
            **verdict,
        }
    text = (
        "point identification along the kernel directions is impossible "
        "for the declared response map: the registered witness pairs are "
        "response-indistinguishable yet distinct in the carrier"
    )
    lint_nonid_text(text)
    return {
        "schema": "pr127.nonid_witnesses.v1",
        "witnesses": rows,
        "statement": text,
        "labels_rule": (
            "physical requires a VERIFIED constraint assignment (parent "
            "identity + matter positivity); otherwise algebraic_only"
        ),
    }


def build_rank_table(spec: dict, sage_result: dict) -> dict:
    probes = spec["added_observable_rank_api"]["registered_probes"]
    probe_ranks = sage_result["probe_ranks"]
    if len(probe_ranks) != len(probes):
        raise GradedNonIdError("sage probe count mismatch")
    rows = []
    for probe, sage_rank in zip(probes, probe_ranks):
        row = tuple(Fraction(x) for x in probe["row"])
        raises = added_row_raises_rank(row, sage_rank)
        if raises != bool(probe["raises_rank"]):
            raise GradedNonIdError(
                f"KILL SWITCH: probe {probe['row']} raises_rank={raises} "
                f"contradicts the registered expectation"
            )
        rows.append({
            "row": [str(x) for x in row],
            "raises_rank": raises,
            "agreed_rank_with_row": sage_rank,
            "note": probe["note"],
        })
    return {
        "schema": "pr127.rank_api_table.v1",
        "rule": spec["added_observable_rank_api"]["rule"],
        "probes": rows,
    }


def run_mutations(spec: dict, sage_result: dict) -> dict:
    rows = []
    forbidden = tuple(spec["forbidden_output_language"])

    def record(mutation_id: str, action) -> None:
        try:
            action()
        except GradedNonIdError as exc:
            message = str(exc)
            for phrase in forbidden:
                message = message.replace(phrase, "[redacted-mutant-text]")
            message = message[:160]
            rows.append({"mutation_id": mutation_id, "executed": True,
                         "killed": True, "kill_message": message})
            return
        rows.append({"mutation_id": mutation_id, "executed": True,
                     "killed": False, "kill_message": None})

    # 1. PSD-clipping a registered cancellation witness — real carrier guard.
    def psd_clip() -> None:
        original = WITNESS_PAIRS["WIT-2-delta_omega_k_direction"][0]
        clipped = CarrierPoint(sigma2=original.sigma2, w2=original.w2,
                               omega_tilt=original.omega_tilt,
                               delta_omega_k=Fraction(0))
        forbid_psd_projection(original, clipped)
    record("psd_projection_kills_witness", psd_clip)

    # 2. rank inflation via the rescaled duplicate row — real 2-engine API.
    def inflate() -> None:
        duplicate = (Fraction(0), Fraction(0), Fraction(2), Fraction(0))
        probes = spec["added_observable_rank_api"]["registered_probes"]
        index = next(i for i, probe in enumerate(probes)
                     if [str(x) for x in duplicate] == probe["row"])
        sage_rank = sage_result["probe_ranks"][index]
        if added_row_raises_rank(duplicate, sage_rank):
            return  # mutant would survive
        raise GradedNonIdError(
            "rank-inflation mutant killed: the rescaled duplicate row lies "
            "inside the registered row span (agreed rank stays 2)"
        )
    record("rank_inflation_duplicate_row", inflate)

    # 3. kernel basis missing e_W2 — real agreement/registration check.
    record("kernel_drop", lambda: require_registered_kernel(
        [("0", "0", "0", "1")]))

    # 4. constraint-free promotion — real A_C validator path.
    def promote() -> None:
        point = WITNESS_PAIRS["WIT-2-delta_omega_k_direction"][0]
        label = witness_label(point, None)
        if label == "physical":
            return  # mutant would survive
        raise GradedNonIdError(
            "constraint-free promotion killed: witness without a verified "
            f"assignment stays {label}"
        )
    record("constraint_free_promotion", promote)

    # 5. one-engine claim — real agreement gate.
    record("engine_disagreement", lambda: require_engine_agreement(
        [sympy_rank_kernel(RESPONSE_ROWS)]))

    # 6. isotropy language — real lint.
    record("non_identification_as_isotropy", lambda: lint_nonid_text(
        "the kernel shows identification impossible in nature, hence "
        "non-identification proves isotropy"))

    registered = [m["mutation_id"] for m in spec["mutation_registry"]]
    executed = [m["mutation_id"] for m in rows]
    if executed != registered:
        raise SystemExit(f"mutation set drifted: {registered} vs {executed}")
    return {
        "schema": "pr127.mutation_report.v1",
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
    if spec.get("schema") != "htt.long_horizon.pr127_graded_nonid.v1":
        raise SystemExit("pr127 spec schema mismatch")
    _verify_remediation_state(spec)
    problems: list[str] = []
    wrote: list[str] = []

    probe_rows = [tuple(Fraction(x) for x in probe["row"])
                  for probe in spec["added_observable_rank_api"][
                      "registered_probes"]]
    sage_result = sage_rank_kernel(RESPONSE_ROWS, probe_rows)

    kernel = build_kernel_receipt(spec, sage_result)
    witnesses = build_witness_registry()
    rank_table = build_rank_table(spec, sage_result)
    mutations = run_mutations(spec, sage_result)
    if mutations["surviving_mutation_count"]:
        print(json.dumps({"ok": False, "survivors": mutations["mutations"]}))
        return 2

    _emit(OUTPUTS["kernel"], kernel, write, problems, wrote)
    _emit(OUTPUTS["witnesses"], witnesses, write, problems, wrote)
    _emit(OUTPUTS["rank_api"], rank_table, write, problems, wrote)
    _emit(OUTPUTS["mutations"], mutations, write, problems, wrote)

    manifest = {
        "schema": "pr127.artifact_manifest.v1",
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
            for rel in ("htt/src/common/graded_nonid.py",
                        "htt/obsstat/egs3_graded_comparator.py")
        ],
        "caveats": [
            "Formal non-identification of the DECLARED response map at C2.",
            "Never an isotropy statement; silent about other maps/transfers.",
            "algebraic_only witnesses carry no physical-constraint claim.",
            "All 102 remediation findings remain OPEN.",
        ],
        "artifacts": {},
    }
    manifest["artifacts"] = {
        rel: (_sha(REPO / rel) if (REPO / rel).is_file() else None)
        for key, rel in OUTPUTS.items() if key != "manifest"
    }
    _emit(OUTPUTS["manifest"], manifest, write, problems, wrote)
    if problems:
        print(json.dumps({"ok": False, "problems": problems}))
        return 2

    for key, rel in OUTPUTS.items():
        payload = json.loads((REPO / rel).read_text(encoding="utf-8"))
        if isinstance(payload, dict):
            payload.pop("forbidden_use", None)
        text = json.dumps(payload, ensure_ascii=False)
        for phrase in spec["forbidden_output_language"]:
            if phrase in text:
                print(json.dumps({"ok": False,
                                  "reason": f"forbidden phrase in {rel}"}))
                return 2
    print(json.dumps({
        "ok": True, "mode": "write" if write else "check", "wrote": wrote,
        "agreed_rank": kernel["rank"],
        "witnesses": len(witnesses["witnesses"]),
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
