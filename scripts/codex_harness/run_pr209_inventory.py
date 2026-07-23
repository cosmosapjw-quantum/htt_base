"""PR-209 runner: immutable legacy inventory + disposition + no-import scan."""

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

from common.revival_legacy_inventory import (  # noqa: E402
    adjudicate,
    archive_integrity,
    disposition_counts,
    load_ledger,
    scan_no_direct_import,
    verify_inventory,
)

SPEC = REPO / "docs/research_program/revival/pr209_spec.yaml"
LEDGER = REPO / "docs/generated/revival_legacy_disposition.json"
DROP = REPO / "htt_legacy_revival_round2_20260721"
CARD = REPO / "docs/generated/pr209_result_card.json"


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _independent_recompute(rows) -> bool:
    """P2 second implementation: recompute each present object's sha directly."""
    for r in rows:
        if not r.present:
            continue
        p = DROP / r.path
        if hashlib.sha256(p.read_bytes()).hexdigest() != r.actual_sha:
            return False
    return True


def build_payload() -> dict:
    ledger = load_ledger(LEDGER)
    drop_present = DROP.is_dir()
    rows = verify_inventory(ledger, DROP) if drop_present else []
    archives = archive_integrity(DROP, ledger) if drop_present else []
    counts = disposition_counts(ledger)
    import_hits = scan_no_direct_import(REPO)
    dispositions = sorted({adjudicate(it["disposition"]) for it in ledger})

    if not drop_present:
        terminal = "BLOCKED_MISSING_LEGACY_DROP"
        all_match = second_impl = archives_ok = False
    else:
        all_match = all(r.matches for r in rows)
        second_impl = _independent_recompute(rows)
        archives_ok = all(a.get("bad_crc") is None for a in archives)
        ok = (all_match and second_impl and archives_ok and not import_hits
              and set(dispositions) <= {"KEEP", "REBUILD", "MUTATION", "RETIRE"})
        terminal = "LEGACY_INVENTORY_HASH_BOUND_ZERO_DIRECT_IMPORT" if ok \
            else "BLOCKED_INVENTORY_GATE_FAILURE"

    return {
        "schema": "htt.pr209.result_card.v1",
        "pr_id": "PR-209",
        "metadata": {
            "owner": "COMMON",
            "spec_sha256": _sha(SPEC),
            "ledger_sha256": _sha(LEDGER),
            "claim_level": {"scheme": "roadmap_rescue_v1", "level": "C1"},
            "public_use": False,
            "readiness_state": "EVIDENCE_READY" if drop_present else "BLOCKED",
            "independence_gate": "OPEN",
            "generating_command": (
                "env PYTHONHASHSEED=0 venv/bin/python -B "
                "scripts/codex_harness/run_pr209_inventory.py --write"
            ),
        },
        "result": {
            "drop_present": drop_present,
            "n_objects": len(ledger),
            "inventory_all_match": all_match,
            "independent_recompute_agrees": second_impl,
            "archives_crc_ok": archives_ok,
            "archives": archives,
            "disposition_counts": counts,
            "disposition_classes": dispositions,
            "direct_legacy_import_hits": import_hits,
            "no_direct_import": not import_hits,
        },
        "terminal": terminal,
        "forbidden_claims_reaffirmed": [
            "legacy artifacts are immutable evidence, never production imports",
            "a legacy number is never copied into a new receipt",
            "MUTATION-class objects are negative controls, not conclusions",
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
