"""PR-175 card gates: cross-engine Bianchi invariant mechanics.

Backlog DoD: (1) preregistered four-axis CAS contract for the invariant
identities and external-anchor comparison; (2) invariant mechanics and
anchor agreement never rank or identify a Bianchi family. Kill: any CAS
axis or anchor mismatch; any atlas rank or family label.
"""

from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from fractions import Fraction
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "htt" / "src"))

from common.pr175_invariant_oracle import (  # noqa: E402
    CANONICAL_TYPES,
    ENGINE_B_TOL,
    anchor_ricci_scalar,
    engine_a_ricci_scalar,
    engine_b_ricci_scalar,
)

SPEC = REPO / "docs/research_program/long_horizon_rescue/pr175_spec.yaml"
CONTRACT = REPO / "docs/generated/pr175_cas/CAS_CONTRACT_PR175_INVARIANT_V2.json"
ADJUDICATION = REPO / "docs/generated/pr175_cas_adjudication.json"
CARD = REPO / "docs/generated/pr175_result_card.json"
AXES = ("sympy", "sage_singular", "wolfram_xact", "lean")


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _card() -> dict:
    return json.loads(CARD.read_text())


def test_spec_frozen_and_card_binds_hashes() -> None:
    card = _card()
    assert card["metadata"]["spec_sha256"] == _sha(SPEC)
    assert card["metadata"]["contract_sha256"] == _sha(CONTRACT)
    assert "frozen_before_result: true" in SPEC.read_text()
    assert card["metadata"]["scientific_artifact_mode"] == "hypothesis_only"
    assert card["metadata"]["public_use"] is False
    assert card["metadata"]["claim_level"]["level"] == "C2"


def test_textbook_sanity_points_exact() -> None:
    """Round S^3 (IX) and unit H^3 (V) ground the normalization."""
    assert engine_a_ricci_scalar("IX") == Fraction(3, 2)
    assert engine_a_ricci_scalar("V") == Fraction(-6)


def test_engine_a_matches_anchor_on_all_eleven_types() -> None:
    for name in CANONICAL_TYPES:
        assert engine_a_ricci_scalar(name) == anchor_ricci_scalar(name), name


def test_engine_b_agrees_within_preregistered_tolerance() -> None:
    for name in ("IX", "V", "VII_h", "II"):
        exact = float(engine_a_ricci_scalar(name))
        numeric = engine_b_ricci_scalar(name)
        assert abs(numeric - exact) <= ENGINE_B_TOL, name


def test_engine_b_point_independence() -> None:
    """Homogeneity: the numeric scalar must not depend on the point."""
    for name in ("IX", "VI_h"):
        first = engine_b_ricci_scalar(name, point=(0.3, -0.7, 0.51))
        second = engine_b_ricci_scalar(name, point=(-0.2, 0.4, 0.9))
        assert abs(first - second) <= 1.0e-5, name


def test_four_axis_adjudication_pass_and_bound() -> None:
    adjudication = json.loads(ADJUDICATION.read_text())
    assert adjudication["contract_sha256"] == _sha(CONTRACT)
    assert adjudication["aggregate_status"] == "CAS_4AXIS_PASS"
    assert all(v == "PASS" for v in adjudication["axis_statuses"].values())
    card = _card()
    assert card["terminal"] == (
        "INVARIANT_ORACLE_CAS_4AXIS_PASS_ANCHOR_CONSISTENT"
    )
    assert card["cas"]["adjudication_sha256"] == _sha(ADJUDICATION)


def test_envelopes_bound_uniform_and_value_pinned() -> None:
    contract = json.loads(CONTRACT.read_text())
    obligations = set(contract["target"]["exact_test_obligations"])
    expected = contract["target"]["expected_exact_values"]
    contract_sha = _sha(CONTRACT)
    for axis in AXES:
        env = json.loads(
            (REPO / f"docs/generated/pr175_cas/axis_result_{axis}.json").read_text()
        )
        assert env["contract_sha256"] == contract_sha, axis
        assert env["status"] == "PASS", axis
        assert set(env["checks"]) == obligations, axis
        assert all(env["checks"].values()), axis
        assert env["sibling_results_read"] == [], axis
        for key, value in expected.items():
            assert env["computed"].get(key) == value, f"{axis}:{key}"


def test_contract_source_pins_match_live_files() -> None:
    contract = json.loads(CONTRACT.read_text())
    for axis_block in contract["axes"].values():
        for ref in axis_block["sources"]:
            assert _sha(REPO / ref["path"]) == ref["sha256"], ref["path"]


def test_mutated_representative_is_killed() -> None:
    """Perturbing a structure constant must break the anchor identity."""
    import dataclasses  # noqa: F401 - explicit std-lib usage marker
    from common import pr175_invariant_oracle as oracle

    original = oracle.CANONICAL_TYPES["IX"]
    try:
        oracle.CANONICAL_TYPES["IX"] = {"n": (1, 1, 2), "a": 0}
        exact = oracle.engine_a_ricci_scalar("IX")
        anchor = Fraction(3, 2)  # the registered IX anchor value
        assert exact != anchor
    finally:
        oracle.CANONICAL_TYPES["IX"] = original


def test_wrong_anchor_formula_is_killed() -> None:
    """A 3a^2 (instead of 6a^2) anchor variant must disagree for class B."""
    for name in ("V", "IV", "III"):
        entry = CANONICAL_TYPES[name]
        n1, n2, n3 = (Fraction(v) for v in entry["n"])
        a = Fraction(entry["a"])
        wrong = (
            -Fraction(1, 2) * (n1**2 + n2**2 + n3**2)
            + (n1 * n2 + n2 * n3 + n3 * n1)
            - 3 * a**2
        )
        assert wrong != engine_a_ricci_scalar(name), name


def test_no_family_ranking_language_or_consumer() -> None:
    for path in (
        REPO / "htt/src/common/pr175_invariant_oracle.py",
        REPO / "docs/generated/pr175_result_card.json",
    ):
        text = path.read_text()
        assert "never rank" in text or "no Bianchi family identification" in text
    consumers = []
    for root in (REPO / "htt", REPO / "scripts"):
        for path in sorted(root.rglob("*.py")):
            rel = path.relative_to(REPO).as_posix()
            if "tests/" in rel or "pr175" in rel:
                continue
            if "pr175_invariant_oracle" in path.read_text(errors="replace"):
                consumers.append(rel)
    assert consumers == []


def test_status_not_pending_and_lane_is_hypothesis_only() -> None:
    status = (REPO / "docs/codex_handoff/pr_status.yaml").read_text()
    pending_block = status.split("pending:")[1].split("dormant_external:")[0]
    assert "PR-175" not in pending_block
    assert "PR-175: hypothesis_only" in status


def test_result_card_is_byte_current_under_read_only_check() -> None:
    proc = subprocess.run(
        [
            str(REPO / "venv/bin/python"),
            "-B",
            str(REPO / "scripts/codex_harness/run_pr175_invariant_card.py"),
            "--check",
        ],
        cwd=REPO,
        capture_output=True,
        text=True,
        timeout=600,
    )
    assert proc.returncode == 0, proc.stdout + proc.stderr
    payload = json.loads(proc.stdout.strip().splitlines()[-1])
    assert payload["ok"] is True and payload["read_only"] is True