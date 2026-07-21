"""PR-223 runner: multi-fluid moment cone + five-axis CAS status."""

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

from common.revival_multifluid import (  # noqa: E402
    antipodal_pair,
    isotropic_same_trace_has_no_stress,
    moment_cone_samples,
)

SPEC = REPO / "docs/research_program/revival/pr223_spec.yaml"
CARD = REPO / "docs/generated/pr223_result_card.json"
CAS_CONTRACT = REPO / "docs/generated/pr223_cas/CAS_CONTRACT_PR223_MULTIFLUID.json"
CAS_ADJUDICATION = REPO / "docs/generated/pr223_cas/adjudication.json"


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _cas_status() -> dict:
    adj = json.loads(CAS_ADJUDICATION.read_text())
    contract_sha = _sha(CAS_CONTRACT)
    return {
        "contract": "docs/generated/pr223_cas/CAS_CONTRACT_PR223_MULTIFLUID.json",
        "contract_sha256": contract_sha,
        "contract_hash_matches_adjudication": adj.get("contract_sha256") == contract_sha,
        "aggregate": adj["aggregate_status"],
        "required_axes": adj.get("required_axes"),
        "axis_statuses": adj["axis_statuses"],
        "kernel_independent_lineages": ["lean", "rocq"],
    }


def build_payload() -> dict:
    pair = antipodal_pair()
    iso = isotropic_same_trace_has_no_stress(pair["trace"])
    cone = moment_cone_samples()
    cas = _cas_status()

    ok = (pair["zero_flux"] and pair["nonzero_tilt_energy"]
          and pair["nonzero_anisotropic_stress"]
          and pair["aniso_3Pi_diag"] == [4.0, -2.0, -2.0]
          and iso and cone["trace_always_nonnegative"]
          and cone["fraction_stress_at_zero_flux"] > 0.99
          and cas["aggregate"] == "CAS_5AXIS_PASS"
          and cas["contract_hash_matches_adjudication"])
    terminal = ("MULTIFLUID_MOMENT_CONE_CERTIFIED_CAS_5AXIS_PASS"
                if ok else "BLOCKED_MULTIFLUID_GATE_FAILURE")
    return {
        "schema": "htt.pr223.result_card.v1",
        "pr_id": "PR-223",
        "metadata": {
            "owner": "COMMON",
            "spec_sha256": _sha(SPEC),
            "claim_level": {"scheme": "roadmap_rescue_v1", "level": "C1"},
            "public_use": False,
            "readiness_state": "EVIDENCE_READY",
            "independence_gate": "OPEN",
            "generating_command": (
                "env PYTHONHASHSEED=0 venv/bin/python -B "
                "scripts/codex_harness/run_pr223_multifluid.py --write"
            ),
        },
        "result": {
            "antipodal_pair": pair,
            "isotropic_same_trace_has_no_stress": iso,
            "moment_cone": cone,
            "cas_status": cas,
        },
        "terminal": terminal,
        "forbidden_claims_reaffirmed": [
            "zero net flux never implies zero tilt energy or zero anisotropic stress",
            "the anisotropic stress, not the flux, distinguishes the antipodal pair from an isotropic comparator",
            "this is pre-solver moment mechanics; no native transfer is claimed",
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
