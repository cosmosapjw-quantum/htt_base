"""PR-187 runner: frame/type algebra gate battery + CAS status (--write/--check)."""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
from fractions import Fraction
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
for entry in (str(REPO / "htt"), str(REPO / "htt" / "src")):
    if entry not in sys.path:
        sys.path.insert(0, entry)

from common.frame_typed_algebra import (  # noqa: E402
    FrameTypeError,
    Typed,
    bridge,
    forbidden_omega_tilt_squared_subtraction,
    kinematic_quadrupole_leading_order,
    omega_tilt_antipodal_pair,
    omega_tilt_leading_order,
    omega_tilt_single_stream,
    omega_tilt_squared_order,
    order_correct_deprojection_order,
    psd_positive_block_only,
    rapidity_roundtrip_residual,
)

SPEC = REPO / "docs/research_program/strengthening/pr187_spec.yaml"
CARD = REPO / "docs/generated/pr187_result_card.json"
CAS_CONTRACT = REPO / "docs/generated/pr187_cas/CAS_CONTRACT_PR187_FRAME_ORDER.json"
CAS_AXIS_RESULTS = tuple(
    REPO / f"docs/generated/pr187_cas/axis_result_{axis}.json"
    for axis in ("wolfram_xact", "sympy", "sage_singular", "lean", "rocq")
)


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _roundtrip_residuals() -> list[str]:
    betas = [Fraction(0), Fraction(1), Fraction(-3), Fraction(1, 2),
             Fraction(-7, 5), Fraction(123, 17)]
    return [str(rapidity_roundtrip_residual(b)) for b in betas]


def _mutation_battery() -> dict:
    """50 wrong-frame / wrong-order / signed-clip mutations; each must raise."""
    rejected = 0
    total = 0
    sig2_n = Typed("Sigma2", Fraction(1, 100), "n", order=None)
    w2_u = Typed("W2", Fraction(1, 1000), "u", order=None)
    a_v = Typed("A_v", Fraction(1, 10), "obs", order=1)
    om = Typed("Omega_tilt", Fraction(1, 50), "u", order=2)
    for i in range(50):
        m = i % 5
        try:
            if m == 0:  # cross-frame add (n + u)
                _ = sig2_n + w2_u
            elif m == 1:  # cross-frame add (obs + u)
                _ = a_v + om
            elif m == 2:  # order mismatch add (order1 + order2 in same frame)
                _ = Typed("x", Fraction(1, 7), "u", order=1) + om
            elif m == 3:  # negative in the positive block
                _ = Typed("Sigma2_bad", Fraction(-1, 3), "n")
            else:  # cross-frame conversion without a registered bridge
                _ = bridge(sig2_n, "obs")  # n->obs unregistered
            total += 1  # reached here => NOT rejected
        except FrameTypeError:
            total += 1
            rejected += 1
    return {"total": total, "rejected": rejected}


def _psd_signed() -> dict:
    pos = psd_positive_block_only({
        "Sigma2": Fraction(1, 10), "W2": Fraction(1, 100),
        "Omega_tilt": Fraction(1, 50), "DeltaOmega_k": Fraction(-3, 7),
    })
    neg = psd_positive_block_only({
        "Sigma2": Fraction(1, 10), "DeltaOmega_k": Fraction(5, 9),
    })
    # PSD-clip of a negative positive-block value must raise
    clipped = False
    try:
        psd_positive_block_only({"Sigma2": Fraction(-1, 2)})
    except FrameTypeError:
        clipped = True
    return {
        "negative_branch_sign": pos["delta_omega_k_sign"],
        "positive_branch_sign": neg["delta_omega_k_sign"],
        "psd_clips_signed_axis": pos["psd_clips_signed_axis"],
        "negative_positive_block_rejected": clipped,
        "carrier": pos["carrier"],
    }


def _pair_density() -> dict:
    w, om_m, b2 = Fraction(0), Fraction(3, 10), Fraction(1, 1000)
    single = omega_tilt_single_stream(w, om_m, b2)
    pair_total = omega_tilt_antipodal_pair(w, om_m, b2, fixed_total_density=True)
    pair_per = omega_tilt_antipodal_pair(w, om_m, b2, fixed_total_density=False)
    return {
        "single_value": str(single.value),
        "pair_total_density_value": str(pair_total.value),
        "pair_per_stream_density_value": str(pair_per.value),
        "total_equals_single": pair_total.value == single.value,
        "per_stream_doubles": pair_per.value == 2 * single.value,
        "single_order": single.order,
    }


