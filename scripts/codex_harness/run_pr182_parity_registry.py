"""PR-182 runner: parity-theorem + handedness-registry result card.

Modes: --write (produce docs/generated/pr182_result_card.json) and
--check (recompute + byte-compare, read-only). The card binds the frozen
spec, the CAS contract, all four sealed axis envelopes, and the
adjudication, and re-derives the terminal from the adjudication bytes —
the terminal is never hand-set.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "htt" / "src"))

from common.pr182_parity_registry import registry_payload  # noqa: E402

SPEC = REPO / "docs/research_program/long_horizon_rescue/pr182_spec.yaml"
CONTRACT = REPO / "docs/generated/pr182_cas/CAS_CONTRACT_PR182_PARITY_V2.json"
ADJUDICATION = REPO / "docs/generated/pr182_cas_adjudication.json"
CARD = REPO / "docs/generated/pr182_result_card.json"
AXES = ("sympy", "sage_singular", "wolfram_xact", "lean")

TERMINALS = {
    "CAS_4AXIS_PASS": "PARITY_IDENTITIES_CAS_4AXIS_PASS_REGISTRY_REGISTERED",
    "CAS_BLOCKED": "PARITY_IDENTITIES_CAS_BLOCKED_REGISTRY_REGISTERED",
    "CAS_FAIL": "PARITY_IDENTITIES_CAS_FAIL_REGISTRY_WITHHELD",
}


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def build_payload() -> dict:
    adjudication = json.loads(ADJUDICATION.read_text())
    aggregate = adjudication["aggregate_status"]
    terminal = TERMINALS.get(aggregate, "PARITY_IDENTITIES_CAS_FAIL_REGISTRY_WITHHELD")
    contract = json.loads(CONTRACT.read_text())
    if adjudication["contract_sha256"] != _sha(CONTRACT):
        raise SystemExit("adjudication is bound to a different contract hash")
    baseline = None
    for line in SPEC.read_text().splitlines():
        if line.startswith("baseline_commit:"):
            baseline = line.split(":", 1)[1].strip()
    envelopes = {}
    for axis in AXES:
        path = REPO / f"docs/generated/pr182_cas/axis_result_{axis}.json"
        envelope = json.loads(path.read_text())
        if envelope["contract_sha256"] != adjudication["contract_sha256"]:
            raise SystemExit(f"{axis} envelope contract binding drifted")
        envelopes[axis] = {
            "path": path.relative_to(REPO).as_posix(),
            "sha256": _sha(path),
            "status": envelope["status"],
        }
    registry = registry_payload()
    include_registry = aggregate in {"CAS_4AXIS_PASS", "CAS_BLOCKED"}
    metadata = {
        "owner": "COMMON",
        "implementation_scope": ["common"],
        "claim_tier": "exploratory",
        "claim_level": {"scheme": "roadmap_rescue_v1", "level": "C1"},
        "scientific_artifact_mode": "hypothesis_only",
        "public_use": False,
        "transfer_source": "none",
        "config_hash": adjudication["contract_sha256"],
        "spec_sha256": _sha(SPEC),
        "contract_sha256": adjudication["contract_sha256"],
        "generating_command": (
            "env PYTHONHASHSEED=0 venv/bin/python -B "
            "scripts/codex_harness/run_pr182_parity_registry.py --write"
        ),
        "git_commit": baseline,
        "git_commit_semantics": (
            "baseline commit pinned by the frozen spec at generation time; "
            "byte-stable so --check stays commit-independent"
        ),
    }
    return {
        "schema": "htt.pr182.result_card.v1",
        "pr_id": "PR-182",
        "metadata": metadata,
        "terminal": terminal,
        "cas": {
            "contract_id": contract["identity"]["contract_id"],
            "contract_path": CONTRACT.relative_to(REPO).as_posix(),
            "contract_sha256": adjudication["contract_sha256"],
            "aggregate_status": aggregate,
            "axis_statuses": adjudication["axis_statuses"],
            "adjudication_path": ADJUDICATION.relative_to(REPO).as_posix(),
            "adjudication_sha256": _sha(ADJUDICATION),
            "axis_envelopes": envelopes,
            "blinding": "sibling_results_read == [] on every envelope; "
            "contract hash frozen before sealed envelope generation",
        },
        "registry": registry if include_registry else {
            "schema": registry["schema"],
            "entries": [],
            "withheld_reason": "CAS_FAIL withholds the registry per spec",
        },
        "forbidden_claims_reaffirmed": [
            "no present-data family identification, ranking, or handedness conclusion",
            "no detection/anisotropy/isotropy/geometry claim",
            "no native-solver or transfer validation claim",
            "no promotion beyond roadmap_rescue_v1:C1 hypothesis_only",
            "a registered-exception pass is never described as a 4-axis pass",
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
        CARD.write_bytes(_render(payload))
        print(f"wrote {CARD.relative_to(REPO)}")
        return 0
    if not CARD.exists() or CARD.read_bytes() != _render(payload):
        print(f"artifact differs under --check: {CARD.relative_to(REPO)}")
        return 1
    print(
        json.dumps(
            {
                "mode": "check",
                "ok": True,
                "read_only": True,
                "terminal": payload["terminal"],
                "aggregate": payload["cas"]["aggregate_status"],
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
