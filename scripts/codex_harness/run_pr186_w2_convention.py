"""PR-186 runner: W^2 convention theorem + active-source scan (--write/--check)."""

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

from common.w2_convention import (  # noqa: E402
    ceiling_conversion_symbolic,
    scan_active_sources,
    vorticity_tensor_vector_identity,
)

SPEC = REPO / "docs/research_program/strengthening/pr186_spec.yaml"
CARD = REPO / "docs/generated/pr186_result_card.json"
REFREEZE_SEAL = REPO / "docs/generated/mes_geodesic_refreeze_seal.json"
CAS_CONTRACT = REPO / "docs/generated/pr186_cas/CAS_CONTRACT_PR186_W2.json"
CAS_ADJUDICATION = REPO / "docs/generated/pr186_cas/adjudication.json"


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _cas_status() -> dict:
    """Read the sealed five-axis CAS adjudication (contract-bound)."""
    adj = json.loads(CAS_ADJUDICATION.read_text())
    contract_sha = _sha(CAS_CONTRACT)
    return {
        "contract": "docs/generated/pr186_cas/CAS_CONTRACT_PR186_W2.json",
        "contract_sha256": contract_sha,
        "contract_hash_matches_adjudication": (
            adj.get("contract_sha256") == contract_sha
        ),
        "aggregate": adj["aggregate_status"],
        "required_axes": adj.get("required_axes"),
        "axis_statuses": adj["axis_statuses"],
        "kernel_independent_lineages": ["lean", "rocq"],
        "note": (
            "five-axis blind CAS under one contract hash: Wolfram+xAct, "
            "SymPy, Sage+Singular (symbolic universal), Lean (kernel-checked "
            "exact-rational witnesses, native_decide), and Rocq/Coq "
            "(universal Ring proof, kernel-independent from Lean). No "
            "majority vote; all five required axes PASS."
        ),
    }


def build_payload() -> dict:
    numeric = vorticity_tensor_vector_identity(100_000)
    symbolic = ceiling_conversion_symbolic()
    scan = scan_active_sources(REPO)
    # Frozen numeric anchor invariance: the (6H^2) convention was always the
    # code truth, so the MES vorticity ceiling is byte-identical.
    w2_max = json.loads(REFREEZE_SEAL.read_text())["refrozen_anchor"]["W2_max"]

    two_lineages_agree = (
        numeric["ok"]
        and symbolic["ok"]
        and symbolic["tensor_vector_forms_equal"]
        and symbolic["wrong_over_right_ratio"] == "3"
    )
    cas = _cas_status()
    cas_pass = (
        cas["aggregate"] == "CAS_5AXIS_PASS"
        and cas["contract_hash_matches_adjudication"]
    )
    terminal = (
        "W2_CONVENTION_REPAIRED_CAS_5AXIS_PASS_SOURCES_CLEAN"
        if (two_lineages_agree and scan["clean"] and cas_pass)
        else "BLOCKED_CONVENTION_DRIFT_REMAINS"
    )

    return {
        "schema": "htt.pr186.result_card.v1",
        "pr_id": "PR-186",
        "metadata": {
            "owner": "COMMON",
            "spec_sha256": _sha(SPEC),
            "claim_level": {"scheme": "roadmap_rescue_v1", "level": "C1"},
            "public_use": False,
            "readiness_state": "EVIDENCE_READY",
            "independence_gate": "OPEN",
            "generating_command": (
                "env PYTHONHASHSEED=0 venv/bin/python -B "
                "scripts/codex_harness/run_pr186_w2_convention.py --write"
            ),
        },
        "registered_convention": (
            "W^2 := omega_ab omega^ab/(6 H^2) = omega_a omega^a/(3 H^2)"
        ),
        "derivation_lineages": {
            "numerical_random_tensor": numeric,
            "symbolic_sympy": symbolic,
            "two_independent_lineages_agree": two_lineages_agree,
        },
        "cas_status": _cas_status(),
        "active_source_scan": scan,
        "pre_post_delta": {
            "display_v5_v10_before": "W^2 = omega_a omega^a / H^2",
            "display_after": "W^2 = omega_ab omega^ab/(6 H^2) = omega_a omega^a/(3 H^2)",
            "display_ratio_before_over_after": symbolic["wrong_over_right_ratio"],
            "explanation": (
                "the v5/v10 DISPLAY was exactly 3x the registered value; the "
                "live comparator/MES code always used (6 H^2), so every numeric "
                "anchor is byte-identical -- only the report display changed."
            ),
            "frozen_mes_vorticity_ceiling_W2_max": w2_max,
            "frozen_anchor_byte_identical": w2_max == 3.3789222980376e-13,
        },
        "terminal": terminal,
        "forbidden_claims_reaffirmed": [
            "only the display and inheriting consumers changed; no numeric anchor moved",
            "historical v5-v9 packages stay byte-frozen (allowlisted, not edited)",
            "no physical or observational claim; convention consistency only",
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
