"""PR-186 gates: W^2 convention theorem + active-source repair (R3-CAS)."""

from __future__ import annotations

import hashlib
import json
import subprocess
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

CARD = REPO / "docs/generated/pr186_result_card.json"
SPEC = REPO / "docs/research_program/strengthening/pr186_spec.yaml"


def _card() -> dict:
    return json.loads(CARD.read_text())


def test_spec_bound_and_terminal() -> None:
    card = _card()
    assert card["metadata"]["spec_sha256"] == hashlib.sha256(
        SPEC.read_bytes()
    ).hexdigest()
    assert card["metadata"]["public_use"] is False
    assert card["metadata"]["independence_gate"] == "OPEN"
    assert card["terminal"] == "W2_CONVENTION_REPAIRED_CAS_5AXIS_PASS_SOURCES_CLEAN"


def test_five_axis_cas_pass_contract_bound() -> None:
    cas = _card()["cas_status"]
    assert cas["aggregate"] == "CAS_5AXIS_PASS"
    assert cas["contract_hash_matches_adjudication"] is True
    assert set(cas["axis_statuses"]) == {
        "wolfram_xact", "sympy", "sage_singular", "lean", "rocq"
    }
    assert all(v == "PASS" for v in cas["axis_statuses"].values())
    # Lean and Rocq are the two kernel-independent proof-assistant lineages
    assert cas["kernel_independent_lineages"] == ["lean", "rocq"]
    # the sealed adjudication agrees
    adj = json.loads(
        (REPO / "docs/generated/pr186_cas/adjudication.json").read_text()
    )
    assert adj["aggregate_status"] == "CAS_5AXIS_PASS"
    assert adj["required_axes"] == [
        "wolfram_xact", "sympy", "sage_singular", "lean", "rocq"
    ]


def test_tensor_vector_identity() -> None:
    r = vorticity_tensor_vector_identity(100_000)
    assert r["ok"] and r["max_abs_error"] < 1e-12


def test_symbolic_convention_and_ceiling() -> None:
    s = ceiling_conversion_symbolic()
    assert s["tensor_vector_forms_equal"] is True
    assert s["W2_registered"] == "wa2/(3*H**2)"
    assert s["wrong_over_right_ratio"] == "3"
    assert s["ceiling_is_three_halves_Bsq"] is True


def test_active_sources_clean() -> None:
    scan = scan_active_sources(REPO)
    assert scan["clean"], scan["active_bad_pattern_hits"][:5]
    assert _card()["active_source_scan"]["n_hits"] == 0


def test_v10_report_display_corrected_and_anchor_invariant() -> None:
    tex = (REPO / "external_audit_research_report_20260721_v10/"
           "external_audit_research_report_v10.tex").read_text()
    assert r"\frac{\omega_{ab}\omega^{ab}}{6H^2} = \frac{\omega_a\omega^a}{3H^2}" in tex
    delta = _card()["pre_post_delta"]
    assert delta["frozen_anchor_byte_identical"] is True
    seal = json.loads(
        (REPO / "docs/generated/mes_geodesic_refreeze_seal.json").read_text()
    )
    assert seal["refrozen_anchor"]["W2_max"] == 3.3789222980376e-13


def test_two_independent_lineages() -> None:
    assert _card()["derivation_lineages"]["two_independent_lineages_agree"] is True


def test_card_byte_stable_under_check() -> None:
    proc = subprocess.run(
        [str(REPO / "venv/bin/python"), "-B",
         str(REPO / "scripts/codex_harness/run_pr186_w2_convention.py"), "--check"],
        cwd=REPO, capture_output=True, text=True, timeout=600,
        env={"PYTHONHASHSEED": "0", "PATH": "/usr/bin:/bin"},
    )
    assert proc.returncode == 0, proc.stdout + proc.stderr
    payload = json.loads(proc.stdout.strip().splitlines()[-1])
    assert payload["ok"] is True