def _cas_status() -> dict:
    contract_sha = _sha(CAS_CONTRACT)
    completed = subprocess.run(
        [
            sys.executable,
            "-B",
            ".agent-harness/scripts/cas_gate.py",
            "adjudicate",
            "--contract",
            str(CAS_CONTRACT.relative_to(REPO)),
            "--results",
            *(str(path.relative_to(REPO)) for path in CAS_AXIS_RESULTS),
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
    stored_cas_diagnostic_only = (
        completed.returncode == 2
        and diagnostic.get("aggregate_status") == "CAS_BLOCKED"
        and diagnostic.get("claim_promotion_cas_eligible") is False
        and diagnostic.get("evidence_origin") == "stored_axis_result_envelopes"
    )
    return {
        "contract": "docs/generated/pr187_cas/CAS_CONTRACT_PR187_FRAME_ORDER.json",
        "contract_sha256": contract_sha,
        "contract_hash_matches_adjudication": (
            stored_cas_diagnostic_only
            and diagnostic.get("contract_sha256") == contract_sha
        ),
        "aggregate": "CAS_BLOCKED",
        "historical_aggregate": diagnostic.get("historical_aggregate_status"),
        "required_axes": diagnostic.get("required_axes", []),
        "axis_statuses": diagnostic.get("axis_statuses", {}),
        "stored_cas_diagnostic_only": stored_cas_diagnostic_only,
        "claim_promotion_cas_eligible": False,
        "kernel_independent_lineages": ["lean", "rocq"],
    }


def build_payload() -> dict:
    residuals = _roundtrip_residuals()
    mutations = _mutation_battery()
    psd = _psd_signed()
    pair = _pair_density()
    cas = _cas_status()

    order_facts = {
        "omega_tilt_order": omega_tilt_leading_order(),
        "quadrupole_order": kinematic_quadrupole_leading_order(),
        "omega_tilt_squared_order": omega_tilt_squared_order(),
        "forbidden_omega_tilt_squared_subtraction": (
            forbidden_omega_tilt_squared_subtraction()
        ),
        "order_correct_deprojection_order": order_correct_deprojection_order(),
    }

    all_ok = (
        all(r == "0" for r in residuals)
        and mutations["rejected"] == mutations["total"] == 50
        and psd["psd_clips_signed_axis"] is False
        and psd["negative_positive_block_rejected"] is True
        and psd["negative_branch_sign"] == -1
        and order_facts["forbidden_omega_tilt_squared_subtraction"] is True
        and order_facts["order_correct_deprojection_order"] == 2
        and pair["total_equals_single"] and pair["per_stream_doubles"]
        and cas["aggregate"] == "CAS_5AXIS_PASS"
        and cas["contract_hash_matches_adjudication"]
    )
    terminal = (
        "FRAME_TYPE_SYSTEM_CAS_5AXIS_PASS"
        if all_ok else "BLOCKED_FRAME_TYPE_GATE_FAILURE"
    )

    return {
        "schema": "htt.pr187.result_card.v1",
        "pr_id": "PR-187",
        "metadata": {
            "owner": "COMMON",
            "spec_sha256": _sha(SPEC),
            "claim_level": {"scheme": "roadmap_rescue_v1", "level": "C1"},
            "public_use": False,
            "readiness_state": "EVIDENCE_READY",
            "independence_gate": "OPEN",
            "generating_command": (
                "env PYTHONHASHSEED=0 venv/bin/python -B "
                "scripts/codex_harness/run_pr187_frame_typed.py --write"
            ),
        },
        "result": {
            "rapidity_roundtrip_residuals": residuals,
            "roundtrip_all_zero": all(r == "0" for r in residuals),
            "mutation_battery": mutations,
            "mutations_all_rejected": mutations["rejected"] == mutations["total"],
            "signed_carrier": psd,
            "order_facts": order_facts,
            "pair_density": pair,
            "cas_status": cas,
        },
        "terminal": terminal,
        "forbidden_claims_reaffirmed": [
            "no implicit cast or default frame; cross-frame only via a registered bridge",
            "DeltaOmega_k is signed on S+^3 x R and never PSD-clipped",
            "Omega_tilt^2 (O(beta^4)) is refused against the O(beta^2) quadrupole",
            "no comparator number is regenerated here; the type system guards them",
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
        print(
            "refusing to overwrite the frozen historical result card without "
            "a new parent-observed cas_gate.py run-adjudicate execution",
            file=sys.stderr,
        )
        return 2
    ok = CARD.exists() and CARD.read_bytes() == _render(payload)
    print(json.dumps({"mode": "check", "ok": ok, "read_only": True,
                      "terminal": payload["terminal"]}, sort_keys=True))
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
