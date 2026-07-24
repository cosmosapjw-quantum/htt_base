"""PR-175 runner: diagnose the frozen invariant-oracle result card.

``--check`` compares the frozen card with a current fail-closed diagnostic.
Stored axis envelopes and adjudication bytes preserve historical evidence but
cannot provide current CAS authority; ``--write`` therefore refuses to replace
the frozen card without a parent-observed ``cas_gate.py run-adjudicate`` run.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
from pathlib import Path

import numpy as np

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "htt" / "src"))

from common.pr175_invariant_oracle import ENGINE_B_TOL, run_oracle  # noqa: E402

SPEC = REPO / "docs/research_program/long_horizon_rescue/pr175_spec.yaml"
CONTRACT = REPO / "docs/generated/pr175_cas/CAS_CONTRACT_PR175_INVARIANT_V2.json"
ADJUDICATION = REPO / "docs/generated/pr175_cas_adjudication.json"
CARD = REPO / "docs/generated/pr175_result_card.json"
AXES = ("sympy", "sage_singular", "wolfram_xact", "lean")

TERMINALS = {
    "CAS_4AXIS_PASS": "INVARIANT_ORACLE_CAS_4AXIS_PASS_ANCHOR_CONSISTENT",
    "CAS_BLOCKED": "INVARIANT_ORACLE_CAS_BLOCKED",
    "CAS_FAIL": "INVARIANT_ORACLE_CAS_FAIL",
    "CAS_CONFLICT": "INVARIANT_ORACLE_CAS_FAIL",
}


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _cas_status() -> dict:
    completed = subprocess.run(
        [
            sys.executable,
            "-B",
            ".agent-harness/scripts/cas_gate.py",
            "adjudicate",
            "--contract",
            str(CONTRACT.relative_to(REPO)),
            "--results",
            *(
                f"docs/generated/pr175_cas/axis_result_{axis}.json"
                for axis in AXES
            ),
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
    valid_diagnostic = (
        completed.returncode == 2
        and diagnostic.get("aggregate_status") == "CAS_BLOCKED"
        and diagnostic.get("claim_promotion_cas_eligible") is False
        and diagnostic.get("evidence_origin") == "stored_axis_result_envelopes"
    )
    return {
        "aggregate_status": "CAS_BLOCKED",
        "historical_aggregate_status": diagnostic.get(
            "historical_aggregate_status"
        ),
        "contract_sha256": diagnostic.get("contract_sha256"),
        "axis_statuses": diagnostic.get("axis_statuses", {}),
        "stored_cas_diagnostic_only": valid_diagnostic,
        "claim_promotion_cas_eligible": False,
    }


def build_payload() -> dict:
    cas_status = _cas_status()
    if cas_status["contract_sha256"] != _sha(CONTRACT):
        raise SystemExit("stored CAS envelopes are bound to a different contract hash")
    oracle = run_oracle()
    aggregate = cas_status["aggregate_status"]
    if not oracle["all_consistent"]:
        terminal = "INVARIANT_ORACLE_BLOCKED_ENGINE_OR_ANCHOR_MISMATCH"
    else:
        terminal = TERMINALS.get(
            aggregate, "INVARIANT_ORACLE_BLOCKED_ENGINE_OR_ANCHOR_MISMATCH"
        )
    baseline = None
    for line in SPEC.read_text().splitlines():
        if line.startswith("baseline_commit:"):
            baseline = line.split(":", 1)[1].strip()
    envelopes = {}
    for axis in AXES:
        path = REPO / f"docs/generated/pr175_cas/axis_result_{axis}.json"
        envelope = json.loads(path.read_text())
        if envelope["contract_sha256"] != cas_status["contract_sha256"]:
            raise SystemExit(f"{axis} envelope contract binding drifted")
        envelopes[axis] = {
            "path": path.relative_to(REPO).as_posix(),
            "sha256": _sha(path),
            "status": envelope["status"],
        }
    # Raw float gaps are deterministic on a fixed runtime (disclosed in
    # runtime_identity); a runtime change fails --check visibly.
    types = {}
    max_gap = 0.0
    for name, row in oracle["types"].items():
        gap = float(row["engine_gap_abs"])
        max_gap = max(max_gap, gap)
        types[name] = {
            "anchor": row["anchor"],
            "engine_a_exact": row["engine_a_exact"],
            "engine_b_gap_abs": gap,
            "engines_agree": row["engines_agree"],
            "anchor_match": row["anchor_match"],
        }
    metadata = {
        "owner": "COMMON",
        "implementation_scope": ["common"],
        "claim_tier": "exploratory",
        "claim_level": {"scheme": "roadmap_rescue_v1", "level": "C2"},
        "scientific_artifact_mode": "hypothesis_only",
        "public_use": False,
        "transfer_source": "none",
        "config_hash": cas_status["contract_sha256"],
        "spec_sha256": _sha(SPEC),
        "contract_sha256": cas_status["contract_sha256"],
        "engine_b_tolerance_abs": ENGINE_B_TOL,
        "generating_command": (
            "env PYTHONHASHSEED=0 venv/bin/python -B "
            "scripts/codex_harness/run_pr175_invariant_card.py --write"
        ),
        "git_commit": baseline,
        "git_commit_semantics": (
            "baseline commit pinned by the frozen spec at generation time"
        ),
        "runtime_identity": {
            "python": sys.version.split()[0],
            "numpy": np.__version__,
            "platform": sys.platform,
        },
    }
    return {
        "schema": "htt.pr175.result_card.v1",
        "pr_id": "PR-175",
        "metadata": metadata,
        "terminal": terminal,
        "cas": {
            "contract_id": "CAS-PR175-INVARIANT-001",
            "contract_path": CONTRACT.relative_to(REPO).as_posix(),
            "contract_sha256": cas_status["contract_sha256"],
            "aggregate_status": aggregate,
            "historical_aggregate_status": cas_status[
                "historical_aggregate_status"
            ],
            "axis_statuses": cas_status["axis_statuses"],
            "stored_cas_diagnostic_only": cas_status[
                "stored_cas_diagnostic_only"
            ],
            "claim_promotion_cas_eligible": False,
            "adjudication_path": ADJUDICATION.relative_to(REPO).as_posix(),
            "adjudication_sha256": _sha(ADJUDICATION),
            "axis_envelopes": envelopes,
        },
        "oracle": {
            "types": types,
            "max_engine_gap_abs": max_gap,
            "engine_b_lineage": (
                "coordinate realization via ad-matrix exponentials, "
                "complex-step first derivatives, central-difference "
                "second step (disclosed)"
            ),
            "axis_verification_depth": (
                "sympy/sage/wolfram axes reproduce the full Koszul "
                "chain; the lean axis machine-checks the closed "
                "rational anchor arithmetic, class-B reconstruction "
                "constraint, and table-bound h-relations only "
                "(disclosed depth asymmetry)"
            ),
            "anchor_lineage": (
                "Ellis-MacCallum 1969 / Wainwright-Ellis formula, "
                "identifiers transcribed, not verified against print; "
                "textbook sanity points IX (round S^3, R*=3/2) and "
                "V (unit H^3, R*=-6) confirmed"
            ),
        },
        "forbidden_claims_reaffirmed": [
            "no Bianchi family identification, ranking, or atlas matching",
            "no geometry measurement or observational claim",
            "no native-solver or transfer validation claim",
            "no promotion beyond roadmap_rescue_v1:C2 hypothesis_only",
        ],
    }


def _render(payload: dict) -> bytes:
    return (json.dumps(payload, sort_keys=True, indent=1) + "\n").encode()


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
    if not CARD.exists() or CARD.read_bytes() != _render(payload):
        print(
            json.dumps(
                {
                    "mode": "check",
                    "ok": False,
                    "read_only": True,
                    "terminal": payload["terminal"],
                    "aggregate": payload["cas"]["aggregate_status"],
                },
                sort_keys=True,
            )
        )
        return 1
    print(json.dumps({"mode": "check", "ok": True, "read_only": True,
                      "terminal": payload["terminal"]}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
