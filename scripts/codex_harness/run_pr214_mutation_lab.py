"""PR-214 runner: hermetic legacy mutation lab + clean-room replay."""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
for entry in (str(REPO / "htt"), str(REPO / "htt" / "src")):
    if entry not in sys.path:
        sys.path.insert(0, entry)

from common.revival_legacy_inventory import scan_no_direct_import  # noqa: E402
from common.revival_mutation_lab import (  # noqa: E402
    active_surface_clean,
    bianchi_class_swap_caught,
    factor_three_w2_caught,
    inactive_occam_caught,
    legacy_negative_controls_present,
    local_equals_global_caught,
)

SPEC = REPO / "docs/research_program/revival/pr214_spec.yaml"
CARD = REPO / "docs/generated/pr214_result_card.json"
DROP = REPO / "htt_legacy_revival_round2_20260721"


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def build_payload() -> dict:
    kill_matrix = {
        "factor_three_w2": factor_three_w2_caught(),
        "bianchi_vi0_viih_class_swap": bianchi_class_swap_caught() == {"VI0", "VIIh"},
        "inactive_parameter_occam": inactive_occam_caught(),
        "local_equals_global_bridge": local_equals_global_caught(),
    }
    active_hits = active_surface_clean()
    import_hits = scan_no_direct_import(REPO)
    neg_controls = legacy_negative_controls_present(DROP)

    ok = (all(kill_matrix.values()) and not active_hits and not import_hits)
    terminal = ("LEGACY_MUTATION_CORPUS_ALL_KILLED_ACTIVE_SURFACE_CLEAN"
                if ok else "BLOCKED_MUTATION_SURVIVED")
    return {
        "schema": "htt.pr214.result_card.v1",
        "pr_id": "PR-214",
        "metadata": {
            "owner": "COMMON",
            "spec_sha256": _sha(SPEC),
            "claim_level": {"scheme": "roadmap_rescue_v1", "level": "C1"},
            "public_use": False,
            "readiness_state": "EVIDENCE_READY",
            "independence_gate": "OPEN",
            "generating_command": (
                "env PYTHONHASHSEED=0 venv/bin/python -B "
                "scripts/codex_harness/run_pr214_mutation_lab.py --write"
            ),
        },
        "result": {
            "mutation_kill_matrix": kill_matrix,
            "all_mutations_killed": all(kill_matrix.values()),
            "active_surface_retired_number_hits": active_hits,
            "active_surface_clean": not active_hits,
            "direct_legacy_import_hits": import_hits,
            "legacy_negative_controls": neg_controls,
        },
        "terminal": terminal,
        "forbidden_claims_reaffirmed": [
            "wrong historical results are preserved as executable negative controls",
            "no retired legacy number is copied into an active revival module",
            "a mutation that survives blocks scientific promotion",
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
        CARD.write_bytes(_render(payload))
        print(f"wrote {CARD.name}; terminal={payload['terminal']}")
        return 0
    ok = CARD.exists() and CARD.read_bytes() == _render(payload)
    print(json.dumps({"mode": "check", "ok": ok, "read_only": True,
                      "terminal": payload["terminal"]}, sort_keys=True))
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
