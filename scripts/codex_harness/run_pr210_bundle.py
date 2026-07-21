"""PR-210 runner: typed DefectBundle constitution + defect-identity seal."""

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

from common.revival_defect_bundle import (  # noqa: E402
    BridgeReceipt,
    BundleError,
    ComponentState,
    Epoch,
    Frame,
    combine,
    comparator_value,
    require_common_frame,
)

SPEC = REPO / "docs/research_program/revival/pr210_spec.yaml"
CARD = REPO / "docs/generated/pr210_result_card.json"


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _defect_identity_seal() -> dict:
    """P2 second lineage: derive x_C = Sigma2 - W2 + Omega_tilt + dOk symbolically."""
    Om, Ol, Ot, S2, W2, Okref, dOk = sp.symbols("Om Ol Ot S2 W2 Okref dOk")
    Of = sp.Symbol("Of")
    Ok = Okref + dOk
    # tilted parent identity: 1 = Om + Ol + Ok + Ot + S2 - W2
    Om_expr = sp.solve(sp.Eq(1, Om + Ol + Ok + Ot + S2 - W2), Om)[0]
    # FLRW comparator: 1 = Of + Ol + Okref
    Of_expr = sp.solve(sp.Eq(1, Of + Ol + Okref), Of)[0]
    derived = sp.expand(Of_expr - Om_expr)
    target = S2 - W2 + Ot + dOk
    ok = sp.simplify(derived - target) == 0
    return {"derived": str(derived), "target": str(target), "seal_pass": bool(ok)}


def _typed_gates() -> dict:
    e = Epoch(redshift=0.0)
    g = ComponentState(0.02, 0.005, 0.01, -0.003, Frame.NORMAL, e)
    xc = comparator_value(g)
    xc_ok = abs(xc - 0.022) < 1e-15

    def raises(fn) -> bool:
        try:
            fn()
            return False
        except BundleError:
            return True

    frame_mix = raises(lambda: require_common_frame(
        g, ComponentState(0.01, 0, 0.001, 0, Frame.MATTER, e)))
    neg_mag = raises(lambda: ComponentState(-1, 0, 0, 0, Frame.NORMAL, e).validate())
    epoch_mix = raises(lambda: combine([
        g, ComponentState(0.01, 0, 0.001, 0, Frame.NORMAL, Epoch(redshift=1.0))]))
    unbridged = raises(lambda: combine([
        g, ComponentState(0.01, 0, 0.001, 0, Frame.MATTER, e)]))
    # a valid bridge lets the frame-mixed combine through
    good_bridge = BridgeReceipt("B1", Frame.MATTER, Frame.NORMAL, {"beta_max": 1e-2},
                                "CERTIFIED", "prov:deadbeef")
    bridged_ok = True
    try:
        combine([g, ComponentState(0.01, 0, 0.001, 0, Frame.MATTER, e)], (good_bridge,))
    except BundleError:
        bridged_ok = False
    # an uncertified bridge is rejected
    bad_bridge = BridgeReceipt("B2", Frame.MATTER, Frame.NORMAL, {}, "PENDING", "")
    bad_rejected = raises(lambda: combine([
        g, ComponentState(0.01, 0, 0.001, 0, Frame.MATTER, e)], (bad_bridge,)))
    return {
        "xC": xc, "xC_matches_0p022": xc_ok,
        "frame_mix_rejected": frame_mix, "negative_magnitude_rejected": neg_mag,
        "epoch_mix_rejected": epoch_mix, "unbridged_frame_combine_rejected": unbridged,
        "certified_bridge_combine_ok": bridged_ok, "uncertified_bridge_rejected": bad_rejected,
    }


def build_payload() -> dict:
    seal = _defect_identity_seal()
    gates = _typed_gates()
    ok = (seal["seal_pass"] and gates["xC_matches_0p022"]
          and gates["frame_mix_rejected"] and gates["negative_magnitude_rejected"]
          and gates["epoch_mix_rejected"] and gates["unbridged_frame_combine_rejected"]
          and gates["certified_bridge_combine_ok"] and gates["uncertified_bridge_rejected"])
    terminal = "TYPED_DEFECT_BUNDLE_CONSTITUTION_CERTIFIED" if ok else "BLOCKED_BUNDLE_GATE_FAILURE"
    return {
        "schema": "htt.pr210.result_card.v1",
        "pr_id": "PR-210",
        "metadata": {
            "owner": "COMMON",
            "spec_sha256": _sha(SPEC),
            "claim_level": {"scheme": "roadmap_rescue_v1", "level": "C1"},
            "public_use": False,
            "readiness_state": "EVIDENCE_READY",
            "independence_gate": "OPEN",
            "generating_command": (
                "env PYTHONHASHSEED=0 venv/bin/python -B "
                "scripts/codex_harness/run_pr210_bundle.py --write"
            ),
        },
        "result": {"defect_identity_seal": seal, "typed_gates": gates},
        "terminal": terminal,
        "forbidden_claims_reaffirmed": [
            "frame/epoch-mixed components are never combined without a validated bridge",
            "DeltaOmega_k is a signed carrier, never forced to a PSD magnitude here",
            "the scalar comparator is one projection of a typed bundle, not the bundle itself",
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
