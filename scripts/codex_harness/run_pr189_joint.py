"""PR-189 runner: joint feasible-set gates + CAS status (--write/--check)."""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
from fractions import Fraction
from pathlib import Path

import numpy as np

REPO = Path(__file__).resolve().parents[2]
for entry in (str(REPO / "htt"), str(REPO / "htt" / "src")):
    if entry not in sys.path:
        sys.path.insert(0, entry)

from common.joint_feasible_set import (  # noqa: E402
    InfeasibleError,
    analyze,
    exact_support,
)

SPEC = REPO / "docs/research_program/strengthening/pr189_spec.yaml"
CARD = REPO / "docs/generated/pr189_result_card.json"
CAS_CONTRACT = REPO / "docs/generated/pr189_cas/CAS_CONTRACT_PR189_JOINT.json"
CAS_AXIS_RESULTS = tuple(
    REPO / f"docs/generated/pr189_cas/axis_result_{axis}.json"
    for axis in ("wolfram_xact", "sympy", "sage_singular", "lean", "rocq")
)

# coupled fixture: c=(1,1), 0<=x<=1, 0<=y<=1, x+y<=1
COUPLED_A = [[-1, 0], [1, 0], [0, -1], [0, 1], [1, 1]]
COUPLED_B = [0, 1, 0, 1, 1]
FACT_A = [[-1, 0], [1, 0], [0, -1], [0, 1]]
FACT_B = [0, 1, 0, 1]
C = [1, 1]


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _empty_classified() -> bool:
    # contradictory: x <= 0 and x >= 1
    A = [[1, 0], [-1, 0], [0, 1], [0, -1]]
    b = [0, -1, 1, 0]
    try:
        exact_support([Fraction(1), Fraction(1)],
                      [[Fraction(x) for x in r] for r in A],
                      [Fraction(x) for x in b])
        return False
    except InfeasibleError:
        return True


def _random_witnesses_inside(n: int = 100_000) -> bool:
    rng = np.random.default_rng(20260721)
    coupled = analyze(C, COUPLED_A, COUPLED_B)
    lo, hi = float(Fraction(coupled["joint_interval"][0])), float(
        Fraction(coupled["joint_interval"][1]))
    outside = 0
    for _ in range(n):
        x, y = rng.random(), rng.random()
        if x + y <= 1:  # feasible for the coupled set
            val = x + y
            if val < lo - 1e-12 or val > hi + 1e-12:
                outside += 1
    return outside == 0


def _cas_status() -> dict:
    contract_sha = _sha(CAS_CONTRACT)
    completed = subprocess.run(
        [
            sys.executable,
            "-B",
            ".agent-harness/scripts/cas_gate.py",
            "adjudicate",
            "--contract",
            str(CAS_CONTRACT.relative_to(REPO)),
            "--results",
            *(str(path.relative_to(REPO)) for path in CAS_AXIS_RESULTS),
            "--historical-replay",
        ],
        cwd=REPO,
        capture_output=True,
        text=True,
        check=False,
    )
    try:
        diagnostic = json.loads(completed.stdout)
    except json.JSONDecodeError:
        diagnostic = {}
    stored_cas_diagnostic_only = (
        completed.returncode == 2
        and diagnostic.get("aggregate_status") == "CAS_BLOCKED"
        and diagnostic.get("claim_promotion_cas_eligible") is False
        and diagnostic.get("evidence_origin") == "stored_axis_result_envelopes"
    )
    return {
        "contract": "docs/generated/pr189_cas/CAS_CONTRACT_PR189_JOINT.json",
        "contract_sha256": contract_sha,
        "contract_hash_matches_adjudication": (
            stored_cas_diagnostic_only
            and diagnostic.get("contract_sha256") == contract_sha
        ),
        "aggregate": "CAS_BLOCKED",
        "historical_aggregate": diagnostic.get("historical_aggregate_status"),
        "required_axes": diagnostic.get("required_axes", []),
        "axis_statuses": diagnostic.get("axis_statuses", {}),
        "stored_cas_diagnostic_only": stored_cas_diagnostic_only,
        "claim_promotion_cas_eligible": False,
        "kernel_independent_lineages": ["lean", "rocq"],
    }


def build_payload() -> dict:
    coupled = analyze(C, COUPLED_A, COUPLED_B)
    factorized = analyze(C, FACT_A, FACT_B)
    empty_ok = _empty_classified()
    witnesses_inside = _random_witnesses_inside()
    cas = _cas_status()

    all_ok = (
        coupled["joint_subset_of_product"] and coupled["strict_narrower"]
        and coupled["highs_cross_check_agrees"]
        and factorized["joint_equals_product"]
        and empty_ok and witnesses_inside
        and cas["aggregate"] == "CAS_5AXIS_PASS"
        and cas["contract_hash_matches_adjudication"]
    )
    terminal = (
        "JOINT_IDENTIFIED_SET_CERTIFIED_CAS_5AXIS_PASS"
        if all_ok else "BLOCKED_JOINT_SET_GATE_FAILURE"
    )
    return {
        "schema": "htt.pr189.result_card.v1",
        "pr_id": "PR-189",
        "metadata": {
            "owner": "HTT",
            "spec_sha256": _sha(SPEC),
            "claim_level": {"scheme": "roadmap_rescue_v1", "level": "C1"},
            "public_use": False,
            "readiness_state": "EVIDENCE_READY",
            "independence_gate": "OPEN",
            "generating_command": (
                "env PYTHONHASHSEED=0 venv/bin/python -B "
                "scripts/codex_harness/run_pr189_joint.py --write"
            ),
        },
        "result": {
            "coupled_fixture": coupled,
            "factorized_fixture": factorized,
            "empty_system_classified": empty_ok,
            "random_witnesses_inside_certified_interval": witnesses_inside,
            "cas_status": cas,
        },
        "terminal": terminal,
        "forbidden_claims_reaffirmed": [
            "the product box is a corollary, not the identified set, on a coupled F",
            "a product endpoint is never reported sharp when the joint set is narrower",
            "the certified exact optimizer is the authority; HiGHS is a cross-check",
        ],
    }


def _render(obj: dict) -> bytes:
    return (json.dumps(obj, sort_keys=True, indent=1) + "\n").encode()


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--write", action="store_true")
    mode.add_argument("--check", action="store_true")
    args = parser.parse_args(argv)
    payload = build_payload()
    if args.write:
        print(
            "refusing to overwrite the frozen historical result card without "
            "a new parent-observed cas_gate.py run-adjudicate execution",
            file=sys.stderr,
        )
        return 2
    ok = CARD.exists() and CARD.read_bytes() == _render(payload)
    print(json.dumps({"mode": "check", "ok": ok, "read_only": True,
                      "terminal": payload["terminal"]}, sort_keys=True))
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
