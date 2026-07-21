"""PR-184 runner: premise-complete B-projector contract result card.

--write produces docs/generated/pr184_result_card.json; --check
recomputes and byte-compares. The frozen production adapter's sha must
still equal the PR-172-pinned value (documented-not-edited guarantee)
or the run fails closed.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "htt" / "src"))

from common.pr184_axisym_contract import run_adjudication  # noqa: E402

SPEC = REPO / "docs/research_program/long_horizon_rescue/pr184_spec.yaml"
CARD = REPO / "docs/generated/pr184_result_card.json"
ADAPTER = REPO / "htt/bass/los/b_mode_projector.py"
PR172_PINNED_ADAPTER_SHA = (
    "4f0268892e59c0145e59e822fb9d6d1828fbb375f8a3d67d5fbb170cae6dacdf"
)


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def build_payload() -> dict:
    adapter_sha = _sha(ADAPTER)
    if adapter_sha != PR172_PINNED_ADAPTER_SHA:
        raise SystemExit(
            "frozen production adapter drifted from the PR-172 pin — "
            "PR-184 kill condition"
        )
    adjudication = run_adjudication()
    baseline = None
    for line in SPEC.read_text().splitlines():
        if line.startswith("baseline_commit:"):
            baseline = line.split(":", 1)[1].strip()
    metadata = {
        "owner": "COMMON",
        "implementation_scope": ["common"],
        "claim_tier": "exploratory",
        "claim_level": {"scheme": "roadmap_rescue_v1", "level": "C1"},
        "scientific_artifact_mode": "standard_internal",
        "public_use": False,
        "transfer_source": "none",
        "config_hash": adapter_sha,
        "spec_sha256": _sha(SPEC),
        "frozen_adapter_sha256": adapter_sha,
        "generating_command": (
            "env PYTHONHASHSEED=0 venv/bin/python -B "
            "scripts/codex_harness/run_pr184_axisym_contract.py --write"
        ),
        "git_commit": baseline,
    }
    return {
        "schema": "htt.pr184.result_card.v1",
        "pr_id": "PR-184",
        "metadata": metadata,
        "adjudication": adjudication,
        "terminal": adjudication["terminal"],
        "forbidden_claims_reaffirmed": [
            "PR-172's falsification and terminal are never relabeled",
            "no physical-parity or observational statement",
            "full spin-harmonic parity action stays UNDERDEFINED_NOT_TESTED",
            "no Bianchi-family or geometry content",
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
    print(json.dumps({"mode": "check", "ok": True, "read_only": True,
                      "terminal": payload["terminal"]}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
