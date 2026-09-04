from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
BASE = ROOT / "docs" / "research_reports" / "verifiers" / "r4a1nf"
CONTRACT = BASE / "CAS_CONTRACT_R4A1NF_DOMAIN.json"
RUN_SPEC = BASE / "CAS_RUN_SPEC_R4A1NF_DOMAIN.json"
SYMPY_AXIS = BASE / "cas" / "axes" / "sympy" / "axis_program.py"
LEAN_AXIS = BASE / "cas" / "axes" / "lean" / "axis_program"
LEAN_MODULE = ROOT / "formal_mathlib" / "Egs3V8Mathlib" / "ReportAConvention.lean"
LEAN_ROOT = ROOT / "formal_mathlib" / "Egs3V8Mathlib.lean"
FORMAL_WORKFLOW = ROOT / ".github" / "workflows" / "report-a-formal-verifiers.yml"
PLAN = (
    ROOT
    / "docs"
    / "codex_handoff"
    / "htt_tensorized_report_first_20260903"
    / "R4A1NF_MULTI_CAS_VERIFICATION_PLAN.yaml"
)

OBLIGATIONS = {
    "photon_null_decomposition",
    "observer_measured_photon_energy",
    "boosted_observer_unit_timelike",
    "regularized_error_envelope_positive_definite",
}


def load_json(path: Path) -> dict:
    value = json.loads(path.read_text(encoding="utf-8"))
    assert isinstance(value, dict)
    return value


def test_r4a1v0_uses_a_canonical_r2_cas_contract_and_run_spec():
    contract = load_json(CONTRACT)
    run_spec = load_json(RUN_SPEC)

    assert contract["schema_version"] == 2
    assert contract["risk_tier"] == "R2"
    assert contract["required_axes"] == ["sympy", "lean"]
    assert contract["identity"]["contract_id"] == "CAS-R4A1NF-DOMAIN-R2"
    assert contract["identity"]["claim_ceiling"] == "SUPPORTING_DOMAIN_LEMMAS_ONLY"
    assert set(contract["identity"]["claim_ids"]) == OBLIGATIONS
    assert set(contract["target"]["exact_test_obligations"]) == OBLIGATIONS
    assert contract["exceptions_adjudication"]["preregistered_exceptions"] == []

    axes = run_spec["axes"]
    assert run_spec["schema_version"] == 1
    assert set(axes) == {"sympy", "lean"}
    assert axes["sympy"]["cwd"] == "."
    assert axes["lean"]["cwd"] == "."
    assert axes["sympy"]["argv"] != axes["lean"]["argv"]
    assert axes["sympy"]["argv"][-1].endswith("cas/axes/sympy/axis_program.py")
    assert axes["lean"]["argv"][-1].endswith("cas/axes/lean/axis_program")


def test_r4a1v0_axis_programs_match_the_runner_json_and_formal_scope():
    sympy_text = SYMPY_AXIS.read_text(encoding="utf-8")
    lean_axis_text = LEAN_AXIS.read_text(encoding="utf-8")
    lean_text = LEAN_MODULE.read_text(encoding="utf-8")
    lean_root_text = LEAN_ROOT.read_text(encoding="utf-8")

    for obligation in OBLIGATIONS:
        assert obligation in sympy_text
        assert obligation in lean_axis_text
    assert '"checks"' in sympy_text
    assert '"domain_assumption_diff"' in sympy_text
    assert '"counterexample"' in sympy_text
    assert "sp.ask" not in sympy_text

    assert "theorem regularized_error_envelope_posDef" in lean_text
    assert "Matrix.PosSemidef" in lean_text
    assert "Matrix.PosDef" in lean_text
    assert "lambdaReg ^ 2" in lean_text
    assert "sorry" not in lean_text
    assert "native_decide" not in lean_text
    assert "import Egs3V8Mathlib.ReportAConvention" in lean_root_text

    assert "formal_mathlib" in lean_axis_text
    assert "lake env lean" in lean_axis_text
    assert "-DwarningAsError=true" in lean_axis_text
    assert "R4A1NFConvention.lean" not in lean_axis_text


def test_r4a1v0_formal_workflow_executes_the_parent_owned_cas_gate():
    text = FORMAL_WORKFLOW.read_text(encoding="utf-8")
    assert ".agent-harness/scripts/cas_gate.py run-adjudicate" in text
    assert "CAS_CONTRACT_R4A1NF_DOMAIN.json" in text
    assert "CAS_RUN_SPEC_R4A1NF_DOMAIN.json" in text
    assert "CAS_ADJUDICATION_R4A1NF_DOMAIN.json" in text
    assert "actions/upload-artifact" in text
    assert "sympy==1.14.0" in text
    assert "mpmath==1.3.0" in text


def test_r4a1v0_plan_separates_required_and_supplemental_axes():
    text = PLAN.read_text(encoding="utf-8")
    assert "CAS-R4A1NF-DOMAIN-R2" in text
    assert "required_axes" in text
    assert "sympy" in text
    assert "lean" in text
    assert "supplemental" in text
    assert "gnu_octave" in text
    assert "sagemath" in text
    assert "singular" in text
    assert "Wolfram" in text or "wolfram" in text
