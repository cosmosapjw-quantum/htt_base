"""PR-212 runner: frame-indexed functor + Frobenius gate (RESCUE)."""

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

from common.revival_defect_bundle import Frame  # noqa: E402
from common.revival_frame_functor import (  # noqa: E402
    REGISTRY,
    FrameFunctorError,
    assemble,
    is_hypersurface_orthogonal,
    n_shear_u_w2_without_bridge_rejected,
    orthogonal_hypersurface_gauss_curvature,
)

SPEC = REPO / "docs/research_program/revival/pr212_spec.yaml"
CARD = REPO / "docs/generated/pr212_result_card.json"
PR187_CARD = REPO / "docs/generated/pr187_result_card.json"


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _gates() -> dict:
    def raises(fn) -> bool:
        try:
            fn()
            return False
        except FrameFunctorError:
            return True

    # Frobenius: vortical congruence has no orthogonal hypersurface
    ho_zero = is_hypersurface_orthogonal(0.0)
    ho_vortical = is_hypersurface_orthogonal(1e-6)
    gauss_zero_ok = abs(orthogonal_hypersurface_gauss_curvature(0.0, 0.7) - 0.7) < 1e-15
    gauss_vortical_rejected = raises(
        lambda: orthogonal_hypersurface_gauss_curvature(1e-6, 0.7))
    # frame-indexed assembly
    same_frame_ok = assemble([REGISTRY["sigma_ab"], REGISTRY["W2_n"]]) == Frame.NORMAL
    mixed_rejected = n_shear_u_w2_without_bridge_rejected()
    bridged_ok = True
    try:
        assemble([REGISTRY["sigma_ab"], REGISTRY["W2_u"]], bridged=True)
    except FrameFunctorError:
        bridged_ok = False
    return {
        "hypersurface_orthogonal_at_zero_vorticity": ho_zero,
        "not_hypersurface_orthogonal_when_vortical": not ho_vortical,
        "gauss_curvature_defined_at_zero_vorticity": gauss_zero_ok,
        "gauss_curvature_undefined_when_vortical_rejected": gauss_vortical_rejected,
        "same_frame_assembly_ok": same_frame_ok,
        "n_shear_u_w2_without_bridge_rejected": mixed_rejected,
        "bridged_cross_frame_assembly_ok": bridged_ok,
    }


def _crossref_pr187() -> dict:
    card = json.loads(PR187_CARD.read_text(encoding="utf-8"))
    return {"pr187_terminal": card.get("terminal"),
            "pr187_cas_five_axis": card.get("terminal") == "FRAME_TYPE_SYSTEM_CAS_5AXIS_PASS"}


def build_payload() -> dict:
    gates = _gates()
    xref = _crossref_pr187()
    ok = all(gates.values()) and xref["pr187_cas_five_axis"]
    terminal = ("FRAME_FUNCTOR_FROBENIUS_GATE_CERTIFIED_PR187_CONSISTENT"
                if ok else "BLOCKED_FRAME_FUNCTOR_GATE_FAILURE")
    return {
        "schema": "htt.pr212.result_card.v1",
        "pr_id": "PR-212",
        "metadata": {
            "owner": "COMMON",
            "spec_sha256": _sha(SPEC),
            "disposition": "LITERAL_RESCUE",
            "cross_references": ["PR-187", "PR-125", "KE-FRAME"],
            "claim_level": {"scheme": "roadmap_rescue_v1", "level": "C1"},
            "public_use": False,
            "readiness_state": "EVIDENCE_READY",
            "independence_gate": "OPEN",
            "generating_command": (
                "env PYTHONHASHSEED=0 venv/bin/python -B "
                "scripts/codex_harness/run_pr212_frame_functor.py --write"
            ),
        },
        "result": {"frobenius_and_assembly_gates": gates, "pr187_crossref": xref,
                   "symbol_registry": {k: {"frame": v.frame.value, "type": v.tensor_type}
                                       for k, v in REGISTRY.items()}},
        "terminal": terminal,
        "forbidden_claims_reaffirmed": [
            "a vortical congruence has no orthogonal-hypersurface Gauss curvature",
            "n-frame shear and u-frame W2 are never assembled without a registered bridge",
            "frame indexing is explicit; there is no implicit default frame",
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
