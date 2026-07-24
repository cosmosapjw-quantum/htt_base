"""PR-187 gates: frame/type algebra + signed carrier + order system (R3-CAS)."""

from __future__ import annotations

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

import pytest  # noqa: E402

from common.frame_typed_algebra import (  # noqa: E402
    FrameTypeError,
    Typed,
    bridge,
    forbidden_omega_tilt_squared_subtraction,
    psd_positive_block_only,
)
from scripts.codex_harness import run_pr187_frame_typed as runner  # noqa: E402

CARD = REPO / "docs/generated/pr187_result_card.json"
SPEC = REPO / "docs/research_program/strengthening/pr187_spec.yaml"
RUNNER = REPO / "scripts/codex_harness/run_pr187_frame_typed.py"


def _card() -> dict:
    return json.loads(CARD.read_text())


def test_spec_bound_and_terminal() -> None:
    c = _card()
    assert c["metadata"]["spec_sha256"] == hashlib.sha256(SPEC.read_bytes()).hexdigest()
    assert c["metadata"]["public_use"] is False
    assert c["metadata"]["independence_gate"] == "OPEN"
    assert c["terminal"] == "FRAME_TYPE_SYSTEM_CAS_5AXIS_PASS"


def test_roundtrip_and_mutations() -> None:
    r = _card()["result"]
    assert r["roundtrip_all_zero"] is True
    assert r["mutation_battery"]["rejected"] == r["mutation_battery"]["total"] == 50


def test_cross_frame_refused_without_bridge() -> None:
    n = Typed("Sigma2", Fraction(1, 10), "n")
    u = Typed("W2", Fraction(1, 100), "u")
    with pytest.raises(FrameTypeError):
        _ = n + u
    with pytest.raises(FrameTypeError):
        _ = bridge(n, "obs")  # n->obs not registered


def test_signed_carrier_not_psd_clipped() -> None:
    r = _card()["result"]["signed_carrier"]
    assert r["carrier"] == "S+^3 x R"
    assert r["psd_clips_signed_axis"] is False
    assert r["negative_branch_sign"] == -1
    assert r["negative_positive_block_rejected"] is True
    # a negative positive-block value is rejected
    with pytest.raises(FrameTypeError):
        psd_positive_block_only({"Sigma2": Fraction(-1, 5)})


def test_order_mismatch_forbids_omega_tilt_squared() -> None:
    of = _card()["result"]["order_facts"]
    assert of["omega_tilt_order"] == 2
    assert of["quadrupole_order"] == 2
    assert of["omega_tilt_squared_order"] == 4
    assert of["forbidden_omega_tilt_squared_subtraction"] is True
    assert of["order_correct_deprojection_order"] == 2
    assert forbidden_omega_tilt_squared_subtraction() is True


def test_pair_density_conventions_explicit() -> None:
    p = _card()["result"]["pair_density"]
    assert p["total_equals_single"] is True
    assert p["per_stream_doubles"] is True
    assert p["single_order"] == 2


def test_stored_five_axis_cas_is_diagnostic_only() -> None:
    cas = runner._cas_status()
    assert cas["aggregate"] == "CAS_BLOCKED"
    assert cas["historical_aggregate"] == "CAS_5AXIS_PASS"
    assert cas["stored_cas_diagnostic_only"] is True
    assert cas["claim_promotion_cas_eligible"] is False
    assert cas["contract_hash_matches_adjudication"] is True
    assert set(cas["axis_statuses"]) == {
        "wolfram_xact", "sympy", "sage_singular", "lean", "rocq"
    }
    assert all(v == "PASS" for v in cas["axis_statuses"].values())
    assert cas["kernel_independent_lineages"] == ["lean", "rocq"]


def test_historical_card_preserves_pre_ma04_cas_label() -> None:
    cas = _card()["result"]["cas_status"]
    assert cas["aggregate"] == "CAS_5AXIS_PASS"
    assert _card()["terminal"] == "FRAME_TYPE_SYSTEM_CAS_5AXIS_PASS"


def test_current_check_blocks_without_live_parent_execution() -> None:
    proc = subprocess.run(
        [sys.executable, "-B", str(RUNNER), "--check"],
        cwd=REPO, capture_output=True, text=True, timeout=300,
        env={"PYTHONHASHSEED": "0", "PATH": "/usr/bin:/bin"},
    )
    assert proc.returncode == 1, proc.stdout + proc.stderr
    payload = json.loads(proc.stdout.strip().splitlines()[-1])
    assert payload["ok"] is False
    assert payload["terminal"] == "BLOCKED_FRAME_TYPE_GATE_FAILURE"


def test_write_refuses_to_overwrite_historical_card() -> None:
    before = hashlib.sha256(CARD.read_bytes()).hexdigest()
    proc = subprocess.run(
        [sys.executable, "-B", str(RUNNER), "--write"],
        cwd=REPO, capture_output=True, text=True, timeout=300,
    )
    assert proc.returncode == 2
    assert "refusing to overwrite" in proc.stderr
    assert hashlib.sha256(CARD.read_bytes()).hexdigest() == before
