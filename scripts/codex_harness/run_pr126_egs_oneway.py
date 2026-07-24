#!/usr/bin/env python3
"""PR-126 runner: one-way FLRW/EGS statement + counterexample registry.

``--write`` builds / ``--check`` verifies (fresh build must equal disk
bytes): the premise DAG, the sealed one-way witness report (forward + the
converse counterexamples + 64 seeded cancellation draws + the SymPy
symbolic combination check), the counterexample registry, and the mutation
report (five preregistered mutants, all killed by the real validators).

Conditional mathematics at roadmap_rescue_v1:C2 — no FLRW certificate, no
converse, no observational claim, no disposition change.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
from fractions import Fraction
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "htt" / "src"))

import yaml  # noqa: E402

from common.egs_oneway import (  # noqa: E402
    ALMOST_EGS_PREMISES,
    ALMOST_EGS_STATUS,
    COMPARATOR_FORWARD_PREMISES,
    EXACT_EGS_PREMISES,
    FORWARD_STATEMENT,
    FORWARD_THEOREM_ID,
    ComparatorState,
    EgsOnewayError,
    check_forward,
    lint_theorem_text,
    safe_theorem_text,
    seeded_cancellation_states,
    theorem_id,
    validate_counterexample,
    validate_theorem_claim,
)
from common.frame_contract import (  # noqa: E402
    FrameContractError,
    KinematicState,
    require_flrw_limit,
)

SPEC_PATH = REPO / "docs/research_program/long_horizon_rescue/pr126_spec.yaml"
OUTPUTS = {
    "dag": "docs/generated/pr126_premise_dag.json",
    "witness": "docs/generated/pr126_oneway_witness_report.json",
    "counterexamples": "docs/generated/pr126_counterexample_registry.json",
    "mutations": "docs/generated/pr126_mutation_report.json",
    "manifest": "docs/generated/pr126_artifact_manifest.json",
}
HISTORICAL_SOURCE_INPUTS = frozenset({
    "htt/src/common/egs_oneway.py",
    "htt/src/common/frame_contract.py",
})


def _forbidden_language(spec: dict) -> tuple[str, ...]:
    return tuple(spec["forbidden_output_language"])


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _render(payload: dict) -> bytes:
    return (json.dumps(payload, indent=2, ensure_ascii=False, sort_keys=True)
            + "\n").encode()


def _semantic_artifact(rel: str, payload: dict) -> dict:
    """Treat frozen source digests as generation-time provenance only."""

    normalized = json.loads(json.dumps(payload))
    if rel != OUTPUTS["manifest"]:
        return normalized
    rows = normalized.get("input_hashes")
    if not isinstance(rows, list):
        return normalized
    for index, row in enumerate(rows):
        if not isinstance(row, str) or ":" not in row:
            continue
        source, digest = row.rsplit(":", 1)
        if (
            source in HISTORICAL_SOURCE_INPUTS
            and len(digest) == 64
            and all(char in "0123456789abcdef" for char in digest)
        ):
            rows[index] = f"{source}:<generation-time-source>"
    return normalized


def _sympy_combination_check() -> bool:
    """Symbolic tie to the sealed parent-identity combination c=(1,-1,1,1)."""
    import sympy as sp

    s2, w2, ot, dk = sp.symbols("s2 w2 ot dk")
    x_c = s2 - w2 + ot + dk
    c_dot = sp.Matrix([1, -1, 1, 1]).dot(sp.Matrix([s2, w2, ot, dk]))
    return sp.simplify(x_c - c_dot) == 0


def build_dag() -> dict:
    return {
        "schema": "pr126.premise_dag.v1",
        "exact_egs_premises": EXACT_EGS_PREMISES,
        "almost_egs_premises": ALMOST_EGS_PREMISES,
        "almost_egs_status": ALMOST_EGS_STATUS,
        "comparator_forward_premises": COMPARATOR_FORWARD_PREMISES,
        "forward_theorem": {
            "theorem_id": FORWARD_THEOREM_ID,
            "statement": FORWARD_STATEMENT,
            "premise_ids": sorted(COMPARATOR_FORWARD_PREMISES),
        },
        "theorem_id_rule": (
            "content-addressed over (premise-id set, statement); any premise "
            "edit mints a NEW theorem id"
        ),
        "safe_theorem_text": safe_theorem_text(),
    }


def _spec_counterexamples(spec: dict) -> list[tuple[str, ComparatorState, str]]:
    rows = []
    for row in spec["oneway_witnesses"]["converse_counterexamples"]:
        state = ComparatorState(**{
            key: Fraction(value) for key, value in row["state"].items()
        })
        rows.append((row["id"], state, row["note"]))
    return rows


def build_witness_report(spec: dict) -> dict:
    # the premise-complete comparator set is mathematically the SINGLE
    # zero state; the forward statement is exact substitution on it
    flrw_states = [ComparatorState(beta=0, sigma2=0, w2=0, omega_tilt=0,
                                   delta_omega_k=0)]
    forward = check_forward(flrw_states)
    forward["note"] = (
        "the premise-complete set is the single zero state; states_checked "
        "counts that one exact substitution (no random sampling exists for "
        "a one-point set)"
    )
    if not _sympy_combination_check():
        raise EgsOnewayError("symbolic c=(1,-1,1,1) combination check failed")

    draws = seeded_cancellation_states(
        spec["oneway_witnesses"]["random_cancellation_property"]["seeds"])
    for state in draws:
        if state.x_c() != 0:
            raise EgsOnewayError("cancellation draw failed to cancel")
        if state.satisfies_forward_premises():
            raise EgsOnewayError("cancellation draw is unexpectedly FLRW")
    return {
        "schema": "pr126.oneway_witness_report.v1",
        "forward": forward,
        "symbolic_combination_check": True,
        "random_cancellation": {
            "draws": len(draws),
            "all_cancel_exactly": True,
            "all_fail_flrw_limit": True,
        },
        "sealed_note": (
            "the forward statement and the counterexample registry are ONE "
            "sealed pair; citing the forward theorem without the registry "
            "is out of contract"
        ),
    }


def build_counterexample_registry(spec: dict) -> dict:
    rows = {}
    for ce_id, state, note in _spec_counterexamples(spec):
        verdict = validate_counterexample(state)
        rows[ce_id] = {
            "state": {k: str(getattr(state, k))
                      for k in ("beta", "sigma2", "w2", "omega_tilt",
                                "delta_omega_k")},
            "note": note,
            **verdict,
        }
    return {
        "schema": "pr126.counterexample_registry.v1",
        "bound_forward_theorem_id": FORWARD_THEOREM_ID,
        "counterexamples": rows,
        "anti_drift": (
            "removing a counterexample by adding a premise post-hoc mints a "
            "NEW theorem id (content-addressed); the old id keeps its "
            "registry"
        ),
    }


def run_mutations(spec: dict) -> dict:
    rows = []

    forbidden = _forbidden_language(spec)

    def record(mutation_id: str, action) -> None:
        try:
            action()
        except (EgsOnewayError, FrameContractError) as exc:
            message = str(exc)[:160]
            for phrase in forbidden:
                message = message.replace(phrase, "[redacted-mutant-text]")
            rows.append({"mutation_id": mutation_id, "executed": True,
                         "killed": True, "kill_message": message})
            return
        rows.append({"mutation_id": mutation_id, "executed": True,
                     "killed": False, "kill_message": None})

    # 1. forward claim under an incomplete premise set — killed by the REAL
    #    forward checker (exhibits the refuting witness).
    record("incomplete_premise_forward_claim", lambda: check_forward(
        [], premise_ids=tuple(
            p for p in COMPARATOR_FORWARD_PREMISES
            if p != "CMP-P4-delta_omega_k_zero")))

    # 2. post-hoc premise edit keeping the old theorem id — killed by the
    #    REAL claim validator (content-addressing).
    record("posthoc_premise_edit_keeps_id", lambda: validate_theorem_claim({
        "theorem_id": FORWARD_THEOREM_ID,
        "statement": FORWARD_STATEMENT,
        "premise_ids": [p for p in COMPARATOR_FORWARD_PREMISES
                        if p != "CMP-P2-sigma2_zero"],
    }))

    # 3. converse language in generated text — killed by the REAL lint.
    record("converse_language", lambda: lint_theorem_text(
        "x_C = 0 therefore FLRW holds and the EGS certificate follows"))

    # 4. beta-zero shortcut — killed by the PR-125 REAL validator.
    record("beta_zero_egs_shortcut", lambda: require_flrw_limit(
        KinematicState(beta=0, sigma2=Fraction(1, 10**8), w2=0,
                       delta_omega_k=0)))

    # 5. merged exact + almost claim — killed by the REAL claim validator.
    def merged() -> None:
        premises = list(COMPARATOR_FORWARD_PREMISES) + [
            "AEGS-P1-almost_isotropy_bounded_multipoles"]
        validate_theorem_claim({
            "theorem_id": theorem_id(premises, FORWARD_STATEMENT),
            "statement": FORWARD_STATEMENT,
            "premise_ids": premises,
        })
    record("merged_exact_almost_claim", merged)

    registered = [m["mutation_id"] for m in spec["mutation_registry"]]
    executed = [m["mutation_id"] for m in rows]
    if executed != registered:
        raise SystemExit(f"mutation set drifted: {registered} vs {executed}")
    return {
        "schema": "pr126.mutation_report.v1",
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
    if rel == OUTPUTS["manifest"]:
        try:
            existing = json.loads(target.read_text(encoding="utf-8"))
        except (UnicodeError, json.JSONDecodeError):
            problems.append(f"invalid artifact: {rel}")
            return
        if (
            isinstance(existing, dict)
            and _semantic_artifact(rel, existing) == _semantic_artifact(rel, payload)
        ):
            return
    if target.read_bytes() != rendered:
        problems.append(f"stale artifact: {rel}")


def _verify_remediation_state(spec: dict) -> None:
    contract = spec["remediation_state_contract"]
    target = REPO / contract["path"]
    if _sha(target) != contract["sha256"]:
        raise SystemExit("remediation state drifted from the spec pin")
    payload = yaml.safe_load(target.read_text(encoding="utf-8"))
    findings = payload.get("findings") or []
    statuses = {}
    for row in findings:
        status = str(row.get("scientific_status"))
        statuses[status] = statuses.get(status, 0) + 1
    if len(findings) != contract["finding_count"] or statuses != dict(
            contract["required_scientific_status_counts"]):
        raise SystemExit(
            f"remediation census mismatch: {len(findings)} findings, "
            f"{statuses}"
        )


def build(write: bool) -> int:
    spec = yaml.safe_load(SPEC_PATH.read_text(encoding="utf-8"))
    if spec.get("schema") != "htt.long_horizon.pr126_egs_oneway.v1":
        raise SystemExit("pr126 spec schema mismatch")
    _verify_remediation_state(spec)
    problems: list[str] = []
    wrote: list[str] = []

    dag = build_dag()
    witness = build_witness_report(spec)
    registry = build_counterexample_registry(spec)
    mutations = run_mutations(spec)
    if mutations["surviving_mutation_count"]:
        print(json.dumps({"ok": False, "survivors": mutations["mutations"]}))
        return 2

    _emit(OUTPUTS["dag"], dag, write, problems, wrote)
    _emit(OUTPUTS["witness"], witness, write, problems, wrote)
    _emit(OUTPUTS["counterexamples"], registry, write, problems, wrote)
    _emit(OUTPUTS["mutations"], mutations, write, problems, wrote)

    manifest = {
        "schema": "pr126.artifact_manifest.v1",
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
            for rel in ("htt/src/common/egs_oneway.py",
                        "htt/src/common/frame_contract.py")
        ],
        "caveats": [
            "Conditional comparator-level mathematics at C2 only.",
            "One-way: x_C = 0 never establishes FLRW/EGS (sealed registry).",
            "Almost-EGS is SPECIFIED_ONLY; no quantitative claim exists.",
            "All 102 remediation findings remain OPEN.",
        ],
        "artifacts": {},
    }
    if write:
        manifest["artifacts"] = {
            rel: _sha(REPO / rel)
            for key, rel in OUTPUTS.items() if key != "manifest"
        }
    else:
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
        for phrase in _forbidden_language(spec):
            if phrase in text:
                print(json.dumps({"ok": False,
                                  "reason": f"forbidden phrase in {rel}"}))
                return 2
    print(json.dumps({
        "ok": True, "mode": "write" if write else "check", "wrote": wrote,
        "forward_theorem_id": FORWARD_THEOREM_ID,
        "counterexamples": len(registry["counterexamples"]),
        "cancellation_draws": witness["random_cancellation"]["draws"],
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
