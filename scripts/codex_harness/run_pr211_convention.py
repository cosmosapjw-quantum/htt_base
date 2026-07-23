"""PR-211 runner: W2 convention successor + signed curvature split (RESCUE)."""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

import sympy as sp

REPO = Path(__file__).resolve().parents[2]
for entry in (str(REPO / "htt"), str(REPO / "htt" / "src")):
    if entry not in sys.path:
        sys.path.insert(0, entry)

from common.revival_w2_convention import (  # noqa: E402
    assert_dual_identity,
    crossref_pr186,
    force_psd_would_lose_sign,
    signed_delta_omega_k,
    w2_ceiling,
    w2_from_tensor,
    w2_from_vector,
)

SPEC = REPO / "docs/research_program/revival/pr211_spec.yaml"
CARD = REPO / "docs/generated/pr211_result_card.json"


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _sympy_seal() -> dict:
    ov, H = sp.symbols("omega_vec_sq H", positive=True)
    ot = 2 * ov  # omega_ab omega^ab = 2 omega_a omega^a
    lhs = sp.simplify(ot / (6 * H**2))
    rhs = sp.simplify(ov / (3 * H**2))
    ok = sp.simplify(lhs - rhs) == 0
    retired = sp.simplify((ov / H**2) / rhs)  # the retired /H^2 form is 3x
    return {"tensor_form": str(lhs), "vector_form": str(rhs),
            "retired_over_correct": str(retired), "seal_pass": bool(ok)}


def _successor_gate() -> dict:
    # numeric dual identity at a physical scale
    H = 70.0
    ov = 1.7e-6
    ot = 2 * ov
    dual_ok = True
    try:
        assert_dual_identity(ot, ov, H)
    except ValueError:
        dual_ok = False
    # mutation: wrong /H^2 vector form breaks the identity vs tensor form
    wrong_mismatch = abs((ov / (H * H)) - w2_from_tensor(ot, H)) > 1e-13
    tensor_eq_vector = abs(w2_from_tensor(ot, H) - w2_from_vector(ov, H)) < 1e-18
    ceiling_ok = abs(w2_ceiling(2.0) - 6.0) < 1e-15
    return {"dual_identity_holds": dual_ok, "wrong_over_h2_mismatch_detected": wrong_mismatch,
            "tensor_equals_vector": tensor_eq_vector, "ceiling_3half_bsq_ok": ceiling_ok}


def _signed_split_gate() -> dict:
    neg = signed_delta_omega_k(-0.004)
    pos = signed_delta_omega_k(0.004)
    sign_kept = neg < 0 < pos
    psd_forcing_caught = force_psd_would_lose_sign(-0.004) and not force_psd_would_lose_sign(0.004)
    return {"delta_omega_k_signed": sign_kept, "psd_forcing_would_lose_sign_detected": psd_forcing_caught}


def build_payload() -> dict:
    seal = _sympy_seal()
    succ = _successor_gate()
    split = _signed_split_gate()
    xref = crossref_pr186()
    ok = (seal["seal_pass"] and all(succ.values()) and all(split.values())
          and xref["frozen_unchanged"] and xref["ratio_is_three"]
          and xref["cas_five_axis_pass"])
    terminal = ("W2_CONVENTION_SUCCESSOR_CERTIFIED_PR186_FROZEN_UNCHANGED"
                if ok else "BLOCKED_CONVENTION_GATE_FAILURE")
    return {
        "schema": "htt.pr211.result_card.v1",
        "pr_id": "PR-211",
        "metadata": {
            "owner": "COMMON",
            "spec_sha256": _sha(SPEC),
            "disposition": "LITERAL_RESCUE",
            "cross_references": ["PR-186", "PR-127", "PR-187"],
            "claim_level": {"scheme": "roadmap_rescue_v1", "level": "C1"},
            "public_use": False,
            "readiness_state": "EVIDENCE_READY",
            "independence_gate": "OPEN",
            "generating_command": (
                "env PYTHONHASHSEED=0 venv/bin/python -B "
                "scripts/codex_harness/run_pr211_convention.py --write"
            ),
        },
        "result": {"sympy_dual_seal": seal, "successor_gate": succ,
                   "signed_curvature_split": split, "pr186_crossref": xref},
        "terminal": terminal,
        "forbidden_claims_reaffirmed": [
            "no anchor is recomputed or re-frozen; PR-186 W2_max stays byte-identical",
            "the omega-vector form must equal the tensor form; the retired /H^2 form is 3x wrong",
            "DeltaOmega_k is a signed carrier; forcing it to a PSD magnitude is a defect",
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
