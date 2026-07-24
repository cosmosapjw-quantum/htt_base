"""PR-190 physical-attainability negative-result gates."""

from __future__ import annotations

import hashlib
import json
import os
import subprocess
import sys
from fractions import Fraction as Fr
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
for entry in (str(REPO / "htt"), str(REPO / "htt" / "src")):
    if entry not in sys.path:
        sys.path.insert(0, entry)

from common.pr190_physical_attainability import (  # noqa: E402
    LOWER_X,
    UPPER_X,
    component_linf_gap,
    develop_dust_witness,
    endpoint_substitution_analysis,
    shear_only_vector,
)
from common.revival_joint_comparator import component_vector_exact  # noqa: E402
from scripts.codex_harness import (  # noqa: E402
    run_pr190_physical_attainability as runner,
)

CARD = REPO / "docs/generated/pr190_result_card.json"
SPEC = REPO / "docs/research_program/strengthening/pr190_spec.yaml"
CONTRACT = (
    REPO
    / "docs/generated/pr190_cas/CAS_CONTRACT_PR190_SHEAR_SUBSTITUTION.json"
)
ADJUDICATION = REPO / "docs/generated/pr190_cas/adjudication.json"
RUNNER = REPO / "scripts/codex_harness/run_pr190_physical_attainability.py"


def _card() -> dict:
    return json.loads(CARD.read_text(encoding="utf-8"))


def test_spec_metadata_and_blocked_terminal() -> None:
    card = _card()
    assert card["metadata"]["spec_sha256"] == hashlib.sha256(
        SPEC.read_bytes()
    ).hexdigest()
    assert card["metadata"]["owner"] == "BASS"
    assert card["metadata"]["public_use"] is False
    assert card["metadata"]["independence_gate"] == "OPEN"
    assert card["terminal"] == "BLOCKED_COMPONENT_ENDPOINT_NOT_ATTAINED"
    assert card["result"]["gate_evaluation"]["conjunctive_pr190_pass"] is False


def test_scalar_matches_do_not_realize_component_endpoints() -> None:
    endpoints = endpoint_substitution_analysis()
    assert endpoints["lower"]["scalar_gap"] == "0"
    assert endpoints["upper"]["scalar_gap"] == "0"
    assert endpoints["lower"]["component_linf_gap"] == "1/50"
    assert endpoints["upper"]["component_linf_gap"] == "3/100"
    assert endpoints["full_endpoint_vectors_realized"] is False


def test_shear_only_mutations_cannot_remove_tilt_gap() -> None:
    lower = component_vector_exact(Fr(0), Fr(-2, 3))
    upper = component_vector_exact(Fr(1), Fr(0))
    for sigma2 in (Fr(0), LOWER_X, Fr(9, 100), UPPER_X, Fr(1, 5)):
        candidate = shear_only_vector(sigma2)
        assert component_linf_gap(lower, candidate) >= Fr(1, 50)
        assert component_linf_gap(upper, candidate) >= Fr(3, 100)


def test_five_efold_dust_developments_preserve_constraints() -> None:
    for sigma2 in (float(LOWER_X), 0.09, float(UPPER_X)):
        result = develop_dust_witness(sigma2)
        assert result.success
        assert result.interval_efolds >= 5.0
        assert result.max_normalized_gauss_residual < 1.0e-10
        assert result.max_sigma2_exact_error < 1.0e-11
        assert result.max_hubble_relative_error < 1.0e-11
        assert result.min_density >= 0.0
        assert result.min_hubble > 0.0
    grid = _card()["result"]["bianchi_i_dust_scalar_match_grid"]
    assert grid["grid_size"] == 100
    assert grid["all_developments_succeeded"] is True


def test_stored_parent_observed_cas_is_diagnostic_only() -> None:
    current_cas = runner._cas_status()
    adjudication = json.loads(ADJUDICATION.read_text(encoding="utf-8"))
    contract = json.loads(CONTRACT.read_text(encoding="utf-8"))
    contract_sha = hashlib.sha256(CONTRACT.read_bytes()).hexdigest()
    assert current_cas["aggregate"] == "CAS_BLOCKED"
    assert current_cas["historical_aggregate"] == "CAS_5AXIS_PASS"
    assert current_cas["stored_cas_diagnostic_only"] is True
    assert current_cas["claim_promotion_cas_eligible"] is False
    assert current_cas["verification_state"] == "STORED_DIAGNOSTIC_ONLY"
    assert current_cas["evidence_origin"] == "stored_adjudication_json"
    assert current_cas["contract_sha256"] == contract_sha
    assert adjudication["contract_sha256"] == contract_sha
    assert set(adjudication["axis_statuses"]) == {
        "wolfram_xact",
        "sympy",
        "sage_singular",
        "lean",
        "rocq",
    }
    assert all(
        status == "PASS" for status in adjudication["axis_statuses"].values()
    )
    for source in contract["identity"]["source_input_hashes"]:
        assert hashlib.sha256((REPO / source["path"]).read_bytes()).hexdigest() == (
            source["sha256"]
        )
    assert current_cas["scientific_role"] == (
        "exact_dust_identities_and_component_mismatch_only"
    )


def test_historical_card_preserves_parent_observed_result() -> None:
    card = _card()
    assert card["result"]["cas_status"]["aggregate"] == "CAS_5AXIS_PASS"
    assert card["terminal"] == "BLOCKED_COMPONENT_ENDPOINT_NOT_ATTAINED"


def test_current_check_blocks_without_live_parent_execution() -> None:
    env = os.environ.copy()
    env["PYTHONHASHSEED"] = "0"
    env["OPENBLAS_NUM_THREADS"] = "4"
    completed = subprocess.run(
        [sys.executable, "-B", str(RUNNER), "--check"],
        cwd=REPO,
        capture_output=True,
        text=True,
        timeout=300,
        env=env,
        check=False,
    )
    assert completed.returncode == 1, completed.stdout + completed.stderr
    result = json.loads(completed.stdout.strip().splitlines()[-1])
    assert result["ok"] is False
    assert result["terminal"] == "BLOCKED_PR190_VALIDATION_FAILURE"


def test_write_refuses_to_overwrite_historical_card() -> None:
    before = hashlib.sha256(CARD.read_bytes()).hexdigest()
    completed = subprocess.run(
        [sys.executable, "-B", str(RUNNER), "--write"],
        cwd=REPO,
        capture_output=True,
        text=True,
        timeout=300,
        check=False,
    )
    assert completed.returncode == 2
    assert "refusing to overwrite" in completed.stderr
    assert hashlib.sha256(CARD.read_bytes()).hexdigest() == before
